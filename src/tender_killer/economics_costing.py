from __future__ import annotations

import math
from typing import Any

from .economics_constants import INTERESTING_MARGIN_PERCENT
from .economics_costing_models import LandedCostTotals


def _item_cost(profile: dict[str, Any]) -> dict[str, Any]:
    economics = _economics_payload(profile)
    assumptions = _assumptions_payload(profile)
    price_source = _price_source_payload(profile)
    cost_model = _cost_model(economics.get("cost_model"))
    if cost_model == "service":
        return _service_item_cost(profile, economics, assumptions, price_source)
    quantity = _number(profile.get("quantity"))
    if quantity is not None and quantity <= 0:
        quantity = None
    unit_cost_basis = _unit_cost_basis(economics.get("unit_cost_basis"))
    pack_quantity = _first_number(economics, ("pack_quantity", "supplier_pack_quantity", "quantity_per_pack", "items_per_pack"))
    if pack_quantity is not None and pack_quantity <= 0:
        pack_quantity = None
    unit_cost = _first_number(economics, ("unit_cost", "unit_cost_rub", "supplier_unit_price", "supplier_unit_price_rub"))
    total_cost = _first_number(economics, ("total_cost", "total_cost_rub", "supplier_total_price", "supplier_total_price_rub"))
    procurement_quantity = None
    normalized_unit_cost = unit_cost
    if total_cost is None and unit_cost is not None and quantity is not None:
        if unit_cost_basis == "supplier_pack" and pack_quantity:
            procurement_quantity = math.ceil(quantity / pack_quantity)
            total_cost = procurement_quantity * unit_cost
        else:
            total_cost = quantity * unit_cost
    elif unit_cost_basis == "supplier_pack" and quantity is not None and pack_quantity:
        procurement_quantity = math.ceil(quantity / pack_quantity)
    if total_cost is not None and quantity is not None and quantity > 0:
        normalized_unit_cost = total_cost / quantity
    logistics_cost = _first_number(economics, ("logistics_cost",)) or 0.0
    documents_cost = _first_number(economics, ("documents_cost",)) or 0.0
    packaging_cost = _first_number(economics, ("packaging_cost",)) or 0.0
    other_costs = _first_number(economics, ("other_costs",)) or 0.0
    extra_costs = logistics_cost + documents_cost + packaging_cost + other_costs
    vat_mode = _vat_mode(assumptions.get("vat_mode"))
    vat_rate_percent = _percent(assumptions.get("vat_rate_percent"))
    if vat_mode == "no_vat":
        vat_rate_percent = 0.0
    risk_reserve_percent = _percent(assumptions.get("risk_reserve_percent")) or 0.0
    target_margin_percent = _percent(assumptions.get("target_margin_percent"))
    base_cost = total_cost + extra_costs if total_cost is not None else None
    totals = _landed_cost_totals(
        base_cost,
        vat_mode,
        vat_rate_percent,
        risk_reserve_percent,
        target_margin_percent,
    )
    rounded_unit_cost = _round_money(unit_cost) if unit_cost is not None else None
    rounded_total_cost = _round_money(total_cost) if total_cost is not None else None
    return {
        "position_index": _positive_int(profile.get("position_index")),
        "product_name": str(profile.get("product_name") or "товарная позиция"),
        "cost_model": "product",
        "quantity": quantity,
        "unit": profile.get("unit"),
        "unit_cost": rounded_unit_cost,
        "unit_cost_basis": unit_cost_basis,
        "pack_quantity": _round_percent(pack_quantity) if pack_quantity is not None else None,
        "procurement_quantity": procurement_quantity,
        "normalized_unit_cost": _round_money(normalized_unit_cost) if normalized_unit_cost is not None else None,
        "total_cost": rounded_total_cost,
        "direct_cost": rounded_total_cost,
        "logistics_cost": _round_money(logistics_cost),
        "documents_cost": _round_money(documents_cost),
        "packaging_cost": _round_money(packaging_cost),
        "other_costs": _round_money(other_costs),
        "extra_costs": _round_money(extra_costs),
        "landed_cost": _round_money(base_cost) if base_cost is not None else None,
        "vat_mode": vat_mode,
        "vat_rate_percent": _round_percent(vat_rate_percent) if vat_rate_percent is not None else None,
        "vat_cost": totals.vat_cost,
        "risk_reserve_percent": _round_percent(risk_reserve_percent),
        "position_risk_reserve": totals.position_risk_reserve,
        "estimated_total_cost": totals.estimated_total_cost,
        "target_margin_percent": _round_percent(target_margin_percent) if target_margin_percent is not None else None,
        "target_price": totals.target_price,
        "price_passport": _price_passport(price_source, economics, rounded_unit_cost, rounded_total_cost),
        "unit_normalization": _unit_normalization(profile, price_source, rounded_unit_cost),
    }


