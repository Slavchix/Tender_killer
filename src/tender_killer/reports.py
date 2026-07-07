from __future__ import annotations

from typing import Any

from tender_killer.reports_analysis_decision import analysis_decision as _analysis_decision
from tender_killer.reports_analysis_decision import analysis_operator_view as _analysis_operator_view
from tender_killer.reports_analysis_decision import report_operator_view as _report_operator_view
from tender_killer.reports_customer_eis import customer_eis_elements as _customer_eis_elements
from tender_killer.reports_docx_writer import DocxElement
from tender_killer.reports_docx_writer import docx_bytes as _docx_bytes
from tender_killer.reports_docx_writer import paragraph as _p
from tender_killer.reports_docx_writer import table as _table
from tender_killer.reports_participation_map import participation_map_elements as _participation_map_elements
from tender_killer.reports_product_profiles import report_product_profile_summary as _product_profile_summary
from tender_killer.reports_tz_four_blocks import analysis_four_block_elements as _analysis_four_block_elements
from tender_killer.reports_tz_sections import analysis_history_elements as _analysis_history_elements
from tender_killer.reports_tz_sections import analysis_management_brief_elements as _analysis_management_brief_elements
from tender_killer.reports_tz_sections import analysis_saas_elements as _analysis_saas_elements
from tender_killer.reports_tz_sections import analysis_tz_passport as _analysis_tz_passport
from tender_killer.reports_tz_sections import analysis_tz_passport_elements as _analysis_tz_passport_elements


def build_tender_report_docx(tender: dict[str, Any]) -> bytes:
    analysis = tender.get("analysis") or {}
    economics = tender.get("economics") or {}
    documents = tender.get("document_records") or []
    product_profiles = tender.get("product_profiles") or []
    product_profile_summary = _product_profile_summary(tender, product_profiles)
    operator_view = _report_operator_view(analysis, documents)
    elements: list[DocxElement] = [
        *_participation_map_elements(
            tender=tender,
            analysis=analysis,
            documents=documents,
            operator_view=operator_view,
            decision=_analysis_decision(analysis, documents),
        ),
        _p("Tender Killer: отчет по закупке", "heading2"),
        _p("Краткое решение", "heading"),
        _table(
            [
                ["Предварительный статус", _analysis_status(analysis.get("status"))],
                ["Уверенность", _confidence(analysis.get("confidence"))],
                ["Товарных позиций", str(product_profile_summary["total"])],
                ["Сумма закупки", _money(tender.get("price"))],
                ["Дедлайн", _value(tender.get("deadline_at"))],
            ]
        ),
        *_tender_decision_elements(tender.get("decision")),
        *_customer_eis_elements(tender),
        *_analysis_management_brief_elements(analysis, documents, operator_view),
        *_analysis_saas_elements(operator_view),
        *_analysis_tz_passport_elements(analysis, documents),
        _p("Паспорт закупки", "heading"),
        _table(
            [
                ["Название", _value(tender.get("title"))],
                ["Номер", _value(tender.get("external_id"))],
                ["Источник", _value(tender.get("source"))],
                ["Ссылка", _value(tender.get("url"))],
                ["Заказчик", _value(tender.get("customer"))],
                ["Регион", _value(tender.get("region"))],
                ["Статус", _value(tender.get("status"))],
                ["НМЦК/цена", _money(tender.get("price"))],
            ]
        ),
        _p("Что закупают", "heading"),
    ]
    items = tender.get("items") or []
    if items:
        item_rows = [["№", "Товар", "Детали", "Кол-во", "Цена", "Классификатор"]]
        for item in items:
            classifier = _classifier_label(item.get("classifier_code") or item.get("okpd2"), item.get("classifier_type"))
            item_rows.append(
                [
                    _value(item.get("position_index")),
                    _value(item.get("name")),
                    _value(item.get("details"), ""),
                    f"{_value(item.get('quantity'))} {_value(item.get('unit'), '')}".strip(),
                    f"{_money(item.get('unit_price'))} / {_money(item.get('total_price'))}",
                    classifier,
                ]
            )
        elements.append(_table(item_rows))
    else:
        elements.append(
            _table(
                [
                    ["Предмет по карточке", _value(tender.get("title"))],
                    ["Категория", _value(tender.get("category"))],
                    ["ОКПД2/КОЗ по карточке", _value(tender.get("okpd2"))],
                    ["Цена по карточке", _money(tender.get("price"))],
                    [
                        "Комментарий",
                        "Структурированные позиции пока не найдены; эти данные используются как базовый предмет для будущего подбора товаров.",
                    ],
                ]
            )
        )

    elements.extend(
        [
            _p("Сводка товарных профилей", "heading"),
            _table(
                [
                    ["Товарные профили", str(product_profile_summary["total"])],
                    ["Готовы к поиску", str(product_profile_summary["ready"])],
                    ["Требуют проверки", str(product_profile_summary["needs_review"])],
                    ["Найдены товары", str(product_profile_summary["matched"])],
                    ["Посчитана экономика", str(product_profile_summary["priced"])],
                    ["Отклонены", str(product_profile_summary["rejected"])],
                ]
            ),
        ]
    )

    elements.append(_p("Документы", "heading"))
    if documents:
        document_rows = [["Документ", "Тип", "Статус текста"]]
        for document in documents:
            document_rows.append(
                [_value(document.get("name")), _value(document.get("document_type")), _value(document.get("text_status"))]
            )
        elements.append(_table(document_rows))
    else:
        elements.append(_p("Документы пока не найдены.", "normal"))

    elements.extend(
        [
            _p("Решение по анализу ТЗ", "heading"),
            *_analysis_decision_elements(analysis, documents),
        *_analysis_four_block_elements(operator_view, analysis),
            *_analysis_history_elements(analysis),
            *_economics_elements(economics),
        ]
    )

    return _docx_bytes(elements)


