from tender_killer.analysis_operator_view_assembler_service import assemble_operator_view


def test_assemble_operator_view_builds_full_contract_from_sections():
    blocker = {
        "id": "risk:license",
        "kind": "risk",
        "type": "risk",
        "label": "Лицензия",
        "description": "Без лицензии заявку могут отклонить.",
        "category": "legal",
        "severity": "high",
        "source_label": "ТЗ.docx",
        "source_context": "Требуется лицензия на работы.",
        "operator_action": "Проверить лицензию.",
        "priority": 90,
        "is_blocker": True,
        "needs_review": True,
    }
    sections = [
        {
            "id": "decision_risks",
            "title": "Итог и риски",
            "count": 1,
            "tone": "danger",
            "empty": "Критичных условий нет.",
            "items": [blocker],
        },
        {
            "id": "product_compliance",
            "title": "Товар и документы",
            "count": 0,
            "tone": "default",
            "empty": "Не найдено.",
            "items": [],
        },
    ]

    view = assemble_operator_view(
        analysis={"confidence": "0.91", "status": "needs_review"},
        sections=sections,
        document_state={"text_ready": 1, "total": 2, "status": "partial"},
        status="needs_review",
        fact_metrics={"unbound": 3},
    )

    assert view["version"] == 3
    assert view["major_blocks"] == sections
    assert view["sections"] == sections
    assert view["metrics"]["facts"] == 1
    assert view["metrics"]["documents_ready"] == 1
    assert view["metrics"]["unbound_facts"] == 3
    assert view["decision_brief"]["status"] == "manual_review"
    assert view["decision_brief"]["blockers"] == ["Лицензия"]
    assert view["condition_groups"]["version"] == 1
    assert [item["id"] for item in view["action_plan"]] == ["decision_risks", "product_compliance"]
    assert "tz_workflow" in view
    assert "ai_questions" in view
    assert "playbooks" in view
    assert "evidence_drilldowns" in view
