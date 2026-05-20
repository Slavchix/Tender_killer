from __future__ import annotations

import json

import pytest

from tender_killer.models import Tender
from tender_killer.pipeline import PipelineStats
from tender_killer.storage import TenderStore
from tender_killer.web_api import (
    build_search_collection,
    get_tender_payload,
    list_tenders_payload,
    run_search_payload,
    update_tender_workflow,
)


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


def test_list_tenders_payload_returns_recent_tenders_with_default_workflow(tmp_path):
    store = _store_with_tenders(tmp_path)

    payload = list_tenders_payload(store.database_path, {})

    assert payload["total"] == 2
    assert payload["items"][0]["title"]
    assert payload["items"][0]["documents_count"] in {0, 1}
    assert payload["items"][0]["workflow_status"] == "new"
    assert payload["items"][0]["workflow_note"] == ""


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


def test_list_tenders_payload_filters_by_federal_law(tmp_path):
    store = _store_with_tenders(tmp_path)

    payload = list_tenders_payload(store.database_path, {"law": "44-ФЗ"})

    assert payload["total"] == 2
    assert {item["law"] for item in payload["items"]} == {"44-ФЗ"}


def test_get_tender_payload_returns_documents_raw_payload_and_default_workflow(tmp_path):
    store = _store_with_tenders(tmp_path)

    payload = get_tender_payload(store.database_path, "moscow_supplier_portal", "10205128")

    assert payload["source"] == "moscow_supplier_portal"
    assert payload["external_id"] == "10205128"
    assert payload["documents"] == ["https://example.test/spec.docx"]
    assert json.loads(payload["raw_payload_json"])["federalLawName"] == "44-ФЗ"
    assert payload["workflow_status"] == "new"
    assert payload["workflow_note"] == ""


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
