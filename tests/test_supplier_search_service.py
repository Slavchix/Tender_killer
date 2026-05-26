from __future__ import annotations

import pytest

from tender_killer.models import ProductProfile
from tender_killer.models import Tender
from tender_killer.storage import TenderStore
from tender_killer.supplier_search_service import build_supplier_search_queries
from tender_killer.supplier_search_service import prepare_profile_supplier_search
from tender_killer.tender_detail_service import get_tender_payload


def test_build_supplier_search_queries_prioritizes_profile_terms() -> None:
    queries = build_supplier_search_queries(
        {
            "product_name": "Office paper A4 80 g/m2",
            "normalized_name": "office paper a4",
            "search_phrases": ["office paper", "A4 paper", "office paper"],
            "okpd2": "17.12.14.110",
            "classifier_code": "17.12.14.110",
        }
    )

    assert queries == [
        {"query": "office paper a4", "kind": "normalized_name", "priority": 1},
        {"query": "office paper", "kind": "search_phrase", "priority": 2},
        {"query": "A4 paper", "kind": "search_phrase", "priority": 3},
        {"query": "17.12.14.110 office paper a4", "kind": "classifier", "priority": 4},
    ]


def test_prepare_profile_supplier_search_persists_queries_and_preserves_options(tmp_path) -> None:
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="supplier-search",
            url="https://market.mosreg.ru/Trade/ViewTrade/supplier-search",
            title="Paper tender",
            price=100000.0,
        )
    )
    store.upsert_product_profiles(
        "mosreg_market",
        "supplier-search",
        [
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="supplier-search",
                position_index=1,
                product_name="Office paper A4 80 g/m2",
                normalized_name="office paper a4",
                search_phrases=["office paper"],
                okpd2="17.12.14.110",
                raw_payload={
                    "supplier_options": [
                        {"name": "Paper shop", "unit_price": 1200.0, "status": "candidate"},
                    ],
                    "note": "keep me",
                },
            )
        ],
    )

    payload = prepare_profile_supplier_search(
        store.database_path,
        "mosreg_market",
        "supplier-search",
        1,
    )

    assert payload == {
        "ok": True,
        "position_index": 1,
        "supplier_search": {
            "status": "ready",
            "queries": [
                {"query": "office paper a4", "kind": "normalized_name", "priority": 1},
                {"query": "office paper", "kind": "search_phrase", "priority": 2},
                {"query": "17.12.14.110 office paper a4", "kind": "classifier", "priority": 3},
            ],
        },
    }
    detail = get_tender_payload(store.database_path, "mosreg_market", "supplier-search")
    profile = detail["product_profiles"][0]
    assert profile["profile_status"] == "searching"
    assert profile["raw_payload"]["supplier_search"] == payload["supplier_search"]
    assert profile["raw_payload"]["supplier_options"] == [
        {"name": "Paper shop", "unit_price": 1200.0, "status": "candidate"},
    ]
    assert profile["raw_payload"]["note"] == "keep me"


def test_prepare_profile_supplier_search_rejects_profiles_without_terms(tmp_path) -> None:
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="empty-supplier-search",
            url="https://market.mosreg.ru/Trade/ViewTrade/empty-supplier-search",
            title="Empty tender",
        )
    )
    store.upsert_product_profiles(
        "mosreg_market",
        "empty-supplier-search",
        [
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="empty-supplier-search",
                position_index=1,
                product_name=" ",
            )
        ],
    )

    with pytest.raises(ValueError, match="No searchable product terms"):
        prepare_profile_supplier_search(store.database_path, "mosreg_market", "empty-supplier-search", 1)
