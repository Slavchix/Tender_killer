from __future__ import annotations

import re
from typing import Any
from urllib.parse import parse_qsl
from urllib.parse import urlparse


SMALL_TENDER_ACTIVE_DISCOVERY_LIMIT = 5
MANUAL_PRICE_PRIMARY_SOURCES = ("price_book_feed", "supplier_quote", "manual_url", "quick_links")

ACTION_QUICK_LINK = "quick_link"
ACTION_PUBLIC_SEARCH_FETCH = "public_search_fetch"
ACTION_PRODUCT_PAGE_FETCH = "product_page_fetch"
ACTION_BROWSER_FETCH = "browser_fetch"
ACTION_INTERNAL_API = "internal_api"

SEARCH_ENGINE_HOST_MARKERS = ("google.", "yandex.")
UNSAFE_PATH_SEGMENTS = {
    "login",
    "auth",
    "checkout",
    "cart",
    "cabinet",
    "lk",
    "user",
    "order",
    "orders",
    "token",
    "session",
    "password",
    "secret",
    "cookie",
    "authorization",
    "api-common",
    "get_price",
    "price",
    "ajax",
    "graphql",
}
UNSAFE_QUERY_KEYS = {
    "login",
    "auth",
    "checkout",
    "cart",
    "cabinet",
    "lk",
    "user",
    "order",
    "orders",
    "token",
    "session",
    "password",
    "secret",
    "cookie",
    "authorization",
}
PATH_SPLIT_RE = re.compile(r"[^0-9a-z_-]+", re.IGNORECASE)


PROVIDER_POLICIES: dict[str, dict[str, Any]] = {
    "lemanapro": {
        "provider": "lemanapro",
        "label": "Lemana Pro",
        "default_mode": "limited_public_search",
        "allow_quick_links": True,
        "allow_public_search_fetch": True,
        "allow_product_page_fetch": True,
        "allow_browser_fetch": True,
        "allow_internal_api": False,
        "public_search_max_positions": SMALL_TENDER_ACTIVE_DISCOVERY_LIMIT,
        "browser_fetch_max_positions": SMALL_TENDER_ACTIVE_DISCOVERY_LIMIT,
        "recommended_flow": "limited_search_manual_url",
        "risk_level": "review_only",
        "operator_note": "Limited public search and browser fallback are allowed only for small tenders; candidates stay review-only.",
    },
    "officemag": {
        "provider": "officemag",
        "label": "OfficeMag",
        "default_mode": "limited_public_search",
        "allow_quick_links": True,
        "allow_public_search_fetch": True,
        "allow_product_page_fetch": True,
        "allow_browser_fetch": True,
        "allow_internal_api": False,
        "public_search_max_positions": SMALL_TENDER_ACTIVE_DISCOVERY_LIMIT,
        "browser_fetch_max_positions": SMALL_TENDER_ACTIVE_DISCOVERY_LIMIT,
        "recommended_flow": "limited_search_manual_url",
        "risk_level": "review_only",
        "operator_note": "Limited public search and browser fallback are allowed only for small tenders; candidates stay review-only.",
    },
    "komus": {
        "provider": "komus",
        "label": "Komus",
        "default_mode": "limited_public_search",
        "allow_quick_links": True,
        "allow_public_search_fetch": True,
        "allow_product_page_fetch": True,
        "allow_browser_fetch": True,
        "allow_internal_api": False,
        "public_search_max_positions": SMALL_TENDER_ACTIVE_DISCOVERY_LIMIT,
        "browser_fetch_max_positions": SMALL_TENDER_ACTIVE_DISCOVERY_LIMIT,
        "recommended_flow": "limited_search_feed_quote",
        "risk_level": "review_only",
        "operator_note": "Limited public search and browser fallback are allowed only for small tenders; use feed or quote if access is blocked.",
    },
    "vseinstrumenti": {
        "provider": "vseinstrumenti",
        "label": "Vseinstrumenti",
        "default_mode": "limited_public_search",
        "allow_quick_links": True,
        "allow_public_search_fetch": True,
        "allow_product_page_fetch": True,
        "allow_browser_fetch": True,
        "allow_internal_api": False,
        "public_search_max_positions": SMALL_TENDER_ACTIVE_DISCOVERY_LIMIT,
        "browser_fetch_max_positions": SMALL_TENDER_ACTIVE_DISCOVERY_LIMIT,
        "recommended_flow": "limited_search_manual_url",
        "risk_level": "limited",
        "operator_note": "Limited public search and browser fallback are allowed only for small tenders; switch to manual URL/feed if access is still blocked.",
    },
    "petrovich": {
        "provider": "petrovich",
        "label": "Petrovich",
        "default_mode": "limited_public_search",
        "allow_quick_links": True,
        "allow_public_search_fetch": True,
        "allow_product_page_fetch": True,
        "allow_browser_fetch": True,
        "allow_internal_api": False,
        "public_search_max_positions": SMALL_TENDER_ACTIVE_DISCOVERY_LIMIT,
        "browser_fetch_max_positions": SMALL_TENDER_ACTIVE_DISCOVERY_LIMIT,
        "recommended_flow": "manual_url_quote_feed",
        "risk_level": "limited",
        "operator_note": "No confirmed public price API; limited public search/browser fallback is small-tender only.",
    },
}

