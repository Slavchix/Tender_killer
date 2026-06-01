from __future__ import annotations

import json
import sqlite3

from tender_killer.analysis_service import analyze_tender_payload
from tender_killer.models import Tender
from tender_killer.models import TenderDocument
from tender_killer.storage import TenderStore
from tender_killer.tender_detail_service import get_tender_payload


def test_analyze_tender_payload_saves_structured_summary_from_extracted_text(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="3668200",
            url="https://market.mosreg.ru/Trade/ViewTrade/3668200",
            title="Fire extinguisher tender",
            document_records=[
                TenderDocument(
                    url="https://example.test/tz.docx",
                    name="tz.docx",
                    document_type="technical specification",
                )
            ],
        )
    )
    with sqlite3.connect(store.database_path) as connection:
        connection.execute(
            """
            UPDATE tender_documents
            SET text_status = ?, text_content = ?, text_extracted_at = ?
            WHERE source = ? AND external_id = ? AND url = ?
            """,
            (
                "ok",
                "Техническое задание: поставка огнетушителей. "
                "Поставщик обязан предоставить сертификат соответствия. "
                "Обеспечение исполнения контракта 5 процентов. "
                "Применяется постановление 1875 и страна происхождения товара.",
                "2026-05-20T10:30:00",
                "mosreg_market",
                "3668200",
                "https://example.test/tz.docx",
            ),
        )

    payload = analyze_tender_payload(store.database_path, "mosreg_market", "3668200")

    assert payload["ok"] is True
    assert payload["analysis"]["status"] == "needs_review"
    assert "поставка огнетушителей" in payload["analysis"]["summary"]
    assert "сертификат/декларация" in payload["analysis"]["requirements"]
    assert "обеспечение исполнения контракта" in payload["analysis"]["risks"]
    assert "национальный режим/страна происхождения" in payload["analysis"]["red_flags"]
    assert payload["analysis"]["checklist"][0]["label"] == "сертификат/декларация"
    assert payload["analysis"]["checklist"][0]["category"] == "documents"
    assert "Поставщик обязан предоставить сертификат" in payload["analysis"]["checklist"][0]["evidence"]
    assert payload["analysis"]["evidence_items"][0]["label"] == "сертификат/декларация"
    assert payload["analysis"]["evidence_items"][0]["type_label"] == "Документы"
    assert payload["analysis"]["evidence_items"][0]["document_name"] == "tz.docx"
    assert "Поставщик обязан предоставить сертификат" in payload["analysis"]["evidence_items"][0]["fragment"]
    assert payload["analysis"]["analysis_facts"]["version"] == 1
    assert payload["analysis"]["analysis_facts"]["metrics"]["blockers"] == 2
    certificate_fact = next(
        fact for fact in payload["analysis"]["analysis_facts"]["items"] if fact["label"] == "сертификат/декларация"
    )
    national_regime_fact = next(
        fact for fact in payload["analysis"]["analysis_facts"]["items"] if fact["label"] == "национальный режим/страна происхождения"
    )
    assert certificate_fact["document_name"] == "tz.docx"
    assert "Поставщик обязан предоставить сертификат" in certificate_fact["fragment"]
    assert national_regime_fact["kind"] == "blocker"
    assert national_regime_fact["is_blocker"] is True

    detail = get_tender_payload(store.database_path, "mosreg_market", "3668200")
    assert detail["analysis"]["summary"] == payload["analysis"]["summary"]
    assert detail["analysis"]["checklist"] == payload["analysis"]["checklist"]
    assert detail["analysis"]["evidence_items"] == payload["analysis"]["evidence_items"]
    assert detail["analysis"]["analysis_facts"] == payload["analysis"]["analysis_facts"]


