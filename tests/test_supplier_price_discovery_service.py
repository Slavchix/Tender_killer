from __future__ import annotations

import pytest

from tender_killer.models import ProductProfile
from tender_killer.models import Tender
from tender_killer.storage import TenderStore
from tender_killer.supplier_price_discovery_service import run_profile_supplier_price_discovery
from tender_killer.tender_detail_service import get_tender_payload


def test_run_profile_supplier_price_discovery_stages_public_search_candidates(tmp_path) -> None:
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="supplier-price-discovery",
            url="https://market.mosreg.ru/Trade/ViewTrade/supplier-price-discovery",
            title="Paper tender",
            price=100000.0,
        )
    )
    store.upsert_product_profiles(
        "mosreg_market",
        "supplier-price-discovery",
        [
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="supplier-price-discovery",
                position_index=1,
                product_name="Office paper A4",
                quantity=10,
                unit="pack",
                raw_payload={
                    "supplier_search": {
                        "status": "ready",
                        "queries": [
                            {
                                "query": "office paper a4",
                                "kind": "normalized_name",
                                "priority": 1,
                                "quick_links": [
                                    {"label": "Google", "url": "https://www.google.com/search?q=office+paper+a4"},
                                    {"label": "Yandex", "url": "https://yandex.ru/search/?text=office+paper+a4"},
                                ],
                            }
                        ],
                    },
                    "note": "keep me",
                },
            )
        ],
    )

    payload = run_profile_supplier_price_discovery(
        store.database_path,
        "mosreg_market",
        "supplier-price-discovery",
        1,
    )

    assert payload == {
        "ok": True,
        "position_index": 1,
        "staged_count": 1,
        "supplier_discovery": {
            "status": "pending_review",
            "candidates": [
                {
                    "name": "Public search: office paper a4",
                    "url": "https://www.google.com/search?q=office+paper+a4",
                    "availability": "unknown",
                    "status": "candidate",
                    "source_query": "office paper a4",
                    "source_kind": "normalized_name",
                    "note": "Google public search result needs manual price review.",
                    "provider": "public_search",
                    "confidence": "needs_review",
                    "confidence_reasons": ["has_url", "has_source_query"],
                    "review_status": "pending",
                }
            ],
        },
    }
    detail = get_tender_payload(store.database_path, "mosreg_market", "supplier-price-discovery")
    profile = detail["product_profiles"][0]
    assert profile["profile_status"] == "matched"
    assert profile["raw_payload"]["note"] == "keep me"
    assert profile["raw_payload"]["supplier_discovery"] == payload["supplier_discovery"]
    assert "supplier_options" not in profile["raw_payload"]
    assert "economics" not in profile["raw_payload"]


def test_run_profile_supplier_price_discovery_skips_existing_candidates(tmp_path) -> None:
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="supplier-price-discovery-duplicates",
            url="https://market.mosreg.ru/Trade/ViewTrade/supplier-price-discovery-duplicates",
            title="Paper tender",
        )
    )
    store.upsert_product_profiles(
        "mosreg_market",
        "supplier-price-discovery-duplicates",
        [
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="supplier-price-discovery-duplicates",
                position_index=1,
                product_name="Office paper A4",
                raw_payload={
                    "supplier_search": {
                        "status": "ready",
                        "queries": [
                            {
                                "query": "office paper a4",
                                "kind": "normalized_name",
                                "priority": 1,
                                "quick_links": [
                                    {"label": "Google", "url": "https://www.google.com/search?q=office+paper+a4"},
                                ],
                            }
                        ],
                    },
                    "supplier_discovery": {
                        "status": "pending_review",
                        "candidates": [
                            {
                                "name": "Public search: office paper a4",
                                "url": "https://www.google.com/search?q=office+paper+a4",
                                "provider": "public_search",
                                "review_status": "pending",
                            }
                        ],
                    },
                },
            )
        ],
    )

    with pytest.raises(ValueError, match="No new supplier discovery candidates"):
        run_profile_supplier_price_discovery(
            store.database_path,
            "mosreg_market",
            "supplier-price-discovery-duplicates",
            1,
        )


def test_run_profile_supplier_price_discovery_rejects_missing_prepared_queries(tmp_path) -> None:
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="supplier-price-discovery-empty",
            url="https://market.mosreg.ru/Trade/ViewTrade/supplier-price-discovery-empty",
            title="Empty tender",
        )
    )
    store.upsert_product_profiles(
        "mosreg_market",
        "supplier-price-discovery-empty",
        [
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="supplier-price-discovery-empty",
                position_index=1,
                product_name="Office paper A4",
            )
        ],
    )

    with pytest.raises(ValueError, match="No prepared supplier search queries"):
        run_profile_supplier_price_discovery(
            store.database_path,
            "mosreg_market",
            "supplier-price-discovery-empty",
            1,
        )