def _service_item_cost(
    profile: dict[str, Any],
    economics: dict[str, Any],
    assumptions: dict[str, Any],
    price_source: dict[str, Any],
) -> dict[str, Any]:
    quantity = _number(profile.get("quantity"))
    if quantity is not None and quantity <= 0:
        quantity = None
    service_rate = _first_number(economics, ("service_rate", "service_tariff", "hour_rate", "shift_rate", "unit_cost"))
    service_volume = _first_number(economics, ("service_volume", "service_hours", "service_shifts", "work_volume")) or quantity
    service_minimum = _first_number(economics, ("service_minimum", "service_minimum_cost", "minimum_cost", "minimum_order_amount")) or 0.0
    total_cost = _first_number(economics, ("total_cost", "total_cost_rub", "service_total_cost"))
    if total_cost is None and service_rate is not None and service_volume is not None:
        total_cost = service_rate * service_volume
    if total_cost is not None:
        total_cost = max(total_cost, service_minimum)
    normalized_unit_cost = total_cost / quantity if total_cost is not None and quantity else service_rate
    logistics_cost = _first_number(economics, ("service_logistics_cost", "logistics_cost")) or 0.0
    equipment_cost = _first_number(economics, ("service_equipment_cost", "equipment_cost")) or 0.0
    documents_cost = _first_number(economics, ("documents_cost",)) or 0.0
    other_costs = _first_number(economics, ("other_costs",)) or 0.0
    extra_costs = logistics_cost + equipment_cost + documents_cost + other_costs
    vat_mode = _vat_mode(assumptions.get("vat_mode"))
    vat_rate_percent = _percent(assumptions.get("vat_rate_percent"))
    if vat_mode == "no_vat":
        vat_rate_percent = 0.0
    risk_reserve_percent = _percent(assumptions.get("risk_reserve_percent")) or 0.0
    target_margin_percent = _percent(assumptions.get("target_margin_percent"))
    base_cost = total_cost + extra_costs if total_cost is not None else None
    totals = _landed_cost_totals(
        base_cost,
        vat_mode,
        vat_rate_percent,
        risk_reserve_percent,
        target_margin_percent,
    )
    rounded_rate = _round_money(service_rate) if service_rate is not None else None
    rounded_total_cost = _round_money(total_cost) if total_cost is not None else None
    return {
        "position_index": _positive_int(profile.get("position_index")),
        "product_name": str(profile.get("product_name") or "услуга"),
        "cost_model": "service",
        "quantity": quantity,
        "unit": profile.get("unit"),
        "unit_cost": rounded_rate,
        "service_rate": rounded_rate,
        "service_volume": _round_percent(service_volume) if service_volume is not None else None,
        "service_minimum": _round_money(service_minimum),
        "unit_cost_basis": "service_rate",
        "pack_quantity": None,
        "procurement_quantity": None,
        "normalized_unit_cost": _round_money(normalized_unit_cost) if normalized_unit_cost is not None else None,
        "total_cost": rounded_total_cost,
        "direct_cost": rounded_total_cost,
        "logistics_cost": _round_money(logistics_cost),
        "service_logistics_cost": _round_money(logistics_cost),
        "equipment_cost": _round_money(equipment_cost),
        "service_equipment_cost": _round_money(equipment_cost),
        "documents_cost": _round_money(documents_cost),
        "packaging_cost": 0.0,
        "other_costs": _round_money(other_costs),
        "extra_costs": _round_money(extra_costs),
        "landed_cost": _round_money(base_cost) if base_cost is not None else None,
        "vat_mode": vat_mode,
        "vat_rate_percent": _round_percent(vat_rate_percent) if vat_rate_percent is not None else None,
        "vat_cost": totals.vat_cost,
        "risk_reserve_percent": _round_percent(risk_reserve_percent),
        "position_risk_reserve": totals.position_risk_reserve,
        "estimated_total_cost": totals.estimated_total_cost,
        "target_margin_percent": _round_percent(target_margin_percent) if target_margin_percent is not None else None,
        "target_price": totals.target_price,
        "price_passport": _price_passport(price_source, economics, rounded_rate, rounded_total_cost),
        "unit_normalization": None,
    }


def _economics_payload(profile: dict[str, Any]) -> dict[str, Any]:
    raw_payload = profile.get("raw_payload")
    if isinstance(raw_payload, dict) and isinstance(raw_payload.get("economics"), dict):
        return raw_payload["economics"]
    return {}


def _price_source_payload(profile: dict[str, Any]) -> dict[str, Any]:
    raw_payload = profile.get("raw_payload")
    if isinstance(raw_payload, dict) and isinstance(raw_payload.get("economics_price_source"), dict):
        return raw_payload["economics_price_source"]
    return {}


