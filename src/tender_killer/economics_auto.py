from __future__ import annotations

import re
from typing import Any

from tender_killer.supplier_price_service import best_supplier_price


DRIVER_RATES = {
    "delivery": 1.5,
    "unloading": 0.5,
    "packaging": 1.0,
    "warranty": 1.0,
    "acceptance": 1.0,
    "certificates": 1.0,
    "short_deadline": 1.0,
    "payment_delay": 1.0,
    "penalties": 0.5,
    "national_regime": 0.5,
    "contract_security": 0.5,
}


def build_auto_economics_estimate(
    profile: dict[str, Any],
    document_records: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    raw_payload = profile.get("raw_payload") if isinstance(profile.get("raw_payload"), dict) else {}
    quantity = _number(profile.get("quantity")) or 1.0
    unit_cost, base_source, base_evidence = _base_unit_cost(profile, raw_payload, quantity)
    document_records = document_records or []
    evidence_text = _profile_text(profile, document_records)

    needs_review: list[str] = []
    if unit_cost is None:
        needs_review.append("Не найдена базовая цена товара")
        unit_cost = 0.0

    base_total_cost = _round_money(unit_cost * quantity)
    cost_drivers = _cost_drivers(profile, document_records, evidence_text, base_total_cost)
    hidden_costs_total = _round_money(sum(driver["amount"] for driver in cost_drivers))
    tax_mode, vat_rate_percent, tax_review = _tax_assumption(evidence_text)
    needs_review.extend(tax_review)
    risk_reserve = _round_money(base_total_cost * 0.01) if needs_review else 0.0
    estimated_total_cost = _round_money(base_total_cost + hidden_costs_total + risk_reserve)
    manual_inputs_present = bool((raw_payload.get("economics") or {}))

    return {
        "status": "needs_review" if needs_review else "ready",
        "base_source": base_source,
        "estimated_unit_cost": _round_money(unit_cost),
        "base_total_cost": base_total_cost,
        "hidden_costs_total": hidden_costs_total,
        "risk_reserve": risk_reserve,
        "estimated_total_cost": estimated_total_cost,
        "tax_mode": tax_mode,
        "vat_rate_percent": vat_rate_percent,
        "confidence": _confidence(base_source, tax_mode, cost_drivers, needs_review),
        "manual_inputs_present": manual_inputs_present,
        "cost_drivers": cost_drivers,
        "needs_review": needs_review,
        "evidence": base_evidence + _evidence_from_documents(document_records),
    }


def _base_unit_cost(profile: dict[str, Any], raw_payload: dict[str, Any], quantity: float) -> tuple[float | None, str, list[dict[str, str]]]:
    supplier_price = best_supplier_price(profile)
    if supplier_price is not None:
        base_source = "selected_supplier" if supplier_price["selection"] == "manual_selected" else "best_supplier_option"
        return supplier_price["unit_price"], base_source, [
            {
                "source": base_source,
                "value": str(supplier_price.get("supplier_name") or supplier_price.get("supplier_url") or "supplier option"),
            }
        ]

    unit_price = _number(profile.get("unit_price"))
    if unit_price is not None:
        return unit_price, "source_position_unit_price", [{"source": "tender_card", "value": "unit_price"}]

    total_price = _number(profile.get("total_price"))
    if total_price is not None and quantity:
        return total_price / quantity, "source_position_total_price", [{"source": "tender_card", "value": "total_price"}]

    return None, "missing", []


def _cost_drivers(
    profile: dict[str, Any],
    document_records: list[dict[str, Any]],
    evidence_text: str,
    base_total_cost: float,
) -> list[dict[str, Any]]:
    drivers: dict[str, dict[str, Any]] = {}
    for requirement in profile.get("fulfillment_requirements") or []:
        if not isinstance(requirement, dict):
            continue
        driver_type = str(requirement.get("type") or "").strip()
        if driver_type in DRIVER_RATES:
            _add_driver(drivers, driver_type, base_total_cost, requirement.get("source") or "profile", requirement.get("value"))

    checks = (
        ("unloading", ("разгруз", "unloading"), "Требуется разгрузка"),
        ("certificates", ("сертификат", "деклараци", "certificate"), "Требуются сертификаты/декларации"),
        ("payment_delay", ("отсроч", "постоплат", "оплата после"), "Есть отсрочка оплаты"),
        ("penalties", ("штраф", "пени", "неустойк"), "Есть штрафы/пени"),
        ("national_regime", ("национальн", "страна происх"), "Есть ограничения по стране происхождения"),
        ("contract_security", ("обеспеч", "банковск"), "Есть обеспечение/банковская гарантия"),
    )
    for driver_type, tokens, value in checks:
        if any(token in evidence_text for token in tokens):
            _add_driver(drivers, driver_type, base_total_cost, "documents", value)

    if _has_short_deadline(evidence_text):
        _add_driver(drivers, "short_deadline", base_total_cost, "documents", "Короткий срок поставки")

    return list(drivers.values())


def _add_driver(
    drivers: dict[str, dict[str, Any]],
    driver_type: str,
    base_total_cost: float,
    source: Any,
    value: Any,
) -> None:
    rate = DRIVER_RATES[driver_type]
    drivers.setdefault(
        driver_type,
        {
            "type": driver_type,
            "rate_percent": rate,
            "amount": _round_money(base_total_cost * rate / 100),
            "source": str(source or "unknown"),
            "value": str(value or driver_type),
        },
    )


def _tax_assumption(text: str) -> tuple[str, float | None, list[str]]:
    if "без учета ндс" in text or "ндс начис" in text:
        return "vat_excluded", 20.0, ["Проверить, добавляется ли НДС к цене поставщика"]
    if "без ндс" in text:
        return "no_vat", 0.0, []
    if "ндс включ" in text or "с учетом ндс" in text or "с ндс" in text:
        return "vat_included", 20.0, []
    return "unknown", None, ["НДС не определен"]


def _confidence(
    base_source: str,
    tax_mode: str,
    cost_drivers: list[dict[str, Any]],
    needs_review: list[str],
) -> float:
    value = 0.5
    if base_source == "selected_supplier":
        value += 0.2
    elif base_source.startswith("source_position"):
        value += 0.1
    if tax_mode != "unknown":
        value += 0.1
    if cost_drivers:
        value += 0.1
    value -= min(0.2, len(needs_review) * 0.05)
    return round(max(0.0, min(0.95, value)), 2)


def _profile_text(profile: dict[str, Any], document_records: list[dict[str, Any]]) -> str:
    values: list[str] = [
        str(profile.get("product_name") or ""),
        str(profile.get("details") or ""),
    ]
    for requirement in profile.get("fulfillment_requirements") or []:
        if isinstance(requirement, dict):
            values.append(str(requirement.get("value") or ""))
    for record in document_records:
        if isinstance(record, dict):
            values.append(str(record.get("text_content") or ""))
    return " ".join(values).lower()


def _evidence_from_documents(document_records: list[dict[str, Any]]) -> list[dict[str, str]]:
    evidence: list[dict[str, str]] = []
    for record in document_records:
        text = str(record.get("text_content") or "").strip() if isinstance(record, dict) else ""
        if not text:
            continue
        evidence.append(
            {
                "source": str(record.get("name") or record.get("document_type") or "document"),
                "value": text[:240],
            }
        )
    return evidence[:3]


def _has_short_deadline(text: str) -> bool:
    for match in re.finditer(r"срок.{0,40}?(\d{1,2})\s*(?:дн|рабоч|календар)", text):
        if int(match.group(1)) <= 5:
            return True
    return False


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
