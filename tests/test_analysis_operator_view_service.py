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
                "evidence": "Contract security is 5%.",
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
                "evidence": "Short delivery in 3 days.",
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
                    "source_context": "Указывается страна происхождения товара.",
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
                    "source_context": "Поставщик предоставляет сертификат.",
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
                    "source_context": "Нужна лицензия на работы.",
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
    assert sections["decision_risks"]["items"][0]["source_binding"]["level"] == "unbound"
    assert sections["decision_risks"]["items"][0]["confidence_level"]["level"] == "low"
    assert sections["product_compliance"]["items"][0]["price_impact"] == "documents"
    assert sections["product_compliance"]["items"][0]["source_binding"]["label"] == "источник подтвержден"
    assert sections["product_compliance"]["items"][0]["confidence_level"]["label"] == "уверенность высокая"


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


def test_build_analysis_operator_view_marks_unbound_non_blockers_as_weak_facts():
    view = build_analysis_operator_view(
        {
            "summary": "Supply goods.",
            "analysis_facts": {
                "version": 1,
                "items": [
                    {
                        "id": "requirement:unclear",
                        "kind": "requirement",
                        "label": "temperature mode",
                        "value": "temperature mode",
                        "category": "general",
                        "severity": "medium",
                        "fragment": "temperature mode",
                        "needs_review": True,
                    }
                ],
            },
        },
        [],
    )

    sections = {section["id"]: section for section in view["sections"]}
    item = sections["product_compliance"]["items"][0]

    assert item["display_tier"] == "weak"
    assert item["weak_reason"]
    assert item["operator_summary"]
    assert item["operator_check"]
    assert not item["is_blocker"]


def test_build_analysis_operator_view_adds_structured_fact_interpretation():
    view = build_analysis_operator_view(
        {
            "summary": "Supply goods.",
            "analysis_facts": {
                "version": 1,
                "items": [
                    {
                        "id": "payment:advance",
                        "kind": "execution_term",
                        "label": "Аванс",
                        "value": "Авансирование не предусмотрено.",
                        "category": "financial",
                        "severity": "medium",
                        "document_name": "Контракт.docx",
                        "fragment": "Авансирование не предусмотрено. Оплата после приемки.",
                    }
                ],
            },
        },
        [],
    )

    sections = {section["id"]: section for section in view["sections"]}
    item = sections["acceptance_payment"]["items"][0]

    assert item["interpretation"]["found"] == "Авансирование не предусмотрено."
    assert "авансом" in item["interpretation"]["meaning"].casefold()
    assert "оборот" in item["interpretation"]["impact"].casefold()


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


def test_build_analysis_operator_view_explains_typical_tz_conditions_for_operator():
    analysis = {
        "summary": "Поставка бумаги",
        "confidence": 0.88,
        "analysis_facts": {
            "version": 1,
            "items": [
                {
                    "kind": "blocker",
                    "label": "национальный режим/страна происхождения",
                    "value": "Нужно указать страну происхождения и реестровый номер.",
                    "category": "national_regime",
                    "severity": "high",
                    "impact": "Проверить до участия: может повлиять на возможность участия.",
                    "operator_action": "Проверить допустимость участия до расчета.",
                    "price_impact": "compliance",
                    "document_name": "ТЗ.docx",
                    "is_blocker": True,
                },
                {
                    "kind": "requirement",
                    "label": "обеспечение исполнения контракта",
                    "value": "Обеспечение исполнения контракта 10% от цены контракта.",
                    "category": "financial",
                    "severity": "medium",
                    "document_name": "Контракт.docx",
                },
                {
                    "kind": "execution_term",
                    "label": "короткий срок поставки",
                    "value": "Поставка товара в течение 2 дней с даты заключения контракта.",
                    "category": "delivery",
                    "severity": "medium",
                    "document_name": "ТЗ.docx",
                },
                {
                    "kind": "execution_term",
                    "label": "УПД и закрывающие документы",
                    "value": "Оплата после подписания УПД и документов о приемке.",
                    "category": "acceptance",
                    "severity": "medium",
                    "document_name": "Контракт.docx",
                },
                {
                    "kind": "execution_term",
                    "label": "монтаж/пусконаладка",
                    "value": "Поставщик выполняет монтаж, пусконаладку и ввод оборудования в эксплуатацию.",
                    "category": "delivery",
                    "severity": "medium",
                    "document_name": "ТЗ.docx",
                },
                {
                    "kind": "supplier_document",
                    "label": "сертификат/декларация",
                    "value": "Поставщик предоставляет сертификат соответствия и декларацию.",
                    "category": "documents",
                    "severity": "medium",
                    "document_name": "ТЗ.docx",
                },
            ],
        },
    }

    view = build_analysis_operator_view(analysis, [{"name": "ТЗ.docx", "local_path": "tz.docx", "text_status": "ok"}])
    items = {
        item["label"]: item
        for section in view["sections"]
        for item in section["items"]
        if item["type"] != "document_summary"
    }

    national = items["национальный режим/страна происхождения"]
    assert "реестр" in national["description"].casefold()
    assert "допуск" in national["impact"].casefold()
    assert "страну происхождения" in national["operator_action"].casefold()

    security = items["обеспечение исполнения контракта"]
    assert "оборот" in security["description"].casefold()
    assert "оборот" in security["impact"].casefold()
    assert "обеспечение" in security["operator_action"].casefold()
    assert security["price_impact"] == "working_capital"

    short_delivery = items["короткий срок поставки"]
    assert "налич" in short_delivery["description"].casefold()
    assert "сроч" in short_delivery["operator_action"].casefold()
    assert "логист" in short_delivery["impact"].casefold()
    assert short_delivery["price_impact"] == "logistics"

    closing_docs = items["УПД и закрывающие документы"]
    assert "упд" in closing_docs["description"].casefold()
    assert "оплат" in closing_docs["operator_action"].casefold()
    assert "приемк" in closing_docs["impact"].casefold()

    montage = items["монтаж/пусконаладка"]
    assert "пусконалад" in montage["description"].casefold()
    assert "специалист" in montage["operator_action"].casefold()
    assert "дополнительные расходы" in montage["impact"].casefold()

    certificate = items["сертификат/декларация"]
    assert "сертифик" in certificate["description"].casefold()
    assert "поставщик" in certificate["operator_action"].casefold()
    assert certificate["price_impact"] == "documents"


