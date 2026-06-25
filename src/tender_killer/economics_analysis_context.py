from __future__ import annotations

from typing import Any

from .economics_costing import (
    _first_number,
    _number,
    _percent,
    _positive_int,
    _round_money,
    _round_percent,
    _text,
)


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


def _risk_reserve_rate_percent(risk_types: list[str]) -> float:
    return _round_percent(min(8.0, sum(RISK_RESERVE_RATES.get(risk_type, 0.5) for risk_type in risk_types)))


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
