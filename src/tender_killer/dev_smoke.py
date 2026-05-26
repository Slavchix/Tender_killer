from __future__ import annotations

import argparse
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from tender_killer.dev_health import check_api_health
from tender_killer.encoding_guard import find_mojibake

FetchTextResult = tuple[int, str]
TextFetcher = Callable[[str, float], FetchTextResult]

REQUIRED_UI_TEXT = ("Панель закупок", "На странице", "Закупок на странице")


def check_dev_site(
    api_base_url: str = "http://127.0.0.1:8000",
    web_base_url: str = "http://127.0.0.1:5173",
    timeout: float = 2.0,
    app_source_path: str | Path = Path("web/src/App.jsx"),
    fetcher: TextFetcher | None = None,
) -> dict[str, Any]:
    fetch = fetcher or _fetch_text
    checks = [
        _api_direct_check(api_base_url, timeout, fetch),
        _frontend_html_check(web_base_url, timeout, fetch),
        _json_endpoint_check(web_base_url, "/api/health", timeout, fetch, lambda payload: payload.get("ok") is True),
        _json_endpoint_check(
            web_base_url,
            "/api/sources/status",
            timeout,
            fetch,
            lambda payload: isinstance(payload.get("sources"), list),
            name="vite_proxy_sources",
        ),
        _json_endpoint_check(
            web_base_url,
            "/api/supplier-catalogs/health",
            timeout,
            fetch,
            lambda payload: payload.get("ok") is True and isinstance(payload.get("catalogs"), list),
            name="vite_proxy_supplier_catalogs",
        ),
        _ui_text_check(Path(app_source_path)),
    ]
    checks[2]["name"] = "vite_proxy_health"
    return {
        "ok": all(check["ok"] for check in checks),
        "api_base_url": api_base_url.rstrip("/"),
        "web_base_url": web_base_url.rstrip("/"),
        "checks": checks,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tender-killer-dev-smoke")
    parser.add_argument("--api-base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--web-base-url", default="http://127.0.0.1:5173")
    parser.add_argument("--timeout", type=float, default=2.0)
    parser.add_argument("--app-source", type=Path, default=Path("web/src/App.jsx"))
    parser.add_argument("--json", action="store_true", help="Print the raw JSON result.")
    args = parser.parse_args(argv)

    result = check_dev_site(
        api_base_url=args.api_base_url,
        web_base_url=args.web_base_url,
        timeout=args.timeout,
        app_source_path=args.app_source,
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        _print_human_result(result)
    return 0 if result["ok"] else 1


def _api_direct_check(base_url: str, timeout: float, fetch: TextFetcher) -> dict[str, Any]:
    def json_fetcher(url: str, request_timeout: float) -> tuple[int, dict[str, Any]]:
        status, body = fetch(url, request_timeout)
        return status, _json_payload(body)

    result = check_api_health(base_url, timeout=timeout, fetcher=json_fetcher)
    errors = [
        f"{check['path']}: {check['error'] or check['status']}"
        for check in result["checks"]
        if not check["ok"]
    ]
    return {
        "name": "api_direct",
        "ok": result["ok"],
        "status": 200 if result["ok"] else None,
        "error": "; ".join(errors),
    }


def _frontend_html_check(base_url: str, timeout: float, fetch: TextFetcher) -> dict[str, Any]:
    url = base_url.rstrip("/") + "/"
    try:
        status, body = fetch(url, timeout)
    except Exception as exc:  # noqa: BLE001 - smoke diagnostics should report connection failures.
        return {"name": "frontend_html", "ok": False, "status": None, "error": str(exc)}
    if not 200 <= status < 300:
        return {"name": "frontend_html", "ok": False, "status": status, "error": f"expected HTTP 2xx, got {status}"}
    if 'id="root"' not in body:
        return {"name": "frontend_html", "ok": False, "status": status, "error": "missing Vite root element"}
    return {"name": "frontend_html", "ok": True, "status": status, "error": ""}


def _json_endpoint_check(
    base_url: str,
    path: str,
    timeout: float,
    fetch: TextFetcher,
    validator: Callable[[dict[str, Any]], bool],
    name: str | None = None,
) -> dict[str, Any]:
    url = urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))
    check_name = name or path.strip("/").replace("/", "_")
    try:
        status, body = fetch(url, timeout)
    except Exception as exc:  # noqa: BLE001 - smoke diagnostics should report connection failures.
        return {"name": check_name, "ok": False, "status": None, "error": str(exc)}
    if not 200 <= status < 300:
        return {"name": check_name, "ok": False, "status": status, "error": f"expected HTTP 2xx, got {status}"}
    payload = _json_payload(body)
    if not validator(payload):
        return {"name": check_name, "ok": False, "status": status, "error": "unexpected JSON payload shape"}
    return {"name": check_name, "ok": True, "status": status, "error": ""}


def _ui_text_check(app_source_path: Path) -> dict[str, Any]:
    try:
        source = app_source_path.read_text(encoding="utf-8")
    except OSError as exc:
        return {"name": "ui_text", "ok": False, "status": None, "error": str(exc)}
    missing = [text for text in REQUIRED_UI_TEXT if text not in source]
    mojibake = find_mojibake(source, app_source_path)
    if missing or mojibake:
        parts = []
        if missing:
            parts.append("missing: " + ", ".join(missing))
        if mojibake:
            parts.append(
                "mojibake present: "
                + ", ".join(f"{finding.path}:{finding.line}:{finding.column}" for finding in mojibake[:5])
            )
        return {"name": "ui_text", "ok": False, "status": None, "error": "; ".join(parts)}
    return {"name": "ui_text", "ok": True, "status": None, "error": ""}


def _fetch_text(url: str, timeout: float) -> FetchTextResult:
    request = Request(url, headers={"Accept": "application/json,text/html,*/*"})
    try:
        with urlopen(request, timeout=timeout) as response:  # noqa: S310 - local dev smoke URL.
            status = int(response.status)
            body = response.read(1048576).decode("utf-8", errors="replace")
            return status, body
    except HTTPError as exc:
        return int(exc.code), exc.read(65536).decode("utf-8", errors="replace")
    except URLError as exc:
        raise RuntimeError(str(exc.reason)) from exc


def _json_payload(body: str) -> dict[str, Any]:
    try:
        payload = json.loads(body or "{}")
    except json.JSONDecodeError:
        return {"raw": body[:200]}
    return payload if isinstance(payload, dict) else {"raw": payload}


def _print_human_result(result: dict[str, Any]) -> None:
    status = "ok" if result["ok"] else "failed"
    print(f"Tender Killer dev smoke: {status}")
    print(f"- API: {result['api_base_url']}")
    print(f"- Web: {result['web_base_url']}")
    for check in result["checks"]:
        marker = "OK" if check["ok"] else "FAIL"
        detail = f" HTTP {check['status']}" if check["status"] is not None else ""
        error = f" - {check['error']}" if check["error"] else ""
        print(f"- {marker} {check['name']}{detail}{error}")


if __name__ == "__main__":
    raise SystemExit(main())
