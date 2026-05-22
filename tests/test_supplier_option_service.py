from __future__ import annotations

import pytest

from tender_killer.models import ProductProfile
from tender_killer.models import Tender
from tender_killer.storage import TenderStore
from tender_killer.supplier_option_service import add_profile_supplier_option
from tender_killer.supplier_option_service import select_profile_supplier_option
from tender_killer.tender_detail_service import get_tender_payload


def test_add_profile_supplier_option_persists_candidate_and_preserves_raw_payload(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="supplier-input",
            url="https://market.mosreg.ru/Trade/ViewTrade/supplier-input",
            title="Paper tender",
            price=100000.0,
        )
    )
    store.upsert_product_profiles(
        "mosreg_market",
        "supplier-input",
        [
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="supplier-input",
                position_index=1,
                product_name="Office paper",
                quantity=10,
                unit="pack",
                raw_payload={"note": "keep me"},
            )
        ],
    )

    payload = add_profile_supplier_option(
        store.database_path,
        "mosreg_market",
        "supplier-input",
        1,
        {
            "name": " Paper shop ",
            "url": " https://example.com/paper ",
            "unit_price": "1 234,50",
            "availability": "in_stock",
            "status": "candidate",
            "note": " VAT included ",
            "ignored": "nope",
        },
    )

    assert payload["ok"] is True
    detail = get_tender_payload(store.database_path, "mosreg_market", "supplier-input")
    profile = detail["product_profiles"][0]
    assert profile["raw_payload"] == {
        "note": "keep me",
        "supplier_options": [
            {
                "name": "Paper shop",
                "url": "https://example.com/paper",
                "unit_price": 1234.5,
                "availability": "in_stock",
                "status": "candidate",
                "note": "VAT included",
            }
        ],
    }


def test_add_profile_supplier_option_rejects_empty_candidate(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="empty-supplier-input",
            url="https://market.mosreg.ru/Trade/ViewTrade/empty-supplier-input",
            title="Paper tender",
        )
    )
    store.upsert_product_profiles(
        "mosreg_market",
        "empty-supplier-input",
        [
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="empty-supplier-input",
                position_index=1,
                product_name="Office paper",
            )
        ],
    )

    with pytest.raises(ValueError, match="Supplier option is empty"):
        add_profile_supplier_option(
            store.database_path,
            "mosreg_market",
            "empty-supplier-input",
            1,
            {"availability": "unknown", "status": "candidate"},
        )


def test_select_profile_supplier_option_marks_selected_and_updates_unit_cost(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="supplier-select",
            url="https://market.mosreg.ru/Trade/ViewTrade/supplier-select",
            title="Paper tender",
            price=100000.0,
        )
    )
    store.upsert_product_profiles(
        "mosreg_market",
        "supplier-select",
        [
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="supplier-select",
                position_index=1,
                product_name="Office paper",
                quantity=10,
                unit="pack",
                raw_payload={
                    "supplier_options": [
                        {"name": "Expensive paper", "unit_price": 1200.0, "status": "candidate"},
                        {"name": "Best paper", "unit_price": 900.0, "status": "suitable"},
                    ]
                },
            )
        ],
    )

    payload = select_profile_supplier_option(
        store.database_path,
        "mosreg_market",
        "supplier-select",
        1,
        1,
    )

    assert payload["ok"] is True
    detail = get_tender_payload(store.database_path, "mosreg_market", "supplier-select")
    profile = detail["product_profiles"][0]
    assert profile["profile_status"] == "priced"
    assert profile["raw_payload"]["selected_supplier_option_index"] == 1
    assert profile["raw_payload"]["supplier_options"][0]["status"] == "candidate"
    assert profile["raw_payload"]["supplier_options"][1]["status"] == "selected"
    assert profile["raw_payload"]["economics"]["unit_cost"] == 900.0
    assert detail["economics"]["supplier_cost"] == 9000.0