UNKNOWN_PROVIDER_POLICY = {
    "provider": "unknown",
    "label": "Unknown supplier",
    "default_mode": "limited_public_search",
    "allow_quick_links": True,
    "allow_public_search_fetch": True,
    "allow_product_page_fetch": True,
    "allow_browser_fetch": False,
    "allow_internal_api": False,
    "public_search_max_positions": SMALL_TENDER_ACTIVE_DISCOVERY_LIMIT,
    "recommended_flow": "manual_url_review",
    "risk_level": "limited",
    "operator_note": "Unknown public suppliers are review-only and limited to small-tender search or manual product URLs.",
}


def get_supplier_provider_policy(provider: str | None) -> dict[str, Any]:
    provider_key = _provider_key(provider)
    if provider_key in PROVIDER_POLICIES:
        return dict(PROVIDER_POLICIES[provider_key])
    policy = dict(UNKNOWN_PROVIDER_POLICY)
    if provider_key:
        policy["provider"] = provider_key
        policy["label"] = provider_key.replace("_", " ").title()
    return policy


def supplier_provider_policies() -> list[dict[str, Any]]:
    return [get_supplier_provider_policy(provider) for provider in PROVIDER_POLICIES]


def supplier_auto_price_policy(tender_position_count: int | None) -> dict[str, Any]:
    position_count = _positive_int(tender_position_count)
    if position_count is not None and position_count <= SMALL_TENDER_ACTIVE_DISCOVERY_LIMIT:
        return {
            "level": "small_review_only_auto_search",
            "position_limit": SMALL_TENDER_ACTIVE_DISCOVERY_LIMIT,
            "position_count": position_count,
            "active_search_allowed": True,
            "review_only": True,
            "mass_launch_allowed": True,
            "primary_sources": ["public_search", "manual_url", "quick_links"],
            "site_parsing_role": "helper",
        }

    return {
        "level": "large_manual_sources" if position_count else "manual_until_positions_known",
        "position_limit": SMALL_TENDER_ACTIVE_DISCOVERY_LIMIT,
        "position_count": position_count,
        "active_search_allowed": False,
        "review_only": True,
        "mass_launch_allowed": False,
        "primary_sources": list(MANUAL_PRICE_PRIMARY_SOURCES),
        "site_parsing_role": "helper_only",
    }


