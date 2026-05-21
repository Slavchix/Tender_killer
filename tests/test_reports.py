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
            "status": "needs_review",
            "confidence": 0.84,
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
    assert "короткий срок поставки" in document_xml
    assert "Будущий расчет экономики" in document_xml
    assert "<w:tbl>" in document_xml
    assert "Краткое решение" in document_xml
    assert "Документы и ТЗ" in document_xml
    assert "Подтверждения из ТЗ" in document_xml
    assert "Поставщик предоставляет сертификат соответствия." in document_xml


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