def report_filename(tender: dict[str, Any]) -> str:
    external_id = str(tender.get("external_id") or "tender")
    return f"tender-killer-{_safe_filename(external_id)}.docx"


def _list_elements(values: list[Any]) -> list[DocxElement]:
    return [_p(f"- {_value(value)}", "normal") for value in values]


def _tender_decision_elements(decision: Any) -> list[DocxElement]:
    if not isinstance(decision, dict) or not any(
        decision.get(key) for key in ("label", "summary", "next_step", "reasons", "blockers")
    ):
        return []

    elements: list[DocxElement] = [
        _p("Решение Tender Killer", "heading"),
        _table(
            [
                ["Статус", _value(decision.get("label"))],
                ["Комментарий", _value(decision.get("summary"))],
                ["Следующий шаг", _value(decision.get("next_step"))],
            ]
        ),
    ]
    reasons = _text_list(decision.get("reasons"))
    blockers = _text_list(decision.get("blockers"))
    if reasons:
        elements.append(_p("Причины решения", "heading2"))
        elements.extend(_list_elements(reasons))
    if blockers:
        elements.append(_p("Блокеры", "heading2"))
        elements.extend(_list_elements(blockers))
    return elements


def _analysis_decision_elements(analysis: dict[str, Any], documents: list[dict[str, Any]]) -> list[DocxElement]:
    decision = _analysis_decision(analysis, documents)
    elements = [
        _table(
            [
                ["Вердикт", decision["title"]],
                ["Комментарий", decision["summary"]],
            ]
        )
    ]
    if decision["reasons"]:
        elements.append(_p("Ключевые причины", "heading2"))
        elements.extend(_list_elements(decision["reasons"][:3]))
    return elements


