from __future__ import annotations

from typing import Any

from tender_killer.analysis_operator_view_service import MAJOR_SECTION_DEFINITIONS
from tender_killer.analysis_operator_view_service import MAJOR_SECTION_IDS
from tender_killer.reports_analysis_items import item_source_text
from tender_killer.reports_analysis_items import operator_feedback_text
from tender_killer.reports_analysis_items import report_item_action
from tender_killer.reports_analysis_items import report_item_found
from tender_killer.reports_analysis_items import report_item_impact
from tender_killer.reports_analysis_items import report_item_meaning
from tender_killer.reports_analysis_items import short_text
from tender_killer.reports_docx_writer import DocxElement
from tender_killer.reports_docx_writer import paragraph as _p
from tender_killer.reports_docx_writer import table as _table


def analysis_four_block_elements(operator_view: dict[str, Any], analysis: dict[str, Any]) -> list[DocxElement]:
    rows = _analysis_four_block_rows(operator_view, analysis)
    if len(rows) <= 1:
        return []
    return [_p("Анализ ТЗ: 4 блока", "heading"), _table(rows, "analysis")]


def _analysis_four_block_rows(operator_view: dict[str, Any], analysis: dict[str, Any] | None = None) -> list[list[Any]]:
    rows: list[list[Any]] = [["Блок", "Пункт", "Что найдено", "Что означает", "Влияние", "Что сделать", "Источник", "Оператор"]]
    sections = operator_view.get("major_blocks") or operator_view.get("sections") or []
    section_map = {section.get("id"): section for section in sections if isinstance(section, dict)}
    supplemental_items = _report_supplemental_items(analysis or {})
    for definition in MAJOR_SECTION_DEFINITIONS:
        section = section_map.get(definition["id"]) or definition
        title = _value(section.get("title"), definition["title"])
        items = _merge_report_items(
            _report_section_items(section),
            supplemental_items.get(definition["id"], []),
        )
        if not items:
            rows.append([title, "Не найдено", _value(section.get("empty"), definition["empty"]), "", "", "", "", ""])
            continue
        for item in items[:7]:
            rows.append(
                [
                    title,
                    short_text(item.get("label"), 90),
                    short_text(report_item_found(item), 180),
                    short_text(report_item_meaning(item), 180),
                    short_text(report_item_impact(item), 170),
                    short_text(report_item_action(item), 170),
                    short_text(item_source_text(item), 220),
                    short_text(operator_feedback_text(item), 170),
                ]
            )
        if len(items) > 7:
            rows.append([title, f"и еще {len(items) - 7} пункт — см. в интерфейсе", "", "", "", "", "", ""])
    return rows


def _merge_report_items(left: list[dict[str, Any]], right: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for item in [*left, *right]:
        key = (short_text(item.get("label"), 80).lower(), short_text(item_source_text(item), 120).lower())
        if key in seen:
            continue
        seen.add(key)
        merged.append(item)
    return sorted(merged, key=lambda item: _int_value(item.get("priority")))


def _report_section_items(section: dict[str, Any]) -> list[dict[str, Any]]:
    items = [
        item
        for item in section.get("items") or []
        if isinstance(item, dict) and item.get("type") != "document_summary" and item.get("kind") != "document_summary"
    ]
    return sorted(items, key=lambda item: _int_value(item.get("priority")))


def _report_supplemental_items(analysis: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    buckets: dict[str, list[dict[str, Any]]] = {section_id: [] for section_id in MAJOR_SECTION_IDS}
    checklist = analysis.get("checklist") if isinstance(analysis, dict) else None
    if not isinstance(checklist, list):
        return buckets
    for index, raw_item in enumerate(checklist):
        if not isinstance(raw_item, dict):
            continue
        evidence = _value(raw_item.get("fragment") or raw_item.get("evidence"), "").strip()
        label = _value(raw_item.get("label"), "").strip()
        if not label or not evidence:
            continue
        section_id = _report_section_id(raw_item)
        item = {
            "label": label,
            "description": _value(raw_item.get("value") or raw_item.get("description") or evidence, ""),
            "operator_action": _value(
                raw_item.get("operator_action"),
                "Проверить допустимость участия до расчета."
                if section_id == "decision_risks"
                else "Проверить условие перед решением.",
            ),
            "source_label": _value(raw_item.get("source_label") or raw_item.get("source") or raw_item.get("document_name"), ""),
            "fragment": evidence,
            "priority": _int_value(raw_item.get("priority")) or 70 + index,
        }
        buckets[section_id].append(item)
    return buckets


def _report_section_id(item: dict[str, Any]) -> str:
    category = str(item.get("category") or "")
    severity = str(item.get("severity") or "")
    if severity in {"high", "critical"} or category in {"legal", "national_regime"}:
        return "decision_risks"
    if category in {"delivery", "contract", "warranty", "storage"}:
        return "fulfillment_terms"
    if category in {"acceptance", "financial", "payment"}:
        return "acceptance_payment"
    return "product_compliance"


def _value(value: Any, fallback: str = "не указано") -> str:
    if value is None or value == "":
        return fallback
    return str(value)


def _int_value(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
