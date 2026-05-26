from __future__ import annotations

import pytest

from tender_killer import supplier_price_discovery_service as price_discovery
from tender_killer.models import ProductProfile
from tender_killer.models import Tender
from tender_killer.storage import TenderStore
from tender_killer.supplier_search_service import prepare_profile_supplier_search
from tender_killer.supplier_price_discovery_service import SchemaOrgProductCollector
from tender_killer.supplier_price_discovery_service import run_profile_supplier_price_discovery
from tender_killer.tender_detail_service import get_tender_payload


def test_schema_org_product_collector_extracts_public_offer_price() -> None:
    html = """
    <html>
      <head>
        <script type="application/ld+json">
          {
            "@context": "https://schema.org",
            "@type": "Product",
            "name": "Office paper A4 80 gsm",
            "url": "https://supplier.example/paper-a4",
            "offers": {
              "@type": "Offer",
              "priceSpecification": {
                "@type": "UnitPriceSpecification",
                "price": "925,50",
                "priceCurrency": "RUB",
                "valueAddedTaxIncluded": true
              },
              "availability": "https://schema.org/InStock",
              "shippingDetails": {
                "@type": "OfferShippingDetails",
                "description": "Delivery in Moscow"
              }
            }
          }
        </script>
      </head>
    </html>
    """
    collector = SchemaOrgProductCollector(fetch_text=lambda url: html)

    candidates = collector.collect(
        {
            "query": "office paper a4",
            "kind": "normalized_name",
            "quick_links": [
                {"label": "Supplier page", "url": "https://supplier.example/paper-a4"},
            ],
        }
    )

    assert candidates == [
        {
            "name": "Office paper A4 80 gsm",
            "url": "https://supplier.example/paper-a4",
            "unit_price": 925.5,
            "currency": "RUB",
            "vat_mode": "vat_included",
            "delivery_note": "Delivery in Moscow",
            "availability": "in_stock",
            "status": "candidate",
            "source_query": "office paper a4",
            "source_kind": "normalized_name",
            "note": "Schema.org product offer from https://supplier.example/paper-a4.",
            "provider": "schema_org_product",
        }
    ]


def test_schema_org_product_collector_skips_search_engine_links() -> None:
    calls: list[str] = []
    collector = SchemaOrgProductCollector(fetch_text=lambda url: calls.append(url) or "<html></html>")

    candidates = collector.collect(
        {
            "query": "office paper a4",
            "kind": "normalized_name",
            "quick_links": [
                {"label": "Google", "url": "https://www.google.com/search?q=office+paper+a4"},
                {"label": "Yandex", "url": "https://yandex.ru/search/?text=office+paper+a4"},
            ],
        }
    )

    assert candidates == []
    assert calls == []


def test_provider_catalog_collector_follows_matching_catalog_product_links() -> None:
    pages = {
        "https://petrovich.ru/search/?q=cement+mix": """
            <html>
              <body>
                <a href="/catalog/cement-25kg">Cement mix 25 kg</a>
              </body>
            </html>
        """,
        "https://petrovich.ru/catalog/cement-25kg": """
            <script type="application/ld+json">
            {
              "@context": "https://schema.org",
              "@type": "Product",
              "name": "Cement mix 25 kg",
              "url": "https://petrovich.ru/catalog/cement-25kg",
              "offers": {
                "@type": "Offer",
                "price": "418.90",
                "priceCurrency": "RUB",
                "availability": "https://schema.org/InStock"
              }
            }
            </script>
        """,
    }
    calls: list[str] = []
    collector = price_discovery.ProviderCatalogCollector(
        "petrovich",
        fetch_text=lambda url: calls.append(url) or pages.get(url, "<html></html>"),
    )

    result = collector.collect_with_diagnostics(
        {
            "query": "cement mix",
            "kind": "normalized_name",
            "quick_links": [
                {"label": "Google", "url": "https://www.google.com/search?q=cement+mix"},
                {
                    "label": "Petrovich",
                    "url": "https://petrovich.ru/search/?q=cement+mix",
                    "provider": "petrovich",
                    "link_kind": "catalog_search",
                    "preset_id": "petrovich_building_materials",
                },
                {
                    "label": "OfficeMag",
                    "url": "https://www.officemag.ru/search/?q=cement+mix",
                    "provider": "officemag",
                    "link_kind": "catalog_search",
                    "preset_id": "officemag_office_supplies",
                },
            ],
        }
    )

    assert calls == [
        "https://petrovich.ru/search/?q=cement+mix",
        "https://petrovich.ru/catalog/cement-25kg",
    ]
    assert result["diagnostics"] == {
        "provider": "catalog_petrovich",
        "queries_seen": 1,
        "links_seen": 3,
        "links_skipped": 2,
        "pages_fetched": 2,
        "candidates_found": 1,
        "errors": [],
    }
    assert result["candidates"] == [
        {
            "name": "Cement mix 25 kg",
            "url": "https://petrovich.ru/catalog/cement-25kg",
            "unit_price": 418.9,
            "currency": "RUB",
            "availability": "in_stock",
            "status": "candidate",
            "source_query": "cement mix",
            "source_kind": "normalized_name",
            "note": "Petrovich catalog offer from https://petrovich.ru/catalog/cement-25kg.",
            "provider": "petrovich",
        }
    ]


