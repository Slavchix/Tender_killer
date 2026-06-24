from __future__ import annotations

from tender_killer.analysis_operator_view_service import MAJOR_SECTION_IDS, build_analysis_operator_view


def test_build_analysis_operator_view_preserves_context_pack_fact_metadata():
    analysis = {
        "analysis_facts": {
            "version": 1,
            "items": [
                {
                    "id": "execution_term:payment_terms",
                    "kind": "execution_term",
                    "label": "условия оплаты",
                    "value": "Оплата после подписания УПД.",
                    "category": "payment",
                    "severity": "medium",
                    "document_name": "pik.zip",
                    "source": "pik.zip",
                    "source_label": "pik.zip · стр. 1",
                    "fragment": "Оплата после подписания УПД.",
                    "source_context": "Оплата после подписания УПД.",
                    "context_document_role": "pik_obligations_payment",
                    "context_document_role_confidence": "high",
                    "context_source_priority": ["payment_terms", "advance"],
                    "context_topics": ["payment_terms", "acceptance_documents"],
                    "context_text_quality": "ok",
                    "context_source_authority": "primary_for_topic",
                    "context_source_reason": "pik_obligations_payment covers payment_terms",
                }
            ],
            "metrics": {"total": 1},
        }
    }

    view = build_analysis_operator_view(analysis, [])
    item = next(
        item
        for section in view["major_blocks"]
        for item in section["items"]
        if item["label"] == "условия оплаты"
    )

    assert item["context_document_role"] == "pik_obligations_payment"
    assert item["context_document_role_confidence"] == "high"
    assert item["context_source_priority"] == ["payment_terms", "advance"]
    assert item["context_topics"] == ["payment_terms", "acceptance_documents"]
    assert item["context_text_quality"] == "ok"
    assert item["context_source_authority"] == "primary_for_topic"
    assert item["context_source_reason"] == "pik_obligations_payment covers payment_terms"


def test_build_analysis_operator_view_builds_condition_groups_for_conflicting_related_facts():
    view = build_analysis_operator_view(
        {
            "analysis_facts": {
                "version": 1,
                "items": [
                    {
                        "id": "fact:advance-negative",
                        "kind": "execution_term",
                        "label": "Аванс",
                        "value": "Авансирование не предусмотрено.",
                        "category": "financial",
                        "severity": "medium",
                        "document_name": "Проект контракта.docx",
                        "source_label": "Проект контракта.docx · стр. 4",
                        "fragment": "Авансирование не предусмотрено.",
                        "source_context": "Авансирование не предусмотрено.",
                        "context_source_authority": "primary_for_topic",
                        "context_source_priority": ["advance", "payment_terms"],
                    },
                    {
                        "id": "fact:advance-positive",
                        "kind": "execution_term",
                        "label": "Аванс",
                        "value": "Предусмотрен аванс 30% от цены контракта.",
                        "category": "financial",
                        "severity": "medium",
                        "document_name": "ПИК.zip",
                        "source_label": "ПИК.zip · стр. 2",
                        "fragment": "Предусмотрен аванс 30% от цены контракта.",
                        "source_context": "Предусмотрен аванс 30% от цены контракта.",
                        "context_source_authority": "primary_for_topic",
                        "context_source_priority": ["advance"],
                    },
                ],
            }
        },
        [{"name": "Проект контракта.docx", "text_status": "ok"}],
    )

    condition_groups = {item["family"]: item for item in view["condition_groups"]["items"]}
    advance = condition_groups["advance"]
    advance_items = [
        item
        for section in view["major_blocks"]
        for item in section["items"]
        if item.get("condition_family") == "advance"
    ]

    assert advance["status"] == "conflict"
    assert advance["source_status"] == "conflicting_sources"
    assert advance["related_fact_ids"] == ["fact:advance-negative", "fact:advance-positive"]
    assert advance["primary_fact_id"] in {"fact:advance-negative", "fact:advance-positive"}
    assert "противореч" in advance["resolution"].casefold()
    assert "Проект контракта.docx · стр. 4" in advance["sources"]
    assert "ПИК.zip · стр. 2" in advance["sources"]
    assert len(advance_items) == 2
    assert all(item["condition_families"] == ["advance"] for item in advance_items)
    assert view["condition_groups"]["metrics"]["conflicts"] == 1


