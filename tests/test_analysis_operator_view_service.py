from __future__ import annotations

from tender_killer.analysis_operator_view_service import MAJOR_SECTION_IDS, build_analysis_operator_view


def test_build_analysis_operator_view_returns_only_four_major_blocks_from_legacy_analysis():
    analysis = {
        "summary": "Supply office paper.",
        "status": "needs_review",
        "confidence": 0.82,
        "requirements": ["certificate"],
        "risks": ["contract security"],
        "red_flags": ["national regime"],
        "checklist": [
            {
                "label": "contract security",
                "category": "financial",
                "severity": "high",
                "evidence": "Security is 5%.",
            },
            {
                "label": "certificate",
                "category": "documents",
                "severity": "medium",
                "evidence": "Certificate is required.",
            },
            {
                "label": "short delivery",
                "category": "delivery",
                "severity": "high",
                "evidence": "Delivery in 3 days.",
            },
        ],
        "execution_terms": [
            {
                "type": "delivery_deadline",
                "label": "Срок поставки",
                "value": "в течение 5 рабочих дней",
                "category": "delivery",
                "severity": "medium",
                "evidence": "Срок поставки товара: в течение 5 рабочих дней.",
            },
            {
                "type": "payment_terms",
                "label": "Оплата",
                "value": "оплата в течение 7 рабочих дней",
                "category": "financial",
                "severity": "medium",
                "evidence": "Оплата в течение 7 рабочих дней.",
            },
        ],
    }
    documents = [
        {"name": "TZ.docx", "text_status": "ok"},
        {"name": "Contract.pdf", "text_status": "empty"},
    ]

    view = build_analysis_operator_view(analysis, documents)

    assert view["version"] == 3
    assert [section["id"] for section in view["sections"]] == list(MAJOR_SECTION_IDS)
    assert [section["id"] for section in view["major_blocks"]] == list(MAJOR_SECTION_IDS)
    assert view["decision_brief"]["status"] == "manual_review"
    assert view["decision_brief"]["primary_section"] == "decision_risks"
    assert view["decision_brief"]["confidence"] == 0.82
    assert [item["id"] for item in view["action_plan"]] == list(MAJOR_SECTION_IDS)
    assert view["metrics"]["major_blocks"] == 4
    assert view["metrics"]["documents_ready"] == 1
    assert view["metrics"]["documents_total"] == 2

    sections = {section["id"]: section for section in view["sections"]}
    assert {item["label"] for item in sections["decision_risks"]["items"]} == {
        "contract security",
        "national regime",
        "short delivery",
    }
    assert {item["label"] for item in sections["product_compliance"]["items"]} >= {
        "Предмет",
        "certificate",
        "Документы для анализа",
    }
    assert [item["label"] for item in sections["fulfillment_terms"]["items"]] == ["Срок поставки"]
    assert [item["label"] for item in sections["acceptance_payment"]["items"]] == ["Оплата"]


def test_build_analysis_operator_view_groups_analysis_facts_into_four_operator_blocks():
    analysis = {
        "summary": "Supply office paper.",
        "confidence": 0.81,
        "analysis_facts": {
            "version": 1,
            "metrics": {"total": 5, "blockers": 1, "price_factors": 2, "unbound": 1},
            "items": [
                {
                    "id": "subject:paper",
                    "kind": "subject",
                    "label": "Предмет",
                    "value": "Supply office paper.",
                    "category": "subject",
                    "severity": "medium",
                },
                {
                    "id": "blocker:national-regime",
                    "kind": "blocker",
                    "label": "национальный режим",
                    "value": "страна происхождения товара",
                    "category": "national_regime",
                    "severity": "high",
                    "document_name": "spec.docx",
                    "fragment": "Указывается страна происхождения товара.",
                    "operator_action": "Проверить допустимость участия до расчета.",
                    "price_impact": "compliance",
                    "priority": 90,
                    "is_blocker": True,
                    "is_price_factor": False,
                },
                {
                    "id": "supplier_document:certificate",
                    "kind": "supplier_document",
                    "label": "сертификат/декларация",
                    "value": "сертификат соответствия",
                    "category": "documents",
                    "severity": "medium",
                    "document_name": "spec.docx",
                    "fragment": "Поставщик предоставляет сертификат.",
                    "operator_action": "Подготовить подтверждающие документы.",
                    "price_impact": "documents",
                    "priority": 50,
                    "is_blocker": False,
                    "is_price_factor": False,
                },
                {
                    "id": "execution_term:delivery",
                    "kind": "execution_term",
                    "label": "Срок поставки",
                    "value": "5 рабочих дней",
                    "category": "delivery",
                    "severity": "medium",
                    "document_name": "contract.docx",
                    "fragment": "Срок поставки 5 рабочих дней.",
                    "operator_action": "Проверить срок исполнения и заложить логистику.",
                    "price_impact": "logistics",
                    "priority": 60,
                    "is_blocker": False,
                    "is_price_factor": True,
                },
                {
                    "id": "execution_term:payment",
                    "kind": "execution_term",
                    "label": "Оплата",
                    "value": "7 рабочих дней",
                    "category": "payment",
                    "severity": "medium",
                    "document_name": "contract.docx",
                    "fragment": "Оплата в течение 7 рабочих дней.",
                    "operator_action": "Проверить оплату.",
                    "price_impact": "working_capital",
                    "priority": 60,
                    "is_blocker": False,
                    "is_price_factor": True,
                },
                {
                    "id": "requirement:license",
                    "kind": "requirement",
                    "label": "лицензия/СРО",
                    "value": "Нужна лицензия на работы.",
                    "category": "legal",
                    "severity": "high",
                    "document_name": "Документ не привязан",
                    "fragment": "Нужна лицензия на работы.",
                    "operator_action": "Проверить источник факта вручную.",
                    "price_impact": "none",
                    "priority": 95,
                    "needs_review": True,
                    "is_blocker": True,
                    "is_price_factor": False,
                },
            ],
        },
    }

    view = build_analysis_operator_view(analysis, [])
    sections = {section["id"]: section for section in view["sections"]}

    assert view["decision_brief"]["primary_section"] == "decision_risks"
    assert view["metrics"]["facts"] == 6
    assert view["metrics"]["unbound_facts"] == 1
    assert [item["label"] for item in sections["decision_risks"]["items"]] == [
        "лицензия/СРО",
        "национальный режим/страна происхождения",
    ]
    assert [item["label"] for item in sections["product_compliance"]["items"]] == [
        "сертификат/декларация",
        "Предмет",
    ]
    assert [item["label"] for item in sections["fulfillment_terms"]["items"]] == ["Срок поставки"]
    assert [item["label"] for item in sections["acceptance_payment"]["items"]] == ["Оплата"]
    assert sections["decision_risks"]["items"][0]["operator_action"] == (
        "Проверить, действительно ли нужна лицензия или СРО, и есть ли подтверждение у участника."
    )
    assert sections["product_compliance"]["items"][0]["price_impact"] == "documents"


