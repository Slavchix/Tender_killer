from __future__ import annotations

import json
import re
import sqlite3
from collections.abc import Callable
from datetime import UTC
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

import httpx
from bs4 import BeautifulSoup

from tender_killer import supplier_browser_fetcher
from tender_killer.schema import initialize_schema
from tender_killer.supplier_catalog_presets import SUPPLIER_CATALOG_PRESETS
from tender_killer.supplier_provider_policy import ACTION_BROWSER_FETCH
from tender_killer.supplier_provider_policy import ACTION_PUBLIC_SEARCH_FETCH
from tender_killer.supplier_provider_policy import SMALL_TENDER_ACTIVE_DISCOVERY_LIMIT
from tender_killer.supplier_provider_policy import get_supplier_provider_policy
from tender_killer.supplier_provider_policy import supplier_fetch_decision


CatalogHealthFetchResult = tuple[int, str]
CatalogHealthFetcher = Callable[[str, float], CatalogHealthFetchResult]

CATALOG_SAMPLE_QUERIES = {
    "officemag": "office paper a4",
    "komus": "office paper a4",
    "petrovich": "cement mix",
    "vseinstrumenti": "\u0441\u0430\u043c\u043e\u0440\u0435\u0437\u044b 4,2x19",
    "lemanapro": "\u0446\u0435\u043c\u0435\u043d\u0442 50 \u043a\u0433",
}
SUPPLIER_CATALOG_HEALTH_CACHE_KEY = "supplier_catalog_health.last_live"
CATALOG_CONNECTION_CONFIGURED = "configured"
CATALOG_CONNECTION_REACHABLE = "reachable"
CATALOG_CONNECTION_BLOCKED = "blocked"
CATALOG_CONNECTION_CAPTCHA = "captcha"
CATALOG_CONNECTION_NO_CARDS = "no_cards"
CATALOG_CONNECTION_PARSER_BROKEN = "parser_broken"
CATALOG_CONNECTION_TIMEOUT = "timeout"
CATALOG_CONNECTION_NETWORK_ERROR = "network_error"
CATALOG_CONNECTION_MANUAL_ONLY = "manual_only"
CATALOG_SEARCH_MODE_ACTIVE_SMALL = "active_small_search"
CATALOG_SEARCH_MODE_MANUAL_ONLY = "manual_only"


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
            if catalog.get("small_tender_active_search"):
                _check_catalog_live(catalog, timeout, fetch)
            else:
                _mark_catalog_manual_only(catalog)
            if catalog.get("small_tender_active_search") and catalog["status"] != "ok":
                ok = False
        catalogs.append(catalog)
    return {
        "ok": ok,
        "live": live,
        "catalogs": catalogs,
    }


def get_cached_supplier_catalog_health_payload(
    database_path: str | Path,
    *,
    live: bool = False,
    timeout: float = 2.0,
    fetcher: CatalogHealthFetcher | None = None,
    now_factory: Callable[[], str] | None = None,
) -> dict[str, Any]:
    if live:
        payload = get_supplier_catalog_health_payload(live=True, timeout=timeout, fetcher=fetcher)
        payload["checked_at"] = _now_iso(now_factory)
        payload["cached"] = False
        _write_cached_catalog_health(database_path, payload)
        return payload

    cached = _read_cached_catalog_health(database_path)
    if cached is not None:
        return {**cached, "live": False, "cached": True}

    payload = get_supplier_catalog_health_payload(live=False, timeout=timeout, fetcher=fetcher)
    payload["checked_at"] = None
    payload["cached"] = False
    return payload


def _catalog_health_item(preset: dict[str, Any]) -> dict[str, Any]:
    provider = str(preset["provider"])
    sample_query = CATALOG_SAMPLE_QUERIES.get(provider.casefold(), "office paper a4")
    sample_url = str(preset["url_template"]).format(query=quote_plus(sample_query))
    policy = get_supplier_provider_policy(provider)
    public_search_decision = supplier_fetch_decision(
        sample_url,
        provider=provider,
        action=ACTION_PUBLIC_SEARCH_FETCH,
        tender_position_count=SMALL_TENDER_ACTIVE_DISCOVERY_LIMIT,
    )
    active_small_search = bool(public_search_decision.get("allowed"))
    status = "configured" if active_small_search else "manual_only"
    connection_state = CATALOG_CONNECTION_CONFIGURED if active_small_search else CATALOG_CONNECTION_MANUAL_ONLY
    access_mode = "configured" if active_small_search else "policy"
    return {
        "preset_id": str(preset["preset_id"]),
        "label": str(preset["label"]),
        "provider": provider,
        "sample_query": sample_query,
        "sample_url": sample_url,
        "status": status,
        "connection_state": connection_state,
        "http_status": None,
        "error_kind": "",
        "error": "",
        "body_preview": "",
        "access_mode": access_mode,
        "search_mode": CATALOG_SEARCH_MODE_ACTIVE_SMALL if active_small_search else CATALOG_SEARCH_MODE_MANUAL_ONLY,
        "small_tender_active_search": active_small_search,
        "policy_reason": str(public_search_decision.get("reason") or ""),
        "policy_mode": str(policy.get("default_mode") or ""),
        "recommended_flow": str(policy.get("recommended_flow") or ""),
        "risk_level": str(policy.get("risk_level") or ""),
        "operator_note": str(policy.get("operator_note") or ""),
        "max_active_positions": SMALL_TENDER_ACTIVE_DISCOVERY_LIMIT,
    }


