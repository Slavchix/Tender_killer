from __future__ import annotations

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

    detail = get_tender_payload(store.database_path, "mosreg_market", "3668200")
    assert detail["analysis"]["summary"] == payload["analysis"]["summary"]
    assert detail["analysis"]["checklist"] == payload["analysis"]["checklist"]
    assert detail["analysis"]["evidence_items"] == payload["analysis"]["evidence_items"]


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
