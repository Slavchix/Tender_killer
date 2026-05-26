from urllib.parse import quote

from tender_killer.api_handlers import handle_get_request, handle_post_request
from tender_killer.models import ProductProfile, Tender
from tender_killer.storage import TenderStore


def _store_with_tender(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="3668200",
            url="https://market.mosreg.ru/Trade/ViewTrade/3668200",
            title="Paper supply",
            customer="School",
            region="Moscow Oblast",
            price=120000.0,
            status="Reception of proposals",
            raw_payload={"SourcePlatformName": "ЕАСУЗ 44"},
        )
    )
    return store


def test_handle_get_request_returns_health_payload(tmp_path) -> None:
    response = handle_get_request(tmp_path / "tenders.sqlite", "/api/health", {})

    assert response.kind == "json"
    assert response.status == 200
    assert response.payload == {"ok": True}


def test_handle_get_request_routes_tender_detail(tmp_path) -> None:
    store = _store_with_tender(tmp_path)

    response = handle_get_request(store.database_path, "/api/tenders/mosreg_market/3668200", {})

    assert response.kind == "json"
    assert response.status == 200
    assert response.payload["source"] == "mosreg_market"
    assert response.payload["external_id"] == "3668200"


def test_handle_post_request_routes_workflow_update(tmp_path) -> None:
    store = _store_with_tender(tmp_path)

    response = handle_post_request(
        store.database_path,
        "/api/tenders/mosreg_market/3668200/workflow",
        {"workflow_status": "interesting", "workflow_note": "check margin"},
    )

    assert response.status == 200
    assert response.payload["workflow_status"] == "interesting"
    assert response.payload["workflow_note"] == "check margin"


def test_handle_post_request_routes_product_profile_economics_update(tmp_path) -> None:
    store = _store_with_tender(tmp_path)
    store.upsert_product_profiles(
        "mosreg_market",
        "3668200",
        [
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="3668200",
                position_index=1,
                product_name="Office paper",
                quantity=10,
                unit="pack",
            )
        ],
    )

    response = handle_post_request(
        store.database_path,
        "/api/tenders/mosreg_market/3668200/product-profiles/1/economics",
        {"unit_cost": 6000, "logistics_cost": 5000},
    )

    assert response.status == 200
    assert response.payload["product_profiles"][0]["raw_payload"]["economics"] == {
        "unit_cost": 6000.0,
        "logistics_cost": 5000.0,
    }
    assert response.payload["economics"]["supplier_cost"] == 65000.0


def test_handle_post_request_routes_product_profile_economics_assumptions_update(tmp_path) -> None:
    store = _store_with_tender(tmp_path)
    store.upsert_product_profiles(
        "mosreg_market",
        "3668200",
        [
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="3668200",
                position_index=1,
                product_name="Office paper",
                quantity=10,
                unit="pack",
                raw_payload={"economics": {"unit_cost": 1000.0, "logistics_cost": 1000.0}},
            )
        ],
    )

    response = handle_post_request(
        store.database_path,
        "/api/tenders/mosreg_market/3668200/product-profiles/1/economics/assumptions",
        {
            "vat_mode": "vat_excluded",
            "vat_rate_percent": 20,
            "risk_reserve_percent": 5,
            "target_margin_percent": 15,
        },
    )

    profile = response.payload["product_profiles"][0]
    assert response.status == 200
    assert profile["raw_payload"]["economics_assumptions"]["vat_mode"] == "vat_excluded"
    assert response.payload["economics"]["items"][0]["estimated_total_cost"] == 13860.0