def test_analyze_tender_payload_binds_execution_terms_to_source_documents(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="moscow_supplier_portal",
            external_id="Auction10212588",
            url="https://zakupki.mos.ru/auction/10212588",
            title="Mountaineering equipment tender",
            document_records=[
                TenderDocument(url="https://example.test/spec.docx", name="spec.docx"),
                TenderDocument(url="https://example.test/contract.docx", name="contract.docx"),
            ],
        )
    )
    with sqlite3.connect(store.database_path) as connection:
        connection.execute(
            """
            UPDATE tender_documents
            SET text_status = ?, text_content = ?, text_extracted_at = ?
            WHERE source = ? AND external_id = ? AND url = ?
            """,
            (
                "ok",
                "Техническое задание: поставка снаряжения альпинистского. "
                "Поставщик обязан предоставить сертификат соответствия.",
                "2026-06-01T10:30:00",
                "moscow_supplier_portal",
                "Auction10212588",
                "https://example.test/spec.docx",
            ),
        )
        connection.execute(
            """
            UPDATE tender_documents
            SET text_status = ?, text_content = ?, text_extracted_at = ?
            WHERE source = ? AND external_id = ? AND url = ?
            """,
            (
                "ok",
                "Срок поставки товара: в течение 5 рабочих дней с даты заключения контракта. "
                "Оплата производится в течение 7 рабочих дней после подписания документа о приемке. "
                "Обеспечение исполнения контракта составляет 5 процентов от цены контракта.",
                "2026-06-01T10:31:00",
                "moscow_supplier_portal",
                "Auction10212588",
                "https://example.test/contract.docx",
            ),
        )

    payload = analyze_tender_payload(store.database_path, "moscow_supplier_portal", "Auction10212588")

    delivery_term = next(
        term for term in payload["analysis"]["execution_terms"] if term["type"] == "delivery_deadline"
    )
    security_term = next(
        term for term in payload["analysis"]["execution_terms"] if term["type"] == "contract_security"
    )
    certificate_evidence = next(
        item for item in payload["analysis"]["evidence_items"] if item["label"] == "сертификат/декларация"
    )
    execution_section = next(
        section for section in payload["analysis"]["operator_view"]["sections"] if section["id"] == "execution_terms"
    )
    passport_sections = {
        section["id"]: section for section in payload["analysis"]["tz_passport"]["sections"]
    }

    assert delivery_term["document_name"] == "contract.docx"
    assert security_term["document_name"] == "contract.docx"
    assert certificate_evidence["document_name"] == "spec.docx"
    assert execution_section["items"][0]["source"] == "contract.docx"
    assert passport_sections["execution"]["items"][0]["source"] == "contract.docx"
    assert passport_sections["supplier_documents"]["items"][0]["source"] == "spec.docx"
    delivery_fact = next(
        fact for fact in payload["analysis"]["analysis_facts"]["items"] if fact["label"] == "Срок поставки"
    )
    security_fact = next(
        fact for fact in payload["analysis"]["analysis_facts"]["items"] if fact["label"] == "Обеспечение исполнения"
    )
    assert delivery_fact["document_name"] == "contract.docx"
    assert delivery_fact["is_price_factor"] is True
    assert security_fact["document_name"] == "contract.docx"
    assert security_fact["is_blocker"] is True


def test_analyze_tender_payload_attaches_source_page_and_context(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="3675299",
            url="https://market.mosreg.ru/Trade/ViewTrade/3675299",
            title="Service materials tender",
            document_records=[
                TenderDocument(url="https://example.test/spec.docx", name="Техническое задание.docx"),
            ],
        )
    )
    with sqlite3.connect(store.database_path) as connection:
        connection.execute(
            """
            UPDATE tender_documents
            SET text_status = ?, text_content = ?, text_extracted_at = ?
            WHERE source = ? AND external_id = ? AND url = ?
            """,
            (
                "ok",
                "Раздел 1. Общие сведения о закупке без требований к подтверждающим документам.\f"
                "Раздел 2. Требования к соответствию товара. "
                "Поставщик обязан предоставить сертификат соответствия на расходные материалы до приемки товара. "
                "Проверка сертификата проводится заказчиком при поставке и влияет на приемку.",
                "2026-06-01T10:30:00",
                "mosreg_market",
                "3675299",
                "https://example.test/spec.docx",
            ),
        )

    payload = analyze_tender_payload(store.database_path, "mosreg_market", "3675299")
    certificate = next(
        item for item in payload["analysis"]["checklist"] if item["label"] == "сертификат/декларация"
    )
    certificate_fact = next(
        fact for fact in payload["analysis"]["analysis_facts"]["items"] if fact["label"] == "сертификат/декларация"
    )
    requirements_section = next(
        section for section in payload["analysis"]["operator_view"]["sections"] if section["id"] == "requirements"
    )
    operator_item = next(item for item in requirements_section["items"] if item["label"] == "сертификат/декларация")

    assert certificate["document_name"] == "Техническое задание.docx"
    assert certificate["source_page"] == 2
    assert certificate["source_label"] == "Техническое задание.docx · стр. 2"
    assert "Раздел 2. Требования к соответствию товара" in certificate["source_context"]
    assert "Проверка сертификата проводится заказчиком" in certificate["source_context"]
    assert certificate_fact["source_page"] == 2
    assert certificate_fact["source_label"] == "Техническое задание.docx · стр. 2"
    assert "Раздел 2. Требования к соответствию товара" in certificate_fact["source_context"]
    assert operator_item["source_page"] == 2
    assert operator_item["source_label"] == "Техническое задание.docx · стр. 2"
    assert "Проверка сертификата проводится заказчиком" in operator_item["source_context"]


