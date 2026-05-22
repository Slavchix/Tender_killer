from __future__ import annotations

from tender_killer.economics_service import update_profile_economics
from tender_killer.models import ProductProfile
from tender_killer.models import Tender
from tender_killer.storage import TenderStore
from tender_killer.tender_detail_service import get_tender_payload


def test_update_profile_economics_persists_manual_cost_inputs_and_recalculates(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="economics-input",
            url="https://market.mosreg.ru/Trade/ViewTrade/economics-input",
            title="Paper tender",
            price=100000.0,
        )
    )
    store.upsert_product_profiles(
        "mosreg_market",
        "economics-input",
        [
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="economics-input",
                position_index=1,
                product_name="Office paper",
                quantity=10,
                unit="pack",
                raw_payload={"note": "keep me"},
                fulfillment_requirements=[{"type": "delivery", "source": "TZ.docx", "value": "Delivery 5 days."}],
            )
        ],
    )

    payload = update_profile_economics(
        store.database_path,
        "mosreg_market",
        "economics-input",
        1,
        {"unit_cost": "6000", "logistics_cost": "5000", "documents_cost": "2000", "other_costs": ""},
    )

    assert payload["ok"] is True
    detail = get_tender_payload(store.database_path, "mosreg_market", "economics-input")
    profile = detail["product_profiles"][0]
    assert profile["profile_status"] == "priced"
    assert profile["raw_payload"] == {
        "note": "keep me",
        "economics": {"unit_cost": 6000.0, "logistics_cost": 5000.0, "documents_cost": 2000.0},
    }
    assert detail["economics"]["supplier_cost"] == 67000.0
    assert detail["economics"]["missing_cost_inputs"] == []