def supplier_fetch_decision(
    url: str,
    *,
    provider: str | None = None,
    action: str,
    tender_position_count: int | None = None,
) -> dict[str, Any]:
    provider_key = _provider_key(provider) or _provider_from_url(url)
    policy = get_supplier_provider_policy(provider_key)
    action_key = _provider_key(action)
    decision = {
        "allowed": False,
        "reason": "unknown_action",
        "provider": policy["provider"],
        "action": action_key,
        "policy": policy,
    }

    if action_key == ACTION_QUICK_LINK:
        decision["allowed"] = bool(policy.get("allow_quick_links"))
        decision["reason"] = "allowed" if decision["allowed"] else "quick_links_not_allowed"
        return decision

    unsafe_reason = unsafe_supplier_url_reason(url, action=action_key)
    if unsafe_reason:
        decision["reason"] = unsafe_reason
        return decision

    if action_key == ACTION_PUBLIC_SEARCH_FETCH:
        if not policy.get("allow_public_search_fetch"):
            decision["reason"] = "public_search_fetch_not_allowed"
            return decision
        if _exceeds_public_search_limit(policy, tender_position_count):
            decision["reason"] = "large_tender_manual_required"
            return decision
        decision["allowed"] = True
        decision["reason"] = "allowed"
        return decision

    if action_key == ACTION_PRODUCT_PAGE_FETCH:
        decision["allowed"] = bool(policy.get("allow_product_page_fetch"))
        decision["reason"] = "allowed" if decision["allowed"] else "product_page_fetch_not_allowed"
        return decision

    if action_key == ACTION_BROWSER_FETCH:
        if not policy.get("allow_browser_fetch"):
            decision["reason"] = "browser_fetch_not_allowed"
            return decision
        if _exceeds_browser_fetch_limit(policy, tender_position_count):
            decision["reason"] = "large_tender_manual_required"
            return decision
        decision["allowed"] = True
        decision["reason"] = "allowed"
        return decision

    if action_key == ACTION_INTERNAL_API:
        decision["allowed"] = bool(policy.get("allow_internal_api"))
        decision["reason"] = "allowed" if decision["allowed"] else "internal_api_not_allowed"
        return decision

    return decision


def unsafe_supplier_url_reason(url: str, *, action: str | None = None) -> str | None:
    parsed = urlparse(str(url or ""))
    if parsed.scheme == "data":
        return None
    if parsed.scheme not in {"http", "https"}:
        return "unsafe_url"
    host = parsed.netloc.casefold()
    action_key = _provider_key(action)
    if action_key != ACTION_QUICK_LINK and any(marker in host for marker in SEARCH_ENGINE_HOST_MARKERS):
        return "search_engine_fetch_not_allowed"

    path = parsed.path.casefold()
    segments = {segment for segment in PATH_SPLIT_RE.split(path) if segment}
    if segments.intersection(UNSAFE_PATH_SEGMENTS):
        return "unsafe_url"
    if "/api-common/" in path or "/get_price" in path or "/price" in path or "/ajax" in path or "/graphql" in path:
        return "unsafe_url"

    query_keys = {str(key or "").casefold() for key, _value in parse_qsl(parsed.query, keep_blank_values=True)}
    if query_keys.intersection(UNSAFE_QUERY_KEYS):
        return "unsafe_url"
    return None


def is_safe_supplier_url(url: str, *, action: str | None = None) -> bool:
    return unsafe_supplier_url_reason(url, action=action) is None


def _exceeds_public_search_limit(policy: dict[str, Any], tender_position_count: int | None) -> bool:
    max_positions = _positive_int(policy.get("public_search_max_positions"))
    position_count = _positive_int(tender_position_count)
    return max_positions is not None and position_count is not None and position_count > max_positions


def _exceeds_browser_fetch_limit(policy: dict[str, Any], tender_position_count: int | None) -> bool:
    max_positions = _positive_int(policy.get("browser_fetch_max_positions"))
    if max_positions is None:
        max_positions = _positive_int(policy.get("public_search_max_positions"))
    position_count = _positive_int(tender_position_count)
    return max_positions is not None and position_count is not None and position_count > max_positions


def _positive_int(value: Any) -> int | None:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def _provider_key(value: str | None) -> str:
    return str(value or "").strip().casefold().replace("-", "_")


def _provider_from_url(url: str) -> str:
    host = urlparse(str(url or "")).netloc.casefold()
    if "officemag.ru" in host:
        return "officemag"
    if "komus.ru" in host:
        return "komus"
    if "petrovich.ru" in host:
        return "petrovich"
    if "vseinstrumenti.ru" in host:
        return "vseinstrumenti"
    if "lemanapro.ru" in host:
        return "lemanapro"
    return ""
