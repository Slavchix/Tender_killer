from __future__ import annotations

from datetime import UTC, datetime

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
