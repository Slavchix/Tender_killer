from __future__ import annotations

import httpx

from tender_killer import document_service
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


def test_document_file_downloader_ignores_system_proxy_environment(monkeypatch, tmp_path):
    captured = {}

    class FakeStream:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def raise_for_status(self):
            return None

        def iter_bytes(self):
            yield b"document"

    def fake_stream(method, url, **kwargs):
        captured["method"] = method
        captured["url"] = url
        captured["kwargs"] = kwargs
        return FakeStream()

    monkeypatch.setattr(document_service.httpx, "stream", fake_stream)

    document_service._download_file("https://easuz.mosreg.ru/file.docx", tmp_path / "file.docx")

    assert captured["method"] == "GET"
    assert captured["url"] == "https://easuz.mosreg.ru/file.docx"
    assert captured["kwargs"]["trust_env"] is False
    assert (tmp_path / "file.docx").read_bytes() == b"document"


def test_document_listing_resolver_ignores_system_proxy_environment(monkeypatch):
    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return [{"Url": "https://example.test/spec.docx"}]

    def fake_get(url, **kwargs):
        captured["url"] = url
        captured["kwargs"] = kwargs
        return FakeResponse()

    monkeypatch.setattr(document_service.httpx, "get", fake_get)

    documents = document_service._resolve_document_listing("https://api.market.mosreg.ru/api/Trade/1/GetTradeDocuments")

    assert documents == [{"Url": "https://example.test/spec.docx"}]
    assert captured["kwargs"]["trust_env"] is False


def test_document_download_timeout_reports_mosreg_storage_outage():
    error = document_service._download_error_message(
        httpx.ReadTimeout("The read operation timed out"),
        "easuz.mosreg.ru",
    )

    assert "Сервер документов МО" in error
    assert "ЕАСУЗ" in error
    assert "не ответил" in error
