from __future__ import annotations

from pathlib import Path
from typing import Any

from tender_killer.storage import TenderStore
from tender_killer.supplier_discovery_service import stage_profile_supplier_candidates


PUBLIC_SEARCH_PROVIDER = "public_search"


def run_profile_supplier_price_discovery(
    database_path: str | Path,
    source: str,
    external_id: str,
    position_index: int,
) -> dict[str, Any]:
    store = TenderStore(database_path)
    store.initialize()
    profiles = store.get_product_profiles(source, external_id)
    if not profiles:
        raise KeyError(f"Product profiles for {source}/{external_id} not found.")

    target = _find_profile(profiles, position_index)
    if target is None:
        raise KeyError(f"Product profile position {position_index} not found.")

    raw_payload = dict(target.get("raw_payload") or {})
    queries = _supplier_search_queries(raw_payload.get("supplier_search"))
    if not queries:
        raise ValueError("No prepared supplier search queries.")

    existing_keys = _existing_candidate_keys(raw_payload)
    candidates = [
        candidate
        for query in queries
        if (candidate := _candidate_from_query(query)) and _candidate_key(candidate) not in existing_keys
    ]
    if not candidates:
        raise ValueError("No new supplier discovery candidates.")

    return stage_profile_supplier_candidates(database_path, source, external_id, position_index, candidates)


def _find_profile(profiles: list[dict[str, Any]], position_index: int) -> dict[str, Any] | None:
    for profile in profiles:
        if int(profile.get("position_index") or 0) == position_index:
            return profile
    return None


def _supplier_search_queries(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, dict):
        return []
    queries = value.get("queries")
    if not isinstance(queries, list):
        return []
    return [dict(item) for item in queries if isinstance(item, dict)]


def _candidate_from_query(query: dict[str, Any]) -> dict[str, Any] | None:
    query_text = _text(query.get("query"))
    if not query_text:
        return None
    link = _first_quick_link(query)
    if link is None:
        return None
    label = _text(link.get("label")) or "Public"
    url = _text(link.get("url"))
    if not url:
        return None
    return {
        "name": f"Public search: {query_text}",
        "url": url,
        "availability": "unknown",
        "status": "candidate",
        "source_query": query_text,
        "source_kind": _text(query.get("kind")) or "supplier_search",
        "note": f"{label} public search result needs manual price review.",
        "provider": PUBLIC_SEARCH_PROVIDER,
    }


def _first_quick_link(query: dict[str, Any]) -> dict[str, Any] | None:
    links = query.get("quick_links")
    if not isinstance(links, list):
        return None
    for link in links:
        if isinstance(link, dict) and _text(link.get("url")):
            return dict(link)
    return None


def _existing_candidate_keys(raw_payload: dict[str, Any]) -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    discovery = raw_payload.get("supplier_discovery")
    if isinstance(discovery, dict):
        for candidate in _dict_items(discovery.get("candidates")):
            keys.add(_candidate_key(candidate))
    for option in _dict_items(raw_payload.get("supplier_options")):
        keys.add(_candidate_key(option))
    return keys


def _dict_items(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]


def _candidate_key(candidate: dict[str, Any]) -> tuple[str, str]:
    url = _text(candidate.get("url"))
    source_query = _text(candidate.get("source_query"))
    return (
        (_text(candidate.get("provider")) or "").casefold(),
        (url or source_query or "").casefold(),
    )


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
