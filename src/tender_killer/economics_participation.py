from __future__ import annotations

from typing import Any

from .economics_constants import INTERESTING_MARGIN_PERCENT, LOW_MARGIN_PERCENT
from .economics_costing import _positive_number, _round_money, _round_percent


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
