from tender_killer.analysis_operator_sections_service import MAJOR_SECTION_IDS, build_major_sections


def test_build_major_sections_routes_operator_items_without_view_side_effects():
    sections = build_major_sections(
        [
            {
                "id": "risk:license",
                "kind": "risk",
                "type": "risk",
                "label": "Лицензия",
                "category": "legal",
                "severity": "high",
                "value": "Требуется лицензия на выполняемые работы.",
                "source_context": "Требуется лицензия на выполняемые работы.",
                "priority": 90,
                "is_blocker": True,
            },
            {
                "id": "term:delivery",
                "kind": "execution_term",
                "type": "execution_term",
                "label": "Срок поставки",
                "category": "delivery",
                "severity": "medium",
                "value": "Срок поставки 5 рабочих дней.",
                "source_context": "Срок поставки 5 рабочих дней.",
                "priority": 40,
            },
            {
                "id": "term:payment",
                "kind": "requirement",
                "type": "requirement",
                "label": "Условия оплаты",
                "category": "payment",
                "severity": "medium",
                "value": "Условия оплаты: 30 календарных дней.",
                "source_context": "Условия оплаты: 30 календарных дней.",
                "priority": 30,
            },
        ],
        [{"name": "ТЗ.docx", "text_status": "ok"}],
    )

    assert [section["id"] for section in sections] == list(MAJOR_SECTION_IDS)
    section_items = {section["id"]: [item["label"] for item in section["items"]] for section in sections}
    assert section_items["decision_risks"] == ["Лицензия"]
    assert "Документы для анализа" in section_items["product_compliance"]
    assert section_items["fulfillment_terms"] == ["Срок поставки"]
    assert section_items["acceptance_payment"] == ["Условия оплаты"]


def test_build_major_sections_marks_pending_empty_sections_as_pending():
    sections = build_major_sections([], [], pending=True)

    assert [section["tone"] for section in sections] == ["pending", "pending", "pending", "pending"]
    assert [section["count"] for section in sections] == [0, 0, 0, 0]