def test_provider_catalog_collector_extracts_officemag_visible_offer_without_schema_org() -> None:
    pages = {
        "https://www.officemag.ru/search/?q=office+paper+a4": """
            <html>
              <body>
                <a href="/catalog/goods/110532/">Office paper A4</a>
              </body>
            </html>
        """,
        "https://www.officemag.ru/catalog/goods/110532/": """
            <html>
              <body>
                <h1>Office paper A4 80 gsm, 500 sheets</h1>
                <p>449,83 руб.</p>
                <p>346,00 руб.</p>
                <p>Наличие на складе в Москве 16891 шт.</p>
              </body>
            </html>
        """,
    }
    calls: list[str] = []
    collector = price_discovery.ProviderCatalogCollector(
        "officemag",
        fetch_text=lambda url: calls.append(url) or pages.get(url, "<html></html>"),
    )

    result = collector.collect_with_diagnostics(
        {
            "query": "office paper a4",
            "kind": "normalized_name",
            "quick_links": [
                {
                    "label": "OfficeMag",
                    "url": "https://www.officemag.ru/search/?q=office+paper+a4",
                    "provider": "officemag",
                    "link_kind": "catalog_search",
                    "preset_id": "officemag_office_supplies",
                }
            ],
        }
    )

    assert calls == [
        "https://www.officemag.ru/search/?q=office+paper+a4",
        "https://www.officemag.ru/catalog/goods/110532/",
    ]
    assert result["diagnostics"]["candidates_found"] == 1
    assert result["candidates"] == [
        {
            "name": "Office paper A4 80 gsm, 500 sheets",
            "url": "https://www.officemag.ru/catalog/goods/110532/",
            "unit_price": 346.0,
            "currency": "RUB",
            "availability": "in_stock",
            "status": "candidate",
            "source_query": "office paper a4",
            "source_kind": "normalized_name",
            "note": "OfficeMag catalog visible offer from https://www.officemag.ru/catalog/goods/110532/.",
            "provider": "officemag",
        }
    ]


def test_provider_catalog_collector_extracts_vseinstrumenti_visible_offer_without_schema_org() -> None:
    pages = {
        "https://www.vseinstrumenti.ru/category/tsement-3432/": """
            <html>
              <body>
                <a href="/product/cement-movatex-5-kg-17134117/">Cement Movatex 5 kg</a>
              </body>
            </html>
        """,
        "https://www.vseinstrumenti.ru/product/cement-movatex-5-kg-17134117/": """
            <html>
              <body>
                <h1>Cement Movatex D0 M500, 5 kg</h1>
                <p>275 ₽</p>
                <p>В корзину</p>
                <p>Самовывоз: сегодня, бесплатно</p>
              </body>
            </html>
        """,
    }
    calls: list[str] = []
    collector = price_discovery.ProviderCatalogCollector(
        "vseinstrumenti",
        fetch_text=lambda url: calls.append(url) or pages.get(url, "<html></html>"),
    )

    result = collector.collect_with_diagnostics(
        {
            "query": "cement",
            "kind": "normalized_name",
            "quick_links": [
                {
                    "label": "Vseinstrumenti",
                    "url": "https://www.vseinstrumenti.ru/category/tsement-3432/",
                    "provider": "vseinstrumenti",
                    "link_kind": "catalog_search",
                    "preset_id": "vseinstrumenti_building_materials",
                }
            ],
        }
    )

    assert calls == [
        "https://www.vseinstrumenti.ru/category/tsement-3432/",
        "https://www.vseinstrumenti.ru/product/cement-movatex-5-kg-17134117/",
    ]
    assert result["diagnostics"]["candidates_found"] == 1
    assert result["candidates"][0]["name"] == "Cement Movatex D0 M500, 5 kg"
    assert result["candidates"][0]["unit_price"] == 275.0
    assert result["candidates"][0]["currency"] == "RUB"
    assert result["candidates"][0]["availability"] == "in_stock"
    assert result["candidates"][0]["provider"] == "vseinstrumenti"


