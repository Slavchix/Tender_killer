from __future__ import annotations

import math
from typing import Any


RISK_RESERVE_RATES = {
    "delivery": 1.5,
    "packaging": 1.0,
    "warranty": 1.0,
    "acceptance": 1.0,
}
ANALYSIS_COST_DRIVER_SECTIONS = {"blockers", "price_factors"}
ANALYSIS_COST_DRIVER_CATEGORIES = {
    "acceptance",
    "contract",
    "delivery",
    "documents",
    "financial",
    "standards",
}
ANALYSIS_RESERVE_HINT_RATES = {
    "high": 2.0,
    "medium": 1.0,
    "low": 0.5,
}
INTERESTING_MARGIN_PERCENT = 15.0
LOW_MARGIN_PERCENT = 7.0


def build_economics_summary(tender: dict[str, Any]) -> dict[str, Any]:
    market_state = _market_state(tender)
    nmc_price = _number(market_state.get("nmc_price")) or _number(tender.get("price"))
    current_offer_price = _positive_number(market_state.get("current_offer_price"))
    revenue = current_offer_price if current_offer_price is not None else nmc_price
    revenue_kind = "current_offer" if current_offer_price is not None else "nmc"
    price_context = _price_context(revenue, revenue_kind, nmc_price, market_state)
    analysis_cost_drivers = _analysis_cost_drivers(tender.get("analysis"))
    analysis_context = {
        "analysis_cost_drivers": analysis_cost_drivers,
        "analysis_reserve_hint": _analysis_reserve_hint(analysis_cost_drivers),
    }
    security_obligations = _security_obligations(tender.get("analysis"), revenue)
    security_amount = _round_money(sum(_number(item.get("amount")) or 0.0 for item in security_obligations))
    item_fallbacks = _items_by_position(tender.get("items"))
    profiles = [
        _profile_with_item_fallback(profile, item_fallbacks.get(_positive_int(profile.get("position_index")) or 0))
        for profile in tender.get("product_profiles") or []
        if isinstance(profile, dict)
    ]
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
    profile_execution_risk_reserve_rate_percent = _risk_reserve_rate_percent(risk_types)
    analysis_execution_risk_reserve_rate_percent = _number(
        analysis_context["analysis_reserve_hint"].get("rate_percent")
    ) or 0.0
    execution_risk_reserve_rate_percent = max(
        profile_execution_risk_reserve_rate_percent,
        analysis_execution_risk_reserve_rate_percent,
    )
    execution_risk_reserve = (
        _round_money(revenue * execution_risk_reserve_rate_percent / 100)
        if revenue is not None
        else 0.0
    )
    position_risk_reserve = _position_risk_reserve_total(items)
    risk_reserve_rate_percent = _combined_risk_reserve_rate_percent(
        _position_risk_reserve_rate_percent(items),
        execution_risk_reserve_rate_percent,
    )
    risk_reserve = _round_money(position_risk_reserve + execution_risk_reserve)

    if revenue is None:
        decision = {
            "status": "needs_price",
            "label": "Нужна НМЦК",
            "limit_price": None,
            "recommendation": "Нужна НМЦК или цена закупки, чтобы принять решение по участию.",
        }
        cost_breakdown = _cost_breakdown(
            items,
            supplier_cost=None,
            estimated_total_cost=None,
            execution_risk_reserve=None,
            risk_reserve=risk_reserve if risk_reserve else None,
            security_amount=security_amount,
        )
        return {
            "status": "needs_price",
            "recommendation": "Нужна НМЦК или цена закупки для расчета.",
            **price_context,
            **analysis_context,
            "financial_model_version": 1,
            "supplier_cost": None,
            "risk_reserve_rate_percent": risk_reserve_rate_percent,
            "risk_reserve": risk_reserve if risk_reserve else None,
            "position_risk_reserve": position_risk_reserve,
            "execution_risk_reserve": None,
            "estimated_total_cost": None,
            "break_even_price": None,
            "minimum_margin_price": None,
            "interesting_price": None,
            "target_bid_price": None,
            "stop_price": None,
            "cost_breakdown": cost_breakdown,
            "security_amount": security_amount,
            "security_obligations": security_obligations,
            "financial_model": _financial_model(
                revenue=None,
                revenue_kind=revenue_kind,
                break_even_price=None,
                minimum_margin_price=None,
                target_margin_percent=None,
                stop_price=None,
                gross_margin=None,
                margin_percent=None,
                risk_reserve=risk_reserve if risk_reserve else None,
                security_amount=security_amount,
                cost_breakdown=cost_breakdown,
                security_obligations=security_obligations,
            ),
            "target_margin_percent": None,
            "gross_margin": None,
            "margin_percent": None,
            "missing_cost_inputs": missing_cost_inputs,
            "risk_types": risk_types,
            "bid_scenarios": [],
            "participation_decision": decision,
            "participation_calculation": _participation_calculation(
                decision,
                current_price=None,
                stop_price=None,
                break_even_price=None,
                profit=None,
                margin_percent=None,
                target_margin_percent=None,
                risk_reserve=risk_reserve if risk_reserve else None,
                security_amount=security_amount,
            ),
            "items": items,
        }

    if missing_cost_inputs or not profiles:
        decision = {
            "status": "needs_costs",
            "label": "Не хватает цен",
            "limit_price": None,
            "recommendation": "Добавьте себестоимость по позициям, чтобы принять решение по участию.",
        }
        cost_breakdown = _cost_breakdown(
            items,
            supplier_cost=None,
            estimated_total_cost=None,
            execution_risk_reserve=execution_risk_reserve,
            risk_reserve=risk_reserve,
            security_amount=security_amount,
        )
        return {
            "status": "needs_costs",
            "recommendation": "Нужно добавить закупочную себестоимость по позициям.",
            **price_context,
            **analysis_context,
            "financial_model_version": 1,
            "supplier_cost": None,
            "risk_reserve_rate_percent": risk_reserve_rate_percent,
            "risk_reserve": risk_reserve,
            "position_risk_reserve": position_risk_reserve,
            "execution_risk_reserve": execution_risk_reserve,
            "estimated_total_cost": None,
            "break_even_price": None,
            "minimum_margin_price": None,
            "interesting_price": None,
            "target_bid_price": None,
            "stop_price": None,
            "cost_breakdown": cost_breakdown,
            "security_amount": security_amount,
            "security_obligations": security_obligations,
            "financial_model": _financial_model(
                revenue=revenue,
                revenue_kind=revenue_kind,
                break_even_price=None,
                minimum_margin_price=None,
                target_margin_percent=None,
                stop_price=None,
                gross_margin=None,
                margin_percent=None,
                risk_reserve=risk_reserve,
                security_amount=security_amount,
                cost_breakdown=cost_breakdown,
                security_obligations=security_obligations,
            ),
            "target_margin_percent": None,
            "gross_margin": None,
            "margin_percent": None,
            "missing_cost_inputs": missing_cost_inputs or ["товарные позиции"],
            "risk_types": risk_types,
            "bid_scenarios": [],
            "participation_decision": decision,
            "participation_calculation": _participation_calculation(
                decision,
                current_price=revenue,
                stop_price=None,
                break_even_price=None,
                profit=None,
                margin_percent=None,
                target_margin_percent=None,
                risk_reserve=risk_reserve,
                security_amount=security_amount,
            ),
            "items": items,
        }

    supplier_cost = _round_money(supplier_cost)
    estimated_total_cost = _round_money(supplier_cost + execution_risk_reserve)
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
        revenue_kind,
        nmc_price,
        market_state,
    )
    gross_margin = _round_money(revenue - estimated_total_cost)
    margin_percent = _round_percent((gross_margin / revenue) * 100) if revenue else None
    status = _status_for_margin(margin_percent)
    participation_decision = _participation_decision(
        revenue,
        break_even_price,
        minimum_margin_price,
        target_bid_price,
    )
    cost_breakdown = _cost_breakdown(
        items,
        supplier_cost=supplier_cost,
        estimated_total_cost=estimated_total_cost,
        execution_risk_reserve=execution_risk_reserve,
        risk_reserve=risk_reserve,
        security_amount=security_amount,
    )
    return {
        "status": status,
        "recommendation": _recommendation_for_status(status),
        **price_context,
        **analysis_context,
        "financial_model_version": 1,
        "supplier_cost": supplier_cost,
        "risk_reserve_rate_percent": risk_reserve_rate_percent,
        "risk_reserve": risk_reserve,
        "position_risk_reserve": position_risk_reserve,
        "execution_risk_reserve": execution_risk_reserve,
        "estimated_total_cost": estimated_total_cost,
        "break_even_price": break_even_price,
        "minimum_margin_price": minimum_margin_price,
        "interesting_price": interesting_price,
        "target_bid_price": target_bid_price,
        "stop_price": target_bid_price,
        "cost_breakdown": cost_breakdown,
        "security_amount": security_amount,
        "security_obligations": security_obligations,
        "financial_model": _financial_model(
            revenue=revenue,
            revenue_kind=revenue_kind,
            break_even_price=break_even_price,
            minimum_margin_price=minimum_margin_price,
            target_margin_percent=target_margin_percent,
            stop_price=target_bid_price,
            gross_margin=gross_margin,
            margin_percent=margin_percent,
            risk_reserve=risk_reserve,
            security_amount=security_amount,
            cost_breakdown=cost_breakdown,
            security_obligations=security_obligations,
        ),
        "target_margin_percent": target_margin_percent,
        "gross_margin": gross_margin,
        "margin_percent": margin_percent,
        "missing_cost_inputs": [],
        "risk_types": risk_types,
        "bid_scenarios": bid_scenarios,
        "participation_decision": participation_decision,
        "participation_calculation": _participation_calculation(
            participation_decision,
            current_price=revenue,
            stop_price=target_bid_price,
            break_even_price=break_even_price,
            profit=gross_margin,
            margin_percent=margin_percent,
            target_margin_percent=target_margin_percent,
            risk_reserve=risk_reserve,
            security_amount=security_amount,
        ),
        "items": items,
    }