def test_handle_post_request_routes_product_profile_auto_economics(tmp_path) -> None:
    store = _store_with_tender(tmp_path)
    store.upsert_product_profiles(
        "mosreg_market",
        "3668200",
        [
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="3668200",
                position_index=1,
                product_name="Office paper",
                quantity=10,
                unit="pack",
                raw_payload={
                    "selected_supplier_option_index": 0,
                    "supplier_options": [{"name": "Paper shop", "unit_price": 900.0, "status": "selected"}],
                },
            )
        ],
    )

    response = handle_post_request(
        store.database_path,
        "/api/tenders/mosreg_market/3668200/product-profiles/1/economics/auto-estimate",
        {},
    )

    profile = response.payload["product_profiles"][0]
    assert response.status == 200
    assert profile["raw_payload"]["economics_auto"]["estimated_unit_cost"] == 900.0
    assert profile["raw_payload"]["economics_auto"]["base_source"] == "selected_supplier"
    assert profile["raw_payload"]["economics_assumptions"]["target_margin_percent"] == 15.0


def test_handle_post_request_routes_product_profile_auto_economics_accept(tmp_path) -> None:
    store = _store_with_tender(tmp_path)
    store.upsert_product_profiles(
        "mosreg_market",
        "3668200",
        [
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="3668200",
                position_index=1,
                product_name="Office paper",
                quantity=10,
                unit="pack",
                raw_payload={
                    "economics_auto": {
                        "estimated_unit_cost": 900.0,
                        "risk_reserve": 100.0,
                        "cost_drivers": [
                            {"type": "delivery", "amount": 135.0},
                            {"type": "certificates", "amount": 90.0},
                        ],
                    }
                },
            )
        ],
    )

    response = handle_post_request(
        store.database_path,
        "/api/tenders/mosreg_market/3668200/product-profiles/1/economics/auto-estimate/accept",
        {},
    )

    profile = response.payload["product_profiles"][0]
    assert response.status == 200
    assert profile["profile_status"] == "priced"
    assert profile["raw_payload"]["economics"] == {
        "unit_cost": 900.0,
        "logistics_cost": 135.0,
        "documents_cost": 90.0,
        "other_costs": 100.0,
    }


def test_handle_post_request_routes_product_profile_supplier_option_create(tmp_path) -> None:
    store = _store_with_tender(tmp_path)
    store.upsert_product_profiles(
        "mosreg_market",
        "3668200",
        [
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="3668200",
                position_index=1,
                product_name="Office paper",
                quantity=10,
                unit="pack",
            )
        ],
    )

    response = handle_post_request(
        store.database_path,
        "/api/tenders/mosreg_market/3668200/product-profiles/1/supplier-options",
        {
            "name": "Paper shop",
            "url": "https://example.com/paper",
            "unit_price": "1234.50",
            "availability": "in_stock",
            "status": "candidate",
            "source_query": "office paper a4",
            "source_kind": "normalized_name",
        },
    )

    assert response.status == 200
    assert response.payload["product_profiles"][0]["raw_payload"]["supplier_options"] == [
        {
            "name": "Paper shop",
            "url": "https://example.com/paper",
            "unit_price": 1234.5,
            "availability": "in_stock",
            "status": "candidate",
            "source_query": "office paper a4",
            "source_kind": "normalized_name",
        }
    ]


def test_handle_post_request_routes_product_profile_supplier_search_prepare(tmp_path) -> None:
    store = _store_with_tender(tmp_path)

    def office_links(query: str) -> list[dict[str, str]]:
        encoded = query.replace(" ", "+")
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

    store.upsert_product_profiles(
        "mosreg_market",
        "3668200",
        [
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="3668200",
                position_index=1,
                product_name="Office paper A4",
                normalized_name="office paper a4",
                search_phrases=["office paper"],
                okpd2="17.12.14.110",
                quantity=10,
                unit="pack",
            )
        ],
    )

    response = handle_post_request(
        store.database_path,
        "/api/tenders/mosreg_market/3668200/product-profiles/1/supplier-search/prepare",
        {},
    )

    profile = response.payload["product_profiles"][0]
    assert response.status == 200
    assert profile["profile_status"] == "searching"
    assert profile["raw_payload"]["supplier_search"] == {
        "status": "ready",
        "queries": [
            {
                "query": "office paper a4",
                "kind": "normalized_name",
                "priority": 1,
                "quick_links": office_links("office paper a4"),
            },
            {
                "query": "office paper",
                "kind": "search_phrase",
                "priority": 2,
                "quick_links": office_links("office paper"),
            },
            {
                "query": "17.12.14.110 office paper a4",
                "kind": "classifier",
                "priority": 3,
                "quick_links": office_links("17.12.14.110 office paper a4"),
            },
        ],
    }