def test_schema_org_product_collector_leaves_builtin_catalog_links_to_provider_collectors() -> None:
    calls: list[str] = []
    collector = SchemaOrgProductCollector(fetch_text=lambda url: calls.append(url) or "<html></html>")

    result = collector.collect_with_diagnostics(
        {
            "query": "cement mix",
            "kind": "normalized_name",
            "quick_links": [
                {
                    "label": "Petrovich",
                    "url": "https://petrovich.ru/search/?q=cement+mix",
                    "provider": "petrovich",
                    "link_kind": "catalog_search",
                    "preset_id": "petrovich_building_materials",
                }
            ],
        }
    )

    assert calls == []
    assert result == {
        "candidates": [],
        "diagnostics": {
            "provider": "schema_org_product",
            "queries_seen": 1,
            "links_seen": 1,
            "links_skipped": 1,
            "pages_fetched": 0,
            "candidates_found": 0,
            "errors": [],
        },
    }


def test_default_price_collectors_try_builtin_catalogs_before_schema_org_fallback() -> None:
    collectors = price_discovery.default_price_collectors(fetch_text=lambda url: "<html></html>")

    assert [collector.provider for collector in collectors] == [
        "catalog_officemag",
        "catalog_komus",
        "catalog_petrovich",
        "catalog_vseinstrumenti",
        "schema_org_product",
    ]


