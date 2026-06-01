from __future__ import annotations

from tender_killer.analysis_facts_service import build_analysis_facts


def test_build_analysis_facts_binds_each_fact_to_document_evidence():
    documents = [
        {
            "name": "spec.docx",
            "text_status": "ok",
            "text_content": "Техническое задание: поставка мебели. Поставщик обязан предоставить сертификат соответствия.",
        },
        {
            "name": "contract.docx",
            "text_status": "ok",
            "text_content": "Срок поставки товара: в течение 5 рабочих дней. Указывается страна происхождения товара.",
        },
    ]
    analysis = {
        "summary": "поставка мебели",
        "confidence": 0.82,
        "checklist": [
            {
                "label": "сертификат/декларация",
                "category": "documents",
                "severity": "medium",
                "evidence": "Поставщик обязан предоставить сертификат соответствия.",
            },
            {
                "label": "национальный режим/страна происхождения",
                "category": "national_regime",
                "severity": "high",
                "evidence": "Указывается страна происхождения товара.",
            },
        ],
        "execution_terms": [
            {
                "type": "delivery_deadline",
                "label": "Срок поставки",
                "category": "delivery",
                "severity": "medium",
                "value": "Срок поставки товара: в течение 5 рабочих дней.",
                "evidence": "Срок поставки товара: в течение 5 рабочих дней.",
            }
        ],
    }

    facts = build_analysis_facts(analysis, documents)
    items = facts["items"]
    by_label = {item["label"]: item for item in items}

    assert facts["version"] == 1
    assert facts["metrics"] == {"total": 4, "blockers": 1, "price_factors": 1, "unbound": 0}
    assert by_label["Предмет"]["kind"] == "subject"
    assert by_label["Предмет"]["value"] == "поставка мебели"
    assert by_label["сертификат/декларация"]["kind"] == "supplier_document"
    assert by_label["сертификат/декларация"]["document_name"] == "spec.docx"
    assert by_label["сертификат/декларация"]["fragment"] == "Поставщик обязан предоставить сертификат соответствия."
    assert by_label["сертификат/декларация"]["rule_id"] == "checklist:сертификат/декларация"
    assert by_label["Срок поставки"]["kind"] == "execution_term"
    assert by_label["Срок поставки"]["document_name"] == "contract.docx"
    assert by_label["Срок поставки"]["is_price_factor"] is True
    assert by_label["национальный режим/страна происхождения"]["kind"] == "blocker"
    assert by_label["национальный режим/страна происхождения"]["document_name"] == "contract.docx"
    assert by_label["национальный режим/страна происхождения"]["is_blocker"] is True
    assert all(item["document_name"] != "Документ не привязан" for item in items if item["kind"] != "subject")


def test_build_analysis_facts_marks_unbound_evidence_for_operator_review():
    facts = build_analysis_facts(
        {
            "summary": "поставка техники",
            "confidence": 0.7,
            "checklist": [
                {
                    "label": "лицензия/СРО",
                    "category": "legal",
                    "severity": "high",
                    "evidence": "Нужна лицензия на выполнение работ.",
                }
            ],
        },
        [{"name": "tz.docx", "text_status": "ok", "text_content": "Документ без такого фрагмента."}],
    )

    license_fact = next(item for item in facts["items"] if item["label"] == "лицензия/СРО")

    assert license_fact["document_name"] == "Документ не привязан"
    assert license_fact["needs_review"] is True
    assert facts["metrics"]["unbound"] == 1
