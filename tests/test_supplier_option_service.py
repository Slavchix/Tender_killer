from __future__ import annotations

import pytest

from tender_killer.models import ProductProfile
from tender_killer.models import Tender
from tender_killer.storage import TenderStore
from tender_killer.supplier_option_service import add_profile_supplier_option
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