def test_run_profile_supplier_price_discovery_stages_schema_org_product_candidates(tmp_path) -> None:
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
                                    {"label": "Supplier page", "url": "https://supplier.example/paper-a4"},
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
        collectors=[
            SchemaOrgProductCollector(
                fetch_text=lambda url: """
                <script type="application/ld+json">
                {
                  "@context": "https://schema.org",
                  "@type": "Product",
                  "name": "Office paper A4 80 gsm",
                  "url": "https://supplier.example/paper-a4",
                  "offers": {
                    "@type": "Offer",
                    "price": "925.50",
                    "availability": "https://schema.org/InStock"
                  }
                }
                </script>
                """
            )
        ],
    )

    assert payload == {
        "ok": True,
        "position_index": 1,
        "staged_count": 1,
        "supplier_discovery": {
            "status": "pending_review",
            "collector_diagnostics": [
                {
                    "provider": "schema_org_product",
                    "queries_seen": 1,
                    "links_seen": 2,
                    "links_skipped": 1,
                    "pages_fetched": 1,
                    "candidates_found": 1,
                    "errors": [],
                }
            ],
            "candidates": [
                {
                    "name": "Office paper A4 80 gsm",
                    "url": "https://supplier.example/paper-a4",
                    "unit_price": 925.5,
                    "availability": "in_stock",
                    "status": "candidate",
                    "source_query": "office paper a4",
                    "source_kind": "normalized_name",
                    "note": "Schema.org product offer from https://supplier.example/paper-a4.",
                    "provider": "schema_org_product",
                    "confidence": "high",
                    "confidence_reasons": ["has_price", "has_url", "has_source_query"],
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


def test_prepared_catalog_link_feeds_schema_org_product_discovery(tmp_path) -> None:
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="supplier-price-discovery-catalog",
            url="https://market.mosreg.ru/Trade/ViewTrade/supplier-price-discovery-catalog",
            title="Paper tender",
        )
    )
    store.upsert_product_profiles(
        "mosreg_market",
        "supplier-price-discovery-catalog",
        [
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="supplier-price-discovery-catalog",
                position_index=1,
                product_name="Office paper A4",
                normalized_name="office paper a4",
                raw_payload={
                    "supplier_catalog_preset_ids": [],
                    "supplier_catalogs": [
                        {
                            "label": "Supplier catalog",
                            "provider": "supplier_example",
                            "url_template": "https://supplier.example/search?q={query}",
                        }
                    ]
                },
            )
        ],
    )
    prepare_profile_supplier_search(
        store.database_path,
        "mosreg_market",
        "supplier-price-discovery-catalog",
        1,
    )
    pages = {
        "https://supplier.example/search?q=office+paper+a4": """
            <script type="application/ld+json">
            {
              "@context": "https://schema.org",
              "@type": "ItemList",
              "itemListElement": [
                {
                  "@type": "ListItem",
                  "item": {
                    "@type": "Product",
                    "name": "Office paper A4 80 gsm",
                    "url": "https://supplier.example/catalog/paper-a4"
                  }
                }
              ]
            }
            </script>
        """,
        "https://supplier.example/catalog/paper-a4": """
            <script type="application/ld+json">
            {
              "@context": "https://schema.org",
              "@type": "Product",
              "name": "Office paper A4 80 gsm",
              "url": "https://supplier.example/catalog/paper-a4",
              "offers": {
                "@type": "Offer",
                "price": "925",
                "priceCurrency": "RUB",
                "availability": "https://schema.org/InStock"
              }
            }
            </script>
        """,
    }
    calls: list[str] = []

    payload = run_profile_supplier_price_discovery(
        store.database_path,
        "mosreg_market",
        "supplier-price-discovery-catalog",
        1,
        collectors=[
            SchemaOrgProductCollector(
                fetch_text=lambda url: calls.append(url) or pages.get(url, "<html></html>")
            )
        ],
    )

    assert calls == [
        "https://supplier.example/search?q=office+paper+a4",
        "https://supplier.example/catalog/paper-a4",
    ]
    assert payload["supplier_discovery"]["collector_diagnostics"] == [
        {
            "provider": "schema_org_product",
            "queries_seen": 1,
            "links_seen": 3,
            "links_skipped": 2,
            "pages_fetched": 2,
            "candidates_found": 1,
            "errors": [],
        }
    ]
    assert payload["supplier_discovery"]["candidates"][0]["url"] == "https://supplier.example/catalog/paper-a4"
    assert payload["supplier_discovery"]["candidates"][0]["unit_price"] == 925.0
    assert payload["supplier_discovery"]["candidates"][0]["currency"] == "RUB"
    assert payload["supplier_discovery"]["candidates"][0]["confidence"] == "high"


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
                                    {"label": "Supplier page", "url": "https://supplier.example/paper-a4"},
                                ],
                            }
                        ],
                    },
                    "supplier_discovery": {
                        "status": "pending_review",
                        "candidates": [
                            {
                                "name": "Office paper",
                                "url": "https://supplier.example/paper-a4",
                                "provider": "schema_org_product",
                                "review_status": "pending",
                            }
                        ],
                    },
                },
            )
        ],
    )
    calls: list[str] = []

    with pytest.raises(ValueError, match="Новых кандидатов поставщиков не найдено"):
        run_profile_supplier_price_discovery(
            store.database_path,
            "mosreg_market",
            "supplier-price-discovery-duplicates",
            1,
            collectors=[
                SchemaOrgProductCollector(
                    fetch_text=lambda url: calls.append(url)
                    or """
                       <script type="application/ld+json">
                       {
                         "@type":"Product",
                         "name":"Office paper",
                         "url":"https://supplier.example/paper-a4",
                         "offers":{"price":"925"}
                       }
                       </script>
                       """
                )
            ],
        )
    assert calls == ["https://supplier.example/paper-a4"]


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

    with pytest.raises(ValueError, match="Сначала подготовь поиск поставщиков"):
        run_profile_supplier_price_discovery(
            store.database_path,
            "mosreg_market",
            "supplier-price-discovery-empty",
            1,
        )