def _text_list(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    return [_value(value, "").strip() for value in values if _value(value, "").strip()]


def _limited_text_list(values: Any, *, fallback: str, limit: int = 8) -> list[str]:
    items = _text_list(values)
    if not items:
        return [fallback]
    if len(items) <= limit:
        return items
    return [*items[:limit], f"и еще {len(items) - limit} пунктов"]


def _short_text(value: Any, limit: int) -> str:
    text = _value(value, "").replace("\n", " ").strip()
    while "  " in text:
        text = text.replace("  ", " ")
    if len(text) <= limit:
        return text
    return f"{text[: max(0, limit - 1)].rstrip()}…"


def _missing_costs_summary(values: Any) -> str:
    missing = _text_list(values)
    if not missing:
        return "нет"
    return f"{len(missing)} позиций"


def _dict_value(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _first_present(*values: Any) -> Any:
    for value in values:
        if value not in (None, ""):
            return value
    return None


def _append_money_row(rows: list[list[Any]], label: str, value: Any) -> None:
    if value not in (None, ""):
        rows.append([label, _money(value)])


def _append_value_row(rows: list[list[Any]], label: str, value: Any) -> None:
    if value not in (None, ""):
        rows.append([label, _value(value)])


def _economics_elements(economics: dict[str, Any]) -> list[DocxElement]:
    if not economics:
        return [
            _p("Экономика", "heading"),
            _p("Расчет экономики еще не подготовлен.", "normal"),
        ]
    missing_cost_inputs = _text_list(economics.get("missing_cost_inputs"))
    participation = _dict_value(economics.get("participation_calculation"))
    cost_breakdown = _dict_value(economics.get("cost_breakdown"))
    rows = [
        ["Статус", _economics_status(economics.get("status"))],
        ["НМЦК/выручка", _money(economics.get("revenue"))],
        ["Себестоимость поставщика", _money(economics.get("supplier_cost"))],
        ["Резерв риска", f"{_money(economics.get('risk_reserve'))} / {_percent(economics.get('risk_reserve_rate_percent'))}"],
        ["Итого затраты", _money(economics.get("estimated_total_cost"))],
        ["Маржа", f"{_money(economics.get('gross_margin'))} / {_percent(economics.get('margin_percent'))}"],
        ["Не хватает цен", _missing_costs_summary(missing_cost_inputs)],
        ["Риски исполнения", ", ".join(_limited_text_list(economics.get("risk_types"), fallback="нет", limit=5))],
    ]
    _append_money_row(rows, "Стоп-цена", _first_present(economics.get("stop_price"), participation.get("stop_price")))
    _append_money_row(rows, "Обеспечение", _first_present(economics.get("security_amount"), participation.get("security_amount")))
    elements = [_p("Экономика", "heading"), _table(rows)]
    if economics.get("recommendation"):
        elements.append(_p(_value(economics.get("recommendation")), "normal"))
    if participation:
        participation_rows = [["Показатель", "Значение"]]
        _append_value_row(participation_rows, "Решение", participation.get("label"))
        _append_money_row(participation_rows, "Ставка", participation.get("current_price"))
        _append_money_row(participation_rows, "Стоп-цена", participation.get("stop_price"))
        _append_money_row(participation_rows, "Прибыль", participation.get("profit"))
        _append_money_row(participation_rows, "Запас до стоп-цены", participation.get("headroom_to_stop_price"))
        _append_money_row(participation_rows, "Резерв", participation.get("risk_reserve"))
        _append_money_row(participation_rows, "Обеспечение", participation.get("security_amount"))
        _append_value_row(participation_rows, "Причина", participation.get("reason"))
        if len(participation_rows) > 1:
            elements.extend([_p("Расчет участия", "heading2"), _table(participation_rows)])
    if cost_breakdown:
        breakdown_rows = [["Статья", "Сумма"]]
        _append_money_row(breakdown_rows, "Товар", cost_breakdown.get("direct_cost"))
        _append_money_row(breakdown_rows, "Логистика", cost_breakdown.get("logistics_cost"))
        _append_money_row(breakdown_rows, "Документы", cost_breakdown.get("documents_cost"))
        _append_money_row(breakdown_rows, "Упаковка", cost_breakdown.get("packaging_cost"))
        _append_money_row(breakdown_rows, "Прочее", cost_breakdown.get("other_costs"))
        _append_money_row(breakdown_rows, "НДС", cost_breakdown.get("vat_cost"))
        _append_money_row(breakdown_rows, "Резерв позиции", cost_breakdown.get("position_risk_reserve"))
        _append_money_row(breakdown_rows, "Резерв исполнения", cost_breakdown.get("execution_risk_reserve"))
        _append_money_row(breakdown_rows, "Денежная нагрузка", cost_breakdown.get("cash_required"))
        if len(breakdown_rows) > 1:
            elements.extend([_p("Разбивка затрат", "heading2"), _table(breakdown_rows)])
    if missing_cost_inputs:
        elements.append(_p("Первые позиции без себестоимости", "heading2"))
        elements.extend(_list_elements(_limited_text_list(missing_cost_inputs, fallback="нет", limit=5)))
    return elements


def _value(value: Any, fallback: str = "не указано") -> str:
    if value is None or value == "":
        return fallback
    return str(value)


def _money(value: Any) -> str:
    try:
        return f"{float(value):,.2f} ₽".replace(",", " ")
    except (TypeError, ValueError):
        return "не указано"


def _percent(value: Any) -> str:
    try:
        return f"{float(value):.2f}%"
    except (TypeError, ValueError):
        return "не указано"


def _classifier_label(code: Any, classifier_type: Any) -> str:
    if code and classifier_type:
        return f"{classifier_type}: {code}"
    if code:
        return str(code)
    if classifier_type:
        return str(classifier_type)
    return "не указано"


def _confidence(value: Any) -> str:
    try:
        return f"{round(float(value) * 100)}%"
    except (TypeError, ValueError):
        return "не указана"


def _analysis_status(value: Any) -> str:
    return {"needs_review": "Нужна проверка", "interesting": "Интересно", "skipped": "Пропустить"}.get(
        str(value or ""),
        "Нужна проверка",
    )


def _economics_status(value: Any) -> str:
    return {
        "interesting": "интересно",
        "manual_review": "ручная проверка",
        "low_margin": "низкая маржа",
        "needs_costs": "нужны себестоимости",
        "needs_price": "нужна НМЦК",
    }.get(str(value or ""), "ручная проверка")


def _trim_text(value: str, limit: int) -> str:
    text = " ".join(str(value).split())
    return text if len(text) <= limit else f"{text[:limit]}..."


def _safe_filename(value: str) -> str:
    return "".join(char if char.isalnum() or char in "._-" else "_" for char in value).strip("._") or "tender"