def test_handle_post_request_routes_product_profile_supplier_discovery_candidates(tmp_path) -> None:
    store = _store_with_tender(tmp_path)
    store.upsert_product_profiles(
        "mosreg_market",
        "3668200",
        [
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="3668200",
                position_index=1,
                product_name="Office paper A4",
                quantity=10,
                unit="pack",
            )
        ],
    )

    response = handle_post_request(
        store.database_path,
        "/api/tenders/mosreg_market/3668200/product-profiles/1/supplier-discovery/candidates",
        {
            "candidates": [
                {
                    "name": "Paper shop",
                    "url": "https://example.com/paper",
                    "unit_price": "900",
                    "provider": "public catalog",
                    "source_query": "office paper a4",
                    "source_kind": "normalized_name",
                }
            ]
        },
    )

    profile = response.payload["product_profiles"][0]
    assert response.status == 200
    assert profile["profile_status"] == "matched"
    assert profile["raw_payload"]["supplier_discovery"]["status"] == "pending_review"
    assert profile["raw_payload"]["supplier_discovery"]["candidates"][0]["review_status"] == "pending"
    assert profile["raw_payload"]["supplier_discovery"]["candidates"][0]["provider"] == "public_catalog"
    assert profile["raw_payload"]["supplier_discovery"]["candidates"][0]["confidence"] == "high"


def test_handle_post_request_routes_product_profile_supplier_discovery_run(tmp_path) -> None:
    store = _store_with_tender(tmp_path)
    product_page = quote(
        """
        <script type="application/ld+json">
        {
          "@context": "https://schema.org",
          "@type": "Product",
          "name": "Office paper A4 80 gsm",
          "url": "https://supplier.example/paper-a4",
          "offers": {"@type": "Offer", "price": "925", "availability": "https://schema.org/InStock"}
        }
        </script>
        """,
        safe="",
    )
    store.upsert_product_profiles(
        "mosreg_market",
        "3668200",
        [
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="3668200",
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
                                    {"label": "Supplier page", "url": f"data:text/html,{product_page}"},
                                ],
                            }
                        ],
                    }
                },
            )
        ],
    )

    response = handle_post_request(
        store.database_path,
        "/api/tenders/mosreg_market/3668200/product-profiles/1/supplier-discovery/run",
        {},
    )

    profile = response.payload["product_profiles"][0]
    assert response.status == 200
    assert profile["profile_status"] == "matched"
    assert profile["raw_payload"]["supplier_discovery"]["status"] == "pending_review"
    assert profile["raw_payload"]["supplier_discovery"]["collector_diagnostics"][0]["provider"] == "schema_org_product"
    assert profile["raw_payload"]["supplier_discovery"]["collector_diagnostics"][0]["candidates_found"] == 1
    assert profile["raw_payload"]["supplier_discovery"]["candidates"][0]["provider"] == "schema_org_product"
    assert profile["raw_payload"]["supplier_discovery"]["candidates"][0]["unit_price"] == 925.0
    assert profile["raw_payload"]["supplier_discovery"]["candidates"][0]["confidence"] == "high"
    assert "supplier_options" not in profile["raw_payload"]
    assert "economics" not in profile["raw_payload"]