def test_build_analysis_operator_view_returns_pending_four_block_contract_without_analysis():
    view = build_analysis_operator_view(None, [{"name": "Spec.docx", "text_status": "pending"}])

    assert view["version"] == 3
    assert view["decision_brief"]["status"] == "pending"
    assert view["decision_brief"]["primary_section"] == "decision_risks"
    assert view["metrics"]["documents_total"] == 1
    assert [section["id"] for section in view["sections"]] == list(MAJOR_SECTION_IDS)
    assert view["sections"][1]["id"] == "product_compliance"
    assert view["sections"][1]["items"][0]["label"] == "Документы для анализа"
    assert view["sections"][1]["items"][0]["type"] == "document_summary"


def test_build_analysis_operator_view_dedupes_semantic_risks_and_adds_operator_context():
    analysis = {
        "summary": "Поставка электроинструмента",
        "confidence": 0.9,
        "analysis_facts": {
            "version": 1,
            "metrics": {"total": 5, "blockers": 4, "price_factors": 0, "unbound": 0},
            "items": [
                {
                    "kind": "blocker",
                    "label": "национальный режим/страна происхождения",
                    "value": "Страна происхождения указывается в заявке.",
                    "category": "national_regime",
                    "severity": "high",
                    "fragment": "Заявка должна содержать наименование страны происхождения товара.",
                    "document_name": "spec.docx",
                    "is_blocker": True,
                },
                {
                    "kind": "blocker",
                    "label": "страна происхождения товара",
                    "value": "Страна происхождения указывается в заявке.",
                    "category": "national_regime",
                    "severity": "high",
                    "fragment": "Заявка должна содержать наименование страны происхождения товара.",
                    "document_name": "spec.docx",
                    "is_blocker": True,
                },
                {
                    "kind": "blocker",
                    "label": "лицензия/СРО",
                    "value": "Требуется допуск СРО.",
                    "category": "legal",
                    "severity": "high",
                    "fragment": "Участник предоставляет подтверждение членства в СРО.",
                    "document_name": "spec.docx",
                    "is_blocker": True,
                },
                {
                    "kind": "requirement",
                    "label": "членство в СРО",
                    "value": "Требуется допуск СРО.",
                    "category": "legal",
                    "severity": "high",
                    "fragment": "Участник предоставляет подтверждение членства в СРО.",
                    "document_name": "spec.docx",
                    "is_blocker": True,
                },
            ],
        },
    }

    view = build_analysis_operator_view(
        analysis,
        [
            {"name": "spec.docx", "local_path": "spec.docx", "text_status": "ok"},
            {"name": "contract.docx", "local_path": "contract.docx", "text_status": "ok"},
        ],
    )
    sections = {section["id"]: section for section in view["sections"]}
    risk_labels = [item["label"] for item in sections["decision_risks"]["items"]]
    document_items = [item for item in sections["product_compliance"]["items"] if item["type"] == "document_summary"]

    assert risk_labels == ["лицензия/СРО", "национальный режим/страна происхождения"]
    assert sections["decision_risks"]["items"][0]["description"] != sections["decision_risks"]["items"][0]["label"]
    assert "участ" in sections["decision_risks"]["items"][0]["description"].casefold()
    assert "СРО" in sections["decision_risks"]["items"][0]["operator_action"]
    assert sections["product_compliance"]["count"] == 0
    assert len(document_items) == 1
    assert document_items[0]["label"] == "Документы для анализа"
    assert "2 файла" in document_items[0]["description"]