def _assumptions_payload(profile: dict[str, Any]) -> dict[str, Any]:
    raw_payload = profile.get("raw_payload")
    if isinstance(raw_payload, dict) and isinstance(raw_payload.get("economics_assumptions"), dict):
        return raw_payload["economics_assumptions"]
    return {}


def _price_passport(
    price_source: dict[str, Any],
    economics: dict[str, Any],
    unit_cost: float | None,
    total_cost: float | None,
) -> dict[str, Any]:
    included = total_cost is not None
    source_type = str(price_source.get("source") or "").strip()
    if not source_type:
        source_type = "manual" if economics and included else "missing"
    status = _price_passport_status(price_source, source_type, included)
    supplier_name = _text(price_source.get("supplier_name"))
    provider = _text(price_source.get("provider"))
    source_label = (
        supplier_name
        or provider
        or _text(price_source.get("product_name"))
        or ("Manual input" if source_type == "manual" else "No price")
    )
    url = _text(price_source.get("source_url") or price_source.get("supplier_url") or price_source.get("url"))
    return {
        "status": status,
        "source_type": source_type,
        "source_label": source_label,
        "supplier_name": supplier_name,
        "url": url,
        "provider": provider,
        "confidence": _text(price_source.get("confidence") or price_source.get("quality_status")),
        "included_in_calculation": included,
        "unit_price": unit_cost,
        "total_price": total_cost,
        "currency": _text(price_source.get("currency")) or ("RUB" if unit_cost is not None else None),
        "selection": _text(price_source.get("selection")),
    }


def _price_passport_status(price_source: dict[str, Any], source_type: str, included: bool) -> str:
    if not included:
        return "missing"
    review_status = str(price_source.get("review_status") or price_source.get("status") or "").strip()
    selection = str(price_source.get("selection") or "").strip()
    confidence = str(price_source.get("confidence") or "").strip()
    if review_status in {"confirmed", "selected"} or selection in {"manual_confirmed", "manual_selected"}:
        return "confirmed"
    if confidence == "confirmed":
        return "confirmed"
    if source_type == "manual":
        return "manual"
    return "review"


def _unit_cost_basis(value: Any) -> str:
    text = str(value or "tender_unit").strip()
    if text in {"tender_unit", "supplier_pack"}:
        return text
    return "tender_unit"


def _cost_model(value: Any) -> str:
    text = str(value or "product").strip()
    if text == "service":
        return "service"
    return "product"


def _unit_normalization(
    profile: dict[str, Any],
    price_source: dict[str, Any],
    unit_cost: float | None,
) -> dict[str, Any]:
    normalization = price_source.get("normalization") if isinstance(price_source.get("normalization"), dict) else {}
    tender_unit = _text(profile.get("unit"))
    supplier_unit = (
        _text(price_source.get("supplier_unit"))
        or _text(price_source.get("source_unit"))
        or _text(price_source.get("candidate_unit"))
        or _text(price_source.get("unit"))
        or tender_unit
    )
    coefficient = (
        _first_number(normalization, ("pack_quantity", "coefficient", "quantity_coefficient"))
        or _first_number(price_source, ("pack_quantity", "coefficient", "quantity_coefficient"))
        or 1.0
    )
    original_unit_price = (
        _first_number(normalization, ("original_unit_price",))
        or _first_number(price_source, ("original_unit_price", "unit_price"))
        or unit_cost
    )
    normalized_unit_price = (
        _first_number(normalization, ("normalized_unit_price",))
        or _first_number(price_source, ("normalized_unit_price",))
        or unit_cost
    )
    status = "normalized" if coefficient and coefficient != 1.0 else "same_unit"
    if unit_cost is None:
        status = "missing"
    return {
        "tender_unit": tender_unit,
        "supplier_unit": supplier_unit,
        "coefficient": _round_percent(coefficient),
        "original_unit_price": _round_money(original_unit_price) if original_unit_price is not None else None,
        "normalized_unit_price": _round_money(normalized_unit_price) if normalized_unit_price is not None else None,
        "source": _text(normalization.get("source") or price_source.get("source_kind") or price_source.get("source")),
        "status": status,
    }


def _vat_mode(value: Any) -> str:
    text = str(value or "unknown").strip()
    if text in {"vat_included", "vat_excluded", "no_vat", "unknown"}:
        return text
    return "unknown"


def _percent(value: Any) -> float | None:
    number = _number(value)
    if number is None:
        return None
    return min(100.0, number)


def _vat_cost(base_cost: float | None, vat_mode: str, vat_rate_percent: float | None) -> float:
    if base_cost is None or vat_mode != "vat_excluded":
        return 0.0
    return _round_money(base_cost * (vat_rate_percent or 0.0) / 100)


