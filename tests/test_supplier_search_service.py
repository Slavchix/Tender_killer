from __future__ import annotations

from urllib.parse import quote_plus

import pytest

from tender_killer.models import ProductProfile
from tender_killer.models import Tender
from tender_killer.storage import TenderStore
from tender_killer.supplier_search_service import build_supplier_search_links
from tender_killer.supplier_search_service import build_supplier_search_queries
from tender_killer.supplier_search_service import prepare_profile_supplier_search
from tender_killer.tender_detail_service import get_tender_payload


def expected_office_links(query: str) -> list[dict[str, str]]:
    encoded = quote_plus(query)
    return [
        {"label": "Google", "url": f"https://www.google.com/search?q={encoded}"},
        {"label": "Yandex", "url": f"https://yandex.ru/search/?text={encoded}"},
        {
            "label": "OfficeMag",
            "url": f"https://www.officemag.ru/search/?q={encoded}",
            "provider": "officemag",
            "link_kind": "catalog_search",
            "preset_id": "officemag_office_supplies",
        },
        {
            "label": "Komus",
            "url": f"https://www.komus.ru/search/?text={encoded}",
            "provider": "komus",
            "link_kind": "catalog_search",
            "preset_id": "komus_office_supplies",
        },
    ]


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
        {
            "query": "office paper a4",
            "kind": "normalized_name",
            "priority": 1,
            "quick_links": expected_office_links("office paper a4"),
        },
        {
            "query": "office paper",
            "kind": "search_phrase",
            "priority": 2,
            "quick_links": expected_office_links("office paper"),
        },
        {
            "query": "A4 paper",
            "kind": "search_phrase",
            "priority": 3,
            "quick_links": expected_office_links("A4 paper"),
        },
        {
            "query": "17.12.14.110 office paper a4",
            "kind": "classifier",
            "priority": 4,
            "quick_links": expected_office_links("17.12.14.110 office paper a4"),
        },
    ]


def test_build_supplier_search_links_encodes_query_for_manual_search() -> None:
    assert build_supplier_search_links("бумага А4 80 г/м2") == [
        {
            "label": "Google",
            "url": "https://www.google.com/search?q=%D0%B1%D1%83%D0%BC%D0%B0%D0%B3%D0%B0+%D0%904+80+%D0%B3%2F%D0%BC2",
        },
        {
            "label": "Yandex",
            "url": "https://yandex.ru/search/?text=%D0%B1%D1%83%D0%BC%D0%B0%D0%B3%D0%B0+%D0%904+80+%D0%B3%2F%D0%BC2",
        },
    ]


def test_build_supplier_search_queries_includes_catalog_provider_links_from_payload() -> None:
    queries = build_supplier_search_queries(
        {
            "normalized_name": "office paper a4",
            "raw_payload": {
                "supplier_catalogs": [
                    {
                        "label": "Supplier catalog",
                        "provider": "supplier_example",
                        "url_template": "https://supplier.example/search?q={query}",
                    }
                ]
            },
        }
    )

    assert queries[0]["quick_links"] == [
        {"label": "Google", "url": "https://www.google.com/search?q=office+paper+a4"},
        {"label": "Yandex", "url": "https://yandex.ru/search/?text=office+paper+a4"},
        {
            "label": "Supplier catalog",
            "url": "https://supplier.example/search?q=office+paper+a4",
            "provider": "supplier_example",
            "link_kind": "catalog_search",
        },
        {
            "label": "OfficeMag",
            "url": "https://www.officemag.ru/search/?q=office+paper+a4",
            "provider": "officemag",
            "link_kind": "catalog_search",
            "preset_id": "officemag_office_supplies",
        },
        {
            "label": "Komus",
            "url": "https://www.komus.ru/search/?text=office+paper+a4",
            "provider": "komus",
            "link_kind": "catalog_search",
            "preset_id": "komus_office_supplies",
        },
    ]


def test_build_supplier_search_queries_includes_matching_catalog_presets() -> None:
    queries = build_supplier_search_queries(
        {
            "product_name": "Office paper A4 80 g/m2",
            "normalized_name": "office paper a4",
            "okpd2": "17.12.14.110",
        }
    )

    assert queries[0]["quick_links"] == expected_office_links("office paper a4")


