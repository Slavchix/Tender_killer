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
        supplier_cost += item["estimated_total_cost"]

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
            "target_bid_price": None,
            "target_margin_percent": None,
            "gross_margin": None,
            "margin_percent": None,
            "missing_cost_inputs": missing_cost_inputs,
            "risk_types": risk_types,
            "bid_scenarios": [],
            "participation_decision": {
                "status": "needs_price",
                "label": "Нужна НМЦК",
                "limit_price": None,
                "recommendation": "Нужна НМЦК или цена закупки, чтобы принять решение по участию.",
            },
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
            "target_bid_price": None,
            "target_margin_percent": None,
            "gross_margin": None,
            "margin_percent": None,
            "missing_cost_inputs": missing_cost_inputs or ["товарные позиции"],
            "risk_types": risk_types,
            "bid_scenarios": [],
            "participation_decision": {
                "status": "needs_costs",
                "label": "Не хватает цен",
                "limit_price": None,
                "recommendation": "Добавьте себестоимость по позициям, чтобы принять решение по участию.",
            },
            "items": items,
        }

    supplier_cost = _round_money(supplier_cost)
    estimated_total_cost = _round_money(supplier_cost + (risk_reserve or 0.0))
    break_even_price = estimated_total_cost
    minimum_margin_price = _price_for_margin(estimated_total_cost, LOW_MARGIN_PERCENT)
    interesting_price = _price_for_margin(estimated_total_cost, INTERESTING_MARGIN_PERCENT)
    target_margin_percent = _target_margin_percent(items)
    target_bid_price = _price_for_margin(estimated_total_cost, target_margin_percent)
    bid_scenarios = _bid_scenarios(
        revenue,
        estimated_total_cost,
        break_even_price,
        minimum_margin_price,
        interesting_price,
        target_bid_price,
        target_margin_percent,
    )
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
        "target_bid_price": target_bid_price,
        "target_margin_percent": target_margin_percent,
        "gross_margin": gross_margin,
        "margin_percent": margin_percent,
        "missing_cost_inputs": [],
        "risk_types": risk_types,
        "bid_scenarios": bid_scenarios,
        "participation_decision": _participation_decision(
            revenue,
            break_even_price,
            minimum_margin_price,
            target_bid_price,
        ),
        "items": items,
    }


def _item_cost(profile: dict[str, Any]) -> dict[str, Any]:
    economics = _economics_payload(profile)
    assumptions = _assumptions_payload(profile)
    quantity = _number(profile.get("quantity")) or 1.0
    unit_cost = _first_number(economics, ("unit_cost", "unit_cost_rub", "supplier_unit_price", "supplier_unit_price_rub"))
    total_cost = _first_number(economics, ("total_cost", "total_cost_rub", "supplier_total_price", "supplier_total_price_rub"))
    if total_cost is None and unit_cost is not None:
        total_cost = quantity * unit_cost
    extra_costs = sum(
        _first_number(economics, (key,)) or 0.0
        for key in ("logistics_cost", "documents_cost", "other_costs")
    )
    vat_mode = _vat_mode(assumptions.get("vat_mode"))
    vat_rate_percent = _percent(assumptions.get("vat_rate_percent"))
    if vat_mode == "no_vat":
        vat_rate_percent = 0.0
    risk_reserve_percent = _percent(assumptions.get("risk_reserve_percent")) or 0.0
    target_margin_percent = _percent(assumptions.get("target_margin_percent"))
    base_cost = total_cost + extra_costs if total_cost is not None else None
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
    return {
        "product_name": str(profile.get("product_name") or "товарная позиция"),
        "quantity": quantity,
        "unit": profile.get("unit"),
        "unit_cost": _round_money(unit_cost) if unit_cost is not None else None,
        "total_cost": _round_money(total_cost) if total_cost is not None else None,
        "extra_costs": _round_money(extra_costs),
        "vat_mode": vat_mode,
        "vat_rate_percent": _round_percent(vat_rate_percent) if vat_rate_percent is not None else None,
        "vat_cost": vat_cost,
        "risk_reserve_percent": _round_percent(risk_reserve_percent),
        "position_risk_reserve": position_risk_reserve,
        "estimated_total_cost": estimated_total_cost,
        "target_margin_percent": _round_percent(target_margin_percent) if target_margin_percent is not None else None,
        "target_price": target_price,
    }