def _now_iso(now_factory: Callable[[], str] | None = None) -> str:
    if now_factory is not None:
        return str(now_factory())
    return datetime.now(UTC).isoformat(timespec="seconds")


def _read_cached_catalog_health(database_path: str | Path) -> dict[str, Any] | None:
    with _connect_cache(database_path) as connection:
        row = connection.execute(
            "SELECT value FROM app_state WHERE key = ?",
            (SUPPLIER_CATALOG_HEALTH_CACHE_KEY,),
        ).fetchone()
    if row is None:
        return None
    try:
        payload = json.loads(str(row["value"]))
    except (TypeError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _write_cached_catalog_health(database_path: str | Path, payload: dict[str, Any]) -> None:
    with _connect_cache(database_path) as connection:
        connection.execute(
            """
            INSERT INTO app_state (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                SUPPLIER_CATALOG_HEALTH_CACHE_KEY,
                json.dumps(payload, ensure_ascii=False, sort_keys=True),
            ),
        )


def _connect_cache(database_path: str | Path) -> sqlite3.Connection:
    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    initialize_schema(connection)
    return connection


def _check_catalog_live(catalog: dict[str, Any], timeout: float, fetch: CatalogHealthFetcher) -> None:
    try:
        status, _body = fetch(catalog["sample_url"], timeout)
    except Exception as exc:  # noqa: BLE001 - health diagnostics should preserve provider failures.
        if _try_browser_catalog_health(catalog, timeout):
            return
        catalog["status"] = "error"
        catalog["connection_state"] = _exception_connection_state(exc)
        catalog["http_status"] = None
        catalog["error_kind"] = "network_error"
        catalog["error"] = str(exc)
        catalog["body_preview"] = ""
        catalog["access_mode"] = "http"
        return
    catalog["http_status"] = int(status)
    if 200 <= int(status) < 400:
        if not _catalog_body_has_parseable_content(str(catalog.get("provider") or ""), _body):
            if _should_try_browser_for_unparseable_body(_body) and _try_browser_catalog_health(catalog, timeout):
                return
            catalog["status"] = "error"
            catalog["connection_state"] = _unparseable_body_connection_state(_body)
            catalog["error_kind"] = "access_blocked"
            catalog["error"] = (
                f"HTTP {status} did not contain parseable {catalog.get('label') or catalog.get('provider')} "
                "product cards"
            )
            catalog["body_preview"] = response_body_preview(_body)
            catalog["access_mode"] = "http"
            return
        catalog["status"] = "ok"
        catalog["connection_state"] = CATALOG_CONNECTION_REACHABLE
        catalog["error_kind"] = ""
        catalog["error"] = ""
        catalog["body_preview"] = ""
        catalog["access_mode"] = "http"
        return
    if http_error_kind(int(status)) == "access_blocked" and _try_browser_catalog_health(catalog, timeout):
        return
    catalog["status"] = "error"
    catalog["connection_state"] = _http_connection_state(int(status), _body)
    catalog["error_kind"] = http_error_kind(int(status))
    catalog["error"] = f"expected HTTP 2xx/3xx, got {status}"
    catalog["body_preview"] = response_body_preview(_body)
    catalog["access_mode"] = "http"


def _mark_catalog_manual_only(catalog: dict[str, Any]) -> None:
    catalog["status"] = "manual_only"
    catalog["connection_state"] = CATALOG_CONNECTION_MANUAL_ONLY
    catalog["http_status"] = None
    catalog["error_kind"] = ""
    catalog["error"] = ""
    catalog["body_preview"] = ""
    catalog["access_mode"] = "policy"
    catalog.pop("browser_error", None)


def _try_browser_catalog_health(catalog: dict[str, Any], timeout: float) -> bool:
    provider = str(catalog.get("provider") or "")
    decision = supplier_fetch_decision(
        str(catalog.get("sample_url") or ""),
        provider=provider,
        action=ACTION_BROWSER_FETCH,
        tender_position_count=SMALL_TENDER_ACTIVE_DISCOVERY_LIMIT,
    )
    if not decision["allowed"]:
        return False
    if not supplier_browser_fetcher.is_enabled_for_provider(provider):
        return False
    try:
        body = supplier_browser_fetcher.fetch_text(
            str(catalog["sample_url"]),
            provider=provider,
            timeout_seconds=timeout,
        )
    except supplier_browser_fetcher.BrowserFetchError as exc:
        catalog["browser_error"] = str(exc)
        return False
    body_text = str(body or "")
    if not body_text.strip():
        catalog["browser_error"] = "browser fetch returned an empty response"
        return False
    if not _catalog_body_has_parseable_content(provider, body_text):
        catalog["status"] = "error"
        catalog["connection_state"] = _unparseable_body_connection_state(body_text)
        catalog["http_status"] = None
        catalog["error_kind"] = "access_blocked"
        catalog["error"] = ""
        catalog["body_preview"] = response_body_preview(body_text)
        catalog["access_mode"] = "browser"
        catalog["browser_error"] = f"browser fetch returned no parseable {catalog.get('label') or provider} product cards"
        return True
    catalog["status"] = "ok"
    catalog["connection_state"] = CATALOG_CONNECTION_REACHABLE
    catalog["http_status"] = None
    catalog["error_kind"] = ""
    catalog["error"] = ""
    catalog["body_preview"] = ""
    catalog["access_mode"] = "browser"
    return True


def _catalog_body_has_parseable_content(provider: str, body: str) -> bool:
    provider_key = provider.casefold()
    soup = BeautifulSoup(body, "html.parser")
    if _body_has_schema_product(soup):
        return True
    if provider_key == "officemag":
        return bool(
            soup.select_one(
                "li.listItem, .js-productListItem, .ProductHead__name, "
                ".Product__price, .js-productSum"
            )
        )
    if provider_key == "komus":
        return bool(soup.select_one("a[href*='/p/'], .product-card, [data-qa*='product' i]"))
    if provider_key == "petrovich":
        return bool(soup.select_one("a[href^='/product/'], a[href*='/product/'], .product-card, [data-test*='product' i]"))
    if provider_key == "vseinstrumenti":
        return bool(soup.select_one("a[href*='/product/'], .product-card, [data-qa*='product' i]"))
    if provider_key == "lemanapro":
        return bool(
            soup.select_one("a[href*='/product/'], .product-card, [data-qa*='product' i]")
            or re.search(r'window\.INITIAL_STATE\["plp"\].*"products"', body, re.IGNORECASE | re.DOTALL)
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


def _http_connection_state(status: int, body: str) -> str:
    if _looks_like_captcha(body):
        return CATALOG_CONNECTION_CAPTCHA
    if http_error_kind(status) == "access_blocked":
        return CATALOG_CONNECTION_BLOCKED
    return CATALOG_CONNECTION_NETWORK_ERROR


def _exception_connection_state(exc: Exception) -> str:
    text = str(exc).casefold()
    if "timed out" in text or "timeout" in text:
        return CATALOG_CONNECTION_TIMEOUT
    return CATALOG_CONNECTION_NETWORK_ERROR


def _unparseable_body_connection_state(body: str) -> str:
    if _looks_like_captcha(body):
        return CATALOG_CONNECTION_CAPTCHA
    if _looks_like_browser_or_access_block(body):
        return CATALOG_CONNECTION_BLOCKED
    if _looks_like_product_data_without_known_cards(body):
        return CATALOG_CONNECTION_PARSER_BROKEN
    return CATALOG_CONNECTION_NO_CARDS


def _should_try_browser_for_unparseable_body(body: str) -> bool:
    return _looks_like_captcha(body) or _looks_like_browser_or_access_block(body)


def _body_has_schema_product(soup: BeautifulSoup) -> bool:
    for script in soup.find_all("script", attrs={"type": re.compile("ld\\+json", re.IGNORECASE)}):
        text = script.string or script.get_text()
        if re.search(r'"@type"\s*:\s*(?:"Product"|\[[^\]]*"Product")', text, re.IGNORECASE):
            return True
    return False


def _looks_like_captcha(body: str) -> bool:
    text = response_body_preview(body).casefold()
    return any(marker in text for marker in ("captcha", "капча", "капчу"))


def _looks_like_browser_or_access_block(body: str) -> bool:
    text = response_body_preview(body).casefold()
    return any(
        marker in text
        for marker in (
            "browser verification",
            "verification required",
            "access denied",
            "проверку",
            "проверка",
            "доступ огранич",
        )
    )


def _looks_like_product_data_without_known_cards(body: str) -> bool:
    text = str(body or "")
    return bool(re.search(r'"@type"|itemprop=|data-price|товар|цена', text, re.IGNORECASE))


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
