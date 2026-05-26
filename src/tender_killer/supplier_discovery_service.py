from __future__ import annotations

from pathlib import Path
from typing import Any

from tender_killer.storage import TenderStore


DISCOVERY_TEXT_FIELDS = ("name", "url", "availability", "status", "source_query", "source_kind", "note")
DISCOVERY_NUMBER_FIELDS = ("unit_price",)
LOCKED_PROFILE_STATUSES = {"priced", "rejected"}


def stage_profile_supplier_candidates(
    database_path: str | Path,
    source: str,
    external_id: str,
    position_index: int,
    candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    store = TenderStore(database_path)
    store.initialize()
    profiles = store.get_product_profiles(source, external_id)
    if not profiles:
        raise KeyError(f"Product profiles for {source}/{external_id} not found.")

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
    discovery["candidates"] = existing_candidates
    raw_payload["supplier_discovery"] = discovery
    target["raw_payload"] = raw_payload
    if str(target.get("profile_status") or "") not in LOCKED_PROFILE_STATUSES:
        target["profile_status"] = "matched"

    store.upsert_product_profiles(source, external_id, profiles)
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
    profiles = store.get_product_profiles(source, external_id)
    if not profiles:
        raise KeyError(f"Product profiles for {source}/{external_id} not found.")

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
        value = _text(data.get(field))
        if value:
            candidate[field] = value
    for field in DISCOVERY_NUMBER_FIELDS:
        number = _number(data.get(field))
        if number is not None:
            candidate[field] = number
    has_candidate_signal = any(candidate.get(field) for field in ("name", "url", "note")) or "unit_price" in candidate
    if not has_candidate_signal:
        return {}
    candidate.setdefault("review_status", "pending")
    return candidate


def _supplier_option_from_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    option: dict[str, Any] = {}
    for field in DISCOVERY_TEXT_FIELDS:
        value = _text(candidate.get(field))
        if value:
            option[field] = value
    for field in DISCOVERY_NUMBER_FIELDS:
        number = _number(candidate.get(field))
        if number is not None:
            option[field] = number
    has_candidate_signal = any(option.get(field) for field in ("name", "url", "note")) or "unit_price" in option
    return option if has_candidate_signal else {}


def _discovery_candidates(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]


def _supplier_options(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _number(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        number = float(str(value).replace(" ", "").replace(",", "."))
    except (TypeError, ValueError):
        return None
    return number if number >= 0 else None
