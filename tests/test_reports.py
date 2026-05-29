from __future__ import annotations

from io import BytesIO
from zipfile import ZipFile

from tender_killer.reports import build_tender_report_docx


def test_build_tender_report_docx_includes_product_profile_summary_for_many_profiles():
    payload = {
        "title": "Тестовая закупка материалов",
        "product_profile_summary": {
            "total": 40,
            "ready": 35,
            "needs_review": 5,
            "matched": 30,
            "priced": 25,
            "rejected": 2,
        },
        "product_profiles": [
            {
                "position_index": index,
                "product_name": f"Материал {index}",
                "profile_status": "ready",
                "category": "Материалы",
                "quantity": index,
                "unit": "шт",
                "search_phrases": [f"Материал {index}"],
            }
            for index in range(1, 41)
        ],
    }

    content = build_tender_report_docx(payload)
    document_xml = _document_xml(content)

    assert "Сводка товарных профилей" in document_xml
    assert "Товарные профили: 40" in document_xml
    assert "Готовы к поиску: 35" in document_xml
    assert "Требуют проверки: 5" in document_xml
    assert "Материал 40" in document_xml


def test_build_tender_report_docx_contains_key_sections():
    payload = {
        "source": "mosreg_market",
        "external_id": "3668200",
        "url": "https://market.mosreg.ru/Trade/ViewTrade/3668200",
        "title": "Поставка огнетушителей",
        "customer": "Школа",
        "region": "Московская область",
        "price": 38064.0,
        "status": "Прием предложений",
        "deadline_at": "2026-05-29T11:50:00",
        "items": [
            {
                "position_index": 1,
                "name": "Огнетушитель порошковый",
                "quantity": 5,
                "unit": "шт",
                "unit_price": 7612.8,
                "total_price": 38064.0,
                "okpd2": "28.29.22.110",
                "classifier_code": "28.29.22.110",
                "classifier_type": "КОЗ-2",
            }
        ],
        "document_records": [
            {
                "name": "Техническое задание.docx",
                "document_type": "Описание объекта закупки",
                "text_status": "ok",
                "text_content": "Поставщик предоставляет сертификат соответствия. Срок поставки 3 дня.",
            }
        ],
        "analysis": {
            "summary": "поставка огнетушителей",
            "requirements": ["сертификат/декларация", "срок поставки"],
            "risks": ["короткий срок поставки"],
            "red_flags": ["национальный режим/страна происхождения"],
            "checklist": [
                {
                    "label": "сертификат/декларация",
                    "category": "documents",
                    "severity": "medium",
                    "evidence": "Поставщик предоставляет сертификат соответствия.",
                },
                {
                    "label": "короткий срок поставки",
                    "category": "delivery",
                    "severity": "high",
                    "evidence": "Срок поставки 3 дня.",
                },
            ],
            "status": "needs_review",
            "confidence": 0.84,
        },
        "economics": {
            "status": "interesting",
            "recommendation": "Маржа выглядит интересной, но требует проверки поставщика и условий исполнения.",
            "revenue": 38064.0,
            "supplier_cost": 25000.0,
            "risk_reserve_rate_percent": 3.5,
            "risk_reserve": 1332.24,
            "estimated_total_cost": 26332.24,
            "gross_margin": 11731.76,
            "margin_percent": 30.82,
            "missing_cost_inputs": [],
            "risk_types": ["delivery", "warranty", "acceptance"],
            "items": [
                {
                    "product_name": "Огнетушитель порошковый",
                    "quantity": 5,
                    "unit": "шт",
                    "unit_cost": 5000.0,
                    "total_cost": 25000.0,
                    "extra_costs": 0.0,
                }
            ],
        },
        "product_profiles": [
            {
                "position_index": 1,
                "product_name": "Огнетушитель порошковый",
                "category": "Противопожарные товары",
                "okpd2": "28.29.22.110",
                "classifier_code": "28.29.22.110",
                "classifier_type": "КОЗ-2",
                "quantity": 5,
                "unit": "шт",
                "required_characteristics": ["сертификат соответствия"],
                "evidence": [
                    {
                        "field": "document_requirement",
                        "source": "Техническое задание.docx",
                        "value": "Поставщик предоставляет сертификат соответствия.",
                    }
                ],
                "search_phrases": ["Огнетушитель порошковый", "Огнетушитель порошковый 28.29.22.110"],
                "stop_words": ["б/у"],
                "source": "item",
            }
        ],
    }

    content = build_tender_report_docx(payload)
    document_xml = _document_xml(content)

    assert "Паспорт закупки" in document_xml
    assert "Поставка огнетушителей" in document_xml
    assert "28.29.22.110" in document_xml
    assert "Товарный профиль для поиска" in document_xml
    assert "КОЗ-2" in document_xml
    assert "Огнетушитель порошковый 28.29.22.110" in document_xml
    assert "сертификат/декларация" in document_xml
    assert "Проверочный список" in document_xml
    assert "documents" in document_xml
    assert "medium" in document_xml
    assert "Поставщик предоставляет сертификат соответствия." in document_xml
    assert "короткий срок поставки" in document_xml
    assert "Черновик экономики" in document_xml
    assert "Маржа" in document_xml
    assert "30.82%" in document_xml
    assert "Маржа выглядит интересной" in document_xml
    assert "<w:tbl>" in document_xml
    assert "Краткое решение" in document_xml
    assert "Документы и ТЗ" in document_xml
    assert "Подтверждения из ТЗ" in document_xml
    assert "Поставщик предоставляет сертификат соответствия." in document_xml


