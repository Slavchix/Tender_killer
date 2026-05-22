from __future__ import annotations

from typing import Any


RISK_RESERVE_RATES = {
    "delivery": 1.5,
    "packaging": 1.0,
    "warranty": 1.0,
    "acceptance": 1.0,
}
INTERESTING_MARGIN_PERCENT = 15.0
LOW_MARGIN_PERCENT = 7.0


def build_economics_summary(tender: dict[str, Any]) -> dict[str, Any]:
    revenue = _number(tender.get("price"))
    profiles = [profile for profile in tender.get("product_profiles") or [] if isinstance(profile, dict)]
    items: list[dict[str, Any]] = []
    missing_cost_inputs: list[str] = []
    supplier_cost = 0.0

    for profile in profiles:
        item = _item_cost(profile)
        items.append(item)
        if item["total_cost"] is None:
            missing_cost_inputs.append(item["product_name"])
            continue
        supplier_cost += item["total_cost"] + item["extra_costs"]

    risk_types = _risk_types(profiles)
    risk_reserve_rate_percent = _risk_reserve_rate_percent(risk_types)
    risk_reserve = _round_money(revenue * risk_reserve_rate_percent / 100) if revenue is not None else None

    if revenue is None:
        return {
            "status": "needs_price",
            "recommendation": "Нужна НМЦК или цена закупки для расчета.",
            "revenue": None,
            "supplier_cost": None,
            "risk_reserve_rate_percent": risk_reserve_rate_percent,
            "risk_reserve": None,
            "estimated_total_cost": None,
            "break_even_price": None,
            "minimum_margin_price": None,
            "interesting_price": None,
            "gross_margin": None,
            "margin_percent": None,
            "missing_cost_inputs": missing_cost_inputs,
            "risk_types": risk_types,
            "items": items,
        }

    if missing_cost_inputs or not profiles:
        return {
            "status": "needs_costs",
            "recommendation": "Нужно добавить закупочную себестоимость по позициям.",
            "revenue": _round_money(revenue),
            "supplier_cost": None,
            "risk_reserve_rate_percent": risk_reserve_rate_percent,
            "risk_reserve": risk_reserve,
            "estimated_total_cost": None,
            "break_even_price": None,
            "minimum_margin_price": None,
            "interesting_price": None,
            "gross_margin": None,
            "margin_percent": None,
            "missing_cost_inputs": missing_cost_inputs or ["товарные позиции"],
            "risk_types": risk_types,
            "items": items,
        }

    supplier_cost = _round_money(supplier_cost)
    estimated_total_cost = _round_money(supplier_cost + (risk_reserve or 0.0))
    break_even_price = estimated_total_cost
    minimum_margin_price = _price_for_margin(estimated_total_cost, LOW_MARGIN_PERCENT)
    interesting_price = _price_for_margin(estimated_total_cost, INTERESTING_MARGIN_PERCENT)
    gross_margin = _round_money(revenue - estimated_total_cost)
    margin_percent = _round_percent((gross_margin / revenue) * 100) if revenue else None
    status = _status_for_margin(margin_percent)
    return {
        "status": status,
        "recommendation": _recommendation_for_status(status),
        "revenue": _round_money(revenue),
        "supplier_cost": supplier_cost,
        "risk_reserve_rate_percent": risk_reserve_rate_percent,
        "risk_reserve": risk_reserve,
        "estimated_total_cost": estimated_total_cost,
        "break_even_price": break_even_price,
        "minimum_margin_price": minimum_margin_price,
        "interesting_price": interesting_price,
        "gross_margin": gross_margin,
        "margin_percent": margin_percent,
        "missing_cost_inputs": [],
        "risk_types": risk_types,
        "items": items,
    }


def _item_cost(profile: dict[str, Any]) -> dict[str, Any]:
    economics = _economics_payload(profile)
    quantity = _number(profile.get("quantity")) or 1.0
    unit_cost = _first_number(economics, ("unit_cost", "unit_cost_rub", "supplier_unit_price", "supplier_unit_price_rub"))
    total_cost = _first_number(economics, ("total_cost", "total_cost_rub", "supplier_total_price", "supplier_total_price_rub"))
    if total_cost is None and unit_cost is not None:
        total_cost = quantity * unit_cost
    extra_costs = sum(
        _first_number(economics, (key,)) or 0.0
        for key in ("logistics_cost", "documents_cost", "other_costs")
    )
    return {
        "product_name": str(profile.get("product_name") or "товарная позиция"),
        "quantity": quantity,
        "unit": profile.get("unit"),
        "unit_cost": _round_money(unit_cost) if unit_cost is not None else None,
        "total_cost": _round_money(total_cost) if total_cost is not None else None,
        "extra_costs": _round_money(extra_costs),
    }


def _economics_payload(profile: dict[str, Any]) -> dict[str, Any]:
    raw_payload = profile.get("raw_payload")
    if isinstance(raw_payload, dict) and isinstance(raw_payload.get("economics"), dict):
        return raw_payload["economics"]
    return {}


def _risk_types(profiles: list[dict[str, Any]]) -> list[str]:
    values: list[str] = []
    for profile in profiles:
        for requirement in profile.get("fulfillment_requirements") or []:
            if isinstance(requirement, dict) and requirement.get("type"):
                values.append(str(requirement["type"]))
    return sorted(set(values))


def _risk_reserve_rate_percent(risk_types: list[str]) -> float:
    return _round_percent(min(8.0, sum(RISK_RESERVE_RATES.get(risk_type, 0.5) for risk_type in risk_types)))


def _status_for_margin(margin_percent: float | None) -> str:
    if margin_percent is None:
        return "manual_review"
    if margin_percent >= INTERESTING_MARGIN_PERCENT:
        return "interesting"
    if margin_percent < LOW_MARGIN_PERCENT:
        return "low_margin"
    return "manual_review"


def _recommendation_for_status(status: str) -> str:
    if status == "interesting":
        return "Маржа выглядит интересной, но требует проверки поставщика и условий исполнения."
    if status == "low_margin":
        return "Маржа низкая: проверь себестоимость, доставку и резерв риска до участия."
    return "Нужна ручная проверка маржи и условий исполнения."


def _first_number(data: dict[str, Any], keys: tuple[str, ...]) -> float | None:
    for key in keys:
        value = _number(data.get(key))
        if value is not None:
            return value
    return None


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


def _round_percent(value: float) -> float:
    return round(value, 2)


def _price_for_margin(cost: float, margin_percent: float) -> float:
    return _round_money(cost / (1 - margin_percent / 100))
