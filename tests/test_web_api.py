from __future__ import annotations

import json
import sqlite3
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import pytest

from tender_killer.analysis_service import analyze_tender_payload
from tender_killer.api_handlers import build_tender_report_response
from tender_killer.api_handlers import rebuild_product_profiles
from tender_killer.api_handlers import update_tender_workflow
from tender_killer.database_view_service import get_database_table_payload
from tender_killer.database_view_service import list_database_tables_payload
from tender_killer.document_service import download_tender_documents_payload
from tender_killer.document_service import extract_tender_document_text_payload
from tender_killer.models import Tender
from tender_killer.models import TenderDocument
from tender_killer.models import TenderItem
from tender_killer.notification_service import send_tender_notification_payload
from tender_killer.pipeline import PipelineStats
from tender_killer.search_service import run_search_payload
from tender_killer.source_run_service import list_source_runs_payload
from tender_killer.storage import TenderStore
from tender_killer.tender_detail_service import get_tender_payload
from tender_killer.tender_detail_service import refresh_tender_detail_payload
from tender_killer.tender_query_service import build_search_collection
from tender_killer.tender_query_service import list_tenders_payload


WEB_API_SOURCE = Path(__file__).resolve().parents[1] / "src" / "tender_killer" / "web_api.py"


def test_web_api_stays_a_thin_http_adapter():
    source = WEB_API_SOURCE.read_text(encoding="utf-8")

    forbidden_imports = (
        "from tender_killer.analysis_service",
        "from tender_killer.database_view_service",
        "from tender_killer.document_service",
        "from tender_killer.notification_service",
        "from tender_killer.search_service",
        "from tender_killer.source_run_service",
        "from tender_killer.tender_detail_service",
        "from tender_killer.tender_query_service",
    )
    for import_line in forbidden_imports:
        assert import_line not in source

    assert "from tender_killer.api_handlers import handle_get_request" in source
    assert "from tender_killer.api_handlers import handle_post_request" in source


def _docx_bytes(text: str) -> bytes:
    buffer = BytesIO()
    with ZipFile(buffer, "w") as archive:
        archive.writestr(
            "word/document.xml",
            (
                '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                f"<w:body><w:p><w:r><w:t>{text}</w:t></w:r></w:p></w:body></w:document>"
            ),
        )
    return buffer.getvalue()


def _store_with_tenders(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="moscow_supplier_portal",
            external_id="10205128",
            url="https://zakupki.mos.ru/auction/10205128",
            title="ДЕКОРАЦИИ",
            customer="Колледж",
            region="г Москва",
            price=50200.0,
            status="Активная",
            documents=["https://example.test/spec.docx"],
            raw_payload={"federalLawName": "44-\u0424\u0417"},
        )
    )
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="3668200",
            url="https://market.mosreg.ru/Trade/ViewTrade/3668200",
            title="Поставка бумаги",
            customer="Школа",
            region="Московская область",
            price=120000.0,
            status="Прием предложений",
            documents=[],
            document_records=[
                TenderDocument(
                    url="https://example.test/tz.docx",
                    name="Техническое задание.docx",
                    document_type="Описание объекта закупки",
                    source_document_id="doc-1",
                )
            ],
            raw_payload={"SourcePlatformName": "ЕАСУЗ 44"},
            items=[
                TenderItem(
                    name="Папка-вкладыш",
                    details='Папка-вкладыш Berlingo "Mirror", A4',
                    quantity=800.0,
                    unit="Штука",
                    unit_price=2.0,
                    total_price=1600.0,
                    okpd2="11.05.01.01.02.01.017",
                    classifier_code="11.05.01.01.02.01.017",
                    classifier_type="КОЗ-2",
                )
            ],
        )
    )
    return store


def test_list_tenders_payload_returns_recent_tenders_with_default_workflow(tmp_path):
    store = _store_with_tenders(tmp_path)

    payload = list_tenders_payload(store.database_path, {})

    assert payload["total"] == 2
    assert payload["items"][0]["title"]
    assert payload["items"][0]["documents_count"] in {0, 1}
    assert payload["items"][0]["items_count"] in {0, 1}
    assert payload["items"][0]["workflow_status"] == "new"
    assert payload["items"][0]["workflow_note"] == ""


