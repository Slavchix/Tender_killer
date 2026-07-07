from __future__ import annotations

from typing import Any

from tender_killer.analysis_operator_sections_service import MAJOR_SECTION_IDS
from tender_killer.analysis_operator_view_service import build_analysis_operator_view


def report_operator_view(analysis: dict[str, Any], documents: list[dict[str, Any]]) -> dict[str, Any]:
    operator_view = analysis.get("operator_view") if isinstance(analysis, dict) else None
    if isinstance(operator_view, dict) and _has_four_block_sections(operator_view):
        if isinstance(operator_view.get("condition_groups"), dict):
            return operator_view
        rebuilt = build_analysis_operator_view(analysis, documents)
        return {
            **operator_view,
            "condition_groups": rebuilt.get("condition_groups", {}),
            "action_plan": rebuilt.get("action_plan", operator_view.get("action_plan", [])),
        }
    return build_analysis_operator_view(analysis, documents)


def analysis_decision(analysis: dict[str, Any], documents: list[dict[str, Any]]) -> dict[str, Any]:
    if not analysis:
        return {
            "title": "Нужен анализ ТЗ",
            "summary": "Сначала извлеките текст документов и запустите анализ.",
            "reasons": [f"Документов в карточке: {len(documents)}"] if documents else [],
        }

    operator_view = analysis.get("operator_view") if isinstance(analysis, dict) else None
    decision = operator_view.get("decision_brief") if isinstance(operator_view, dict) else None
    if isinstance(decision, dict) and any(decision.get(key) for key in ("title", "summary", "reasons")):
        return {
            "title": _value(decision.get("title"), "Analysis decision"),
            "summary": _value(decision.get("summary"), ""),
            "reasons": _text_list(decision.get("reasons")),
        }

    red_flags = _text_list(analysis.get("red_flags"))
    risks = _text_list(analysis.get("risks"))
    requirements = _text_list(analysis.get("requirements"))
    checklist = [item for item in analysis.get("checklist") or [] if isinstance(item, dict)]
    has_high_check = any(item.get("severity") == "high" for item in checklist)
    status_text = _analysis_status(analysis.get("status"))
    confidence_text = _confidence(analysis.get("confidence"))
    reasons = [
        *[f"Красный флаг: {item}" for item in red_flags],
        *[f"Риск: {item}" for item in risks],
        *[f"Требование: {item}" for item in requirements],
    ]

    if red_flags or has_high_check:
        return {
            "title": "Нужна ручная проверка",
            "summary": f"{status_text}, уверенность {confidence_text}. Сначала проверьте критичные условия.",
            "reasons": reasons,
        }
    if risks or requirements:
        return {
            "title": "Проверить условия",
            "summary": f"{status_text}, уверенность {confidence_text}. Существенных блокеров нет, но условия надо сверить.",
            "reasons": reasons,
        }
    return {
        "title": "Критичных рисков не видно",
        "summary": f"{status_text}, уверенность {confidence_text}. Можно переходить к экономике и поставщикам.",
        "reasons": [_value(analysis.get("summary"), "Анализ не нашел явных рисков и требований.")],
    }


def analysis_operator_view(analysis: dict[str, Any], documents: list[dict[str, Any]]) -> dict[str, Any]:
    return build_analysis_operator_view(analysis, documents)


def _has_four_block_sections(operator_view: dict[str, Any]) -> bool:
    sections = operator_view.get("major_blocks") or operator_view.get("sections")
    if not isinstance(sections, list):
        return False
    section_ids = {str(section.get("id") or "") for section in sections if isinstance(section, dict)}
    return set(MAJOR_SECTION_IDS).issubset(section_ids)


def _text_list(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    return [_value(value, "").strip() for value in values if _value(value, "").strip()]


def _value(value: Any, fallback: str = "не указано") -> str:
    if value is None or value == "":
        return fallback
    return str(value)


def _confidence(value: Any) -> str:
    try:
        return f"{float(value) * 100:.0f}%"
    except (TypeError, ValueError):
        return "не указано"


def _analysis_status(value: Any) -> str:
    labels = {
        "high_risk": "высокий риск",
        "needs_review": "нужна проверка",
        "ok": "можно продолжать",
        "no_text": "нет текста документов",
    }
    return labels.get(str(value or ""), _value(value, "не указан"))
