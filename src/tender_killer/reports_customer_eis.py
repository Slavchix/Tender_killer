from __future__ import annotations

from typing import Any

from tender_killer.reports_docx_writer import DocxElement
from tender_killer.reports_docx_writer import paragraph as _p
from tender_killer.reports_docx_writer import table as _table


def customer_eis_elements(tender: dict[str, Any]) -> list[DocxElement]:
    risk_profile = tender.get("customer_risk_profile")
    eis_reference = tender.get("eis_reference")
    if not isinstance(risk_profile, dict) and not isinstance(eis_reference, dict):
        return []

    risk_profile = risk_profile if isinstance(risk_profile, dict) else {}
    eis_reference = eis_reference if isinstance(eis_reference, dict) else {}
    customer = risk_profile.get("customer") if isinstance(risk_profile.get("customer"), dict) else {}
    identifiers = eis_reference.get("identifiers") if isinstance(eis_reference.get("identifiers"), dict) else {}
    history = risk_profile.get("history") if isinstance(risk_profile.get("history"), dict) else {}
    network_fetch = "network fetch: on" if eis_reference.get("network_fetch_enabled") else "network fetch: off"
    rows = [
        ["Заказчик", _value(customer.get("name") or tender.get("customer"))],
        ["ИНН", _value(customer.get("inn") or identifiers.get("customer_inn") or tender.get("customer_inn"))],
        ["Риск", _customer_risk_text(risk_profile)],
        ["История", f"{_int_value(history.get('total'))} закупок"],
        ["Номер ЕИС", _value(identifiers.get("purchase_number"), "ручной поиск")],
        ["Проверка ЕИС", network_fetch],
    ]
    elements: list[DocxElement] = [_p("Заказчик / ЕИС", "heading"), _table(rows)]

    factors = [
        factor
        for factor in risk_profile.get("factors") or []
        if isinstance(factor, dict) and factor.get("evidence")
    ]
    if factors:
        elements.append(_p("Сигналы по заказчику", "heading2"))
        elements.extend(_list_elements([factor["evidence"] for factor in factors[:4]]))

    links = [
        link
        for link in eis_reference.get("links") or []
        if isinstance(link, dict) and link.get("url")
    ]
    if links:
        elements.append(_p("Ссылки ЕИС", "heading2"))
        elements.append(
            _table(
                [
                    ["Раздел", "Ссылка"],
                    *[
                        [_value(link.get("label") or link.get("id")), _value(link.get("url"))]
                        for link in links[:4]
                    ],
                ]
            )
        )
    return elements


def _customer_risk_text(risk_profile: dict[str, Any]) -> str:
    level = _value(risk_profile.get("level"), "не рассчитан")
    score = risk_profile.get("score")
    if score in (None, ""):
        return level
    return f"{level} / {score}"


def _list_elements(values: list[Any]) -> list[DocxElement]:
    return [_p(f"- {_value(value)}", "normal") for value in values]


def _int_value(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _value(value: Any, fallback: str = "не указано") -> str:
    if value is None or value == "":
        return fallback
    return str(value)
