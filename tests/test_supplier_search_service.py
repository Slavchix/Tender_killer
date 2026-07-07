from __future__ import annotations

from urllib.parse import quote_plus

import pytest

from tender_killer.models import ProductProfile
from tender_killer.models import Tender
from tender_killer.storage import TenderStore
from tender_killer.supplier_search_service import build_best_supplier_product_link
from tender_killer.supplier_search_service import build_supplier_search_intent
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


def query_contract(query: dict[str, object]) -> dict[str, object]:
    return {
        "query": query["query"],
        "kind": query["kind"],
        "priority": query["priority"],
        "quick_links": query["quick_links"],
    }


def query_contracts(queries: list[dict[str, object]]) -> list[dict[str, object]]:
    return [query_contract(query) for query in queries]


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

    assert query_contracts(queries) == [
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
    assert all(isinstance(query["query_score"], int) for query in queries)
    assert all(query["query_quality"] in {"good", "review", "weak"} for query in queries)


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


def test_build_supplier_search_queries_routes_hygiene_goods_to_office_catalogs() -> None:
    queries = build_supplier_search_queries(
        {
            "product_name": "Дозатор для жидкого мыла LAIMA BASIC, 0,5 л, зеркальный",
            "normalized_name": "дозатор жидкого мыла laima basic нержавеющая сталь зеркальный",
            "category": "Инвентарь для санузлов",
        }
    )

    provider_links = [
        link.get("provider")
        for link in queries[0]["quick_links"]
        if link.get("link_kind") == "catalog_search"
    ]
    assert provider_links == ["officemag", "komus"]


def test_build_supplier_search_queries_prefers_flexible_water_connector_terms() -> None:
    queries = build_supplier_search_queries(
        {
            "product_name": "Гибкая подводка 60 см",
            "normalized_name": "Гибкая подводка 60 см",
            "category": "Краны, клапаны для раковин, моек, биде, унитазов, ванн и аналогичная арматура",
        }
    )

    assert [query["query"] for query in queries] == [
        "подводка гибкая для воды 60 см",
        "Гибкая подводка 60 см",
        "подводка гибкая для смесителя 60 см",
    ]
    assert not any("Краны, клапаны" in query["query"] for query in queries)
    first_provider_links = [
        link
        for link in queries[0]["quick_links"]
        if link.get("link_kind") == "catalog_search"
    ]
    assert [link["provider"] for link in first_provider_links] == ["vseinstrumenti", "lemanapro"]
    assert first_provider_links[0]["url"] == (
        "https://www.vseinstrumenti.ru/search/?what="
        "%D0%BF%D0%BE%D0%B4%D0%B2%D0%BE%D0%B4%D0%BA%D0%B0+%D0%B3%D0%B8%D0%B1%D0%BA%D0%B0%D1%8F+"
        "%D0%B4%D0%BB%D1%8F+%D0%B2%D0%BE%D0%B4%D1%8B+60+%D1%81%D0%BC"
    )
    assert queries[0]["query_score"] > queries[1]["query_score"]
    assert queries[0]["query_quality"] == "good"


def test_build_supplier_search_intent_keeps_category_out_of_product_query() -> None:
    intent = build_supplier_search_intent(
        {
            "product_name": "Гибкая подводка 60 см",
            "normalized_name": "Гибкая подводка 60 см",
            "category": "Краны, клапаны для раковин, моек, биде, унитазов, ванн и аналогичная арматура",
        }
    )

    assert intent["family"] == "flexible_water_connector"
    assert intent["best_query"] == "подводка гибкая для воды 60 см"
    assert "Краны" not in intent["product_text"]
    assert "Краны" in intent["routing_text"]
    assert intent["attributes"]["length"] == "60 см"
    assert intent["required_terms"] == ["подводка", "гибкая"]


def test_build_supplier_search_intent_ranks_query_candidates_and_marks_routing_noise() -> None:
    intent = build_supplier_search_intent(
        {
            "product_name": "Гибкая подводка 60 см",
            "normalized_name": "Гибкая подводка 60 см",
            "category": "Краны, клапаны для раковин, моек, биде, унитазов, ванн и аналогичная арматура",
        }
    )

    candidates = intent["query_candidates"]

    assert candidates[0]["query"] == "подводка гибкая для воды 60 см"
    assert candidates[0]["query_score"] >= candidates[1]["query_score"]
    assert candidates[0]["query_quality"] == "good"
    assert "клапаны" in intent["noise_terms"]
    assert "раковин" in intent["noise_terms"]
    assert not any("Краны" in candidate["query"] for candidate in candidates)


def test_build_supplier_search_queries_do_not_use_category_as_query_text() -> None:
    queries = build_supplier_search_queries(
        {
            "product_name": "Болт стальной шестигранный M16x80 ГОСТ 7798-70",
            "normalized_name": "Болт стальной шестигранный M16x80 ГОСТ 7798-70",
            "category": "Крепежные изделия и аналогичные товары",
        }
    )

    assert not any("Крепежные изделия" in query["query"] for query in queries)
    assert queries[0]["query"] == "Болт стальной шестигранный M16x80 ГОСТ 7798-70"
    assert queries[0]["query_score"] >= 60
    assert queries[0]["query_quality"] == "good"


def test_build_best_supplier_product_link_prefers_highest_scored_catalog_query() -> None:
    supplier_search = {
        "status": "ready",
        "queries": [
            {
                "query": "крепление для унитаза набор риф",
                "query_score": 20,
                "quick_links": [
                    {
                        "label": "ВсеИнструменты",
                        "provider": "vseinstrumenti",
                        "url": "https://www.vseinstrumenti.ru/search/?what=wrong",
                        "link_kind": "catalog_search",
                    }
                ],
            },
            {
                "query": "гибкая подводка 60 см",
                "query_score": 90,
                "quick_links": [
                    {
                        "label": "ВсеИнструменты",
                        "provider": "vseinstrumenti",
                        "url": "https://www.vseinstrumenti.ru/search/?what=right",
                        "link_kind": "catalog_search",
                    }
                ],
            },
        ],
    }

    link = build_best_supplier_product_link(supplier_search, fetch_text=None)

    assert link is not None
    assert link["source_query"] == "гибкая подводка 60 см"
    assert link["search_url"] == "https://www.vseinstrumenti.ru/search/?what=right"


def test_build_best_supplier_product_link_fetches_one_catalog_and_picks_best_product() -> None:
    queries = build_supplier_search_queries(
        {
            "product_name": "Office paper A4 80 g/m2",
            "normalized_name": "office paper a4",
            "okpd2": "17.12.14.110",
        }
    )
    calls: list[str] = []

    def fake_fetch(url: str) -> str:
        calls.append(url)
        return """
        <html>
          <body>
            <a href="/catalog/goods/000001/">Random envelopes C5</a>
            <a href="/catalog/goods/123456/">Office paper A4 80 g/m2 500 sheets</a>
          </body>
        </html>
        """

    link = build_best_supplier_product_link({"status": "ready", "queries": queries}, fetch_text=fake_fetch)

    assert calls == ["https://www.officemag.ru/search/?q=office+paper+a4"]
    assert link is not None
    assert link["status"] == "product_link"
    assert link["provider"] == "officemag"
    assert link["label"] == "OfficeMag"
    assert link["title"] == "Office paper A4 80 g/m2 500 sheets"
    assert link["url"] == "https://www.officemag.ru/catalog/goods/123456/"
    assert link["search_url"] == "https://www.officemag.ru/search/?q=office+paper+a4"
    assert link["source_query"] == "office paper a4"
    assert link["match_score"] > 0


def test_build_best_supplier_product_link_falls_back_to_search_when_catalog_blocks() -> None:
    queries = build_supplier_search_queries(
        {
            "product_name": "Office paper A4 80 g/m2",
            "normalized_name": "office paper a4",
            "okpd2": "17.12.14.110",
        }
    )
    calls: list[str] = []

    def fake_fetch(url: str) -> str:
        calls.append(url)
        raise RuntimeError("HTTP 403 access blocked")

    link = build_best_supplier_product_link({"status": "ready", "queries": queries}, fetch_text=fake_fetch)

    assert calls == ["https://www.officemag.ru/search/?q=office+paper+a4"]
    assert link == {
        "status": "fallback_search",
        "provider": "officemag",
        "label": "OfficeMag",
        "title": "Открыть поиск в OfficeMag",
        "url": "https://www.officemag.ru/search/?q=office+paper+a4",
        "search_url": "https://www.officemag.ru/search/?q=office+paper+a4",
        "source_query": "office paper a4",
        "message": "Сайт не дал выбрать карточку автоматически. Открой поиск вручную.",
    }


def test_build_supplier_search_queries_routes_building_materials_to_building_catalogs() -> None:
    queries = build_supplier_search_queries(
        {
            "product_name": "Cement M500 50 kg",
            "normalized_name": "cement m500 50 kg",
            "okpd2": "23.51.12.110",
        }
    )

    provider_links = [
        link.get("provider")
        for link in queries[0]["quick_links"]
        if link.get("link_kind") == "catalog_search"
    ]
    assert provider_links == ["petrovich", "vseinstrumenti", "lemanapro"]
    assert "officemag" not in provider_links
    assert "komus" not in provider_links


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


def test_build_supplier_search_queries_adds_constraint_hint_for_generic_catalog_items() -> None:
    queries = build_supplier_search_queries(
        {
            "product_name": "Supply of reinforced self drilling screw FastenPro 4.2x19 zinc pack 200 pcs",
            "normalized_name": "reinforced self drilling screw FastenPro 4.2x19 zinc pack 200 pcs",
        }
    )

    assert [query["query"] for query in queries] == [
        "reinforced self drilling screw FastenPro 4.2x19 zinc pack 200 pcs",
        "reinforced self drilling screw fastenpro zinc 4.2x19 200 pcs",
    ]
    assert queries[1]["kind"] == "catalog_hint"


def test_build_supplier_search_queries_adds_weight_and_volume_constraint_hints() -> None:
    screw_queries = build_supplier_search_queries(
        {
            "product_name": "Supply of Gigant zinc self drilling screws 1 kg",
            "normalized_name": "self drilling screws",
        }
    )
    paint_queries = build_supplier_search_queries(
        {
            "product_name": "Supply of white acrylic paint 5 l",
            "normalized_name": "paint",
        }
    )

    assert [query["query"] for query in screw_queries] == [
        "self drilling screws",
        "self drilling screws gigant zinc 1 kg",
    ]
    assert [query["query"] for query in paint_queries] == [
        "paint",
        "paint white acrylic 5 l",
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

    assert payload["ok"] is True
    assert payload["position_index"] == 1
    assert payload["supplier_search"]["status"] == "ready"
    assert payload["supplier_search"]["catalog_providers"] == ["officemag", "komus"]
    assert payload["supplier_search"]["search_intent"]["best_query"] == "office paper a4"
    assert query_contracts(payload["supplier_search"]["queries"]) == [
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
    ]
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
