from __future__ import annotations

from tender_killer.models import ProductProfile
from tender_killer.models import Tender
from tender_killer.models import TenderDocument
from tender_killer.models import TenderItem
from tender_killer.storage import TenderStore
from tender_killer.tender_detail_service import get_tender_payload
from tender_killer.tender_detail_service import refresh_tender_detail_payload


def test_refresh_tender_detail_payload_saves_detail_and_rebuilds_profiles(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="3668200",
            url="https://market.mosreg.ru/Trade/ViewTrade/3668200",
            title="Paper tender",
            raw_payload={"Id": 3668200},
        )
    )

    class DetailAdapter:
        source = "mosreg_market"

        def enrich_payload(self, payload):
            enriched = dict(payload)
            enriched["__detail"] = {"loaded": True}
            return enriched

        def normalize_payload(self, payload):
            return Tender(
                source="mosreg_market",
                external_id="3668200",
                url="https://market.mosreg.ru/Trade/ViewTrade/3668200",
                title="Paper tender detail",
                raw_payload=payload,
                items=[
                    TenderItem(
                        name="Office paper",
                        quantity=10.0,
                        unit="pack",
                        okpd2="17.12.14.110",
                    )
                ],
                document_records=[
                    TenderDocument(
                        url="https://example.test/tz.docx",
                        name="tz.docx",
                        document_type="technical specification",
                    )
                ],
            )

    response = refresh_tender_detail_payload(
        store.database_path,
        "mosreg_market",
        "3668200",
        adapter=DetailAdapter(),
    )

    assert response["ok"] is True
    assert response["refreshed"] is True
    assert response["summary"]["items_count"] == 1
    assert response["summary"]["documents_count"] == 1
    assert response["summary"]["product_profiles_count"] == 1
    assert response["tender"]["items"][0]["name"] == "Office paper"
    assert response["tender"]["document_records"][0]["name"] == "tz.docx"

    detail = get_tender_payload(store.database_path, "mosreg_market", "3668200")
    assert detail["product_profile_summary"]["total"] == 1
    assert detail["product_profiles"][0]["product_name"] == "Office paper"


def test_refresh_tender_detail_payload_preserves_saved_product_economics(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="3668201",
            url="https://market.mosreg.ru/Trade/ViewTrade/3668201",
            title="Paper tender",
            price=100000.0,
            raw_payload={"Id": 3668201},
        )
    )
    store.upsert_product_profiles(
        "mosreg_market",
        "3668201",
        [
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="3668201",
                position_index=1,
                product_name="Office paper",
                quantity=10,
                unit="pack",
                profile_status="priced",
                raw_payload={
                    "economics": {"unit_cost": 6000.0, "logistics_cost": 5000.0},
                    "economics_assumptions": {"vat_mode": "vat_included", "risk_reserve_percent": 5.0},
                },
            )
        ],
    )

    class DetailAdapter:
        source = "mosreg_market"

        def enrich_payload(self, payload):
            enriched = dict(payload)
            enriched["__detail"] = {"loaded": True}
            return enriched

        def normalize_payload(self, payload):
            return Tender(
                source="mosreg_market",
                external_id="3668201",
                url="https://market.mosreg.ru/Trade/ViewTrade/3668201",
                title="Paper tender detail",
                price=100000.0,
                raw_payload=payload,
                items=[
                    TenderItem(
                        name="Office paper updated",
                        quantity=10.0,
                        unit="pack",
                        okpd2="17.12.14.110",
                    )
                ],
            )

    response = refresh_tender_detail_payload(
        store.database_path,
        "mosreg_market",
        "3668201",
        adapter=DetailAdapter(),
    )

    profile = response["tender"]["product_profiles"][0]
    assert profile["product_name"] == "Office paper updated"
    assert profile["profile_status"] == "priced"
    assert profile["raw_payload"]["economics"] == {"unit_cost": 6000.0, "logistics_cost": 5000.0}
    assert profile["raw_payload"]["economics_assumptions"] == {
        "vat_mode": "vat_included",
        "risk_reserve_percent": 5.0,
    }
    assert response["tender"]["economics"]["supplier_cost"] == 68250.0