def test_build_analysis_operator_view_condition_groups_choose_primary_topic_source():
    view = build_analysis_operator_view(
        {
            "analysis_facts": {
                "version": 1,
                "items": [
                    {
                        "id": "fact:payment-contract",
                        "kind": "execution_term",
                        "label": "условия оплаты",
                        "value": "Оплата в течение 7 рабочих дней после подписания УПД.",
                        "category": "payment",
                        "severity": "medium",
                        "document_name": "Контракт.docx",
                        "source_label": "Контракт.docx · стр. 8",
                        "fragment": "Оплата в течение 7 рабочих дней после подписания УПД.",
                        "source_context": "Оплата в течение 7 рабочих дней после подписания УПД.",
                        "context_source_authority": "primary_for_topic",
                        "context_source_priority": ["payment_terms", "acceptance_documents"],
                    },
                    {
                        "id": "fact:payment-notice",
                        "kind": "execution_term",
                        "label": "оплата",
                        "value": "Оплата после приемки товара.",
                        "category": "payment",
                        "severity": "medium",
                        "document_name": "Извещение.docx",
                        "source_label": "Извещение.docx · стр. 1",
                        "fragment": "Оплата после приемки товара.",
                        "source_context": "Оплата после приемки товара.",
                        "context_source_authority": "supporting_document",
                    },
                ],
            }
        },
        [{"name": "Контракт.docx", "text_status": "ok"}],
    )

    payment = {item["family"]: item for item in view["condition_groups"]["items"]}["payment"]

    assert payment["status"] == "confirmed"
    assert payment["source_status"] == "primary_source"
    assert payment["primary_fact_id"] == "fact:payment-contract"
    assert payment["related_fact_ids"] == ["fact:payment-contract", "fact:payment-notice"]
    assert payment["summary"].startswith("Оплата в течение 7 рабочих дней")
    assert "главному источнику" in payment["resolution"].casefold()
    assert view["condition_groups"]["metrics"]["confirmed"] >= 1


def test_build_analysis_operator_view_action_plan_uses_condition_groups_not_duplicate_facts():
    view = build_analysis_operator_view(
        {
            "analysis_facts": {
                "version": 1,
                "items": [
                    {
                        "id": "fact:payment",
                        "kind": "execution_term",
                        "label": "Оплата",
                        "value": "Оплата в течение 15 рабочих дней после поставки.",
                        "category": "payment",
                        "document_name": "Проект контракта.docx",
                        "source_label": "Проект контракта.docx · стр. 8",
                        "context_source_authority": "primary_for_topic",
                        "context_source_priority": ["payment_terms"],
                    },
                    {
                        "id": "fact:advance-negative",
                        "kind": "execution_term",
                        "label": "Аванс",
                        "value": "Аванс не предусмотрен.",
                        "category": "financial",
                        "document_name": "Проект контракта.docx",
                        "source_label": "Проект контракта.docx · стр. 4",
                        "fragment": "Аванс не предусмотрен.",
                    },
                    {
                        "id": "fact:advance-positive",
                        "kind": "execution_term",
                        "label": "Аванс",
                        "value": "Предусмотрен аванс 30 процентов.",
                        "category": "financial",
                        "document_name": "ПИК.zip",
                        "source_label": "ПИК.zip · стр. 2",
                        "fragment": "Предусмотрен аванс 30 процентов.",
                    },
                ],
            }
        },
        [{"name": "Проект контракта.docx", "text_status": "ok"}],
    )

    acceptance_step = next(step for step in view["action_plan"] if step["id"] == "acceptance_payment")

    assert acceptance_step["status"] == "manual_review"
    assert acceptance_step["items"] == [
        "аванс · противоречие",
        "условия оплаты · подтверждено",
        "приемка и закрывающие документы · не найдено",
    ]
    assert "fact:advance-negative" in acceptance_step["condition_fact_ids"]
    assert "fact:advance-positive" in acceptance_step["condition_fact_ids"]
    assert "Разобрать противоречие" in acceptance_step["next_step"]
    assert acceptance_step["source"] == "condition_groups"


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
    found_decision_labels = {item["label"] for item in sections["decision_risks"]["items"] if not item.get("expected_missing")}
    found_fulfillment_labels = [item["label"] for item in sections["fulfillment_terms"]["items"] if not item.get("expected_missing")]
    found_acceptance_labels = [item["label"] for item in sections["acceptance_payment"]["items"] if not item.get("expected_missing")]
    assert found_decision_labels == {
        "contract security",
        "short delivery",
    }
    assert {item["label"] for item in sections["product_compliance"]["items"]} >= {
        "Предмет",
        "certificate",
        "Документы для анализа",
    }
    assert found_fulfillment_labels == ["Срок поставки"]
    assert found_acceptance_labels == ["Оплата"]


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