def test_build_tender_report_docx_renders_analysis_decision_and_evidence():
    payload = {
        "source": "mosreg_market",
        "external_id": "3668200",
        "title": "Поставка огнетушителей",
        "document_records": [
            {
                "name": "ТЗ.docx",
                "text_status": "ok",
                "text_content": "Поставщик предоставляет сертификат. Срок поставки 3 дня.",
            }
        ],
        "analysis": {
            "summary": "поставка огнетушителей",
            "requirements": ["сертификат/декларация"],
            "risks": ["короткий срок поставки"],
            "red_flags": [],
            "status": "needs_review",
            "confidence": 0.78,
            "checklist": [
                {
                    "label": "сертификат/декларация",
                    "category": "documents",
                    "severity": "medium",
                    "evidence": "Поставщик предоставляет сертификат.",
                    "source": "ТЗ.docx",
                },
                {
                    "label": "короткий срок поставки",
                    "category": "delivery",
                    "severity": "high",
                    "evidence": "Срок поставки 3 дня.",
                    "source": "ТЗ.docx",
                },
            ],
        },
    }

    content = build_tender_report_docx(payload)
    document_xml = _document_xml(content)

    assert "Решение по анализу ТЗ" in document_xml
    assert "Нужна ручная проверка" in document_xml
    assert "Ключевые причины" in document_xml
    assert "Риск: короткий срок поставки" in document_xml
    assert "Требование: сертификат/декларация" in document_xml
    assert "Доказательства из документов" in document_xml
    assert "Тип условия" in document_xml
    assert "Важность" in document_xml
    assert "Документ" in document_xml
    assert "Фрагмент" in document_xml
    assert "Влияние" in document_xml
    assert "Документы" in document_xml
    assert "Сроки и поставка" in document_xml
    assert "важно" in document_xml
    assert "ТЗ.docx" in document_xml
    assert "Может повлиять на решение, цену или возможность участия." in document_xml


def test_build_tender_report_docx_falls_back_to_card_subject_when_items_missing():
    payload = {
        "source": "mosreg_market",
        "external_id": "3670000",
        "url": "https://market.mosreg.ru/Trade/ViewTrade/3670000",
        "title": "Поставка садовых инструментов",
        "category": "Хозяйственные товары",
        "okpd2": "25.73.10",
        "price": 191156.0,
        "items": [],
        "document_records": [],
        "analysis": None,
    }

    content = build_tender_report_docx(payload)
    document_xml = _document_xml(content)

    assert "Поставка садовых инструментов" in document_xml
    assert "Хозяйственные товары" in document_xml
    assert "25.73.10" in document_xml
    assert "Позиции пока не найдены" not in document_xml


def _document_xml(content: bytes) -> str:
    with ZipFile(BytesIO(content)) as archive:
        return archive.read("word/document.xml").decode("utf-8")
