from __future__ import annotations

from pathlib import Path
from typing import Any

from tender_killer.economics_auto import build_auto_economics_estimate
from tender_killer.storage import TenderStore


ECONOMICS_INPUT_FIELDS = ("unit_cost", "total_cost", "logistics_cost", "documents_cost", "other_costs")


def update_profile_economics(
    database_path: str | Path,
    source: str,
    external_id: str,
    position_index: int,
    data: dict[str, Any],
) -> dict[str, Any]:
    store = TenderStore(database_path)
    store.initialize()
    profiles = store.get_product_profiles(source, external_id)
    if not profiles:
        raise KeyError(f"Product profiles for {source}/{external_id} not found.")

    target = None
    for profile in profiles:
        if int(profile.get("position_index") or 0) == position_index:
            target = profile
            break
    if target is None:
        raise KeyError(f"Product profile position {position_index} not found.")

    economics = _economics_inputs(data)
    raw_payload = dict(target.get("raw_payload") or {})
    raw_payload["economics"] = economics
    target["raw_payload"] = raw_payload
    if any(key in economics for key in ("unit_cost", "total_cost")):
        target["profile_status"] = "priced"

    store.upsert_product_profiles(source, external_id, profiles)
    return {"ok": True}


def update_profile_auto_economics(
    database_path: str | Path,
    source: str,
    external_id: str,
    position_index: int,
    document_records: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    store = TenderStore(database_path)
    store.initialize()
    profiles = store.get_product_profiles(source, external_id)
    if not profiles:
        raise KeyError(f"Product profiles for {source}/{external_id} not found.")

    target = None
    for profile in profiles:
        if int(profile.get("position_index") or 0) == position_index:
            target = profile
            break
    if target is None:
        raise KeyError(f"Product profile position {position_index} not found.")

    estimate = build_auto_economics_estimate(target, document_records or [])
    raw_payload = dict(target.get("raw_payload") or {})
    raw_payload["economics_auto"] = estimate
    target["raw_payload"] = raw_payload

    store.upsert_product_profiles(source, external_id, profiles)
    return {"ok": True, "economics_auto": estimate}


def _economics_inputs(data: dict[str, Any]) -> dict[str, float]:
    values: dict[str, float] = {}
    for field in ECONOMICS_INPUT_FIELDS:
        number = _number(data.get(field))
        if number is not None:
            values[field] = number
    return values


def _number(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        number = float(str(value).replace(" ", "").replace(",", "."))
    except (TypeError, ValueError):
        return None
    return number if number >= 0 else None