def test_build_analysis_operator_view_surfaces_context_pack_manual_checks():
    analysis = {
        "summary": "Поставка системных блоков.",
        "context_pack": {
            "version": 1,
            "mismatch_flags": ["subject_mismatch"],
            "expected_missing_reasons": ["missing_because_primary_doc_unread"],
            "documents": [
                {
                    "id": "document:1",
                    "name": "Приложение 5 ООЗ.docx",
                    "document_role": "technical_spec",
                    "mismatch_flags": ["subject_mismatch"],
                    "tender_identity_match": {
                        "subject": {
                            "status": "mismatch",
                            "tender_title": "Поставка системных блоков",
                            "document_subject": "Поставка велотренажеров спортивных",
                        }
                    },
                },
                {
                    "id": "document:2",
                    "name": "ООЗ.rar",
                    "document_role": "unsupported_primary",
                    "text_quality": {"status": "extraction_error", "text_error": "unsupported archive"},
                },
            ],
        },
    }

    view = build_analysis_operator_view(analysis, [])
    sections = {section["id"]: section for section in view["sections"]}
    decision_labels = {item["label"] for item in sections["decision_risks"]["items"]}
    product_labels = {item["label"] for item in sections["product_compliance"]["items"]}
    mismatch_item = next(
        item
        for item in sections["decision_risks"]["items"]
        if item["label"] == "Документ не совпадает с карточкой закупки"
    )

    assert "Документ не совпадает с карточкой закупки" in decision_labels
    assert "Главный документ ТЗ не прочитан" in product_labels
    assert mismatch_item["needs_review"] is True
    assert mismatch_item["source_label"] == "Приложение 5 ООЗ.docx"
    assert "велотренажеров" in mismatch_item["fragment"]
    assert view["decision_brief"]["status"] == "manual_review"


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
    risk_items = [item for item in sections["decision_risks"]["items"] if not item.get("expected_missing")]
    risk_labels = [item["label"] for item in risk_items]
    document_items = [item for item in sections["product_compliance"]["items"] if item["type"] == "document_summary"]
    product_items = [
        item
        for item in sections["product_compliance"]["items"]
        if item["type"] != "document_summary" and not item.get("expected_missing")
    ]

    assert risk_labels == ["лицензия/СРО", "национальный режим/страна происхождения"]
    assert risk_items[0]["description"] != risk_items[0]["label"]
    assert "участ" in risk_items[0]["description"].casefold()
    assert "СРО" in risk_items[0]["operator_action"]
    assert product_items == []
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
    assert decision_step["items"][0] == "национальный режим · подтверждено"
    assert national["id"] in decision_step["condition_fact_ids"]
    assert decision_step["source"] == "condition_groups"
    assert product_step["next_step"] == certificate["operator_action"]
    assert product_step["items"][0] == "сертификаты и декларации · подтверждено"
    assert certificate["id"] in product_step["condition_fact_ids"]
    assert product_step["source"] == "condition_groups"


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
    items = [item for item in sections["acceptance_payment"]["items"] if item.get("conflict_flags")]

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


def test_build_analysis_operator_view_adds_full_expected_missing_matrix_without_hiding_present_families():
    view = build_analysis_operator_view(
        {
            "summary": "Поставка бумаги",
            "analysis_facts": {
                "version": 1,
                "items": [
                    {
                        "kind": "execution_term",
                        "label": "Оплата",
                        "value": "Оплата производится в течение 7 рабочих дней.",
                        "category": "payment",
                        "severity": "medium",
                        "document_name": "Контракт.docx",
                        "fragment": "Оплата производится в течение 7 рабочих дней.",
                    }
                ],
            },
        },
        [{"name": "Контракт.docx", "local_path": "contract.docx", "text_status": "ok"}],
    )

    sections = {section["id"]: section for section in view["sections"]}
    labels_by_section = {
        section_id: [item["label"] for item in section["items"] if item.get("expected_missing")]
        for section_id, section in sections.items()
    }

    assert "условия оплаты" not in labels_by_section["acceptance_payment"]
    assert "приемка и закрывающие документы" in labels_by_section["acceptance_payment"]
    assert "аванс" in labels_by_section["acceptance_payment"]
    assert "срок поставки" in labels_by_section["fulfillment_terms"]
    assert "место поставки" in labels_by_section["fulfillment_terms"]
    assert "обеспечение заявки" in labels_by_section["decision_risks"]
    assert "обеспечение исполнения контракта" in labels_by_section["decision_risks"]
    assert "гарантия" in labels_by_section["fulfillment_terms"]
    assert "штрафы и пени" in labels_by_section["decision_risks"]
    assert "национальный режим/страна происхождения" in labels_by_section["decision_risks"]
    assert "сертификаты и декларации" in labels_by_section["product_compliance"]
    assert "лицензии или СРО" in labels_by_section["product_compliance"]
    assert "упаковка и маркировка" in labels_by_section["product_compliance"]
    assert view["metrics"]["expected_missing"] >= 12


