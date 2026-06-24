from __future__ import annotations

from pathlib import Path
from typing import Any

from tender_killer.economics_auto import build_auto_economics_estimate
from tender_killer.product_profile_service import ensure_product_profiles
from tender_killer.storage import TenderStore


ECONOMICS_NUMERIC_INPUT_FIELDS = (
    "unit_cost",
    "total_cost",
    "pack_quantity",
    "logistics_cost",
    "documents_cost",
    "packaging_cost",
    "other_costs",
    "service_rate",
    "service_volume",
    "service_minimum",
    "service_logistics_cost",
    "service_equipment_cost",
)
ECONOMICS_UNIT_COST_BASES = {"tender_unit", "supplier_pack"}
ECONOMICS_COST_MODELS = {"product", "service"}
VAT_MODES = {"unknown", "vat_included", "vat_excluded", "no_vat"}
DEFAULT_TARGET_MARGIN_PERCENT = 15.0


def update_profile_economics(
    database_path: str | Path,
    source: str,
    external_id: str,
    position_index: int,
    data: dict[str, Any],
) -> dict[str, Any]:
    store = TenderStore(database_path)
    store.initialize()
    profiles = ensure_product_profiles(database_path, source, external_id)

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
    if any(key in economics for key in ("unit_cost", "total_cost", "service_rate", "service_minimum")):
        target["profile_status"] = "priced"

    store.upsert_product_profiles(source, external_id, profiles)
    return {"ok": True}


def update_profile_economics_assumptions(
    database_path: str | Path,
    source: str,
    external_id: str,
    position_index: int,
    data: dict[str, Any],
) -> dict[str, Any]:
    store = TenderStore(database_path)
    store.initialize()
    profiles = ensure_product_profiles(database_path, source, external_id)

    target = _find_profile(profiles, position_index)
    assumptions = _assumptions_inputs(data)
    raw_payload = dict(target.get("raw_payload") or {})
    raw_payload["economics_assumptions"] = assumptions
    target["raw_payload"] = raw_payload

    store.upsert_product_profiles(source, external_id, profiles)
    return {"ok": True, "economics_assumptions": assumptions}


def update_profile_auto_economics(
    database_path: str | Path,
    source: str,
    external_id: str,
    position_index: int,
    document_records: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    store = TenderStore(database_path)
    store.initialize()
    profiles = ensure_product_profiles(database_path, source, external_id)

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
    raw_payload["economics_assumptions"] = _merge_auto_assumptions(
        raw_payload.get("economics_assumptions"),
        _assumptions_from_auto_estimate(estimate),
    )
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
    profiles = ensure_product_profiles(database_path, source, external_id)

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

    logistics_cost = _driver_amounts(estimate, {"delivery", "unloading"})
    documents_cost = _driver_amounts(estimate, {"certificates"})
    packaging_cost = _driver_amounts(estimate, {"packaging"})
    hidden_costs_total = _number(estimate.get("hidden_costs_total")) or 0.0
    risk_reserve = _number(estimate.get("risk_reserve")) or 0.0
    other_costs = max(0.0, hidden_costs_total - logistics_cost - documents_cost - packaging_cost) + risk_reserve

    if logistics_cost:
        economics["logistics_cost"] = _round_money(logistics_cost)
    if documents_cost:
        economics["documents_cost"] = _round_money(documents_cost)
    if packaging_cost:
        economics["packaging_cost"] = _round_money(packaging_cost)
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


def _economics_inputs(data: dict[str, Any]) -> dict[str, Any]:
    values: dict[str, Any] = {}
    cost_model = _cost_model(data.get("cost_model"))
    if cost_model:
        values["cost_model"] = cost_model
    for field in ECONOMICS_NUMERIC_INPUT_FIELDS:
        number = _number(data.get(field))
        if number is not None:
            values[field] = number
    unit_cost_basis = _unit_cost_basis(data.get("unit_cost_basis"))
    if unit_cost_basis:
        values["unit_cost_basis"] = unit_cost_basis
    return values


def _unit_cost_basis(value: Any) -> str | None:
    text = str(value or "").strip()
    return text if text in ECONOMICS_UNIT_COST_BASES else None


def _cost_model(value: Any) -> str | None:
    text = str(value or "").strip()
    return text if text in ECONOMICS_COST_MODELS else None


def _assumptions_inputs(data: dict[str, Any]) -> dict[str, Any]:
    assumptions: dict[str, Any] = {"vat_mode": _vat_mode(data.get("vat_mode"))}
    for field in ("vat_rate_percent", "risk_reserve_percent", "target_margin_percent"):
        number = _percent(data.get(field))
        if number is not None:
            assumptions[field] = number
    return assumptions


def _assumptions_from_auto_estimate(estimate: dict[str, Any]) -> dict[str, Any]:
    assumptions: dict[str, Any] = {
        "vat_mode": _vat_mode(estimate.get("tax_mode")),
        "target_margin_percent": DEFAULT_TARGET_MARGIN_PERCENT,
    }
    vat_rate_percent = _percent(estimate.get("vat_rate_percent"))
    if vat_rate_percent is not None:
        assumptions["vat_rate_percent"] = vat_rate_percent
    base_total_cost = _number(estimate.get("base_total_cost")) or 0.0
    risk_reserve = _number(estimate.get("risk_reserve")) or 0.0
    assumptions["risk_reserve_percent"] = _round_money((risk_reserve / base_total_cost) * 100) if base_total_cost else 0.0
    return assumptions


def _merge_auto_assumptions(current: Any, inferred: dict[str, Any]) -> dict[str, Any]:
    current_payload = dict(current) if isinstance(current, dict) else {}
    if current_payload:
        merged = {**inferred, **current_payload}
        if "vat_mode" in current_payload and "vat_rate_percent" not in current_payload:
            merged.pop("vat_rate_percent", None)
        return merged
    return inferred


def _vat_mode(value: Any) -> str:
    text = str(value or "unknown").strip()
    return text if text in VAT_MODES else "unknown"


def _percent(value: Any) -> float | None:
    number = _number(value)
    if number is None:
        return None
    return _round_money(min(100.0, number))


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
