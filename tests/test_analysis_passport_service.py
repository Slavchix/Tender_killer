from __future__ import annotations

from tender_killer.analysis_passport_service import build_analysis_tz_passport


def test_build_analysis_tz_passport_groups_operator_ready_sections():
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
                "type": "contract_security",
                "label": "Обеспечение исполнения",
                "value": "5 процентов от цены контракта",
                "category": "financial",
                "severity": "high",
                "document_name": "contract.docx",
            },
        ],
    }

    passport = build_analysis_tz_passport(analysis, [])

    assert passport["version"] == 1
    assert passport["title"] == "Поставка снаряжения альпинистского"
    assert [section["id"] for section in passport["sections"]] == [
        "subject",
        "execution",
        "supplier_documents",
        "blockers",
        "price_factors",
    ]

    sections = {section["id"]: section for section in passport["sections"]}
    assert sections["subject"]["items"][0]["value"] == "Поставка снаряжения альпинистского"
    assert [item["label"] for item in sections["execution"]["items"]] == [
        "Срок поставки",
        "Обеспечение исполнения",
    ]
    assert sections["execution"]["items"][0]["source"] == "contract.docx"
    assert [item["label"] for item in sections["supplier_documents"]["items"]] == [
        "сертификат/декларация"
    ]
    assert [item["label"] for item in sections["blockers"]["items"]] == [
        "национальный режим/страна происхождения",
        "Обеспечение исполнения",
    ]
    assert sections["price_factors"]["items"][0]["label"] == "Срок поставки"


def test_build_analysis_tz_passport_returns_pending_contract_without_analysis():
    passport = build_analysis_tz_passport(None, [{"name": "tz.docx", "text_status": "pending"}])

    assert passport["version"] == 1
    assert passport["status"] == "pending"
    assert passport["sections"][0]["id"] == "subject"
    assert passport["sections"][0]["items"] == []
