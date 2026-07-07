from tender_killer.analysis_operator_sections_service import build_major_sections
from tender_killer.analysis_operator_summary_service import build_operator_decision_brief
from tender_killer.analysis_operator_summary_service import build_operator_view_metrics


def test_build_operator_decision_brief_marks_blockers_for_manual_review():
    sections = build_major_sections(
        [
            {
                "id": "risk:license",
                "kind": "risk",
                "type": "risk",
                "label": "Лицензия",
                "description": "Без лицензии заявку могут отклонить.",
                "category": "legal",
                "severity": "high",
                "source_label": "ТЗ.docx",
                "source_context": "Требуется лицензия на выполняемые работы.",
                "operator_action": "Проверить лицензию до подачи заявки.",
                "priority": 90,
                "is_blocker": True,
                "needs_review": True,
            }
        ],
        [],
    )

    decision = build_operator_decision_brief({"confidence": "0.76"}, sections, "needs_review")

    assert decision["status"] == "manual_review"
    assert decision["tone"] == "danger"
    assert decision["title"] == "Нужна ручная проверка"
    assert decision["confidence"] == 0.76
    assert decision["summary"].startswith("Сначала проверить: Лицензия.")
    assert decision["next_step"] == "Проверить лицензию до подачи заявки."
    assert decision["reasons"] == ["Лицензия — Без лицензии заявку могут отклонить. (ТЗ.docx)"]


def test_build_operator_view_metrics_counts_actual_and_expected_items():
    items = [
        {
            "id": "risk:license",
            "kind": "risk",
            "label": "Лицензия",
            "is_blocker": True,
            "needs_review": True,
        },
        {
            "id": "term:delivery",
            "kind": "execution_term",
            "label": "Срок поставки",
            "is_price_factor": True,
        },
        {
            "id": "expected:payment",
            "kind": "requirement",
            "label": "Условия оплаты",
            "expected_missing": True,
            "needs_review": True,
            "conflict_flags": ["Нужна ручная проверка"],
        },
    ]
    sections = [{"id": "decision_risks", "items": [items[0]]}, {"id": "acceptance_payment", "items": [items[2]]}]

    metrics = build_operator_view_metrics(
        items,
        sections,
        {"text_ready": 2, "total": 3},
        {"unbound": "7"},
    )

    assert metrics == {
        "major_blocks": 2,
        "facts": 3,
        "requirements": 1,
        "risks": 1,
        "blockers": 1,
        "actual_blockers": 1,
        "needs_review": 2,
        "price_factors": 1,
        "execution_terms": 1,
        "conflicts": 1,
        "actual_conflicts": 0,
        "expected_missing": 1,
        "documents_ready": 2,
        "documents_total": 3,
        "unbound_facts": 7,
    }
