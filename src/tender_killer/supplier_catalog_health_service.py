from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any
from urllib.parse import quote_plus

import httpx
from bs4 import BeautifulSoup

from tender_killer import supplier_browser_fetcher
from tender_killer.supplier_catalog_presets import SUPPLIER_CATALOG_PRESETS


CatalogHealthFetchResult = tuple[int, str]
CatalogHealthFetcher = Callable[[str, float], CatalogHealthFetchResult]

CATALOG_SAMPLE_QUERIES = {
    "officemag": "office paper a4",
    "komus": "office paper a4",
    "petrovich": "cement mix",
    "vseinstrumenti": "cement mix",
}


def get_supplier_catalog_health_payload(
    *,
    live: bool = False,
    timeout: float = 2.0,
    fetcher: CatalogHealthFetcher | None = None,
) -> dict[str, Any]:
    fetch = fetcher or _fetch_catalog_status
    catalogs: list[dict[str, Any]] = []
    ok = True
    for preset in SUPPLIER_CATALOG_PRESETS:
        catalog = _catalog_health_item(preset)
        if live:
            _check_catalog_live(catalog, timeout, fetch)
            if catalog["status"] != "ok":
                ok = False
        catalogs.append(catalog)
    return {
        "ok": ok,
        "live": live,
        "catalogs": catalogs,
    }


def _catalog_health_item(preset: dict[str, Any]) -> dict[str, Any]:
    provider = str(preset["provider"])
    sample_query = CATALOG_SAMPLE_QUERIES.get(provider.casefold(), "office paper a4")
    sample_url = str(preset["url_template"]).format(query=quote_plus(sample_query))
    return {
        "preset_id": str(preset["preset_id"]),
        "label": str(preset["label"]),
        "provider": provider,
        "sample_query": sample_query,
        "sample_url": sample_url,
        "status": "configured",
        "http_status": None,
        "error_kind": "",
        "error": "",
        "body_preview": "",
        "access_mode": "configured",
    }


def _check_catalog_live(catalog: dict[str, Any], timeout: float, fetch: CatalogHealthFetcher) -> None:
    try:
        status, _body = fetch(catalog["sample_url"], timeout)
    except Exception as exc:  # noqa: BLE001 - health diagnostics should preserve provider failures.
        if _try_browser_catalog_health(catalog):
            return
        catalog["status"] = "error"
        catalog["http_status"] = None
        catalog["error_kind"] = "network_error"
        catalog["error"] = str(exc)
        catalog["body_preview"] = ""
        catalog["access_mode"] = "http"
        return
    catalog["http_status"] = int(status)
    if 200 <= int(status) < 400:
        if not _catalog_body_has_parseable_content(str(catalog.get("provider") or ""), _body):
            catalog["status"] = "error"
            catalog["error_kind"] = "access_blocked"
            catalog["error"] = (
                f"HTTP {status} did not contain parseable {catalog.get('label') or catalog.get('provider')} "
                "product cards"
            )
            catalog["body_preview"] = response_body_preview(_body)
            catalog["access_mode"] = "http"
            return
        catalog["status"] = "ok"
        catalog["error_kind"] = ""
        catalog["error"] = ""
        catalog["body_preview"] = ""
        catalog["access_mode"] = "http"
        return
    if http_error_kind(int(status)) == "access_blocked" and _try_browser_catalog_health(catalog):
        return
    catalog["status"] = "error"
    catalog["error_kind"] = http_error_kind(int(status))
    catalog["error"] = f"expected HTTP 2xx/3xx, got {status}"
    catalog["body_preview"] = response_body_preview(_body)
    catalog["access_mode"] = "http"


def _try_browser_catalog_health(catalog: dict[str, Any]) -> bool:
    provider = str(catalog.get("provider") or "")
    if not supplier_browser_fetcher.is_enabled_for_provider(provider):
        return False
    try:
        body = supplier_browser_fetcher.fetch_text(str(catalog["sample_url"]), provider=provider)
    except supplier_browser_fetcher.BrowserFetchError as exc:
        catalog["browser_error"] = str(exc)
        return False
    body_text = str(body or "")
    if not body_text.strip():
        catalog["browser_error"] = "browser fetch returned an empty response"
        return False
    if not _catalog_body_has_parseable_content(provider, body_text):
        catalog["status"] = "error"
        catalog["http_status"] = None
        catalog["error_kind"] = "access_blocked"
        catalog["error"] = ""
        catalog["body_preview"] = response_body_preview(body_text)
        catalog["access_mode"] = "browser"
        catalog["browser_error"] = f"browser fetch returned no parseable {catalog.get('label') or provider} product cards"
        return True
    catalog["status"] = "ok"
    catalog["http_status"] = None
    catalog["error_kind"] = ""
    catalog["error"] = ""
    catalog["body_preview"] = ""
    catalog["access_mode"] = "browser"
    return True


def _catalog_body_has_parseable_content(provider: str, body: str) -> bool:
    provider_key = provider.casefold()
    if provider_key == "officemag":
        soup = BeautifulSoup(body, "html.parser")
        return bool(
            soup.select_one(
                "li.listItem, .js-productListItem, .ProductHead__name, "
                ".Product__price, .js-productSum, a[href*='/catalog/goods/']"
            )
        )
    return bool(body.strip())


def _fetch_catalog_status(url: str, timeout: float) -> CatalogHealthFetchResult:
    response = httpx.get(
        url,
        follow_redirects=True,
        timeout=timeout,
        trust_env=False,
        headers={"User-Agent": "TenderKiller/0.1 public catalog health"},
    )
    return int(response.status_code), response.text


def http_error_kind(status: int) -> str:
    if status in {401, 403, 429, 503}:
        return "access_blocked"
    return "http_error"


def response_body_preview(body: str) -> str:
    raw_body = str(body or "")
    soup = BeautifulSoup(raw_body, "html.parser")
    for node in soup(["script", "style", "template", "noscript"]):
        node.decompose()
    text = " ".join(soup.get_text(" ").split())
    if not text:
        text = " ".join(re.sub(r"<[^>]+>", " ", raw_body).split())
    if not text or _looks_like_css_preview(text):
        return "HTML response without readable text"
    return text[:180]


def _looks_like_css_preview(text: str) -> bool:
    stripped = text.strip()
    if stripped.startswith((".", "#", "@")) and "{" in stripped[:80] and ":" in stripped[:160]:
        return True
    return bool(re.fullmatch(r"(?:[.#]?[a-zA-Z0-9_-]+\s*\{[^{}]*:[^{}]*\}\s*)+", stripped))
