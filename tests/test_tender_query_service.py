from __future__ import annotations

from datetime import UTC, datetime, timedelta

from tender_killer.models import Tender
from tender_killer.storage import TenderStore
from tender_killer.tender_query_service import list_tenders_payload


def test_tender_query_service_returns_total_limit_and_offset(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    for index in range(3):
        store.upsert_tender(
            Tender(
                source="mosreg_market",
                external_id=f"mo-{index}",
                url=f"https://example.test/mo-{index}",
                title=f"Paper tender {index}",
                published_at=datetime(2026, 5, 20 + index, tzinfo=UTC),
            )
        )

    payload = list_tenders_payload(store.database_path, {"limit": "1", "offset": "1"})

    assert payload["total"] == 3
    assert payload["limit"] == 1
    assert payload["offset"] == 1
    assert payload["has_previous"] is True
    assert payload["previous_offset"] == 0
    assert payload["has_next"] is True
    assert payload["next_offset"] == 2
    assert len(payload["items"]) == 1
    assert payload["items"][0]["external_id"] == "mo-1"


def test_tender_query_service_filters_with_normalized_columns(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="match",
            url="https://example.test/match",
            title="Paper supply",
            region="Moscow Oblast",
            status="Reception of proposals",
            raw_payload={
                "federalLawName": "44-FZ",
                "customers": [{"inn": "5047152960"}],
                "tradeType": 1,
            },
        )
    )
    store.upsert_tender(
        Tender(
            source="moscow_supplier_portal",
            external_id="skip",
            url="https://example.test/skip",
            title="Paper supply",
            region="Moscow",
            status="Completed",
            raw_payload={"federalLawName": "223-FZ"},
        )
    )

    payload = list_tenders_payload(
        store.database_path,
        {
            "source_family": "mosreg",
            "status": "active",
            "region": "MO",
            "procedure_type": "electronic_shop",
            "customer_inn": "5047152960",
        },
    )

    assert payload["total"] == 1
    assert payload["items"][0]["external_id"] == "match"


def test_tender_query_service_active_status_hides_expired_deadlines(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    now = datetime.now(UTC)
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="expired",
            url="https://example.test/expired",
            title="Expired active-looking tender",
            status="Прием предложений",
            deadline_at=now - timedelta(days=1),
        )
    )
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="actual",
            url="https://example.test/actual",
            title="Actual tender",
            status="Прием предложений",
            deadline_at=now + timedelta(days=1),
        )
    )

    payload = list_tenders_payload(store.database_path, {"status": "active"})

    assert payload["total"] == 1
    assert payload["items"][0]["external_id"] == "actual"


def test_tender_query_service_expands_construction_material_search_query(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="materials",
            url="https://example.test/materials",
            title="Поставка материалов для ремонта помещений",
            status="Прием предложений",
        )
    )

    payload = list_tenders_payload(store.database_path, {"q": "строительные материалы"})

    assert payload["total"] == 1
    assert payload["items"][0]["external_id"] == "materials"


def test_tender_query_service_does_not_match_expanded_query_only_in_raw_payload(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="fuel",
            url="https://example.test/fuel",
            title="Поставка автомобильного бензина",
            status="Прием предложений",
            raw_payload={"note": "материал заказчика"},
        )
    )

    payload = list_tenders_payload(store.database_path, {"q": "строительные материалы"})

    assert payload["total"] == 0


def test_tender_query_service_does_not_treat_generic_information_materials_as_construction(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="media",
            url="https://example.test/media",
            title="Оказание услуг по выпуску информационных материалов",
            status="Прием предложений",
        )
    )

    payload = list_tenders_payload(store.database_path, {"q": "строительные материалы"})

    assert payload["total"] == 0


def test_tender_query_service_does_not_treat_repair_works_as_materials(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="road-works",
            url="https://example.test/road-works",
            title="Выполнение работ по текущему ремонту автомобильной дороги",
            status="Прием предложений",
        )
    )

    payload = list_tenders_payload(store.database_path, {"q": "строительные материалы"})

    assert payload["total"] == 0
