from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from tender_killer.product_profile_service import ensure_product_profiles
from tender_killer.storage import TenderStore


DISCOVERY_TEXT_FIELDS = (
    "name",
    "url",
    "source_url",
    "availability",
    "status",
    "source_query",
    "source_kind",
    "note",
    "provider",
    "supplier_name",
    "brand",
    "manufacturer",
    "product_code",
    "image_url",
    "unit",
    "confidence",
    "currency",
    "vat_mode",
    "delivery_note",
)
DISCOVERY_NUMBER_FIELDS = (
    "unit_price",
    "stock_quantity",
    "preorder_quantity",
    "minimum_order_quantity",
    "pack_quantity",
)
DISCOVERY_LIST_FIELDS = (
    "confidence_reasons",
    "match_reasons",
)
DISCOVERY_JSON_FIELDS = (
    "image_urls",
    "price_breaks",
    "product_attributes",
)
DISCOVERY_CONFIDENCE_VALUES = {"high", "medium", "needs_review"}
LOCKED_PROFILE_STATUSES = {"priced", "rejected"}
TOKEN_PATTERN = re.compile(r"[^\w]+", re.UNICODE)


def stage_profile_supplier_candidates(
    database_path: str | Path,
    source: str,
    external_id: str,
    position_index: int,
    candidates: list[dict[str, Any]],
    collector_diagnostics: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    store = TenderStore(database_path)
    store.initialize()
    profiles = ensure_product_profiles(database_path, source, external_id)

    target = _find_profile(profiles, position_index)
    if target is None:
        raise KeyError(f"Product profile position {position_index} not found.")

    staged = [_discovery_candidate(candidate) for candidate in candidates]
    staged = [candidate for candidate in staged if candidate]
    if not staged:
        raise ValueError("No supplier discovery candidates.")

    raw_payload = dict(target.get("raw_payload") or {})
    discovery = dict(raw_payload.get("supplier_discovery") or {})
    existing_candidates = _discovery_candidates(discovery.get("candidates"))
    existing_candidates.extend(staged)
    discovery["status"] = "pending_review"
    if collector_diagnostics is not None:
        discovery["collector_diagnostics"] = collector_diagnostics
    discovery["candidates"] = existing_candidates
    raw_payload["supplier_discovery"] = discovery
    target["raw_payload"] = raw_payload
    if str(target.get("profile_status") or "") not in LOCKED_PROFILE_STATUSES:
        target["profile_status"] = "matched"

    store.upsert_product_profiles(source, external_id, profiles)
    store.upsert_price_candidates(source, external_id, position_index, staged, origin="supplier_discovery")
    return {
        "ok": True,
        "position_index": position_index,
        "staged_count": len(staged),
        "supplier_discovery": discovery,
    }


def import_profile_supplier_candidate(
    database_path: str | Path,
    source: str,
    external_id: str,
    position_index: int,
    candidate_index: int,
) -> dict[str, Any]:
    store = TenderStore(database_path)
    store.initialize()
    profiles = ensure_product_profiles(database_path, source, external_id)

    target = _find_profile(profiles, position_index)
    if target is None:
        raise KeyError(f"Product profile position {position_index} not found.")

    raw_payload = dict(target.get("raw_payload") or {})
    discovery = dict(raw_payload.get("supplier_discovery") or {})
    candidates = _discovery_candidates(discovery.get("candidates"))
    if candidate_index < 0 or candidate_index >= len(candidates):
        raise IndexError(f"Supplier discovery candidate index {candidate_index} not found.")

    candidate = candidates[candidate_index]
    option = _supplier_option_from_candidate(candidate)
    if not option:
        raise ValueError("Supplier discovery candidate is empty.")

    supplier_options = _supplier_options(raw_payload.get("supplier_options"))
    supplier_options.append(option)
    supplier_option_index = len(supplier_options) - 1
    candidate["review_status"] = "imported"
    candidate["supplier_option_index"] = supplier_option_index
    discovery["candidates"] = candidates
    raw_payload["supplier_options"] = supplier_options
    raw_payload["supplier_discovery"] = discovery
    target["raw_payload"] = raw_payload
    if str(target.get("profile_status") or "") not in LOCKED_PROFILE_STATUSES:
        target["profile_status"] = "matched"

    store.upsert_product_profiles(source, external_id, profiles)
    store.upsert_price_candidates(source, external_id, position_index, [candidate], origin="supplier_discovery")
    store.update_price_candidate_review(
        source,
        external_id,
        position_index,
        candidate,
        review_status="imported",
        supplier_option_index=supplier_option_index,
    )
    return {
        "ok": True,
        "position_index": position_index,
        "candidate_index": candidate_index,
        "supplier_option_index": supplier_option_index,
    }


def _find_profile(profiles: list[dict[str, Any]], position_index: int) -> dict[str, Any] | None:
    for profile in profiles:
        if int(profile.get("position_index") or 0) == position_index:
            return profile
    return None


def _discovery_candidate(data: dict[str, Any]) -> dict[str, Any]:
    candidate: dict[str, Any] = {}
    for field in DISCOVERY_TEXT_FIELDS:
        value = _normalized_text_field(field, data.get(field))
        if value:
            candidate[field] = value
    for field in DISCOVERY_NUMBER_FIELDS:
        number = _number(data.get(field))
        if number is not None:
            candidate[field] = number
    for field in DISCOVERY_LIST_FIELDS:
        items = _text_items(data.get(field))
        if items:
            candidate[field] = items
    for field in DISCOVERY_JSON_FIELDS:
        value = _json_list_or_dicts(data.get(field))
        if value:
            candidate[field] = value
    has_candidate_signal = any(candidate.get(field) for field in ("name", "url", "note")) or "unit_price" in candidate
    if not has_candidate_signal:
        return {}
    confidence_reasons = _text_items(candidate.get("confidence_reasons")) or _confidence_reasons(candidate)
    candidate["confidence"] = _confidence(data.get("confidence")) or _confidence_from_reasons(confidence_reasons)
    candidate["confidence_reasons"] = confidence_reasons
    candidate.setdefault("review_status", "pending")
    return candidate


def _supplier_option_from_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    option: dict[str, Any] = {}
    for field in DISCOVERY_TEXT_FIELDS:
        value = _normalized_text_field(field, candidate.get(field))
        if value:
            option[field] = value
    for field in DISCOVERY_NUMBER_FIELDS:
        number = _number(candidate.get(field))
        if number is not None:
            option[field] = number
    for field in DISCOVERY_JSON_FIELDS:
        value = _json_list_or_dicts(candidate.get(field))
        if value:
            option[field] = value
    has_candidate_signal = any(option.get(field) for field in ("name", "url", "note")) or "unit_price" in option
    return option if has_candidate_signal else {}


def _discovery_candidates(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]


def _text_items(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    items: list[str] = []
    for item in value:
        text = _text(item)
        if text:
            items.append(text)
    return items


def _json_list_or_dicts(value: Any) -> list[Any]:
    if not isinstance(value, list):
        return []
    items: list[Any] = []
    for item in value:
        if isinstance(item, dict):
            items.append(dict(item))
        elif isinstance(item, (str, int, float, bool)):
            items.append(item)
    return items


def _supplier_options(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _normalized_text_field(field: str, value: Any) -> str | None:
    if field == "provider":
        return _token(value)
    if field == "confidence":
        return _confidence(value)
    return _text(value)


def _token(value: Any) -> str | None:
    text = _text(value)
    if not text:
        return None
    token = TOKEN_PATTERN.sub("_", text.casefold()).strip("_")
    return token or None


def _confidence(value: Any) -> str | None:
    token = _token(value)
    if token in DISCOVERY_CONFIDENCE_VALUES:
        return token
    return None


def _confidence_reasons(candidate: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if "unit_price" in candidate:
        reasons.append("has_price")
    if candidate.get("url"):
        reasons.append("has_url")
    if candidate.get("source_query"):
        reasons.append("has_source_query")
    return reasons


def _confidence_from_reasons(reasons: list[str]) -> str:
    reason_set = set(reasons)
    if {"has_price", "has_url", "has_source_query"}.issubset(reason_set):
        return "high"
    if "has_price" in reason_set and reason_set.intersection({"has_url", "has_source_query"}):
        return "medium"
    return "needs_review"


def _number(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        number = float(str(value).replace(" ", "").replace(",", "."))
    except (TypeError, ValueError):
        return None
    return number if number >= 0 else None
