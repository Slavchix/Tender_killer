from __future__ import annotations

from typing import Any

from .economics_constants import INTERESTING_MARGIN_PERCENT, LOW_MARGIN_PERCENT
from .economics_analysis_context import (
    _analysis_cost_drivers,
    _analysis_reserve_hint,
    _risk_reserve_rate_percent,
    _risk_types,
    _security_obligations,
)
from .economics_costing import (
    _cost_breakdown,
    _item_cost,
    _number,
    _positive_int,
    _positive_number,
    _position_risk_reserve_rate_percent,
    _position_risk_reserve_total,
    _price_for_margin,
    _round_money,
    _round_percent,
    _target_margin_percent,
)
from .economics_participation import (
    _bid_scenarios,
    _combined_risk_reserve_rate_percent,
    _participation_calculation,
    _participation_decision,
    _recommendation_for_status,
    _status_for_margin,
)
from .economics_price_quality import _price_quality_summary


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

    price_quality = _price_quality_summary(profiles, items)
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
            "price_quality": price_quality,
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
            "price_quality": price_quality,
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
        "price_quality": price_quality,
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
