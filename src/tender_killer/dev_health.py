from __future__ import annotations

import argparse
import json
from collections.abc import Callable
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

FetchResult = tuple[int, dict[str, Any]]
Fetcher = Callable[[str, float], FetchResult]
Validator = Callable[[dict[str, Any]], str]

REQUIRED_API_CAPABILITIES: tuple[str, ...] = (
    "supplier_search_prepare",
    "supplier_catalog_presets",
    "supplier_catalog_health",
    "supplier_discovery_url",
    "web_auto_search",
    "market_state_import",
    "dashboard_queues",
    "price_candidate_auto_stage",
    "price_memory_stage",
    "price_auto_apply",
    "price_discovery_run",
    "price_discovery_jobs",
)


def check_api_health(
    base_url: str,
    timeout: float = 2.0,
    fetcher: Fetcher | None = None,
) -> dict[str, Any]:
    fetch = fetcher or _fetch_json
    checks = [
        _check_endpoint(base_url, "/api/health", timeout, fetch, _health_payload_error),
        _check_endpoint(base_url, "/api/sources/status", timeout, fetch, _source_status_payload_error),
        _check_endpoint(
            base_url,
            "/api/supplier-catalogs/health",
            timeout,
            fetch,
            _supplier_catalog_health_payload_error,
        ),
    ]
    return {
        "ok": all(check["ok"] for check in checks),
        "base_url": base_url.rstrip("/"),
        "checks": checks,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tender-killer-dev-health")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--timeout", type=float, default=2.0)
    parser.add_argument("--json", action="store_true", help="Print the raw JSON result.")
    parser.add_argument("--quiet", action="store_true", help="Only use the process exit code.")
    args = parser.parse_args(argv)

    result = check_api_health(args.base_url, timeout=args.timeout)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif not args.quiet:
        _print_human_result(result)
    return 0 if result["ok"] else 1


def _check_endpoint(
    base_url: str,
    path: str,
    timeout: float,
    fetch: Fetcher,
    validator: Validator,
) -> dict[str, Any]:
    url = urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))
    try:
        status, payload = fetch(url, timeout)
    except Exception as exc:  # noqa: BLE001 - diagnostics must surface connection failures.
        return {"path": path, "ok": False, "status": None, "error": str(exc)}

    if not 200 <= status < 300:
        return {"path": path, "ok": False, "status": status, "error": f"expected HTTP 2xx, got {status}"}
    validation_error = validator(payload)
    if validation_error:
        return {"path": path, "ok": False, "status": status, "error": validation_error}
    return {"path": path, "ok": True, "status": status, "error": ""}


def _fetch_json(url: str, timeout: float) -> FetchResult:
    request = Request(url, headers={"Accept": "application/json"})
    try:
        with urlopen(request, timeout=timeout) as response:  # noqa: S310 - local dev health URL.
            status = int(response.status)
            body = response.read(65536).decode("utf-8")
    except HTTPError as exc:
        body = exc.read(65536).decode("utf-8", errors="replace")
        return int(exc.code), _json_payload(body)
    except URLError as exc:
        raise RuntimeError(str(exc.reason)) from exc
    return status, _json_payload(body)


def _json_payload(body: str) -> dict[str, Any]:
    try:
        payload = json.loads(body or "{}")
    except json.JSONDecodeError:
        return {"raw": body[:200]}
    return payload if isinstance(payload, dict) else {"raw": payload}


def _health_payload_error(payload: dict[str, Any]) -> str:
    if payload.get("ok") is not True:
        return "expected ok=true"
    capabilities = payload.get("capabilities")
    capability_set = {str(item) for item in capabilities} if isinstance(capabilities, list) else set()
    missing = [capability for capability in REQUIRED_API_CAPABILITIES if capability not in capability_set]
    if missing:
        return "missing API capabilities: " + ", ".join(missing)
    return ""


def _source_status_payload_error(payload: dict[str, Any]) -> str:
    if not isinstance(payload.get("sources"), list):
        return "expected sources list"
    return ""


def _supplier_catalog_health_payload_error(payload: dict[str, Any]) -> str:
    if not isinstance(payload.get("catalogs"), list):
        return "expected catalogs list"
    if not isinstance(payload.get("ok"), bool):
        return "expected ok boolean"
    return ""


def _print_human_result(result: dict[str, Any]) -> None:
    status = "ok" if result["ok"] else "failed"
    print(f"Tender Killer API health: {status} ({result['base_url']})")
    for check in result["checks"]:
        marker = "OK" if check["ok"] else "FAIL"
        detail = f" HTTP {check['status']}" if check["status"] is not None else ""
        error = f" - {check['error']}" if check["error"] else ""
        print(f"- {marker} {check['path']}{detail}{error}")


if __name__ == "__main__":
    raise SystemExit(main())