def test_build_analysis_operator_view_prioritizes_actions_and_source_context():
    analysis = {
        "summary": "Поставка бумаги",
        "confidence": 0.91,
        "analysis_facts": {
            "version": 1,
            "items": [
                {
                    "kind": "blocker",
                    "label": "страна происхождения товара",
                    "value": "Заявка должна содержать страну происхождения товара и реестровый номер.",
                    "category": "national_regime",
                    "severity": "high",
                    "fragment": "Участник указывает страну происхождения товара в заявке.",
                    "document_name": "ТЗ.docx",
                    "source_page": 4,
                    "is_blocker": True,
                },
                {
                    "kind": "supplier_document",
                    "label": "сертификат/декларация",
                    "value": "Поставщик предоставляет сертификат соответствия.",
                    "category": "documents",
                    "severity": "medium",
                    "fragment": "При поставке предоставляется сертификат соответствия.",
                    "document_name": "ТЗ.docx",
                    "source_page": 6,
                },
                {
                    "kind": "execution_term",
                    "label": "оплата после приемки",
                    "value": "Оплата производится после подписания документов о приемке.",
                    "category": "payment",
                    "severity": "medium",
                    "fragment": "Оплата после подписания документов о приемке.",
                    "document_name": "Контракт.docx",
                },
            ],
        },
    }

    view = build_analysis_operator_view(analysis, [{"name": "ТЗ.docx", "local_path": "tz.docx", "text_status": "ok"}])
    sections = {section["id"]: section for section in view["sections"]}
    national = sections["decision_risks"]["items"][0]
    certificate = sections["product_compliance"]["items"][0]
    decision_step = next(item for item in view["action_plan"] if item["id"] == "decision_risks")
    product_step = next(item for item in view["action_plan"] if item["id"] == "product_compliance")

    assert view["decision_brief"]["next_step"] == national["operator_action"]
    assert view["decision_brief"]["reasons"][0].startswith("национальный режим/страна происхождения")
    assert "отклон" in view["decision_brief"]["reasons"][0].casefold()
    assert "Почему важно" in national["source_context"]
    assert "допуск" in national["source_context"].casefold()
    assert national["evidence_summary"].startswith("ТЗ.docx · стр. 4")
    assert "Участник указывает страну происхождения" in national["evidence_summary"]
    assert decision_step["next_step"] == national["operator_action"]
    assert decision_step["items"][0] == "национальный режим/страна происхождения · ТЗ.docx · стр. 4"
    assert product_step["next_step"] == certificate["operator_action"]
    assert product_step["items"][0] == "сертификат/декларация · ТЗ.docx · стр. 6"
def test_build_analysis_operator_view_marks_conflicting_conditions_for_manual_review():
    view = build_analysis_operator_view(
        {
            "summary": "Поставка бумаги",
            "analysis_facts": {
                "version": 1,
                "items": [
                    {
                        "kind": "execution_term",
                        "label": "Аванс",
                        "value": "Авансирование не предусмотрено.",
                        "category": "financial",
                        "severity": "medium",
                        "document_name": "Контракт.docx",
                        "fragment": "Авансирование не предусмотрено.",
                    },
                    {
                        "kind": "execution_term",
                        "label": "Аванс",
                        "value": "Предусмотрен аванс 30% от цены контракта.",
                        "category": "financial",
                        "severity": "medium",
                        "document_name": "Проект контракта.docx",
                        "fragment": "Предусмотрен аванс 30% от цены контракта.",
                    },
                ],
            },
        },
        [{"name": "Контракт.docx", "local_path": "contract.docx", "text_status": "ok"}],
    )

    sections = {section["id"]: section for section in view["sections"]}
    items = sections["acceptance_payment"]["items"]

    assert len(items) == 2
    assert all(item["conflict_flags"] for item in items)
    assert all(item["needs_review"] for item in items)
    assert "противореч" in items[0]["operator_check"].casefold()
    assert view["metrics"]["conflicts"] == 2


def test_build_analysis_operator_view_adds_expected_missing_checks_from_context():
    view = build_analysis_operator_view(
        {
            "summary": "Поставка бумаги",
            "analysis_facts": {
                "version": 1,
                "items": [
                    {
                        "kind": "subject",
                        "label": "Предмет",
                        "value": "Поставка бумаги",
                        "category": "subject",
                        "severity": "medium",
                        "document_name": "ТЗ.docx",
                        "fragment": "Поставка бумаги",
                    }
                ],
            },
        },
        [{"name": "ТЗ.docx", "local_path": "tz.docx", "text_status": "ok"}],
    )

    sections = {section["id"]: section for section in view["sections"]}
    labels = [item["label"] for item in sections["acceptance_payment"]["items"]]

    assert "условия оплаты" in labels
    assert "приемка и закрывающие документы" in labels
    expected_item = next(item for item in sections["acceptance_payment"]["items"] if item["label"] == "условия оплаты")
    assert expected_item["display_tier"] == "expected_missing"
    assert expected_item["interpretation"]["confidence"] == "missing"
    assert "точная формулировка" in expected_item["operator_check"].casefold()
