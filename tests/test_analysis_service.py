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

    detail = get_tender_payload(store.database_path, "mosreg_market", "3668200")
    assert detail["analysis"]["summary"] == payload["analysis"]["summary"]
    assert detail["analysis"]["checklist"] == payload["analysis"]["checklist"]
