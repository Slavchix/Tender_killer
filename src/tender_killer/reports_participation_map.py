from __future__ import annotations

from typing import Any

from tender_killer.analysis_operator_sections_service import MAJOR_SECTION_IDS
from tender_killer.reports_analysis_items import report_item_action as _report_item_action
from tender_killer.reports_analysis_items import report_item_meaning as _report_item_meaning
from tender_killer.reports_analysis_items import short_text as _short_text
from tender_killer.reports_docx_writer import DocxElement
from tender_killer.reports_docx_writer import paragraph as _p
from tender_killer.reports_docx_writer import table as _table


def participation_map_elements(
    *,
    tender: dict[str, Any],
    analysis: dict[str, Any],
    documents: list[dict[str, Any]],
    operator_view: dict[str, Any],
    decision: dict[str, Any],
) -> list[DocxElement]:
    title = _value(tender.get("title"))
    elements: list[DocxElement] = [
        _p("КАРТА УЧАСТИЯ", "title"),
        _table(
            [
                ["Закупка", title],
                ["Заказчик", _value(tender.get("customer"))],
                ["НМЦК", _money(tender.get("price"))],
                ["Дедлайн", _value(tender.get("deadline_at"))],
                ["Площадка", _value(tender.get("source"))],
                ["Ссылка", _value(tender.get("url"))],
            ]
        ),
        _p("Краткое решение", "heading"),
        _table(
            [
                ["Решение", _value(decision.get("title"))],
                ["Комментарий", _value(decision.get("summary"))],
                ["Уверенность анализа", _confidence(analysis.get("confidence") if isinstance(analysis, dict) else None)],
                ["Ключевые причины", "; ".join(decision.get("reasons") or []) or "нет явных причин"],
            ]
        ),
    ]
    risk_rows = _participation_risk_rows(operator_view)
    if len(risk_rows) > 1:
        elements.extend([_p("Таблица рисков", "heading"), _table(risk_rows, "analysis")])
    checklist_rows = _participation_checklist_rows(operator_view)
    if len(checklist_rows) > 1:
        elements.extend([_p("Чеклист участия", "heading"), _table(checklist_rows, "analysis")])
    source_rows = _participation_source_rows(operator_view)
    if len(source_rows) > 1:
        elements.extend([_p("Источники", "heading"), _table(source_rows, "analysis")])
    elements.extend([_p("Приложения", "heading"), *_participation_appendix_elements(documents)])
    return elements


def _participation_risk_rows(operator_view: dict[str, Any]) -> list[list[Any]]:
    rows: list[list[Any]] = [["Риск", "Влияние", "Действие", "Источник", "Уверенность"]]
    for item in _operator_items_by_section(operator_view, {"decision_risks"})[:10]:
        rows.append(
            [
                _short_text(item.get("label"), 80),
                _short_text(_report_item_meaning(item), 150),
                _short_text(_report_item_action(item), 150),
                _short_text(_source_label_for_item(item), 120),
                _source_confidence_text(item),
            ]
        )
    return rows


def _participation_checklist_rows(operator_view: dict[str, Any]) -> list[list[Any]]:
    rows: list[list[Any]] = [["Шаг", "Что сделать", "Пункты"]]
    action_plan = operator_view.get("action_plan") if isinstance(operator_view, dict) else None
    if isinstance(action_plan, list) and action_plan:
        for step in action_plan[:8]:
            if not isinstance(step, dict):
                continue
            rows.append(
                [
                    _short_text(step.get("title") or step.get("id"), 80),
                    _short_text(step.get("next_step"), 180),
                    _short_text(", ".join(_text_list(step.get("items"))), 180),
                ]
            )
        return rows
    for item in _operator_items_by_section(operator_view, set(MAJOR_SECTION_IDS))[:12]:
        rows.append(
            [
                _short_text(item.get("label"), 80),
                _short_text(_report_item_action(item), 180),
                _short_text(_source_label_for_item(item), 180),
            ]
        )
    return rows


def _participation_source_rows(operator_view: dict[str, Any]) -> list[list[Any]]:
    rows: list[list[Any]] = [["Пункт", "Источник", "Фрагмент", "Привязка"]]
    seen: set[tuple[str, str]] = set()
    for item in _operator_items_by_section(operator_view, set(MAJOR_SECTION_IDS))[:7]:
        source = _source_label_for_item(item)
        if not source:
            continue
        key = (_short_text(item.get("label"), 80).lower(), source.lower())
        if key in seen:
            continue
        seen.add(key)
        rows.append(
            [
                _short_text(item.get("label"), 80),
                _short_text(source, 120),
                _short_text(item.get("fragment") or item.get("source_context"), 180),
                _source_confidence_text(item),
            ]
        )
    return rows


