from __future__ import annotations

from tender_killer.economics_service import update_profile_economics
from tender_killer.economics_service import update_profile_economics_assumptions
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


def test_update_profile_economics_persists_landed_cost_pack_inputs(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="economics-pack-input",
            url="https://market.mosreg.ru/Trade/ViewTrade/economics-pack-input",
            title="Folders tender",
            price=5000.0,
        )
    )
    store.upsert_product_profiles(
        "mosreg_market",
        "economics-pack-input",
        [
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="economics-pack-input",
                position_index=1,
                product_name="Folder",
                quantity=25,
                unit="pcs",
                raw_payload={"note": "keep me"},
            )
        ],
    )

    payload = update_profile_economics(
        store.database_path,
        "mosreg_market",
        "economics-pack-input",
        1,
        {
            "unit_cost": "100",
            "unit_cost_basis": "supplier_pack",
            "pack_quantity": "10",
            "logistics_cost": "300",
            "documents_cost": "50",
            "packaging_cost": "25",
            "other_costs": "10",
        },
    )

    assert payload["ok"] is True
    detail = get_tender_payload(store.database_path, "mosreg_market", "economics-pack-input")
    profile = detail["product_profiles"][0]
    assert profile["raw_payload"]["economics"] == {
        "unit_cost": 100.0,
        "unit_cost_basis": "supplier_pack",
        "pack_quantity": 10.0,
        "logistics_cost": 300.0,
        "documents_cost": 50.0,
        "packaging_cost": 25.0,
        "other_costs": 10.0,
    }
    assert detail["economics"]["items"][0]["landed_cost"] == 685.0


def test_update_profile_economics_assumptions_persists_and_recalculates(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="economics-assumptions",
            url="https://market.mosreg.ru/Trade/ViewTrade/economics-assumptions",
            title="Fuel tender",
            price=20000.0,
        )
    )
    store.upsert_product_profiles(
        "mosreg_market",
        "economics-assumptions",
        [
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="economics-assumptions",
                position_index=1,
                product_name="Fuel",
                quantity=10,
                unit="l",
                raw_payload={
                    "economics": {"unit_cost": 1000.0, "logistics_cost": 1000.0},
                    "note": "keep me",
                },
            )
        ],
    )

    payload = update_profile_economics_assumptions(
        store.database_path,
        "mosreg_market",
        "economics-assumptions",
        1,
        {
            "vat_mode": "vat_excluded",
            "vat_rate_percent": "20",
            "risk_reserve_percent": "5",
            "target_margin_percent": "15",
        },
    )

    assert payload["ok"] is True
    detail = get_tender_payload(store.database_path, "mosreg_market", "economics-assumptions")
    profile = detail["product_profiles"][0]
    assert profile["raw_payload"]["note"] == "keep me"
    assert profile["raw_payload"]["economics_assumptions"] == {
        "vat_mode": "vat_excluded",
        "vat_rate_percent": 20.0,
        "risk_reserve_percent": 5.0,
        "target_margin_percent": 15.0,
    }
    assert detail["economics"]["items"][0]["target_price"] == 16305.88
    assert detail["economics"]["supplier_cost"] == 13860.0
