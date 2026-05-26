from __future__ import annotations

from pathlib import Path
from typing import Any

from tender_killer.storage import TenderStore


LOCKED_PROFILE_STATUSES = {"matched", "priced", "rejected"}


def build_supplier_search_queries(profile: dict[str, Any]) -> list[dict[str, Any]]:
    base_query = _text(profile.get("normalized_name")) or _text(profile.get("product_name"))
    queries: list[dict[str, Any]] = []
    seen: set[str] = set()

    if base_query:
        kind = "normalized_name" if _text(profile.get("normalized_name")) else "product_name"
        _append_query(queries, seen, base_query, kind)

    for phrase in _text_items(profile.get("search_phrases")):
        _append_query(queries, seen, phrase, "search_phrase")

    classifier = _text(profile.get("okpd2")) or _text(profile.get("classifier_code"))
    if classifier:
        classifier_query = f"{classifier} {base_query}" if base_query else classifier
        _append_query(queries, seen, classifier_query, "classifier")

    return queries


def prepare_profile_supplier_search(
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

    queries = build_supplier_search_queries(target)
    if not queries:
        raise ValueError("No searchable product terms.")

    supplier_search = {"status": "ready", "queries": queries}
    raw_payload = dict(target.get("raw_payload") or {})
    raw_payload["supplier_search"] = supplier_search
    target["raw_payload"] = raw_payload
    if str(target.get("profile_status") or "") not in LOCKED_PROFILE_STATUSES:
        target["profile_status"] = "searching"

    store.upsert_product_profiles(source, external_id, profiles)
    return {
        "ok": True,
        "position_index": position_index,
        "supplier_search": supplier_search,
    }


def _find_profile(profiles: list[dict[str, Any]], position_index: int) -> dict[str, Any] | None:
    for profile in profiles:
        if int(profile.get("position_index") or 0) == position_index:
            return profile
    return None


def _append_query(queries: list[dict[str, Any]], seen: set[str], query: str, kind: str) -> None:
    normalized = " ".join(query.split())
    if not normalized:
        return
    key = normalized.casefold()
    if key in seen:
        return
    seen.add(key)
    queries.append({"query": normalized, "kind": kind, "priority": len(queries) + 1})


def _text_items(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [text for item in value if (text := _text(item))]


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