def test_list_database_tables_payload_returns_admin_readonly_tables(tmp_path):
    store = _store_with_tenders(tmp_path)

    payload = list_database_tables_payload(store.database_path)

    assert payload["tables"] == [
        {"name": "tenders", "rows": 2},
        {"name": "tender_items", "rows": 1},
        {"name": "tender_documents", "rows": 2},
        {"name": "tender_analysis", "rows": 0},
        {"name": "tender_workflow", "rows": 0},
        {"name": "product_profiles", "rows": 0},
        {"name": "source_runs", "rows": 0},
    ]


def test_database_table_payloads_initialize_product_profiles_on_legacy_database(tmp_path):
    database_path = tmp_path / "legacy.sqlite"
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE tenders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                external_id TEXT NOT NULL,
                url TEXT NOT NULL,
                title TEXT NOT NULL,
                documents_json TEXT NOT NULL,
                raw_payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(source, external_id)
            )
            """
        )

    tables = list_database_tables_payload(database_path)
    product_profiles = get_database_table_payload(database_path, "product_profiles", {})

    assert {"name": "product_profiles", "rows": 0} in tables["tables"]
    assert product_profiles["table"] == "product_profiles"
    assert "okpd2" in product_profiles["columns"]
    assert product_profiles["rows"] == []


def test_list_source_runs_payload_returns_source_checkpoints_for_site(tmp_path):
    store = _store_with_tenders(tmp_path)
    store.record_source_error("mosreg_market", "timeout")

    payload = list_source_runs_payload(store.database_path)

    by_source = {row["source"]: row for row in payload["sources"]}
    assert by_source["mosreg_market"]["last_error"] == "timeout"
    assert by_source["moscow_supplier_portal"]["source"] == "moscow_supplier_portal"


def test_get_database_table_payload_returns_columns_and_rows(tmp_path):
    store = _store_with_tenders(tmp_path)

    payload = get_database_table_payload(store.database_path, "tenders", {"limit": "1"})

    assert payload["table"] == "tenders"
    assert "source" in payload["columns"]
    assert "external_id" in payload["columns"]
    assert payload["total"] == 2
    assert len(payload["rows"]) == 1
    assert payload["rows"][0]["source"] in {"moscow_supplier_portal", "mosreg_market"}


def test_get_database_table_payload_rejects_unknown_table(tmp_path):
    store = _store_with_tenders(tmp_path)

    with pytest.raises(KeyError, match="not allowed"):
        get_database_table_payload(store.database_path, "sqlite_master", {})


def test_list_tenders_payload_filters_by_source_and_query(tmp_path):
    store = _store_with_tenders(tmp_path)

    payload = list_tenders_payload(store.database_path, {"source": "mosreg_market", "q": "бумаг"})

    assert payload["total"] == 1
    assert payload["items"][0]["source"] == "mosreg_market"
    assert payload["items"][0]["title"] == "Поставка бумаги"


def test_list_tenders_payload_active_status_includes_mosreg_reception(tmp_path):
    store = _store_with_tenders(tmp_path)

    payload = list_tenders_payload(store.database_path, {"source": "mosreg_market", "status": "active"})

    assert payload["total"] == 1
    assert payload["items"][0]["status"] == "Прием предложений"


def test_list_tenders_payload_returns_normalized_filter_fields(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="mo-normalized",
            url="https://example.test/mo-normalized",
            title="Paper supply",
            region="Moscow Oblast",
            status="Reception of proposals",
            raw_payload={
                "federalLawName": "44-\u0424\u0417",
                "customers": [{"inn": "5047152960"}],
                "tradeType": 1,
            },
        )
    )

    payload = list_tenders_payload(
        store.database_path,
        {
            "law": "44-\u0424\u0417",
            "status": "active",
            "region": "MO",
            "procedure_type": "electronic_shop",
            "customer_inn": "5047152960",
        },
    )

    assert payload["total"] == 1
    assert payload["items"][0]["law"] == "44-\u0424\u0417"
    assert payload["items"][0]["status_normalized"] == "active"
    assert payload["items"][0]["region_code"] == "50"
    assert payload["items"][0]["source_family"] == "mosreg"
    assert payload["items"][0]["procedure_type"] == "electronic_shop"
    assert payload["items"][0]["customer_inn"] == "5047152960"


def test_list_tenders_payload_filters_by_federal_law(tmp_path):
    store = _store_with_tenders(tmp_path)

    payload = list_tenders_payload(store.database_path, {"law": "44-ФЗ"})

    assert payload["total"] == 2
    assert {item["law"] for item in payload["items"]} == {"44-ФЗ"}


def test_list_tenders_payload_filters_by_multiple_sources_and_quick_region(tmp_path):
    store = _store_with_tenders(tmp_path)

    payload = list_tenders_payload(
        store.database_path,
        {"source": "moscow_supplier_portal,mosreg_market", "region": "Москва + МО"},
    )

    assert payload["total"] == 2
    assert {item["source"] for item in payload["items"]} == {"moscow_supplier_portal", "mosreg_market"}


def test_list_tenders_payload_filters_by_multiple_okpd2_prefixes_and_items(tmp_path):
    store = _store_with_tenders(tmp_path)

    payload = list_tenders_payload(store.database_path, {"okpd2": "17.12, 11.05"})

    assert payload["total"] == 1
    assert payload["items"][0]["source"] == "mosreg_market"


def test_get_tender_payload_returns_documents_raw_payload_and_default_workflow(tmp_path):
    store = _store_with_tenders(tmp_path)

    payload = get_tender_payload(store.database_path, "moscow_supplier_portal", "10205128")

    assert payload["source"] == "moscow_supplier_portal"
    assert payload["external_id"] == "10205128"
    assert payload["documents"] == ["https://example.test/spec.docx"]
    assert json.loads(payload["raw_payload_json"])["federalLawName"] == "44-ФЗ"
    assert payload["workflow_status"] == "new"
    assert payload["workflow_note"] == ""


def test_get_tender_payload_returns_tender_items(tmp_path):
    store = _store_with_tenders(tmp_path)

    payload = get_tender_payload(store.database_path, "mosreg_market", "3668200")

    assert payload["items"] == [
        {
            "position_index": 1,
            "name": "Папка-вкладыш",
            "details": 'Папка-вкладыш Berlingo "Mirror", A4',
            "quantity": 800.0,
            "unit": "Штука",
            "unit_price": 2.0,
            "total_price": 1600.0,
            "okpd2": "11.05.01.01.02.01.017",
            "classifier_code": "11.05.01.01.02.01.017",
            "classifier_type": "КОЗ-2",
            "raw_payload": {},
        }
    ]


def test_get_tender_payload_returns_product_profiles(tmp_path):
    store = _store_with_tenders(tmp_path)

    payload = get_tender_payload(store.database_path, "mosreg_market", "3668200")

    assert payload["product_profiles"][0]["product_name"] == "Папка-вкладыш"
    assert payload["product_profiles"][0]["okpd2"] == "11.05.01.01.02.01.017"
    assert payload["product_profiles"][0]["classifier_code"] == "11.05.01.01.02.01.017"
    assert payload["product_profiles"][0]["classifier_type"] == "КОЗ-2"
    assert payload["product_profiles"][0]["quantity"] == 800.0
    assert "Папка-вкладыш 11.05.01.01.02.01.017" in payload["product_profiles"][0]["search_phrases"]


def test_rebuild_product_profiles_persists_profiles_and_payload_returns_saved_profile(tmp_path):
    store = _store_with_tenders(tmp_path)

    result = rebuild_product_profiles(store.database_path, "mosreg_market", "3668200")

    assert result["ok"] is True
    assert result["summary"]["total"] == 1
    assert result["summary"]["ready"] == 1

    saved = store.get_product_profiles("mosreg_market", "3668200")
    assert saved[0]["product_name"] == result["product_profiles"][0]["product_name"]

    payload = get_tender_payload(store.database_path, "mosreg_market", "3668200")
    assert payload["product_profiles"][0]["product_name"] == saved[0]["product_name"]
    assert payload["product_profiles"][0]["okpd2"] == result["product_profiles"][0]["okpd2"]
    assert payload["product_profile_summary"] == result["summary"]


def test_get_tender_payload_prefers_stored_product_profiles_over_computed_profile(tmp_path):
    store = _store_with_tenders(tmp_path)
    store.upsert_product_profiles(
        "mosreg_market",
        "3668200",
        [
            {
                "position_index": 1,
                "product_name": "Stored product profile",
                "profile_status": "rejected",
            }
        ],
    )

    payload = get_tender_payload(store.database_path, "mosreg_market", "3668200")

    assert payload["product_profiles"][0]["product_name"] == "Stored product profile"
    assert payload["product_profile_summary"]["total"] == 1
    assert payload["product_profile_summary"]["rejected"] == 1


def test_get_tender_payload_can_skip_product_profiles(tmp_path):
    store = _store_with_tenders(tmp_path)

    payload = get_tender_payload(store.database_path, "mosreg_market", "3668200", include_product_profiles=False)

    assert payload["product_profiles"] == []
    assert payload["product_profile_summary"] == {
        "total": 0,
        "draft": 0,
        "needs_review": 0,
        "ready": 0,
        "searching": 0,
        "matched": 0,
        "priced": 0,
        "rejected": 0,
    }


def test_rebuild_product_profiles_handles_forty_items(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="bulk",
            url="https://market.mosreg.ru/Trade/ViewTrade/bulk",
            title="Bulk tender",
            customer="School",
            items=[
                TenderItem(
                    name=f"Item {index}",
                    quantity=float(index),
                    okpd2=f"17.12.{index:02d}",
                    classifier_type="okpd2",
                )
                for index in range(1, 41)
            ],
        )
    )

    result = rebuild_product_profiles(store.database_path, "mosreg_market", "bulk")

    assert result["summary"]["total"] == 40
    assert result["summary"]["ready"] == 40
    assert len(result["product_profiles"]) == 40
    assert result["product_profiles"][39]["product_name"] == "Item 40"
    assert len(store.get_product_profiles("mosreg_market", "bulk")) == 40


def test_refresh_tender_detail_payload_saves_detail_items_documents_and_profiles(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="moscow_supplier_portal",
            external_id="10205109",
            url="https://zakupki.mos.ru/auction/10205109",
            title="ТОВАРЫ СТРОИТЕЛЬНЫЕ",
            customer="Школа",
            raw_payload={
                "auctionId": 10205109,
                "number": "10205109",
                "name": "ТОВАРЫ СТРОИТЕЛЬНЫЕ",
                "stateName": "Активная",
            },
        )
    )

    class DetailAdapter:
        source = "moscow_supplier_portal"

        def enrich_payload(self, payload):
            enriched = dict(payload)
            enriched["__detail"] = {
                "id": 10205109,
                "name": "ТОВАРЫ СТРОИТЕЛЬНЫЕ",
                "startCost": 86330.0,
                "state": {"name": "Активная"},
                "files": [{"id": 275311511, "name": "Проект контракта.pdf"}],
                "items": [
                    {
                        "name": "Краска акриловая",
                        "productionDirectoryName": "Краска акриловая интерьерная",
                        "currentValue": 50,
                        "costPerUnit": 1567,
                        "okeiName": "шт",
                        "okpd2": "20.30.11.120",
                    }
                ],
            }
            return enriched

        def normalize_payload(self, payload):
            from tender_killer.adapters.moscow import MoscowSupplierPortalAdapter

            return MoscowSupplierPortalAdapter(enrich_details=False).normalize_payload(payload)

    payload = refresh_tender_detail_payload(
        store.database_path,
        "moscow_supplier_portal",
        "10205109",
        adapter=DetailAdapter(),
    )

    assert payload["ok"] is True
    assert payload["refreshed"] is True
    assert payload["summary"]["items_count"] == 1
    assert payload["summary"]["documents_count"] == 1
    assert payload["summary"]["product_profiles_count"] == 1
    assert payload["tender"]["items"][0]["name"] == "Краска акриловая"
    assert payload["tender"]["document_records"][0]["name"] == "Проект контракта.pdf"
    assert payload["tender"]["product_profiles"][0]["product_name"] == "Краска акриловая"


def test_refresh_tender_detail_payload_keeps_existing_data_when_detail_unavailable(tmp_path):
    store = _store_with_tenders(tmp_path)

    class EmptyAdapter:
        source = "mosreg_market"

        def enrich_payload(self, payload):
            return dict(payload)

        def normalize_payload(self, payload):
            raise AssertionError("refresh should not normalize unchanged payload")

    payload = refresh_tender_detail_payload(
        store.database_path,
        "mosreg_market",
        "3668200",
        adapter=EmptyAdapter(),
    )

    assert payload["ok"] is True
    assert payload["refreshed"] is False
    assert payload["tender"]["items"][0]["name"] == "Папка-вкладыш"


def test_refresh_tender_detail_payload_parses_mosreg_html_items(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="3666760",
            url="https://market.mosreg.ru/Trade/ViewTrade/3666760",
            title="Поставка зачетных книжек",
            price=105637.0,
            raw_payload={"Id": 3666760, "TradeName": "Поставка зачетных книжек"},
        )
    )

    class HtmlDetailAdapter:
        source = "mosreg_market"

        def enrich_payload(self, payload):
            enriched = dict(payload)
            enriched["__html"] = """
            <div class="informationAboutCustomer__resultBlock objectPurchase">
              <div class="outputResults__oneResult">
                <p><span class="grayText">Наименование товара, работ, услуг:</span> Бланк из бумаги или картона</p>
                <p><span class="grayText">Детализированное наименование:</span> Поставка зачетных книжек</p>
                <p><span class="grayText">Код классификатор:</span><span>11.105.01.02.08.01.008</span></p>
                <p><span class="grayText">Тип классификатор:</span><span>КОЗ-2</span></p>
                <p><span class="grayText">Единицы измерения:</span> Штука</p>
                <p><span class="grayText">Количество:</span> 700,00000000000</p>
                <p><span class="grayText">Стоимость единицы продукции ( в т.ч. НДС при наличии):</span> 150,91000</p>
                <p><span class="grayText">Стоимость поставленого товара, выполненых работ, оказываемых услуг ( в т.ч. НДС при наличии):</span> 105637,00</p>
              </div>
            </div>
            """
            return enriched

        def normalize_payload(self, payload):
            from tender_killer.adapters.mosreg import MosregMarketAdapter

            return MosregMarketAdapter(enrich_documents=False).normalize_payload(payload)

    payload = refresh_tender_detail_payload(
        store.database_path,
        "mosreg_market",
        "3666760",
        adapter=HtmlDetailAdapter(),
    )

    item = payload["tender"]["items"][0]
    profile = payload["tender"]["product_profiles"][0]
    assert item["name"] == "Бланк из бумаги или картона"
    assert item["details"] == "Поставка зачетных книжек"
    assert item["quantity"] == 700.0
    assert item["unit"] == "Штука"
    assert item["classifier_code"] == "11.105.01.02.08.01.008"
    assert item["classifier_type"] == "КОЗ-2"
    assert profile["product_name"] == "Бланк из бумаги или картона"
    assert profile["quantity"] == 700.0
    assert profile["classifier_code"] == "11.105.01.02.08.01.008"


def test_get_tender_payload_returns_document_records(tmp_path):
    store = _store_with_tenders(tmp_path)

    payload = get_tender_payload(store.database_path, "mosreg_market", "3668200")

    assert payload["document_records"] == [
        {
            "document_index": 1,
            "name": "Техническое задание.docx",
            "document_type": "Описание объекта закупки",
            "url": "https://example.test/tz.docx",
            "source_document_id": "doc-1",
            "local_path": None,
            "downloaded_at": None,
            "text_status": "pending",
            "text_content": None,
            "text_extracted_at": None,
            "text_error": None,
            "raw_payload": {},
        }
    ]


def test_download_tender_documents_payload_updates_local_paths(tmp_path):
    store = _store_with_tenders(tmp_path)
    downloaded = []

    def fake_downloader(url, target_path):
        downloaded.append((url, target_path.name))
        target_path.write_bytes(b"doc")

    payload = download_tender_documents_payload(
        store.database_path,
        "mosreg_market",
        "3668200",
        tmp_path / "documents",
        downloader=fake_downloader,
    )

    assert payload["downloaded"] == 1
    assert downloaded == [("https://example.test/tz.docx", "Техническое задание.docx")]
    detail = get_tender_payload(store.database_path, "mosreg_market", "3668200")
    assert detail["document_records"][0]["local_path"].endswith("Техническое задание.docx")
    assert detail["document_records"][0]["downloaded_at"]


def test_download_tender_documents_payload_backfills_legacy_document_urls(tmp_path):
    store = _store_with_tenders(tmp_path)
    downloaded = []

    def fake_downloader(url, target_path):
        downloaded.append((url, target_path.name))
        target_path.write_bytes(b"legacy")

    payload = download_tender_documents_payload(
        store.database_path,
        "moscow_supplier_portal",
        "10205128",
        tmp_path / "documents",
        downloader=fake_downloader,
    )

    assert payload["downloaded"] == 1
    assert downloaded == [("https://example.test/spec.docx", "spec.docx")]
    detail = get_tender_payload(store.database_path, "moscow_supplier_portal", "10205128")
    assert detail["document_records"][0]["name"] == "spec.docx"


def test_download_tender_documents_payload_expands_mosreg_document_listing(tmp_path):
    store = _store_with_tenders(tmp_path)
    with sqlite3.connect(store.database_path) as connection:
        connection.execute(
            "DELETE FROM tender_documents WHERE source = ? AND external_id = ?",
            ("mosreg_market", "3668200"),
        )
        connection.execute(
            "UPDATE tenders SET documents_json = ? WHERE source = ? AND external_id = ?",
            (
                '["https://api.market.mosreg.ru/api/Trade/3668200/GetTradeDocuments"]',
                "mosreg_market",
                "3668200",
            ),
        )
    downloaded = []

    def fake_resolver(url):
        assert url.endswith("/GetTradeDocuments")
        return [
            {
                "FileName": "Техническое задание.docx",
                "Type": "Описание объекта закупки",
                "Url": "https://example.test/real-tz.docx",
                "Id": "doc-real",
            }
        ]

    def fake_downloader(url, target_path):
        downloaded.append((url, target_path.name))
        target_path.write_bytes(b"real")

    payload = download_tender_documents_payload(
        store.database_path,
        "mosreg_market",
        "3668200",
        tmp_path / "documents",
        downloader=fake_downloader,
        document_listing_resolver=fake_resolver,
    )

    assert payload["downloaded"] == 1
    assert downloaded == [("https://example.test/real-tz.docx", "Техническое задание.docx")]
    assert payload["document_records"][0]["url"] == "https://example.test/real-tz.docx"
    assert payload["document_records"][0]["document_type"] == "Описание объекта закупки"


def test_download_tender_documents_payload_avoids_duplicate_filenames(tmp_path):
    store = _store_with_tenders(tmp_path)
    with sqlite3.connect(store.database_path) as connection:
        connection.execute(
            "DELETE FROM tender_documents WHERE source = ? AND external_id = ?",
            ("mosreg_market", "3668200"),
        )
        connection.executemany(
            """
            INSERT INTO tender_documents (
                source, external_id, document_index, name, document_type, url,
                source_document_id, raw_payload_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                ("mosreg_market", "3668200", 1, "ООЗ.docx", "ТЗ", "https://example.test/1.docx", "1", "{}"),
                ("mosreg_market", "3668200", 2, "ООЗ.docx", "ТЗ", "https://example.test/2.docx", "2", "{}"),
            ],
        )

    def fake_downloader(url, target_path):
        target_path.write_bytes(url.encode("utf-8"))

    payload = download_tender_documents_payload(
        store.database_path,
        "mosreg_market",
        "3668200",
        tmp_path / "documents",
        downloader=fake_downloader,
    )

    paths = [document["local_path"] for document in payload["document_records"]]
    assert paths[0].endswith("ООЗ.docx")
    assert paths[1].endswith("ООЗ-2.docx")
    assert paths[0] != paths[1]