def _item_cost(profile: dict[str, Any]) -> dict[str, Any]:
    economics = _economics_payload(profile)
    assumptions = _assumptions_payload(profile)
    price_source = _price_source_payload(profile)
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
    rounded_unit_cost = _round_money(unit_cost) if unit_cost is not None else None
    rounded_total_cost = _round_money(total_cost) if total_cost is not None else None
    return {
        "position_index": _positive_int(profile.get("position_index")),
        "product_name": str(profile.get("product_name") or "товарная позиция"),
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
        "vat_cost": vat_cost,
        "risk_reserve_percent": _round_percent(risk_reserve_percent),
        "position_risk_reserve": position_risk_reserve,
        "estimated_total_cost": estimated_total_cost,
        "target_margin_percent": _round_percent(target_margin_percent) if target_margin_percent is not None else None,
        "target_price": target_price,
        "price_passport": _price_passport(price_source, economics, rounded_unit_cost, rounded_total_cost),
        "unit_normalization": _unit_normalization(profile, price_source, rounded_unit_cost),
    }


def _items_by_position(items: Any) -> dict[int, dict[str, Any]]:
    if not isinstance(items, list):
        return {}
    result: dict[int, dict[str, Any]] = {}
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            continue
        position_index = _positive_int(item.get("position_index")) or index
        if position_index > 0:
            result[position_index] = item
    return result


