from __future__ import annotations

from typing import Any

from tender_killer.supplier_catalog_presets import SUPPLIER_CATALOG_PRESETS
from tender_killer.supplier_price_discovery_diagnostics import CATALOG_SEARCH_LINK_KIND
from tender_killer.supplier_price_discovery_diagnostics import MANUAL_PRODUCT_LINK_KIND
from tender_killer.supplier_price_discovery_utils import _is_public_product_page_url
from tender_killer.supplier_price_discovery_utils import _text
from tender_killer.supplier_search_service import build_supplier_search_queries


BUILT_IN_CATALOG_PROVIDERS = tuple(str(preset["provider"]) for preset in SUPPLIER_CATALOG_PRESETS)
BUILT_IN_CATALOG_PROVIDER_SET = {provider.casefold() for provider in BUILT_IN_CATALOG_PROVIDERS}


def _catalog_providers_for_queries(queries: list[dict[str, Any]]) -> set[str]:
    providers: set[str] = set()
    for query in queries:
        for link in _quick_links(query):
            link_kind = _text(link.get("link_kind"))
            provider = _text(link.get("provider"))
            if link_kind in {CATALOG_SEARCH_LINK_KIND, MANUAL_PRODUCT_LINK_KIND} and provider:
                providers.add(provider.casefold())
    return providers


def _manual_product_catalog_providers_for_queries(queries: list[dict[str, Any]]) -> set[str]:
    providers: set[str] = set()
    for query in queries:
        for link in _quick_links(query):
            link_kind = _text(link.get("link_kind"))
            provider = _text(link.get("provider"))
            if link_kind == MANUAL_PRODUCT_LINK_KIND and provider:
                providers.add(provider.casefold())
    return providers


def _supplier_search_queries(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, dict):
        return []
    queries = value.get("queries")
    if not isinstance(queries, list):
        return []
    return [dict(item) for item in queries if isinstance(item, dict)]


def _refreshed_supplier_search_queries(profile: dict[str, Any], raw_payload: dict[str, Any]) -> list[dict[str, Any]]:
    existing_queries = _supplier_search_queries(raw_payload.get("supplier_search"))
    fresh_queries = build_supplier_search_queries(profile)
    if not existing_queries:
        return fresh_queries
    return _unique_supplier_search_queries([*existing_queries, *fresh_queries])


def _unique_supplier_search_queries(queries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unique: list[dict[str, Any]] = []
    index_by_key: dict[str, int] = {}
    for query in queries:
        query_text = _text(query.get("query"))
        if not query_text:
            continue
        key = query_text.casefold()
        if key in index_by_key:
            unique[index_by_key[key]] = _merge_supplier_search_query(unique[index_by_key[key]], query)
            continue
        index_by_key[key] = len(unique)
        unique.append(dict(query))
    return unique


def _merge_supplier_search_query(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    merged = dict(left)
    if _has_direct_supplier_quick_link(left):
        return merged
    merged_links = _unique_quick_links([*_quick_links(left), *_quick_links(right)])
    if merged_links:
        merged["quick_links"] = merged_links
    return merged


def _has_direct_supplier_quick_link(query: dict[str, Any]) -> bool:
    for link in _quick_links(query):
        if _text(link.get("link_kind")) == CATALOG_SEARCH_LINK_KIND:
            continue
        url = _text(link.get("url"))
        if url and _is_public_product_page_url(url):
            return True
    return False


def _unique_quick_links(links: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unique: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str]] = set()
    for link in links:
        url = _text(link.get("url"))
        if not url:
            continue
        key = (
            url.casefold(),
            _text(link.get("provider")) or "",
            _text(link.get("link_kind")) or "",
            _text(link.get("preset_id")) or "",
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(dict(link))
    return unique


def _quick_links(query: dict[str, Any]) -> list[dict[str, Any]]:
    links = query.get("quick_links")
    if not isinstance(links, list):
        return []
    return [dict(link) for link in links if isinstance(link, dict) and _text(link.get("url"))]


def _is_builtin_catalog_search_link(link: dict[str, Any]) -> bool:
    provider = _text(link.get("provider"))
    return (
        _text(link.get("link_kind")) in {CATALOG_SEARCH_LINK_KIND, MANUAL_PRODUCT_LINK_KIND}
        and provider is not None
        and provider.casefold() in BUILT_IN_CATALOG_PROVIDER_SET
    )


def _is_catalog_search_link_for_provider(link: dict[str, Any], provider: str) -> bool:
    link_provider = _text(link.get("provider"))
    return (
        _text(link.get("link_kind")) in {CATALOG_SEARCH_LINK_KIND, MANUAL_PRODUCT_LINK_KIND}
        and link_provider is not None
        and link_provider.casefold() == provider.casefold()
    )
