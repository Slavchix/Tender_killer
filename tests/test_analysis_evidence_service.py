from __future__ import annotations

from tender_killer.analysis_evidence_service import build_analysis_evidence_items


def test_build_analysis_evidence_items_labels_document_and_impact():
    analysis = {
        "checklist": [
            {
                "label": "сертификат/декларация",
                "category": "documents",
                "severity": "medium",
                "evidence": "Поставщик обязан предоставить сертификат соответствия.",
            },
            {
                "label": "короткий срок поставки",
                "category": "delivery",
                "severity": "high",
                "evidence": "Срок поставки 3 дня.",
            },
        ],
    }
    documents = [{"name": "ТЗ.docx", "text_status": "ok"}]

    items = build_analysis_evidence_items(analysis, documents)

    assert items[0] == {
        "id": "сертификат/декларация-0",
        "label": "сертификат/декларация",
        "category": "documents",
        "severity": "medium",
        "type_label": "Документы",
        "importance_label": "проверить",
        "document_name": "ТЗ.docx",
        "fragment": "Поставщик обязан предоставить сертификат соответствия.",
        "impact": "Проверьте, какие документы нужно приложить или получить у поставщика.",
    }
    assert items[1]["type_label"] == "Сроки и поставка"
    assert items[1]["importance_label"] == "важно"
    assert items[1]["impact"] == "Может повлиять на решение, цену или возможность участия."
