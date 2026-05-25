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


def accept_profile_auto_economics(
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
    estimate = _auto_estimate_payload(target)
    economics = _economics_from_auto_estimate(estimate)
    raw_payload = dict(target.get("raw_payload") or {})
    raw_payload["economics"] = economics
    raw_payload["economics_acceptance"] = {
        "source": "auto_estimate",
        "accepted": True,
    }
    target["raw_payload"] = raw_payload
    if any(key in economics for key in ("unit_cost", "total_cost")):
        target["profile_status"] = "priced"

    store.upsert_product_profiles(source, external_id, profiles)
    return {"ok": True, "economics": economics}


def _find_profile(profiles: list[dict[str, Any]], position_index: int) -> dict[str, Any]:
    for profile in profiles:
        if int(profile.get("position_index") or 0) == position_index:
            return profile
    raise KeyError(f"Product profile position {position_index} not found.")


def _auto_estimate_payload(profile: dict[str, Any]) -> dict[str, Any]:
    raw_payload = profile.get("raw_payload") if isinstance(profile.get("raw_payload"), dict) else {}
    estimate = raw_payload.get("economics_auto")
    if not isinstance(estimate, dict):
        raise KeyError("Product profile auto economics estimate not found.")
    return estimate


def _economics_from_auto_estimate(estimate: dict[str, Any]) -> dict[str, float]:
    economics: dict[str, float] = {}
    unit_cost = _number(estimate.get("estimated_unit_cost"))
    if unit_cost is not None:
        economics["unit_cost"] = unit_cost

    logistics_cost = _driver_amounts(estimate, {"delivery", "unloading", "packaging"})
    documents_cost = _driver_amounts(estimate, {"certificates"})
    hidden_costs_total = _number(estimate.get("hidden_costs_total")) or 0.0
    risk_reserve = _number(estimate.get("risk_reserve")) or 0.0
    other_costs = max(0.0, hidden_costs_total - logistics_cost - documents_cost) + risk_reserve

    if logistics_cost:
        economics["logistics_cost"] = _round_money(logistics_cost)
    if documents_cost:
        economics["documents_cost"] = _round_money(documents_cost)
    if other_costs:
        economics["other_costs"] = _round_money(other_costs)

    return economics


def _driver_amounts(estimate: dict[str, Any], driver_types: set[str]) -> float:
    total = 0.0
    for driver in estimate.get("cost_drivers") or []:
        if not isinstance(driver, dict) or driver.get("type") not in driver_types:
            continue
        total += _number(driver.get("amount")) or 0.0
    return _round_money(total)


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


def _round_money(value: float) -> float:
    return round(value, 2)
