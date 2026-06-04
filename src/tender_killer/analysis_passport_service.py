from __future__ import annotations

from typing import Any

from tender_killer.analysis_operator_view_service import MAJOR_SECTION_IDS, build_analysis_operator_view


def build_analysis_tz_passport(
    analysis: dict[str, Any] | None,
    documents: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a compact TZ passport from the same four-block Analysis contract."""
    operator_view = build_analysis_operator_view(analysis, documents)
    decision = operator_view.get("decision_brief") if isinstance(operator_view.get("decision_brief"), dict) else {}
    sections = [_passport_section(section) for section in operator_view.get("sections", []) if section.get("id") in MAJOR_SECTION_IDS]
    return {
        "version": 2,
        "status": str(decision.get("status") or "pending"),
        "title": str(decision.get("title") or "Паспорт ТЗ появится после анализа."),
        "summary": str(decision.get("summary") or ""),
        "confidence": decision.get("confidence"),
        "sections": sections,
    }


def _passport_section(section: dict[str, Any]) -> dict[str, Any]:
    items = [_passport_item(item) for item in section.get("items", []) if isinstance(item, dict)]
    return {
        "id": str(section.get("id") or ""),
        "title": str(section.get("title") or ""),
        "count": len(items),
        "tone": str(section.get("tone") or "default"),
        "empty": str(section.get("empty") or ""),
        "items": items,
    }


def _passport_item(item: dict[str, Any]) -> dict[str, Any]:
    kind = str(item.get("kind") or item.get("type") or "fact")
    label = str(item.get("label") or "Условие")
    if kind == "subject":
        label = "Кратко"
    return {
        "id": str(item.get("id") or label),
        "type": kind,
        "label": label,
        "value": str(item.get("value") or item.get("description") or item.get("fragment") or ""),
        "category": str(item.get("category") or "general"),
        "severity": str(item.get("severity") or "medium"),
        "source": str(item.get("source_label") or item.get("source") or ""),
        "impact": str(item.get("impact") or item.get("operator_action") or ""),
    }
