from __future__ import annotations

import pytest

from tender_killer.models import ProductProfile
from tender_killer.models import Tender
from tender_killer.storage import TenderStore
from tender_killer.supplier_discovery_service import import_profile_supplier_candidate
from tender_killer.supplier_discovery_service import stage_profile_supplier_candidates
from tender_killer.tender_detail_service import get_tender_payload


def test_stage_profile_supplier_candidates_persists_review_queue(tmp_path) -> None:
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="supplier-discovery",
            url="https://market.mosreg.ru/Trade/ViewTrade/supplier-discovery",
            title="Paper tender",
            price=100000.0,
        )
    )
    store.upsert_product_profiles(
        "mosreg_market",
        "supplier-discovery",
        [
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="supplier-discovery",
                position_index=1,
                product_name="Office paper",
                raw_payload={"note": "keep me"},
            )
        ],
    )

    payload = stage_profile_supplier_candidates(
        store.database_path,
        "mosreg_market",
        "supplier-discovery",
        1,
        [
            {
                "name": " Paper shop ",
                "url": " https://example.com/paper ",
                "unit_price": "900,50",
                "availability": "in_stock",
                "status": "candidate",
                "provider": " Public catalog ",
                "currency": " rub ",
                "vat_mode": "vat_included",
                "delivery_note": " Delivery in Moscow ",
                "source_query": "office paper a4",
                "source_kind": "normalized_name",
                "note": " VAT included ",
                "ignored": "drop",
            }
        ],
    )

    assert payload == {
        "ok": True,
        "position_index": 1,
        "staged_count": 1,
        "supplier_discovery": {
            "status": "pending_review",
            "candidates": [
                {
                    "name": "Paper shop",
                    "url": "https://example.com/paper",
                    "unit_price": 900.5,
                    "availability": "in_stock",
                    "status": "candidate",
                    "provider": "public_catalog",
                    "currency": "rub",
                    "vat_mode": "vat_included",
                    "delivery_note": "Delivery in Moscow",
                    "source_query": "office paper a4",
                    "source_kind": "normalized_name",
                    "note": "VAT included",
                    "confidence": "high",
                    "confidence_reasons": ["has_price", "has_url", "has_source_query"],
                    "review_status": "pending",
                }
            ],
        },
    }
    detail = get_tender_payload(store.database_path, "mosreg_market", "supplier-discovery")
    profile = detail["product_profiles"][0]
    assert profile["profile_status"] == "matched"
    assert profile["raw_payload"]["note"] == "keep me"
    assert profile["raw_payload"]["supplier_discovery"] == payload["supplier_discovery"]
    assert "economics" not in profile["raw_payload"]


def test_import_profile_supplier_candidate_moves_candidate_to_options_without_pricing(tmp_path) -> None:
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="supplier-discovery-import",
            url="https://market.mosreg.ru/Trade/ViewTrade/supplier-discovery-import",
            title="Paper tender",
            price=100000.0,
        )
    )
    store.upsert_product_profiles(
        "mosreg_market",
        "supplier-discovery-import",
        [
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="supplier-discovery-import",
                position_index=1,
                product_name="Office paper",
                quantity=10,
                unit="pack",
                raw_payload={
                    "supplier_options": [
                        {"name": "Existing", "unit_price": 1200.0, "status": "candidate"},
                    ],
                    "supplier_discovery": {
                        "status": "pending_review",
                        "candidates": [
                            {
                                "name": "Paper shop",
                                "url": "https://example.com/paper",
                                "unit_price": 900.0,
                                "availability": "in_stock",
                                "status": "candidate",
                                "provider": "public_catalog",
                                "confidence": "high",
                                "confidence_reasons": ["has_price", "has_url", "has_source_query"],
                                "currency": "rub",
                                "vat_mode": "vat_included",
                                "delivery_note": "Delivery in Moscow",
                                "source_query": "office paper a4",
                                "source_kind": "normalized_name",
                                "review_status": "pending",
                            }
                        ],
                    },
                },
            )
        ],
    )

    payload = import_profile_supplier_candidate(
        store.database_path,
        "mosreg_market",
        "supplier-discovery-import",
        1,
        0,
    )

    assert payload == {"ok": True, "position_index": 1, "candidate_index": 0, "supplier_option_index": 1}
    detail = get_tender_payload(store.database_path, "mosreg_market", "supplier-discovery-import")
    profile = detail["product_profiles"][0]
    assert profile["profile_status"] == "matched"
    assert profile["raw_payload"]["supplier_options"] == [
        {"name": "Existing", "unit_price": 1200.0, "status": "candidate"},
        {
            "name": "Paper shop",
            "url": "https://example.com/paper",
            "unit_price": 900.0,
            "availability": "in_stock",
            "status": "candidate",
            "provider": "public_catalog",
            "confidence": "high",
            "currency": "rub",
            "vat_mode": "vat_included",
            "delivery_note": "Delivery in Moscow",
            "source_query": "office paper a4",
            "source_kind": "normalized_name",
        },
    ]
    assert profile["raw_payload"]["supplier_discovery"]["candidates"][0]["review_status"] == "imported"
    assert profile["raw_payload"]["supplier_discovery"]["candidates"][0]["supplier_option_index"] == 1
    assert "economics" not in profile["raw_payload"]
    assert detail["economics"]["status"] == "needs_costs"


def test_stage_profile_supplier_candidates_rejects_empty_candidates(tmp_path) -> None:
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="empty-discovery",
            url="https://market.mosreg.ru/Trade/ViewTrade/empty-discovery",
            title="Empty tender",
        )
    )
    store.upsert_product_profiles(
        "mosreg_market",
        "empty-discovery",
        [
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="empty-discovery",
                position_index=1,
                product_name="Office paper",
            )
        ],
    )

    with pytest.raises(ValueError, match="No supplier discovery candidates"):
        stage_profile_supplier_candidates(
            store.database_path,
            "mosreg_market",
            "empty-discovery",
            1,
            [{"availability": "unknown"}],
        )