def _participation_appendix_elements(documents: list[dict[str, Any]]) -> list[DocxElement]:
    if not documents:
        return [_p("Документы не найдены или еще не скачаны.", "normal")]
    rows = [["Документ", "Тип", "Текст"]]
    for document in documents:
        rows.append(
            [
                _value(document.get("name")),
                _value(document.get("document_type"), ""),
                _value(document.get("text_status")),
            ]
        )
    return [_table(rows)]


def _operator_items_by_section(operator_view: dict[str, Any], section_ids: set[str]) -> list[dict[str, Any]]:
    sections = operator_view.get("major_blocks") or operator_view.get("sections") or []
    items: list[dict[str, Any]] = []
    for section in sections:
        if not isinstance(section, dict) or section.get("id") not in section_ids:
            continue
        for item in section.get("items") or []:
            if isinstance(item, dict) and item.get("type") != "document_summary" and item.get("kind") != "document_summary":
                items.append(item)
    return sorted(items, key=lambda item: _int_value(item.get("priority")))


def _source_label_for_item(item: dict[str, Any]) -> str:
    binding = item.get("source_binding")
    if isinstance(binding, dict):
        source_label = _value(binding.get("source_label"), "").strip()
        if source_label:
            return source_label
    return _value(item.get("source_label") or item.get("document_name") or item.get("source"), "").strip()


def _source_confidence_text(item: dict[str, Any]) -> str:
    binding = item.get("source_binding")
    confidence = item.get("confidence_level")
    binding_label = _value(binding.get("label"), "") if isinstance(binding, dict) else ""
    confidence_label = _value(confidence.get("label"), "") if isinstance(confidence, dict) else ""
    authority_text = _source_authority_text(item)
    weak_reason = _value(item.get("weak_reason"), "")
    parts = [part for part in (binding_label, confidence_label, authority_text, weak_reason) if part]
    return " / ".join(parts) or "нужна сверка"


def _source_authority_text(item: dict[str, Any]) -> str:
    authority = _value(item.get("context_source_authority"), "")
    role = _value(item.get("context_document_role"), "")
    reason = _value(item.get("context_source_reason"), "")
    priority = _text_list(item.get("context_source_priority"))
    topics = _text_list(item.get("context_topics"))
    parts = [
        _source_authority_label(authority),
        _source_document_role_label(role),
        _source_topic_text(priority or topics),
        reason,
    ]
    return "; ".join(part for part in parts if part)


def _source_authority_label(value: str) -> str:
    if value == "primary_for_topic":
        return "главный источник по теме"
    if value == "primary_document":
        return "основной документ"
    if value == "supporting_document":
        return "вспомогательный источник"
    return ""


def _source_document_role_label(value: str) -> str:
    if value in {"technical_spec", "technical_specification"}:
        return "ТЗ"
    if value == "technical_spec_appendix":
        return "приложение к ТЗ"
    if value == "contract_project":
        return "проект контракта"
    if value == "pik_obligations_payment":
        return "ПИК, оплата и приемка"
    if value == "participant_requirements":
        return "требования к участнику"
    if value == "unsupported_primary":
        return "основной документ без текста"
    return value


def _source_topic_text(values: list[str]) -> str:
    labels = [_source_topic_label(value) for value in values[:4]]
    return ", ".join(label for label in labels if label)


def _source_topic_label(value: str) -> str:
    labels = {
        "acceptance_documents": "приемочные документы",
        "acceptance_process": "приемка",
        "advance": "аванс",
        "certificates_closing_docs": "сертификаты и закрывающие",
        "contract_security": "обеспечение контракта",
        "delivery_place": "место поставки",
        "delivery_schedule": "срок поставки",
        "logistics_responsibility": "логистика",
        "participant_requirements": "требования к участнику",
        "payment_terms": "условия оплаты",
        "penalties": "штрафы",
        "technical_characteristics": "характеристики",
        "warranty": "гарантия",
    }
    return labels.get(value, value)


def _text_list(values: Any) -> list[str]:
    if isinstance(values, list):
        return [_value(value, "").strip() for value in values if _value(value, "").strip()]
    value = _value(values, "").strip()
    return [value] if value else []


def _int_value(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _value(value: Any, fallback: str = "не указано") -> str:
    if value is None or value == "":
        return fallback
    return str(value)


def _money(value: Any) -> str:
    try:
        amount = float(value)
    except (TypeError, ValueError):
        return "не указано"
    return f"{amount:,.2f} ₽".replace(",", " ")


def _confidence(value: Any) -> str:
    try:
        return f"{float(value) * 100:.0f}%"
    except (TypeError, ValueError):
        return "не указано"
