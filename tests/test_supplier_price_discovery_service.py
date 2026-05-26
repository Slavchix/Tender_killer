from __future__ import annotations

import pytest

from tender_killer.models import ProductProfile
from tender_killer.models import Tender
from tender_killer.storage import TenderStore
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
