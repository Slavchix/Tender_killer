from __future__ import annotations

from tender_killer.models import Tender
from tender_killer.models import TenderDocument
from tender_killer.document_service import download_tender_documents_payload
from tender_killer.storage import TenderStore


def test_document_service_downloads_records_without_web_api_dependency(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="3668200",
            url="https://market.mosreg.ru/Trade/ViewTrade/3668200",
            title="Поставка бумаги",
            document_records=[
                TenderDocument(
                    url="https://example.test/spec.docx",
                    name="Техническое задание.docx",
                    document_type="Описание объекта закупки",
                    source_document_id="doc-1",
                )
            ],
        )
    )

    def fake_downloader(url, target_path):
        target_path.write_bytes(b"document")

    payload = download_tender_documents_payload(
        store.database_path,
        "mosreg_market",
        "3668200",
        tmp_path / "documents",
        downloader=fake_downloader,
    )

    assert payload["downloaded"] == 1
    assert payload["failed"] == []
    assert payload["document_records"][0]["local_path"].endswith("Техническое задание.docx")