def test_get_tender_payload_rebuilds_stale_analysis_source_context(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="3675300",
            url="https://market.mosreg.ru/Trade/ViewTrade/3675300",
            title="Existing analysis tender",
            document_records=[
                TenderDocument(url="https://example.test/spec.docx", name="ТЗ расходные материалы.docx"),
            ],
        )
    )
    raw_payload = {
        "summary": "Поставка расходных материалов",
        "checklist": [
            {
                "label": "сертификат/декларация",
                "category": "documents",
                "severity": "medium",
                "evidence": "Поставщик обязан предоставить сертификат соответствия на расходные материалы до приемки товара.",
            }
        ],
        "analysis_facts": {
            "version": 1,
            "items": [
                {
                    "id": "supplier_document:сертификат-декларация",
                    "kind": "supplier_document",
                    "label": "сертификат/декларация",
                    "value": "Поставщик обязан предоставить сертификат соответствия на расходные материалы до приемки товара.",
                    "category": "documents",
                    "severity": "medium",
                    "document_name": "ТЗ расходные материалы.docx",
                    "source": "ТЗ расходные материалы.docx",
                    "fragment": "Поставщик обязан предоставить сертификат соответствия на расходные материалы до приемки товара.",
                }
            ],
            "metrics": {"total": 1, "blockers": 0, "price_factors": 0, "unbound": 0},
        },
        "operator_view": {
            "version": 2,
            "sections": [
                {
                    "id": "requirements",
                    "title": "Что подготовить",
                    "count": 1,
                    "items": [
                        {
                            "id": "supplier_document:сертификат-декларация",
                            "label": "сертификат/декларация",
                            "description": "Поставщик обязан предоставить сертификат соответствия на расходные материалы до приемки товара.",
                            "source": "ТЗ расходные материалы.docx",
                        }
                    ],
                }
            ],
        },
    }
    with sqlite3.connect(store.database_path) as connection:
        connection.execute(
            """
            UPDATE tender_documents
            SET text_status = ?, text_content = ?, text_extracted_at = ?
            WHERE source = ? AND external_id = ? AND url = ?
            """,
            (
                "ok",
                "Страница 1. Общие сведения.\f"
                "Страница 2. Подтверждающие документы. "
                "Поставщик обязан предоставить сертификат соответствия на расходные материалы до приемки товара. "
                "Этот пункт нужно проверить у поставщика до участия.",
                "2026-06-01T10:30:00",
                "mosreg_market",
                "3675300",
                "https://example.test/spec.docx",
            ),
        )
        connection.execute(
            """
            INSERT INTO tender_analysis (
                source, external_id, summary, requirements_json, risks_json, red_flags_json,
                recommended_status, confidence, raw_payload_json, analyzed_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "mosreg_market",
                "3675300",
                "Поставка расходных материалов",
                json.dumps(["сертификат/декларация"], ensure_ascii=False),
                "[]",
                "[]",
                "needs_review",
                0.42,
                json.dumps(raw_payload, ensure_ascii=False),
                "2026-06-01T11:00:00",
            ),
        )

    detail = get_tender_payload(store.database_path, "mosreg_market", "3675300")
    requirements_section = next(
        section for section in detail["analysis"]["operator_view"]["sections"] if section["id"] == "requirements"
    )
    operator_item = requirements_section["items"][0]
    certificate_fact = next(
        fact for fact in detail["analysis"]["analysis_facts"]["items"] if fact["label"] == "сертификат/декларация"
    )

    assert detail["analysis"]["checklist"][0]["source_page"] == 2
    assert certificate_fact["source_page"] == 2
    assert operator_item["source_label"] == "ТЗ расходные материалы.docx · стр. 2"
    assert "Страница 2. Подтверждающие документы" in operator_item["source_context"]
