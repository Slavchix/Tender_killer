from __future__ import annotations

import re
from typing import Any

from tender_killer.analysis_types import OperatorItem
from tender_killer.analysis_types import OperatorSection
from tender_killer.analysis_types import OperatorViewMetrics


def build_operator_decision_brief(
    analysis: dict[str, Any],
    sections: list[OperatorSection],
    status: str,
) -> dict[str, Any]:
    section_map = {section["id"]: section for section in sections}
    decision_items = section_map["decision_risks"]["items"]
    blockers = [item for item in decision_items if item.get("is_blocker") or item.get("needs_review")]
    confidence = _number_or_none(analysis.get("confidence"))

    if status == "pending":
        return {
            "status": "pending",
            "tone": "pending",
            "title": "Нужен анализ ТЗ",
            "summary": "Сначала извлеките текст документов и запустите анализ.",
            "next_step": "Извлечь текст и запустить анализ ТЗ",
            "confidence": confidence,
            "primary_section": "decision_risks",
            "reasons": [],
        }

    if blockers:
        primary_item = blockers[0]
        return {
            "status": "manual_review",
            "tone": "danger",
            "title": "Нужна ручная проверка",
            "summary": _decision_summary(
                primary_item,
                "В ТЗ есть условия, которые могут повлиять на участие, цену или закрывающие документы.",
            ),
            "next_step": _text(primary_item.get("operator_action"))
            or "Разобрать риски до расчета и решения об участии",
            "confidence": confidence,
            "primary_section": "decision_risks",
            "reasons": [_decision_reason(item) for item in blockers[:3]],
        }

    non_empty_sections = [section for section in sections if section["items"]]
    if non_empty_sections:
        reasons = []
        for section in non_empty_sections:
            reasons.extend(_decision_reason(item) for item in section["items"][:2] if item.get("type") != "document")
        primary_item = next(
            (item for section in non_empty_sections for item in section["items"] if item.get("type") != "document"),
            None,
        )
        return {
            "status": "needs_review",
            "tone": "review",
            "title": "Проверить условия ТЗ",
            "summary": _decision_summary(
                primary_item,
                "Критичных блокеров не видно, но условия товара, поставки, приемки и оплаты нужно сверить перед расчетом.",
            ),
            "next_step": _text(primary_item.get("operator_action"))
            if primary_item
            else "Пройти четыре блока анализа и зафиксировать влияние на заявку",
            "confidence": confidence,
            "primary_section": "product_compliance",
            "reasons": reasons[:3],
        }

    return {
        "status": "ok",
        "tone": "ok",
        "title": "Критичных рисков не видно",
        "summary": "Анализ не нашел явных блокеров; можно переходить к следующему этапу проверки.",
        "next_step": "Сверить экономику и поставщиков",
        "confidence": confidence,
        "primary_section": "decision_risks",
        "reasons": _text_list([analysis.get("summary")])[:1],
    }


def build_operator_view_metrics(
    items: list[OperatorItem],
    sections: list[OperatorSection],
    document_state: dict[str, Any],
    fact_metrics: Any,
) -> OperatorViewMetrics:
    source_metrics = fact_metrics if isinstance(fact_metrics, dict) else {}
    actual_items = [item for item in items if not item.get("expected_missing")]
    return {
        "major_blocks": len(sections),
        "facts": len(items),
        "requirements": sum(1 for item in items if item.get("kind") in {"requirement", "supplier_document"}),
        "risks": len([item for item in items if item.get("kind") in {"risk", "red_flag", "blocker"} or item.get("is_blocker")]),
        "blockers": sum(1 for item in items if item.get("is_blocker")),
        "actual_blockers": sum(1 for item in actual_items if item.get("is_blocker")),
        "needs_review": sum(1 for item in items if item.get("needs_review")),
        "price_factors": sum(1 for item in items if item.get("is_price_factor")),
        "execution_terms": sum(1 for item in items if item.get("kind") == "execution_term"),
        "conflicts": sum(1 for item in items if item.get("conflict_flags")),
        "actual_conflicts": sum(1 for item in actual_items if item.get("conflict_flags")),
        "expected_missing": sum(1 for item in items if item.get("expected_missing")),
        "documents_ready": document_state["text_ready"],
        "documents_total": document_state["total"],
        "unbound_facts": _int_metric(
            source_metrics.get("unbound"),
            sum(1 for item in items if item.get("needs_review")),
        ),
    }


def _decision_summary(item: dict[str, Any] | None, fallback: str) -> str:
    if not item:
        return fallback
    label = _text(item.get("label"))
    impact = _text(item.get("impact") or item.get("description"))
    if not label or not impact:
        return fallback
    return f"Сначала проверить: {label}. {_compact_text(impact, 180)}"


def _decision_reason(item: dict[str, Any]) -> str:
    label = _text(item.get("label")) or "условие"
    impact = _text(item.get("impact") or item.get("description") or item.get("operator_action"))
    source = _text(item.get("source_label") or item.get("document_name") or item.get("source"))
    reason = label
    if impact:
        reason = f"{reason} — {_compact_text(impact, 150)}"
    if source:
        reason = f"{reason} ({source})"
    return reason


def _text_list(value: Any) -> list[str]:
    values = value if isinstance(value, list) else [value]
    return [_text(item) for item in values if _text(item)]


def _number_or_none(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int_metric(value: Any, fallback: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def _compact_text(value: Any, limit: int) -> str:
    text = re.sub(r"\s+", " ", _text(value)).strip()
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip(" .,;:") + "…"


def _text(value: Any) -> str:
    return "" if value in (None, "") else str(value).strip()
