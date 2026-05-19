from __future__ import annotations

import json

from tender_killer.models import Tender
from tender_killer.storage import TenderStore
from tender_killer.web_api import get_tender_payload, list_tenders_payload


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
            raw_payload={"federalLawName": "44-ФЗ"},
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
            raw_payload={"SourcePlatformName": "ЕАСУЗ 44"},
        )
    )
    return store


def test_list_tenders_payload_returns_recent_tenders(tmp_path):
    store = _store_with_tenders(tmp_path)

    payload = list_tenders_payload(store.database_path, {})

    assert payload["total"] == 2
    assert payload["items"][0]["title"]
    assert payload["items"][0]["documents_count"] in {0, 1}


def test_list_tenders_payload_filters_by_source_and_query(tmp_path):
    store = _store_with_tenders(tmp_path)

    payload = list_tenders_payload(store.database_path, {"source": "mosreg_market", "q": "бумаг"})

    assert payload["total"] == 1
    assert payload["items"][0]["source"] == "mosreg_market"
    assert payload["items"][0]["title"] == "Поставка бумаги"


def test_list_tenders_payload_filters_by_federal_law(tmp_path):
    store = _store_with_tenders(tmp_path)

    payload = list_tenders_payload(store.database_path, {"law": "44-ФЗ"})

    assert payload["total"] == 2
    assert {item["law"] for item in payload["items"]} == {"44-ФЗ"}


def test_get_tender_payload_returns_documents_and_raw_payload(tmp_path):
    store = _store_with_tenders(tmp_path)

    payload = get_tender_payload(store.database_path, "moscow_supplier_portal", "10205128")

    assert payload["source"] == "moscow_supplier_portal"
    assert payload["external_id"] == "10205128"
    assert payload["documents"] == ["https://example.test/spec.docx"]
    assert json.loads(payload["raw_payload_json"])["federalLawName"] == "44-ФЗ"