def test_handle_post_request_routes_product_profile_supplier_discovery_candidate_import(tmp_path) -> None:
    store = _store_with_tender(tmp_path)
    store.upsert_product_profiles(
        "mosreg_market",
        "3668200",
        [
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="3668200",
                position_index=1,
                product_name="Office paper A4",
                quantity=10,
                unit="pack",
                raw_payload={
                    "supplier_discovery": {
                        "status": "pending_review",
                        "candidates": [
                            {
                                "name": "Paper shop",
                                "url": "https://example.com/paper",
                                "unit_price": 900.0,
                                "provider": "public_catalog",
                                "confidence": "high",
                                "source_query": "office paper a4",
                                "source_kind": "normalized_name",
                                "review_status": "pending",
                            }
                        ],
                    }
                },
            )
        ],
    )

    response = handle_post_request(
        store.database_path,
        "/api/tenders/mosreg_market/3668200/product-profiles/1/supplier-discovery/candidates/0/import",
        {},
    )

    profile = response.payload["product_profiles"][0]
    assert response.status == 200
    assert profile["raw_payload"]["supplier_options"] == [
        {
            "name": "Paper shop",
            "url": "https://example.com/paper",
            "unit_price": 900.0,
            "provider": "public_catalog",
            "confidence": "high",
            "source_query": "office paper a4",
            "source_kind": "normalized_name",
        }
    ]
    assert profile["raw_payload"]["supplier_discovery"]["candidates"][0]["review_status"] == "imported"
    assert "economics" not in profile["raw_payload"]


def test_handle_post_request_routes_product_profile_supplier_option_select(tmp_path) -> None:
    store = _store_with_tender(tmp_path)
    store.upsert_product_profiles(
        "mosreg_market",
        "3668200",
        [
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="3668200",
                position_index=1,
                product_name="Office paper",
                quantity=10,
                unit="pack",
                raw_payload={
                    "supplier_options": [
                        {"name": "Paper shop", "unit_price": 1200.0, "status": "candidate"},
                        {"name": "Better paper", "unit_price": 900.0, "status": "suitable"},
                    ]
                },
            )
        ],
    )

    response = handle_post_request(
        store.database_path,
        "/api/tenders/mosreg_market/3668200/product-profiles/1/supplier-options/1/select",
        {},
    )

    profile = response.payload["product_profiles"][0]
    assert response.status == 200
    assert profile["raw_payload"]["selected_supplier_option_index"] == 1
    assert profile["raw_payload"]["supplier_options"][1]["status"] == "selected"
    assert profile["raw_payload"]["economics"]["unit_cost"] == 900.0
    assert response.payload["economics"]["supplier_cost"] == 9000.0


def test_handle_post_request_routes_product_profile_best_supplier_option_select(tmp_path) -> None:
    store = _store_with_tender(tmp_path)
    store.upsert_product_profiles(
        "mosreg_market",
        "3668200",
        [
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="3668200",
                position_index=1,
                product_name="Office paper",
                quantity=10,
                unit="pack",
                raw_payload={
                    "supplier_options": [
                        {"name": "Paper shop", "unit_price": 1200.0, "status": "candidate", "availability": "in_stock"},
                        {"name": "Better paper", "unit_price": 900.0, "status": "suitable", "availability": "in_stock"},
                    ]
                },
            )
        ],
    )

    response = handle_post_request(
        store.database_path,
        "/api/tenders/mosreg_market/3668200/product-profiles/1/supplier-options/best/select",
        {},
    )

    profile = response.payload["product_profiles"][0]
    assert response.status == 200
    assert profile["raw_payload"]["selected_supplier_option_index"] == 1
    assert profile["raw_payload"]["supplier_options"][1]["status"] == "selected"
    assert profile["raw_payload"]["economics"]["unit_cost"] == 900.0
    assert profile["raw_payload"]["economics_price_source"]["selection"] == "auto_best"
    assert response.payload["economics"]["supplier_cost"] == 9000.0


def test_handle_request_reports_invalid_tender_route(tmp_path) -> None:
    response = handle_get_request(tmp_path / "tenders.sqlite", "/api/tenders/mosreg_market/3668200/extra", {})

    assert response.status == 400
    assert response.payload == {"error": "invalid tender path"}