def test_build_supplier_search_queries_expands_real_russian_office_paper_terms() -> None:
    queries = build_supplier_search_queries(
        {
            "product_name": "Бумага для офисной техники",
            "normalized_name": "Бумага для офисной техники",
            "search_phrases": ["Бумага для офисной техники"],
            "okpd2": "17.12.14.110",
        }
    )

    assert [query["query"] for query in queries] == [
        "Бумага для офисной техники",
        "бумага офисная белая а4 80 г/м2 500 листов",
        "бумага офисная а4 80 г/м2 500 листов",
        "бумага офисная",
        "бумага офисная а4",
        "бумага для принтера",
        "17.12.14.110 Бумага для офисной техники",
    ]
    office_links = [
        link
        for query in queries
        for link in query["quick_links"]
        if link.get("provider") == "officemag"
    ]
    assert [link["url"] for link in office_links] == [
        "https://www.officemag.ru/search/?q=%D0%91%D1%83%D0%BC%D0%B0%D0%B3%D0%B0+%D0%B4%D0%BB%D1%8F+%D0%BE%D1%84%D0%B8%D1%81%D0%BD%D0%BE%D0%B9+%D1%82%D0%B5%D1%85%D0%BD%D0%B8%D0%BA%D0%B8",
        "https://www.officemag.ru/search/?q=%D0%B1%D1%83%D0%BC%D0%B0%D0%B3%D0%B0+%D0%BE%D1%84%D0%B8%D1%81%D0%BD%D0%B0%D1%8F+%D0%B1%D0%B5%D0%BB%D0%B0%D1%8F+%D0%B04+80+%D0%B3%2F%D0%BC2+500+%D0%BB%D0%B8%D1%81%D1%82%D0%BE%D0%B2",
        "https://www.officemag.ru/search/?q=%D0%B1%D1%83%D0%BC%D0%B0%D0%B3%D0%B0+%D0%BE%D1%84%D0%B8%D1%81%D0%BD%D0%B0%D1%8F+%D0%B04+80+%D0%B3%2F%D0%BC2+500+%D0%BB%D0%B8%D1%81%D1%82%D0%BE%D0%B2",
        "https://www.officemag.ru/search/?q=%D0%B1%D1%83%D0%BC%D0%B0%D0%B3%D0%B0+%D0%BE%D1%84%D0%B8%D1%81%D0%BD%D0%B0%D1%8F",
        "https://www.officemag.ru/search/?q=%D0%B1%D1%83%D0%BC%D0%B0%D0%B3%D0%B0+%D0%BE%D1%84%D0%B8%D1%81%D0%BD%D0%B0%D1%8F+%D0%B04",
        "https://www.officemag.ru/search/?q=%D0%B1%D1%83%D0%BC%D0%B0%D0%B3%D0%B0+%D0%B4%D0%BB%D1%8F+%D0%BF%D1%80%D0%B8%D0%BD%D1%82%D0%B5%D1%80%D0%B0",
        "https://www.officemag.ru/search/?q=17.12.14.110+%D0%91%D1%83%D0%BC%D0%B0%D0%B3%D0%B0+%D0%B4%D0%BB%D1%8F+%D0%BE%D1%84%D0%B8%D1%81%D0%BD%D0%BE%D0%B9+%D1%82%D0%B5%D1%85%D0%BD%D0%B8%D0%BA%D0%B8",
    ]


def test_build_supplier_search_queries_expands_real_russian_cartridge_terms() -> None:
    product_name = "Картридж однокомпонентный лазерного принтера"

    queries = build_supplier_search_queries(
        {
            "product_name": product_name,
            "normalized_name": product_name,
            "search_phrases": [product_name],
            "okpd2": "28.23.25.000",
        }
    )

    assert [query["query"] for query in queries] == [
        product_name,
        "картридж лазерный",
        "картридж для принтера",
        f"28.23.25.000 {product_name}",
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
                {
                    "query": "office paper a4",
                    "kind": "normalized_name",
                    "priority": 1,
                    "quick_links": expected_office_links("office paper a4"),
                },
                {
                    "query": "office paper",
                    "kind": "search_phrase",
                    "priority": 2,
                    "quick_links": expected_office_links("office paper"),
                },
                {
                    "query": "17.12.14.110 office paper a4",
                    "kind": "classifier",
                    "priority": 3,
                    "quick_links": expected_office_links("17.12.14.110 office paper a4"),
                },
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