def test_extract_tender_document_text_payload_saves_text_for_downloaded_documents(tmp_path):
    store = _store_with_tenders(tmp_path)
    document_path = tmp_path / "documents" / "tz.docx"
    document_path.parent.mkdir(parents=True)
    document_path.write_bytes(_docx_bytes("Paper whiteness 146 CIE. Delivery: Moscow."))
    with sqlite3.connect(store.database_path) as connection:
        connection.execute(
            """
            UPDATE tender_documents
            SET local_path = ?, downloaded_at = ?, text_status = ?
            WHERE source = ? AND external_id = ? AND url = ?
            """,
            (
                str(document_path),
                "2026-05-20T10:00:00",
                "downloaded",
                "mosreg_market",
                "3668200",
                "https://example.test/tz.docx",
            ),
        )

    payload = extract_tender_document_text_payload(store.database_path, "mosreg_market", "3668200")

    assert payload["extracted"] == 1
    assert payload["failed"] == []
    document = payload["document_records"][0]
    assert document["text_status"] == "ok"
    assert "Paper whiteness 146 CIE" in document["text_content"]
    assert document["text_extracted_at"]
    assert document["text_error"] == ""


def test_extract_tender_document_text_payload_reports_missing_local_files(tmp_path):
    store = _store_with_tenders(tmp_path)
    missing_path = tmp_path / "missing.docx"
    with sqlite3.connect(store.database_path) as connection:
        connection.execute(
            """
            UPDATE tender_documents
            SET local_path = ?, downloaded_at = ?, text_status = ?
            WHERE source = ? AND external_id = ? AND url = ?
            """,
            (
                str(missing_path),
                "2026-05-20T10:00:00",
                "downloaded",
                "mosreg_market",
                "3668200",
                "https://example.test/tz.docx",
            ),
        )

    payload = extract_tender_document_text_payload(store.database_path, "mosreg_market", "3668200")

    assert payload["extracted"] == 0
    assert payload["failed"] == [{"url": "https://example.test/tz.docx", "error": "local file is missing"}]
    document = payload["document_records"][0]
    assert document["text_status"] == "missing_file"
    assert document["text_error"] == "local file is missing"