def test_get_tender_payload_includes_economics_summary_from_product_profiles(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="economics-1",
            url="https://market.mosreg.ru/Trade/ViewTrade/economics-1",
            title="Paper tender",
            price=100000.0,
        )
    )
    store.upsert_product_profiles(
        "mosreg_market",
        "economics-1",
        [
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="economics-1",
                position_index=1,
                product_name="Office paper",
                quantity=10,
                unit="pack",
                fulfillment_requirements=[{"type": "delivery", "source": "TZ.docx", "value": "Delivery 5 days."}],
                raw_payload={"economics": {"unit_cost": 6000, "logistics_cost": 5000}},
            )
        ],
    )

    detail = get_tender_payload(store.database_path, "mosreg_market", "economics-1")

    assert detail["economics"]["status"] == "interesting"
    assert detail["economics"]["supplier_cost"] == 65000.0
    assert detail["economics"]["risk_reserve"] == 1500.0
    assert detail["economics"]["gross_margin"] == 33500.0


def test_get_tender_payload_includes_decision_summary(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="decision-1",
            url="https://market.mosreg.ru/Trade/ViewTrade/decision-1",
            title="Paper tender",
            price=100000.0,
        )
    )
    store.upsert_product_profiles(
        "mosreg_market",
        "decision-1",
        [
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="decision-1",
                position_index=1,
                product_name="Office paper",
                quantity=10,
                unit="pack",
                profile_status="priced",
                raw_payload={"economics": {"unit_cost": 6000, "logistics_cost": 5000}},
            )
        ],
    )

    detail = get_tender_payload(store.database_path, "mosreg_market", "decision-1")

    assert detail["decision"]["status"] == "interesting"
    assert detail["decision"]["label"] == "Интересно"
    assert detail["decision"]["metrics"]["nmc_price"] == 100000.0
    assert detail["decision"]["metrics"]["positions_priced"] == 1


def test_get_tender_payload_includes_latest_price_change(tmp_path):
    from dataclasses import replace

    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    tender = Tender(
        source="mosreg_market",
        external_id="price-change",
        url="https://example.test/price-change",
        title="Поставка топлива",
        price=100000.0,
    )
    store.upsert_tender(tender)
    store.upsert_tender(replace(tender, price=95000.0))

    detail = get_tender_payload(store.database_path, "mosreg_market", "price-change")

    assert detail["price_change"]["direction"] == "decreased"
    assert detail["price_change"]["previous_price"] == 100000.0
    assert detail["price_change"]["current_price"] == 95000.0


def test_get_tender_payload_includes_eis_reference_and_customer_risk_profile(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    for external_id, title in (("history-1", "Old paper"), ("history-2", "Old frames")):
        store.upsert_tender(
            Tender(
                source="mosreg_market",
                external_id=external_id,
                url=f"https://example.test/{external_id}",
                title=title,
                customer="School",
                status="completed",
                raw_payload={
                    "customers": [{"inn": "5047152960"}],
                    "__detail": {"uniqueSupplierCount": 0},
                },
            )
        )
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="current-risk",
            url="https://example.test/current-risk",
            title="Paper supply",
            customer="School",
            status="active",
            raw_payload={
                "purchaseNumber": "0373200000126000012",
                "customers": [{"inn": "5047152960"}],
                "__detail": {"uniqueSupplierCount": 0},
            },
        )
    )

    detail = get_tender_payload(store.database_path, "mosreg_market", "current-risk")

    assert detail["eis_reference"]["identifiers"]["purchase_number"] == "0373200000126000012"
    assert detail["eis_reference"]["identifiers"]["customer_inn"] == "5047152960"
    assert detail["customer_risk_profile"]["status"] == "ready"
    assert detail["customer_risk_profile"]["history"]["total"] == 2
    assert detail["customer_risk_profile"]["history"]["market_state_counts"]["no_participants"] == 2
    assert "repeated_no_participants" in {
        factor["id"] for factor in detail["customer_risk_profile"]["factors"]
    }
