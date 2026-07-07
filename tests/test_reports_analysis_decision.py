from __future__ import annotations

import importlib
import importlib.util

from tender_killer.analysis_operator_sections_service import MAJOR_SECTION_IDS


def _decision_service():
    spec = importlib.util.find_spec("tender_killer.reports_analysis_decision")
    assert spec is not None
    return importlib.import_module("tender_killer.reports_analysis_decision")


def test_analysis_decision_uses_operator_brief_when_available():
    service = _decision_service()

    decision = service.analysis_decision(
        {
            "operator_view": {
                "decision_brief": {
                    "title": "Нужна ручная проверка",
                    "summary": "Проверить допуск до расчета.",
                    "reasons": ["СРО", "", "обеспечение"],
                }
            }
        },
        documents=[],
    )

    assert decision == {
        "title": "Нужна ручная проверка",
        "summary": "Проверить допуск до расчета.",
        "reasons": ["СРО", "обеспечение"],
    }


def test_analysis_decision_marks_high_checklist_as_manual_review():
    service = _decision_service()

    decision = service.analysis_decision(
        {
            "status": "needs_review",
            "confidence": 0.81,
            "requirements": ["сертификат"],
            "risks": ["короткий срок"],
            "checklist": [{"label": "СРО", "severity": "high"}],
        },
        documents=[{"name": "ТЗ.docx"}],
    )

    assert decision["title"] == "Нужна ручная проверка"
    assert "81%" in decision["summary"]
    assert "Риск: короткий срок" in decision["reasons"]
    assert "Требование: сертификат" in decision["reasons"]


def test_report_operator_view_preserves_complete_view_and_adds_condition_groups():
    service = _decision_service()
    operator_view = {
        "major_blocks": [{"id": section_id, "items": []} for section_id in MAJOR_SECTION_IDS],
        "action_plan": [{"id": "existing"}],
        "decision_brief": {"title": "Проверить условия"},
    }

    result = service.report_operator_view(
        {
            "operator_view": operator_view,
            "analysis_facts": {"version": 1, "items": []},
        },
        documents=[{"name": "ТЗ.docx", "text_status": "ok"}],
    )

    assert result["major_blocks"] == operator_view["major_blocks"]
    assert result["decision_brief"] == operator_view["decision_brief"]
    assert isinstance(result["condition_groups"], dict)
    assert result["action_plan"]
    assert result["action_plan"] != operator_view["action_plan"]