def _economics_payload(profile: dict[str, Any]) -> dict[str, Any]:
    raw_payload = profile.get("raw_payload")
    if isinstance(raw_payload, dict) and isinstance(raw_payload.get("economics"), dict):
        return raw_payload["economics"]
    return {}


def _assumptions_payload(profile: dict[str, Any]) -> dict[str, Any]:
    raw_payload = profile.get("raw_payload")
    if isinstance(raw_payload, dict) and isinstance(raw_payload.get("economics_assumptions"), dict):
        return raw_payload["economics_assumptions"]
    return {}


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


def _target_margin_percent(items: list[dict[str, Any]]) -> float:
    margins = [
        item["target_margin_percent"]
        for item in items
        if _number(item.get("target_margin_percent")) is not None
    ]
    if not margins:
        return INTERESTING_MARGIN_PERCENT
    return _round_percent(max(margins))


def _bid_scenarios(
    revenue: float,
    estimated_total_cost: float,
    break_even_price: float,
    minimum_margin_price: float,
    interesting_price: float,
    target_bid_price: float,
    target_margin_percent: float,
) -> list[dict[str, Any]]:
    scenarios = [
        ("break_even", "Безубыток", break_even_price, 0.0),
        ("minimum_margin", "Минимум", minimum_margin_price, LOW_MARGIN_PERCENT),
        ("target", "Цель", target_bid_price, target_margin_percent),
        ("interesting", "Интересно", interesting_price, INTERESTING_MARGIN_PERCENT),
        ("current_nmc", "НМЦК", _round_money(revenue), _margin_percent(revenue, estimated_total_cost)),
    ]
    return [
        _bid_scenario(scenario_id, label, price, margin_percent, estimated_total_cost)
        for scenario_id, label, price, margin_percent in scenarios
    ]


def _participation_decision(
    revenue: float,
    break_even_price: float,
    minimum_margin_price: float,
    target_bid_price: float,
) -> dict[str, Any]:
    if revenue >= target_bid_price:
        return {
            "status": "can_bid",
            "label": "Можно заходить",
            "limit_price": target_bid_price,
            "recommendation": "НМЦК выше целевой цены. Можно участвовать, если поставщик и условия подтверждены.",
        }
    if revenue >= minimum_margin_price:
        return {
            "status": "guarded_bid",
            "label": "Только с лимитом",
            "limit_price": minimum_margin_price,
            "recommendation": "НМЦК ниже целевой цены. Участвовать только если не снижаться ниже минимальной цены.",
        }
    if revenue >= break_even_price:
        return {
            "status": "low_margin",
            "label": "Низкая маржа",
            "limit_price": break_even_price,
            "recommendation": "НМЦК покрывает себестоимость, но не дает минимальную маржу. Участвовать рискованно.",
        }
    return {
        "status": "do_not_bid",
        "label": "Не заходить",
        "limit_price": break_even_price,
        "recommendation": "НМЦК ниже безубытка. Участие приведет к убытку без пересмотра себестоимости.",
    }


def _bid_scenario(
    scenario_id: str,
    label: str,
    price: float,
    margin_percent: float,
    estimated_total_cost: float,
) -> dict[str, Any]:
    return {
        "id": scenario_id,
        "label": label,
        "price": _round_money(price),
        "margin_amount": _round_money(price - estimated_total_cost),
        "margin_percent": _round_percent(margin_percent),
    }


def _margin_percent(price: float, cost: float) -> float:
    return _round_percent(((price - cost) / price) * 100) if price else 0.0


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
