from __future__ import annotations

import json
import re
from collections import Counter
from typing import Any

from tender_killer.tender_metadata import normalize_customer_inn


def build_customer_risk_profile(
    tender: dict[str, Any],
    history: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    raw_payload = _raw_payload(tender)
    customer = {
        "name": _text(tender.get("customer")),
        "inn": _customer_inn(tender, raw_payload),
    }
    history_items = [_history_item(item) for item in history or []]
    history_state_counts = Counter(
        str(item.get("market_state", {}).get("status") or "unknown")
        for item in history_items
    )
    factors = _factors(
        tender=tender,
        raw_payload=raw_payload,
        customer=customer,
        history_items=history_items,
        history_state_counts=history_state_counts,
    )
    score = min(100, sum(int(factor["score"]) for factor in factors))

    return {
        "version": 1,
        "status": "ready" if customer["name"] or customer["inn"] else "needs_customer_identity",
        "customer": customer,
        "level": _risk_level(score),
        "score": score,
        "factors": factors,
        "history": {
            "total": len(history_items),
            "market_state_counts": dict(history_state_counts),
            "recent": history_items[:5],
        },
        "basis": {
            "local_history": len(history_items),
            "eis_context_available": bool(_eis_context(raw_payload)),
        },
    }


def _factors(
    *,
    tender: dict[str, Any],
    raw_payload: dict[str, Any],
    customer: dict[str, str | None],
    history_items: list[dict[str, Any]],
    history_state_counts: Counter[str],
) -> list[dict[str, Any]]:
    factors: list[dict[str, Any]] = []
    if not customer["name"] and not customer["inn"]:
        factors.append(_factor("missing_customer_identity", "medium", 30, "Customer identity is missing."))

    market_state = _dict(tender.get("market_state"))
    if market_state.get("status") == "no_participants":
        factors.append(_factor("current_no_participants", "medium", 18, "Current tender has no participants."))
    elif _int_or_none(market_state.get("participant_count")) == 1:
        factors.append(_factor("single_participant", "low", 8, "Current tender has one known participant."))

    repeated_no_participants = history_state_counts.get("no_participants", 0)
    if len(history_items) >= 2 and repeated_no_participants >= 2:
        factors.append(
            _factor(
                "repeated_no_participants",
                "high",
                24,
                f"Local history has {repeated_no_participants} tenders without participants.",
            )
        )

    analysis = _dict(tender.get("analysis"))
    red_flags = _list(analysis.get("red_flags"))
    if red_flags:
        factors.append(_factor("analysis_red_flags", "medium", min(18, 8 + len(red_flags) * 5), "Analysis has red flags."))

    context = _eis_context(raw_payload)
    terminated = _int_or_none(context.get("terminated_contracts_count"))
    if terminated:
        factors.append(_factor("terminated_contracts", "high", min(28, 14 + terminated * 4), f"Terminated contracts: {terminated}."))
    complaints = _int_or_none(context.get("complaints_count"))
    if complaints:
        factors.append(_factor("customer_complaints", "medium", min(22, 10 + complaints * 3), f"Customer complaints: {complaints}."))
    payment_delay = _int_or_none(context.get("payment_delay_count"))
    if payment_delay:
        factors.append(_factor("payment_delay", "high", min(24, 12 + payment_delay * 4), f"Payment delay signals: {payment_delay}."))
    rejected = _int_or_none(context.get("rejected_applications_count"))
    if rejected:
        factors.append(_factor("rejected_applications", "medium", min(18, 8 + rejected * 3), f"Rejected application signals: {rejected}."))
    return factors


def _history_item(item: dict[str, Any]) -> dict[str, Any]:
    result = {
        "source": _text(item.get("source")),
        "external_id": _text(item.get("external_id")),
        "title": _text(item.get("title")),
        "status_normalized": _text(item.get("status_normalized")),
        "market_state": _dict(item.get("market_state")),
    }
    price = _number(item.get("price"))
    if price is not None:
        result["price"] = price
    return result


def _factor(factor_id: str, severity: str, score: int, evidence: str) -> dict[str, Any]:
    return {
        "id": factor_id,
        "severity": severity,
        "score": score,
        "evidence": evidence,
    }


def _risk_level(score: int) -> str:
    if score >= 65:
        return "high"
    if score >= 25:
        return "medium"
    return "low"


def _eis_context(raw_payload: dict[str, Any]) -> dict[str, Any]:
    context = raw_payload.get("eis_customer_context")
    return context if isinstance(context, dict) else {}


def _customer_inn(tender: dict[str, Any], raw_payload: dict[str, Any]) -> str | None:
    value = tender.get("customer_inn")
    digits = re.sub(r"\D+", "", str(value or ""))
    if len(digits) in {10, 12}:
        return digits
    return normalize_customer_inn(raw_payload)


def _raw_payload(tender: dict[str, Any]) -> dict[str, Any]:
    raw_payload = tender.get("raw_payload")
    if isinstance(raw_payload, dict):
        return raw_payload
    raw_payload_json = tender.get("raw_payload_json")
    if isinstance(raw_payload_json, str) and raw_payload_json.strip():
        try:
            data = json.loads(raw_payload_json)
        except json.JSONDecodeError:
            return {}
        return data if isinstance(data, dict) else {}
    return {}


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _text(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None


def _int_or_none(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or value in (None, ""):
        return None
    try:
        number = float(str(value).replace(" ", "").replace(",", "."))
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None