def test_analyze_tender_payload_saves_structured_summary_from_extracted_text(tmp_path):
    store = _store_with_tenders(tmp_path)
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
                "Поставщик предоставляет сертификат соответствия. "
                "Срок поставки в течение 3 рабочих дней. "
                "Обеспечение исполнения контракта 5 процентов. "
                "Применяется постановление 1875 и страна происхождения товара.",
                "2026-05-20T10:30:00",
                "mosreg_market",
                "3668200",
                "https://example.test/tz.docx",
            ),
        )

    payload = analyze_tender_payload(store.database_path, "mosreg_market", "3668200")

    assert payload["analysis"]["status"] == "needs_review"
    assert "поставка огнетушителей" in payload["analysis"]["summary"]
    assert "сертификат/декларация" in payload["analysis"]["requirements"]
    assert "обеспечение исполнения контракта" in payload["analysis"]["risks"]
    assert "национальный режим/страна происхождения" in payload["analysis"]["red_flags"]
    detail = get_tender_payload(store.database_path, "mosreg_market", "3668200")
    assert detail["analysis"]["summary"] == payload["analysis"]["summary"]


def test_build_tender_report_response_returns_docx_bytes(tmp_path):
    store = _store_with_tenders(tmp_path)
    analyze_tender_payload(store.database_path, "mosreg_market", "3668200")

    response = build_tender_report_response(store.database_path, "mosreg_market", "3668200")

    assert response["filename"] == "tender-killer-3668200.docx"
    assert response["content_type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    assert response["body"].startswith(b"PK")


def test_update_tender_workflow_persists_status_and_note(tmp_path):
    store = _store_with_tenders(tmp_path)

    payload = update_tender_workflow(
        store.database_path,
        "moscow_supplier_portal",
        "10205128",
        {"workflow_status": "interesting", "workflow_note": "Check margin and delivery."},
    )

    assert payload["workflow_status"] == "interesting"
    assert payload["workflow_note"] == "Check margin and delivery."
    detail = get_tender_payload(store.database_path, "moscow_supplier_portal", "10205128")
    assert detail["workflow_status"] == "interesting"
    assert detail["workflow_note"] == "Check margin and delivery."


def test_list_tenders_payload_filters_by_workflow_status(tmp_path):
    store = _store_with_tenders(tmp_path)
    update_tender_workflow(
        store.database_path,
        "moscow_supplier_portal",
        "10205128",
        {"workflow_status": "interesting"},
    )

    payload = list_tenders_payload(store.database_path, {"workflow_status": "interesting"})

    assert payload["total"] == 1
    assert payload["items"][0]["external_id"] == "10205128"


def test_update_tender_workflow_rejects_unknown_status(tmp_path):
    store = _store_with_tenders(tmp_path)

    with pytest.raises(ValueError, match="Unknown workflow status"):
        update_tender_workflow(
            store.database_path,
            "moscow_supplier_portal",
            "10205128",
            {"workflow_status": "maybe_later"},
        )


def test_run_search_payload_returns_pipeline_stats_and_notification_state(tmp_path):
    class FakeSettings:
        telegram_bot_token = "token"
        telegram_chat_id = "123"

    def fake_runner(settings, collection):
        assert settings.telegram_chat_id == "123"
        assert collection is None
        return PipelineStats(fetched=10, saved=2, matched=3, notified=1, failed_sources=0)

    payload = run_search_payload(FakeSettings(), fake_runner)

    assert payload["ok"] is True
    assert payload["notifications_enabled"] is True
    assert payload["stats"] == {
        "fetched": 10,
        "saved": 2,
        "matched": 3,
        "notified": 1,
        "failed_sources": 0,
        "failed_source_names": [],
        "failed_source_errors": [],
    }


def test_build_search_collection_uses_site_filters_for_manual_search():
    collection = build_search_collection(
        {
            "filters": {
                "q": "бумага, кабель",
                "source": "mosreg_market",
                "law": "44-ФЗ",
                "region": "Московская область",
                "status": "active",
                "okpd2": "17.12",
                "min_price": "50000",
                "max_price": "200000",
            }
        }
    )

    profile = collection.active_profiles()[0].profile
    assert profile.keywords == ("бумага", "кабель")
    assert profile.sources == ("mosreg",)
    assert profile.laws == ("44-ФЗ",)
    assert profile.regions == ("Московская область",)
    assert profile.only_active is True
    assert profile.statuses == ()
    assert profile.okpd2 == ("17.12",)
    assert profile.min_price == 50000.0
    assert profile.max_price == 200000.0


def test_build_search_collection_supports_multiselect_site_filters():
    collection = build_search_collection(
        {
            "filters": {
                "q": "бумага, кабель",
                "source": "moscow_supplier_portal, mosreg_market",
                "law": "44-ФЗ, 223-ФЗ",
                "region": "Москва + МО",
                "status": "active",
                "okpd2": "17.12, 11.05",
            }
        }
    )

    profile = collection.active_profiles()[0].profile
    assert profile.sources == ("moscow", "mosreg")
    assert profile.laws == ("44-ФЗ", "223-ФЗ")
    assert profile.regions == ("Москва", "Московская область")
    assert profile.okpd2 == ("17.12", "11.05")


def test_run_search_payload_passes_site_filter_collection_to_runner():
    class FakeSettings:
        telegram_bot_token = ""
        telegram_chat_id = ""

    captured = {}

    def fake_runner(settings, collection):
        captured["profile"] = collection.active_profiles()[0].profile
        return PipelineStats(fetched=1, saved=1, matched=1, notified=0, failed_sources=0)

    payload = run_search_payload(
        FakeSettings(),
        fake_runner,
        {"filters": {"source": "moscow_supplier_portal", "status": "active", "q": "бетон"}},
    )

    assert payload["stats"]["matched"] == 1
    assert captured["profile"].sources == ("moscow",)
    assert captured["profile"].keywords == ("бетон",)


def test_send_tender_notification_payload_sends_selected_card(tmp_path):
    store = _store_with_tenders(tmp_path)

    class FakeSettings:
        telegram_bot_token = "token"
        telegram_chat_id = "123"
        dry_run = False

    class FakeNotifier:
        def __init__(self):
            self.messages = []

        def send(self, text):
            self.messages.append(text)
            return True

    notifier = FakeNotifier()

    payload = send_tender_notification_payload(
        store.database_path,
        "mosreg_market",
        "3668200",
        FakeSettings(),
        notifier=notifier,
    )

    assert payload == {"ok": True, "sent": True}
    assert len(notifier.messages) == 1
    assert "Поставка бумаги" in notifier.messages[0]
