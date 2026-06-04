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