def _profile_with_item_fallback(profile: dict[str, Any], item: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(item, dict):
        return profile
    enriched = dict(profile)
    for key in ("quantity", "unit"):
        if enriched.get(key) in (None, "") and item.get(key) not in (None, ""):
            enriched[key] = item.get(key)
    return enriched


def _market_state(tender: dict[str, Any]) -> dict[str, Any]:
    state = tender.get("market_state")
    market_state = dict(state) if isinstance(state, dict) else {}
    if "current_offer_price" in market_state:
        market_state["current_offer_price"] = _positive_number(market_state.get("current_offer_price"))
    else:
        current_offer_price = _positive_number(tender.get("current_offer_price"))
        if current_offer_price is not None:
            market_state["current_offer_price"] = current_offer_price
    if "nmc_price" not in market_state and _number(tender.get("price")) is not None:
        market_state["nmc_price"] = _number(tender.get("price"))
    return market_state


def _price_context(
    revenue: float | None,
    revenue_kind: str,
    nmc_price: float | None,
    market_state: dict[str, Any],
) -> dict[str, Any]:
    return {
        "revenue": _round_money(revenue) if revenue is not None else None,
        "revenue_kind": revenue_kind,
        "nmc_price": _round_money(nmc_price) if nmc_price is not None else None,
        "market_state": {
            **market_state,
            "nmc_price": _round_money(nmc_price) if nmc_price is not None else market_state.get("nmc_price"),
        },
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


def _financial_model(
    *,
    revenue: float | None,
    revenue_kind: str,
    break_even_price: float | None,
    minimum_margin_price: float | None,
    target_margin_percent: float | None,
    stop_price: float | None,
    gross_margin: float | None,
    margin_percent: float | None,
    risk_reserve: float | None,
    security_amount: float,
    cost_breakdown: dict[str, Any],
    security_obligations: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "version": 1,
        "revenue": _round_money(revenue) if revenue is not None else None,
        "revenue_kind": revenue_kind,
        "break_even_price": _round_money(break_even_price) if break_even_price is not None else None,
        "minimum_margin_price": _round_money(minimum_margin_price) if minimum_margin_price is not None else None,
        "target_margin_percent": _round_percent(target_margin_percent) if target_margin_percent is not None else None,
        "stop_price": _round_money(stop_price) if stop_price is not None else None,
        "gross_margin": _round_money(gross_margin) if gross_margin is not None else None,
        "margin_percent": _round_percent(margin_percent) if margin_percent is not None else None,
        "risk_reserve": _round_money(risk_reserve) if risk_reserve is not None else None,
        "security_amount": security_amount,
        "cost_breakdown": cost_breakdown,
        "security_obligations": security_obligations,
    }


def _participation_calculation(
    decision: dict[str, Any],
    *,
    current_price: float | None,
    stop_price: float | None,
    break_even_price: float | None,
    profit: float | None,
    margin_percent: float | None,
    target_margin_percent: float | None,
    risk_reserve: float | None,
    security_amount: float,
) -> dict[str, Any]:
    return {
        "status": decision.get("status"),
        "label": decision.get("label"),
        "current_price": _round_money(current_price) if current_price is not None else None,
        "stop_price": _round_money(stop_price) if stop_price is not None else None,
        "break_even_price": _round_money(break_even_price) if break_even_price is not None else None,
        "profit": _round_money(profit) if profit is not None else None,
        "margin_percent": _round_percent(margin_percent) if margin_percent is not None else None,
        "target_margin_percent": _round_percent(target_margin_percent) if target_margin_percent is not None else None,
        "risk_reserve": _round_money(risk_reserve) if risk_reserve is not None else None,
        "security_amount": security_amount,
        "headroom_to_stop_price": _money_delta(current_price, stop_price),
        "headroom_to_break_even": _money_delta(current_price, break_even_price),
        "reason": _participation_reason(str(decision.get("status") or "")),
    }


def _security_obligations(analysis: Any, revenue: float | None) -> list[dict[str, Any]]:
    if not isinstance(analysis, dict):
        return []

    items: list[dict[str, Any]] = []
    facts = analysis.get("analysis_facts")
    fact_items = facts.get("items") if isinstance(facts, dict) and facts.get("version") == 1 else None
    if isinstance(fact_items, list):
        items.extend(item for item in fact_items if isinstance(item, dict))
    execution_terms = analysis.get("execution_terms")
    if isinstance(execution_terms, list):
        items.extend(item for item in execution_terms if isinstance(item, dict))

    obligations: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for item in items:
        if not _is_security_obligation(item):
            continue
        label = _text(item.get("label") or item.get("type")) or "Обеспечение исполнения"
        source = _text(item.get("document_name") or item.get("source")) or ""
        key = (label.casefold(), source.casefold())
        if key in seen:
            continue
        seen.add(key)
        amount_percent = _percent(item.get("amount_percent") or item.get("percent"))
        amount = _first_number(item, ("amount", "amount_rub", "amount_value", "security_amount", "security_amount_rub"))
        if amount is None and amount_percent is not None and revenue is not None:
            amount = revenue * amount_percent / 100
        obligations.append(
            {
                "label": label,
                "amount_percent": _round_percent(amount_percent) if amount_percent is not None else None,
                "amount": _round_money(amount) if amount is not None else None,
                "source": source,
                "source_page": _positive_int(item.get("source_page")),
                "impact": _text(item.get("price_impact") or item.get("impact_type")) or "working_capital",
            }
        )
    return obligations


def _sum_item_money(items: list[dict[str, Any]], key: str) -> float:
    return _round_money(sum(_number(item.get(key)) or 0.0 for item in items))


def _money_delta(left: float | None, right: float | None) -> float | None:
    if left is None or right is None:
        return None
    return _round_money(left - right)


def _participation_reason(status: str) -> str:
    if status == "can_bid":
        return "Ставка выше стоп-цены, целевая маржа сохранена."
    if status == "guarded_bid":
        return "Ставка ниже целевой стоп-цены: можно участвовать только с жестким лимитом."
    if status == "low_margin":
        return "Ставка покрывает затраты, но запас ниже минимальной маржи."
    if status == "do_not_bid":
        return "Ставка ниже безубытка: участие убыточно без пересмотра затрат."
    if status == "needs_price":
        return "Нужна НМЦК или текущая ставка, чтобы посчитать лимит участия."
    return "Нужны цены поставщиков, чтобы собрать расчет участия."


def _is_security_obligation(item: dict[str, Any]) -> bool:
    combined = " ".join(
        str(item.get(key) or "")
        for key in ("amount_type", "type", "family", "label", "value", "fragment", "evidence")
    ).casefold()
    return (
        "contract_security" in combined
        or "security" in combined
        or "независим" in combined
        or ("обеспеч" in combined and ("исполн" in combined or "контракт" in combined or "договор" in combined))
    )


def _combined_risk_reserve_rate_percent(position_rate: float, execution_rate: float) -> float:
    return _round_percent(position_rate + execution_rate)


def _bid_scenarios(
    revenue: float,
    estimated_total_cost: float,
    break_even_price: float,
    minimum_margin_price: float,
    interesting_price: float,
    target_bid_price: float,
    target_margin_percent: float,
    revenue_kind: str,
    nmc_price: float | None,
    market_state: dict[str, Any],
) -> list[dict[str, Any]]:
    current_id = "current_offer" if revenue_kind == "current_offer" else "current_nmc"
    current_label = "Текущая ставка" if revenue_kind == "current_offer" else "НМЦК"
    scenarios = [
        ("break_even", "Безубыток", break_even_price, 0.0),
        ("minimum_margin", "Минимум", minimum_margin_price, LOW_MARGIN_PERCENT),
        ("target", "Цель", target_bid_price, target_margin_percent),
        ("interesting", "Интересно", interesting_price, INTERESTING_MARGIN_PERCENT),
        (current_id, current_label, _round_money(revenue), _margin_percent(revenue, estimated_total_cost)),
    ]
    current_scenario = scenarios.pop()
    if revenue_kind == "current_offer" and nmc_price is not None:
        scenarios.append(
            (
                "nmc",
                "НМЦК",
                _round_money(nmc_price),
                _margin_percent(nmc_price, estimated_total_cost),
                "reference",
                "nmc_reference",
                False,
            )
        )
    next_bid_price = _positive_number(market_state.get("next_bid_price"))
    if next_bid_price is not None and next_bid_price != revenue:
        scenarios.append(
            (
                "next_bid",
                "Следующий шаг",
                next_bid_price,
                _margin_percent(next_bid_price, estimated_total_cost),
                "aggressive",
                "next_bid",
                False,
            )
        )
    scenarios.append(current_scenario)

    result = []
    for scenario in scenarios:
        scenario_id, label, price, margin_percent = scenario[:4]
        if len(scenario) >= 7:
            role, decision, is_current = scenario[4:7]
        else:
            role, decision, is_current = _bid_scenario_meta(str(scenario_id))
        result.append(
            _bid_scenario(
                str(scenario_id),
                str(label),
                price,
                margin_percent,
                estimated_total_cost,
                str(role),
                str(decision),
                bool(is_current),
            )
        )
    return result


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
    role: str,
    decision: str,
    is_current: bool,
) -> dict[str, Any]:
    profit = _round_money(price - estimated_total_cost)
    return {
        "id": scenario_id,
        "label": label,
        "price": _round_money(price),
        "margin_amount": profit,
        "profit": profit,
        "margin_percent": _round_percent(margin_percent),
        "role": role,
        "decision": decision,
        "is_current": is_current,
    }


def _bid_scenario_meta(scenario_id: str) -> tuple[str, str, bool]:
    metadata = {
        "break_even": ("threshold", "break_even", False),
        "minimum_margin": ("threshold", "minimum_margin", False),
        "target": ("target", "target_margin", False),
        "interesting": ("target", "interesting_margin", False),
        "current_offer": ("current", "current_offer", True),
        "current_nmc": ("current", "current_nmc", True),
    }
    return metadata.get(scenario_id, ("reference", scenario_id, False))


def _margin_percent(price: float, cost: float) -> float:
    return _round_percent(((price - cost) / price) * 100) if price else 0.0


def _risk_types(profiles: list[dict[str, Any]]) -> list[str]:
    values: list[str] = []
    for profile in profiles:
        for requirement in profile.get("fulfillment_requirements") or []:
            if isinstance(requirement, dict) and requirement.get("type"):
                values.append(str(requirement["type"]))
    return sorted(set(values))


def _analysis_cost_drivers(analysis: Any) -> list[dict[str, Any]]:
    if not isinstance(analysis, dict):
        return []
    fact_drivers = _analysis_fact_cost_drivers(analysis)
    if fact_drivers:
        return fact_drivers
    sections = _analysis_cost_driver_sections(analysis)
    if not sections:
        return []

    drivers: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for section in sections:
        if not isinstance(section, dict) or section.get("id") not in ANALYSIS_COST_DRIVER_SECTIONS:
            continue
        for item in section.get("items") or []:
            if not isinstance(item, dict) or not item.get("label"):
                continue
            category = str(item.get("category") or "general")
            severity = str(item.get("severity") or "medium")
            if category not in ANALYSIS_COST_DRIVER_CATEGORIES and severity != "high":
                continue
            key = (str(item["label"]), category)
            if key in seen:
                continue
            seen.add(key)
            drivers.append(
                {
                    "label": str(item["label"]),
                    "category": category,
                    "severity": severity,
                    "source": str(item.get("source") or ""),
                    "impact": str(item.get("impact") or item.get("description") or item.get("value") or ""),
                    "reserve_hint_percent": _analysis_driver_reserve_hint(severity),
                }
            )
    return drivers


def _analysis_fact_cost_drivers(analysis: dict[str, Any]) -> list[dict[str, Any]]:
    facts = analysis.get("analysis_facts")
    fact_items = facts.get("items") if isinstance(facts, dict) and facts.get("version") == 1 else None
    if not isinstance(fact_items, list):
        return []

    drivers: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for item in fact_items:
        if not isinstance(item, dict) or not item.get("label"):
            continue
        if not item.get("is_blocker") and not item.get("is_price_factor"):
            continue
        category = str(item.get("category") or "general")
        severity = str(item.get("severity") or "medium")
        if category not in ANALYSIS_COST_DRIVER_CATEGORIES and severity != "high":
            continue
        key = (str(item["label"]), category)
        if key in seen:
            continue
        seen.add(key)
        drivers.append(
            {
                "label": str(item["label"]),
                "category": category,
                "severity": severity,
                "source": str(item.get("document_name") or item.get("source") or ""),
                "impact": str(item.get("impact") or item.get("fragment") or ""),
                "reserve_hint_percent": _analysis_driver_reserve_hint(severity),
                **_analysis_driver_source_label(item),
            }
        )
    return drivers


def _analysis_cost_driver_sections(analysis: dict[str, Any]) -> list[dict[str, Any]]:
    sections: list[dict[str, Any]] = []

    passport = analysis.get("tz_passport")
    passport_sections = passport.get("sections") if isinstance(passport, dict) and passport.get("version") == 1 else None
    if isinstance(passport_sections, list):
        sections.extend(section for section in passport_sections if isinstance(section, dict))

    operator_view = analysis.get("operator_view")
    operator_sections = operator_view.get("sections") if isinstance(operator_view, dict) else None
    if isinstance(operator_sections, list):
        sections.extend(section for section in operator_sections if isinstance(section, dict))

    return sections


def _analysis_reserve_hint(drivers: list[dict[str, Any]]) -> dict[str, Any]:
    rate = _round_percent(
        min(
            8.0,
            sum(_number(driver.get("reserve_hint_percent")) or 0.0 for driver in drivers),
        )
    )
    severity_values = {str(driver.get("severity") or "") for driver in drivers}
    if not drivers:
        level = "none"
    elif "high" in severity_values or rate >= 4.0:
        level = "high"
    elif rate >= 2.0:
        level = "medium"
    else:
        level = "low"
    return {
        "driver_count": len(drivers),
        "level": level,
        "rate_percent": rate,
    }


def _analysis_driver_reserve_hint(severity: str) -> float:
    return ANALYSIS_RESERVE_HINT_RATES.get(severity, ANALYSIS_RESERVE_HINT_RATES["medium"])


def _analysis_driver_source_label(item: dict[str, Any]) -> dict[str, str]:
    explicit = str(item.get("source_label") or "").strip()
    if explicit:
        return {"source_label": explicit}
    source = str(item.get("document_name") or item.get("source") or "").strip()
    page = _positive_int(item.get("source_page"))
    if source and page is not None:
        return {"source_label": f"{source} · стр. {page}"}
    return {}


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
