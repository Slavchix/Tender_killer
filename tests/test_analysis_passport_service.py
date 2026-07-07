from __future__ import annotations

from tender_killer.analysis_passport_service import build_analysis_tz_passport


def test_build_analysis_tz_passport_uses_four_block_operator_contract():
    analysis = {
        "summary": "Поставка снаряжения альпинистского",
        "status": "needs_review",
        "confidence": 0.82,
        "checklist": [
            {
                "label": "сертификат/декларация",
                "category": "documents",
                "severity": "medium",
                "evidence": "Поставщик обязан предоставить сертификат соответствия.",
                "document_name": "spec.docx",
            },
            {
                "label": "национальный режим/страна происхождения",
                "category": "national_regime",
                "severity": "high",
                "evidence": "Страна происхождения товара подтверждается документами.",
                "document_name": "spec.docx",
            },
        ],
        "execution_terms": [
            {
                "type": "delivery_deadline",
                "label": "Срок поставки",
                "value": "в течение 5 рабочих дней",
                "category": "delivery",
                "severity": "medium",
                "document_name": "contract.docx",
            },
            {
                "type": "payment_terms",
                "label": "Оплата",
                "value": "в течение 7 рабочих дней",
                "category": "payment",
                "severity": "medium",
                "document_name": "contract.docx",
            },
        ],
    }

    passport = build_analysis_tz_passport(analysis, [])

    assert passport["version"] == 2
    assert passport["status"] == "manual_review"
    assert passport["confidence"] == 0.82
    assert [section["id"] for section in passport["sections"]] == [
        "decision_risks",
        "product_compliance",
        "fulfillment_terms",
        "acceptance_payment",
    ]
    sections = {section["id"]: section for section in passport["sections"]}
    assert [item["label"] for item in sections["decision_risks"]["items"]] == [
        "национальный режим/страна происхождения"
    ]
    assert {item["label"] for item in sections["product_compliance"]["items"]} == {
        "Кратко",
        "сертификат/декларация",
    }
    assert [item["label"] for item in sections["fulfillment_terms"]["items"]] == ["Срок поставки"]
    assert [item["label"] for item in sections["acceptance_payment"]["items"]] == ["Оплата"]


def test_build_analysis_tz_passport_returns_pending_four_block_contract_without_analysis():
    passport = build_analysis_tz_passport(None, [{"name": "tz.docx", "text_status": "pending"}])

    assert passport["version"] == 2
    assert passport["status"] == "pending"
    assert [section["id"] for section in passport["sections"]] == [
        "decision_risks",
        "product_compliance",
        "fulfillment_terms",
        "acceptance_payment",
    ]
    assert passport["sections"][1]["items"][0]["label"] == "Документы для анализа"


def test_build_analysis_tz_passport_exposes_compact_management_block():
    analysis = {
        "summary": "Поставка офисной бумаги",
        "status": "needs_review",
        "confidence": 0.81,
        "analysis_facts": {
            "version": 1,
            "items": [
                {
                    "id": "subject:paper",
                    "kind": "subject",
                    "label": "Предмет",
                    "value": "Поставка офисной бумаги",
                    "category": "subject",
                    "document_name": "ТЗ.docx",
                    "fragment": "Поставка офисной бумаги",
                },
                {
                    "id": "advance:no",
                    "kind": "execution_term",
                    "label": "Аванс",
                    "value": "Аванс не предусмотрен.",
                    "category": "financial",
                    "document_name": "ТЗ.docx",
                    "fragment": "Аванс не предусмотрен.",
                },
                {
                    "id": "advance:yes",
                    "kind": "execution_term",
                    "label": "Аванс",
                    "value": "Предусмотрен аванс 30 процентов.",
                    "category": "financial",
                    "document_name": "Проект контракта.docx",
                    "fragment": "Предусмотрен аванс 30 процентов.",
                },
                {
                    "id": "national-regime",
                    "kind": "red_flag",
                    "label": "Национальный режим",
                    "value": "Применяется национальный режим.",
                    "category": "national_regime",
                    "severity": "high",
                    "document_name": "ТЗ.docx",
                    "fragment": "Применяется национальный режим.",
                    "is_blocker": True,
                },
            ],
        },
    }
    documents = [
        {"name": "ТЗ.docx", "local_path": "tz.docx", "text_status": "ok"},
        {"name": "Проект контракта.docx", "local_path": "contract.docx", "text_status": "ok"},
    ]

    passport = build_analysis_tz_passport(analysis, documents)

    assert passport["version"] == 2
    assert passport["subject"] == "Поставка офисной бумаги"
    assert passport["documents"]["status"] == "ready"
    assert passport["documents"]["label"] == "документы готовы"
    assert passport["verdict"] == {
        "code": "high_risk",
        "label": "высокий риск",
    }
    assert any("национальный режим" in item for item in passport["red_flags"])
    assert "Аванс" in passport["conflicts"]
    assert "приемка и закрывающие документы" in passport["expected_missing"]
    assert passport["summary_block"] == {
        "subject": "Поставка офисной бумаги",
        "documents": "документы готовы",
        "key_conditions": passport["key_conditions"],
        "red_flags": passport["red_flags"],
        "conflicts": passport["conflicts"],
        "expected_missing": passport["expected_missing"],
        "condition_groups": passport["summary_block"]["condition_groups"],
        "verdict": "высокий риск",
    }


def test_build_analysis_tz_passport_exposes_condition_groups():
    analysis = {
        "summary": "Поставка офисной бумаги",
        "status": "needs_review",
        "analysis_facts": {
            "version": 1,
            "items": [
                {
                    "id": "payment",
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
                    "id": "advance:no",
                    "kind": "execution_term",
                    "label": "Аванс",
                    "value": "Аванс не предусмотрен.",
                    "category": "financial",
                    "document_name": "ТЗ.docx",
                    "source_label": "ТЗ.docx · стр. 2",
                    "fragment": "Аванс не предусмотрен.",
                },
                {
                    "id": "advance:yes",
                    "kind": "execution_term",
                    "label": "Аванс",
                    "value": "Предусмотрен аванс 30 процентов.",
                    "category": "financial",
                    "document_name": "Проект контракта.docx",
                    "source_label": "Проект контракта.docx · стр. 4",
                    "fragment": "Предусмотрен аванс 30 процентов.",
                },
            ],
        },
    }

    passport = build_analysis_tz_passport(
        analysis,
        [
            {"name": "ТЗ.docx", "text_status": "ok"},
            {"name": "Проект контракта.docx", "text_status": "ok"},
        ],
    )

    groups = {item["family"]: item for item in passport["condition_groups"]["items"]}

    assert passport["condition_groups"]["metrics"]["conflicts"] == 1
    assert groups["payment"]["status"] == "confirmed"
    assert groups["payment"]["source_status"] == "primary_source"
    assert groups["advance"]["status"] == "conflict"
    assert groups["advance"]["related_fact_ids"] == ["advance:no", "advance:yes"]
    assert "Проект контракта.docx · стр. 4" in groups["advance"]["sources"]
    assert passport["summary_block"]["condition_groups"][:2] == [
        "условия оплаты · подтверждено",
        "аванс · противоречие",
    ]
    assert "приемка и закрывающие документы · не найдено" in passport["summary_block"]["condition_groups"]
