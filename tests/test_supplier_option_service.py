from __future__ import annotations

import pytest

from tender_killer.models import ProductProfile
from tender_killer.models import Tender
from tender_killer.storage import TenderStore
from tender_killer.supplier_option_service import apply_best_profile_supplier_option
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


def test_apply_best_profile_supplier_option_selects_lowest_eligible_price(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="supplier-auto-select",
            url="https://market.mosreg.ru/Trade/ViewTrade/supplier-auto-select",
            title="Paper tender",
            price=100000.0,
        )
    )
    store.upsert_product_profiles(
        "mosreg_market",
        "supplier-auto-select",
        [
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="supplier-auto-select",
                position_index=1,
                product_name="Office paper",
                quantity=10,
                unit="pack",
                raw_payload={
                    "supplier_options": [
                        {"name": "Expensive paper", "unit_price": 1200.0, "status": "candidate", "availability": "in_stock"},
                        {"name": "Rejected cheap", "unit_price": 500.0, "status": "rejected", "availability": "in_stock"},
                        {"name": "Better paper", "url": "https://example.com/better", "unit_price": 900.0, "status": "suitable", "availability": "on_request"},
                        {"name": "Unavailable cheap", "unit_price": 700.0, "status": "candidate", "availability": "not_available"},
                    ]
                },
            )
        ],
    )

    payload = apply_best_profile_supplier_option(
        store.database_path,
        "mosreg_market",
        "supplier-auto-select",
        1,
    )

    assert payload["ok"] is True
    assert payload["selected_index"] == 2
    assert payload["selection_reason"] == "auto_best"
    assert payload["price_source"] == {
        "source": "supplier_option",
        "selection": "auto_best",
        "option_index": 2,
        "supplier_name": "Better paper",
        "supplier_url": "https://example.com/better",
        "unit_price": 900.0,
        "availability": "on_request",
        "status": "suitable",
        "confidence": "medium",
    }
    detail = get_tender_payload(store.database_path, "mosreg_market", "supplier-auto-select")
    profile = detail["product_profiles"][0]
    assert profile["profile_status"] == "priced"
    assert profile["raw_payload"]["selected_supplier_option_index"] == 2
    assert profile["raw_payload"]["supplier_options"][2]["status"] == "selected"
    assert profile["raw_payload"]["supplier_options"][1]["status"] == "rejected"
    assert profile["raw_payload"]["economics"]["unit_cost"] == 900.0
    assert profile["raw_payload"]["economics_price_source"] == payload["price_source"]
    assert detail["economics"]["supplier_cost"] == 9000.0


def test_apply_best_profile_supplier_option_keeps_existing_manual_selection(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="supplier-manual-select",
            url="https://market.mosreg.ru/Trade/ViewTrade/supplier-manual-select",
            title="Paper tender",
            price=100000.0,
        )
    )
    store.upsert_product_profiles(
        "mosreg_market",
        "supplier-manual-select",
        [
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="supplier-manual-select",
                position_index=1,
                product_name="Office paper",
                quantity=10,
                unit="pack",
                raw_payload={
                    "selected_supplier_option_index": 0,
                    "supplier_options": [
                        {"name": "Trusted paper", "unit_price": 1100.0, "status": "selected", "availability": "in_stock"},
                        {"name": "Cheaper candidate", "unit_price": 900.0, "status": "candidate", "availability": "in_stock"},
                    ]
                },
            )
        ],
    )

    payload = apply_best_profile_supplier_option(
        store.database_path,
        "mosreg_market",
        "supplier-manual-select",
        1,
    )

    assert payload["selected_index"] == 0
    assert payload["selection_reason"] == "manual_selected"
    detail = get_tender_payload(store.database_path, "mosreg_market", "supplier-manual-select")
    profile = detail["product_profiles"][0]
    assert profile["raw_payload"]["selected_supplier_option_index"] == 0
    assert profile["raw_payload"]["supplier_options"][0]["status"] == "selected"
    assert profile["raw_payload"]["supplier_options"][1]["status"] == "candidate"
    assert profile["raw_payload"]["economics"]["unit_cost"] == 1100.0