def test_build_analysis_operator_view_marks_numeric_term_conflicts_for_manual_review():
    view = build_analysis_operator_view(
        {
            "summary": "Поставка бумаги",
            "analysis_facts": {
                "version": 1,
                "items": [
                    {
                        "kind": "execution_term",
                        "label": "Срок поставки",
                        "value": "Поставка товара в течение 5 рабочих дней.",
                        "category": "delivery",
                        "severity": "medium",
                        "document_name": "ТЗ.docx",
                        "fragment": "Поставка товара в течение 5 рабочих дней.",
                    },
                    {
                        "kind": "execution_term",
                        "label": "Срок поставки",
                        "value": "Поставка товара в течение 20 рабочих дней.",
                        "category": "delivery",
                        "severity": "medium",
                        "document_name": "Контракт.docx",
                        "fragment": "Поставка товара в течение 20 рабочих дней.",
                    },
                    {
                        "kind": "execution_term",
                        "label": "Обеспечение контракта",
                        "value": "Обеспечение исполнения контракта 5%.",
                        "category": "contract",
                        "severity": "medium",
                        "document_name": "Извещение.docx",
                        "fragment": "Обеспечение исполнения контракта 5%.",
                    },
                    {
                        "kind": "execution_term",
                        "label": "Обеспечение контракта",
                        "value": "Обеспечение исполнения контракта составляет 30%.",
                        "category": "contract",
                        "severity": "medium",
                        "document_name": "Контракт.docx",
                        "fragment": "Обеспечение исполнения контракта составляет 30%.",
                    },
                ],
            },
        },
        [{"name": "ТЗ.docx", "local_path": "tz.docx", "text_status": "ok"}],
    )

    sections = {section["id"]: section for section in view["sections"]}
    conflicted = [
        item
        for section in sections.values()
        for item in section["items"]
        if item.get("conflict_flags")
    ]

    assert {item["label"] for item in conflicted} == {"Срок поставки", "обеспечение исполнения контракта"}
    assert all(item["evidence_quality"]["level"] == "conflict" for item in conflicted)
    assert view["metrics"]["conflicts"] == 4


def test_build_analysis_operator_view_exposes_evidence_quality_for_exact_missing_and_inferred_facts():
    view = build_analysis_operator_view(
        {
            "summary": "Поставка бумаги",
            "analysis_facts": {
                "version": 1,
                "items": [
                    {
                        "kind": "requirement",
                        "label": "сертификат/декларация",
                        "value": "Поставщик предоставляет декларацию соответствия.",
                        "category": "documents",
                        "severity": "medium",
                        "document_name": "ТЗ.docx",
                        "fragment": "Поставщик предоставляет декларацию соответствия.",
                        "source_context": "Поставщик предоставляет декларацию соответствия на товар.",
                    },
                        {
                            "kind": "risk",
                            "label": "неясная приемка",
                            "value": "Неясная приемка требует уточнения.",
                            "category": "acceptance",
                            "severity": "medium",
                        },
                ],
            },
        },
        [{"name": "ТЗ.docx", "local_path": "tz.docx", "text_status": "ok"}],
    )

    items = [
        item
        for section in view["sections"]
        for item in section["items"]
        if item.get("label") in {"сертификат/декларация", "неясная приемка", "условия оплаты"}
    ]
    by_label = {item["label"]: item for item in items}

    assert by_label["сертификат/декларация"]["evidence_quality"] == {
        "level": "exact",
        "label": "точное доказательство",
        "detail": "Есть документ, фрагмент и контекст источника.",
    }
    assert by_label["неясная приемка"]["evidence_quality"]["level"] == "inferred"
    assert by_label["условия оплаты"]["evidence_quality"]["level"] == "missing"