def _position_risk_reserve(base_cost: float | None, vat_cost: float, risk_reserve_percent: float) -> float:
    if base_cost is None:
        return 0.0
    return _round_money((base_cost + vat_cost) * risk_reserve_percent / 100)


def _landed_cost_totals(
    base_cost: float | None,
    vat_mode: str,
    vat_rate_percent: float | None,
    risk_reserve_percent: float,
    target_margin_percent: float | None,
) -> LandedCostTotals:
    vat_cost = _vat_cost(base_cost, vat_mode, vat_rate_percent)
    position_risk_reserve = _position_risk_reserve(base_cost, vat_cost, risk_reserve_percent)
    estimated_total_cost = (
        _round_money(base_cost + vat_cost + position_risk_reserve)
        if base_cost is not None
        else None
    )
    target_price = (
        _price_for_margin(estimated_total_cost, target_margin_percent)
        if estimated_total_cost is not None and target_margin_percent is not None and target_margin_percent < 100
        else None
    )
    return LandedCostTotals(
        base_cost=base_cost,
        vat_mode=vat_mode,
        vat_rate_percent=vat_rate_percent,
        vat_cost=vat_cost,
        risk_reserve_percent=risk_reserve_percent,
        position_risk_reserve=position_risk_reserve,
        estimated_total_cost=estimated_total_cost,
        target_margin_percent=target_margin_percent,
        target_price=target_price,
    )


def _target_margin_percent(items: list[dict[str, Any]]) -> float:
    margins = [
        item["target_margin_percent"]
        for item in items
        if _number(item.get("target_margin_percent")) is not None
    ]
    if not margins:
        return INTERESTING_MARGIN_PERCENT
    return _round_percent(max(margins))


def _position_risk_reserve_total(items: list[dict[str, Any]]) -> float:
    return _round_money(sum(_number(item.get("position_risk_reserve")) or 0.0 for item in items))


def _position_risk_reserve_rate_percent(items: list[dict[str, Any]]) -> float:
    reserve = _position_risk_reserve_total(items)
    if not reserve:
        return 0.0
    base_cost = sum(
        _position_risk_reserve_base(item)
        for item in items
    )
    return _round_percent((reserve / base_cost) * 100) if base_cost else 0.0


def _position_risk_reserve_base(item: dict[str, Any]) -> float:
    estimated_total = _number(item.get("estimated_total_cost")) or 0.0
    reserve = _number(item.get("position_risk_reserve")) or 0.0
    return max(0.0, estimated_total - reserve)


def _cost_breakdown(
    items: list[dict[str, Any]],
    *,
    supplier_cost: float | None,
    estimated_total_cost: float | None,
    execution_risk_reserve: float | None,
    risk_reserve: float | None,
    security_amount: float,
) -> dict[str, Any]:
    cash_required = (
        _round_money((estimated_total_cost or 0.0) + security_amount)
        if estimated_total_cost is not None or security_amount
        else None
    )
    return {
        "direct_cost": _sum_item_money(items, "direct_cost"),
        "logistics_cost": _sum_item_money(items, "logistics_cost"),
        "equipment_cost": _sum_item_money(items, "equipment_cost"),
        "documents_cost": _sum_item_money(items, "documents_cost"),
        "packaging_cost": _sum_item_money(items, "packaging_cost"),
        "other_costs": _sum_item_money(items, "other_costs"),
        "vat_cost": _sum_item_money(items, "vat_cost"),
        "position_risk_reserve": _position_risk_reserve_total(items),
        "execution_risk_reserve": _round_money(execution_risk_reserve) if execution_risk_reserve is not None else None,
        "risk_reserve": _round_money(risk_reserve) if risk_reserve is not None else None,
        "supplier_cost": _round_money(supplier_cost) if supplier_cost is not None else None,
        "estimated_total_cost": _round_money(estimated_total_cost) if estimated_total_cost is not None else None,
        "security_amount": security_amount,
        "cash_required": cash_required,
    }


def _sum_item_money(items: list[dict[str, Any]], key: str) -> float:
    return _round_money(sum(_number(item.get(key)) or 0.0 for item in items))


def _first_number(data: dict[str, Any], keys: tuple[str, ...]) -> float | None:
    for key in keys:
        value = _number(data.get(key))
        if value is not None:
            return value
    return None


def _text(value: Any) -> str | None:
    if value in (None, ""):
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


def _positive_number(value: Any) -> float | None:
    number = _number(value)
    if number is None or number <= 0:
        return None
    return number


def _positive_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def _round_money(value: float) -> float:
    return round(value, 2)


def _round_percent(value: float) -> float:
    return round(value, 2)


def _price_for_margin(cost: float, margin_percent: float) -> float:
    return _round_money(cost / (1 - margin_percent / 100))
