import json
from urllib.parse import quote

from tender_killer.api_handlers import handle_get_request, handle_post_request
from tender_killer.models import ProductProfile, Tender, TenderItem
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


def _store_with_materializable_tender_item(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="moscow_supplier_portal",
            external_id="Auction10211242",
            url="https://zakupki.mos.ru/auction/10211242",
            title="Battery Delta DTM",
            customer="School",
            region="Moscow",
            price=5080.0,
            status="Active",
            items=[
                TenderItem(
                    name="Battery Delta DTM",
                    quantity=4.0,
                    unit="pcs",
                    unit_price=1270.0,
                    total_price=5080.0,
                )
            ],
        )
    )
    return store


def _store_with_moscow_market_state_tender(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="moscow_supplier_portal",
            external_id="Auction10212588",
            url="https://zakupki.mos.ru/auction/10212588",
            title="Climbing gear",
            customer="School",
            region="Moscow",
            price=48460.0,
            status="Active",
            raw_payload={
                "auctionId": 10212588,
                "startPrice": 48460.0,
                "stateId": 19000002,
                "stateName": "Active",
                "__detail": {
                    "state": {"name": "Active", "id": 19000002},
                    "startCost": 48460.0,
                    "lastBetCost": None,
                    "uniqueSupplierCount": 1,
                    "bets": [],
                },
            },
        )
    )
    return store


def test_handle_get_request_returns_health_payload(tmp_path) -> None:
    response = handle_get_request(tmp_path / "tenders.sqlite", "/api/health", {})

    assert response.kind == "json"
    assert response.status == 200
    assert response.payload["ok"] is True
    assert "supplier_search_prepare" in response.payload["capabilities"]
    assert "supplier_catalog_presets" in response.payload["capabilities"]
    assert "supplier_catalog_health" in response.payload["capabilities"]
    assert "supplier_discovery_url" in response.payload["capabilities"]
    assert "web_auto_search" in response.payload["capabilities"]
    assert "market_state_import" in response.payload["capabilities"]
    assert "dashboard_queues" in response.payload["capabilities"]
    assert "price_candidate_review" in response.payload["capabilities"]
    assert "price_candidate_bulk_review" in response.payload["capabilities"]
    assert "price_candidate_auto_stage" in response.payload["capabilities"]
    assert "price_auto_apply" in response.payload["capabilities"]
    assert "price_discovery_run" in response.payload["capabilities"]
    assert "price_discovery_jobs" in response.payload["capabilities"]


def test_handle_get_request_routes_supplier_catalog_health(tmp_path) -> None:
    response = handle_get_request(tmp_path / "tenders.sqlite", "/api/supplier-catalogs/health", {})

    assert response.kind == "json"
    assert response.status == 200
    assert response.payload["ok"] is True
    assert response.payload["live"] is False
    assert [catalog["provider"] for catalog in response.payload["catalogs"]] == [
        "officemag",
        "komus",
        "petrovich",
        "vseinstrumenti",
        "lemanapro",
    ]
    assert response.payload["catalogs"][0]["status"] == "configured"
    assert response.payload["catalogs"][0]["search_mode"] == "active_small_search"
    assert response.payload["catalogs"][2]["status"] == "configured"
    assert response.payload["catalogs"][2]["search_mode"] == "active_small_search"


def test_handle_get_request_routes_supplier_catalog_health_live_to_cached_service(tmp_path, monkeypatch) -> None:
    calls: list[dict[str, object]] = []

    def fake_catalog_health(database_path, *, live=False):
        calls.append({"database_path": database_path, "live": live})
        return {"ok": False, "live": live, "cached": False, "catalogs": []}

    monkeypatch.setattr("tender_killer.api_handlers.get_cached_supplier_catalog_health_payload", fake_catalog_health)

    response = handle_get_request(tmp_path / "tenders.sqlite", "/api/supplier-catalogs/health", {"live": "1"})

    assert response.kind == "json"
    assert response.status == 200
    assert response.payload == {"ok": False, "live": True, "cached": False, "catalogs": []}
    assert calls == [{"database_path": tmp_path / "tenders.sqlite", "live": True}]


def test_handle_get_request_routes_tender_detail(tmp_path) -> None:
    store = _store_with_tender(tmp_path)

    response = handle_get_request(store.database_path, "/api/tenders/mosreg_market/3668200", {})

    assert response.kind == "json"
    assert response.status == 200
    assert response.payload["source"] == "mosreg_market"
    assert response.payload["external_id"] == "3668200"


def test_handle_get_request_routes_tender_list(tmp_path) -> None:
    store = _store_with_tender(tmp_path)

    response = handle_get_request(store.database_path, "/api/tenders", {"status": "active", "limit": "25", "offset": "0"})

    assert response.kind == "json"
    assert response.status == 200
    assert response.payload["total"] == 1
    assert response.payload["items"][0]["external_id"] == "3668200"


def test_handle_get_request_routes_dashboard_queues(tmp_path) -> None:
    store = _store_with_tender(tmp_path)

    response = handle_get_request(store.database_path, "/api/dashboard/queues", {"status": "active"})

    assert response.kind == "json"
    assert response.status == 200
    assert response.payload["ok"] is True
    assert "summary" in response.payload
    assert "queues" in response.payload


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


def test_handle_post_request_imports_moscow_market_state_payload(tmp_path) -> None:
    store = _store_with_moscow_market_state_tender(tmp_path)

    response = handle_post_request(
        store.database_path,
        "/api/tenders/moscow_supplier_portal/Auction10212588/market-state/import",
        {
            "endDate": "28.05.2026 16:26:11",
            "state": {"name": "Active", "id": 19000002},
            "nextCost": 47975.4,
            "lastBetSupplier": {"name": "Other participant", "id": None},
            "lastBetCost": 48217.7,
            "betsDiff": [],
            "uniqueSupplierCount": 1,
            "rowVersion": "AAAAAvAo3L0=",
        },
    )

    assert response.status == 200
    assert response.payload["market_state"]["status"] == "has_current_offer"
    assert response.payload["market_state"]["current_offer_price"] == 48217.7
    assert response.payload["market_state"]["next_bid_price"] == 47975.4
    assert response.payload["market_state"]["price_source"] == "moscow_get_bet_update_import"
    assert response.payload["market_state"]["participant_count"] == 1
    assert response.payload["market_state"]["bid_count"] == 1
    assert response.payload["market_state"]["last_offer_supplier"] == "Other participant"
    raw_payload = json.loads(response.payload["raw_payload_json"])
    assert raw_payload["__market_state_import"]["lastBetCost"] == 48217.7
    assert "Authorization" not in json.dumps(raw_payload, ensure_ascii=False)


def test_handle_post_request_rejects_sensitive_market_state_import_payload(tmp_path) -> None:
    store = _store_with_moscow_market_state_tender(tmp_path)

    response = handle_post_request(
        store.database_path,
        "/api/tenders/moscow_supplier_portal/Auction10212588/market-state/import",
        {
            "lastBetCost": 48217.7,
            "headers": {
                "Authorization": "Bearer secret",
            },
        },
    )

    assert response.status == 400
    assert "sensitive" in response.payload["error"]


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


def test_handle_post_request_materializes_missing_product_profiles_for_economics_update(tmp_path) -> None:
    store = _store_with_materializable_tender_item(tmp_path)
    assert store.get_product_profiles("moscow_supplier_portal", "Auction10211242") == []

    response = handle_post_request(
        store.database_path,
        "/api/tenders/moscow_supplier_portal/Auction10211242/product-profiles/1/economics",
        {"unit_cost": "3500", "logistics_cost": "200"},
    )

    profile = response.payload["product_profiles"][0]
    assert response.status == 200
    assert profile["product_name"] == "Battery Delta DTM"
    assert profile["raw_payload"]["economics"] == {"unit_cost": 3500.0, "logistics_cost": 200.0}
    assert store.get_product_profiles("moscow_supplier_portal", "Auction10211242")[0]["raw_payload"][
        "economics"
    ] == {"unit_cost": 3500.0, "logistics_cost": 200.0}


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


def test_handle_post_request_routes_product_profile_supplier_search_prepare(tmp_path, monkeypatch) -> None:
    store = _store_with_tender(tmp_path)
    fetch_calls: list[str] = []

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

    def fake_fetch(url: str) -> str:
        fetch_calls.append(url)
        return """
        <html>
          <body>
            <a href="/catalog/goods/123456/">Office paper A4 80 g/m2 500 sheets</a>
          </body>
        </html>
        """

    monkeypatch.setattr("tender_killer.supplier_search_service._fetch_catalog_search_text", fake_fetch)

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
    supplier_search = profile["raw_payload"]["supplier_search"]
    assert supplier_search["status"] == "ready"
    assert supplier_search["catalog_providers"] == ["officemag", "komus"]
    assert supplier_search["search_intent"]["best_query"] == "office paper a4"
    assert supplier_search["best_product_link"] == {
        "status": "product_link",
        "provider": "officemag",
        "label": "OfficeMag",
        "title": "Office paper A4 80 g/m2 500 sheets",
        "url": "https://www.officemag.ru/catalog/goods/123456/",
        "search_url": "https://www.officemag.ru/search/?q=office+paper+a4",
        "source_query": "office paper a4",
        "match_score": 20,
    }
    assert [
        {
            "query": query["query"],
            "kind": query["kind"],
            "priority": query["priority"],
            "quick_links": query["quick_links"],
        }
        for query in supplier_search["queries"]
    ] == [
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
    ]
    assert fetch_calls == ["https://www.officemag.ru/search/?q=office+paper+a4"]


def test_handle_post_request_materializes_missing_product_profiles_for_supplier_search_prepare(tmp_path) -> None:
    store = _store_with_materializable_tender_item(tmp_path)
    assert store.get_product_profiles("moscow_supplier_portal", "Auction10211242") == []

    response = handle_post_request(
        store.database_path,
        "/api/tenders/moscow_supplier_portal/Auction10211242/product-profiles/1/supplier-search/prepare",
        {},
    )

    profile = response.payload["product_profiles"][0]
    assert response.status == 200
    assert profile["profile_status"] == "searching"
    assert profile["raw_payload"]["supplier_search"]["queries"][0]["query"] == "battery delta dtm"
    assert store.get_product_profiles("moscow_supplier_portal", "Auction10211242")[0]["raw_payload"][
        "supplier_search"
    ]["status"] == "ready"


def test_handle_post_request_routes_product_profile_supplier_catalog_presets_update(tmp_path) -> None:
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
                raw_payload={
                    "supplier_options": [{"name": "Paper shop", "unit_price": 1200.0}],
                    "supplier_search": {"status": "ready", "queries": [{"query": "office paper a4"}]},
                },
            )
        ],
    )

    response = handle_post_request(
        store.database_path,
        "/api/tenders/mosreg_market/3668200/product-profiles/1/supplier-catalog-presets",
        {"preset_ids": ["petrovich_building_materials", "missing", "petrovich_building_materials"]},
    )

    profile = response.payload["product_profiles"][0]
    assert response.status == 200
    assert profile["raw_payload"]["supplier_catalog_preset_ids"] == ["petrovich_building_materials"]
    assert "supplier_search" not in profile["raw_payload"]
    assert profile["raw_payload"]["supplier_options"] == [{"name": "Paper shop", "unit_price": 1200.0}]

    response = handle_post_request(
        store.database_path,
        "/api/tenders/mosreg_market/3668200/product-profiles/1/supplier-catalog-presets",
        {"preset_ids": None},
    )

    profile = response.payload["product_profiles"][0]
    assert "supplier_catalog_preset_ids" not in profile["raw_payload"]


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
    diagnostics = {
        item["provider"]: item
        for item in profile["raw_payload"]["supplier_discovery"]["collector_diagnostics"]
    }
    assert diagnostics["schema_org_product"]["candidates_found"] == 1
    assert profile["raw_payload"]["supplier_discovery"]["candidates"][0]["provider"] == "schema_org_product"
    assert profile["raw_payload"]["supplier_discovery"]["candidates"][0]["unit_price"] == 925.0
    assert profile["raw_payload"]["supplier_discovery"]["candidates"][0]["confidence"] == "high"
    assert "supplier_options" not in profile["raw_payload"]
    assert "economics" not in profile["raw_payload"]


def test_handle_post_request_routes_product_profile_supplier_discovery_url(tmp_path) -> None:
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
            )
        ],
    )

    response = handle_post_request(
        store.database_path,
        "/api/tenders/mosreg_market/3668200/product-profiles/1/supplier-discovery/url",
        {"url": f"data:text/html,{product_page}", "source_query": "office paper a4"},
    )

    profile = response.payload["product_profiles"][0]
    assert response.status == 200
    assert profile["raw_payload"]["supplier_discovery"]["status"] == "pending_review"
    diagnostics = {
        item["provider"]: item
        for item in profile["raw_payload"]["supplier_discovery"]["collector_diagnostics"]
    }
    assert diagnostics["schema_org_product"]["candidates_found"] == 1
    assert profile["raw_payload"]["supplier_discovery"]["candidates"][0]["source_kind"] == "manual_product_url"
    assert profile["raw_payload"]["supplier_discovery"]["candidates"][0]["unit_price"] == 925.0
    assert "supplier_options" not in profile["raw_payload"]
    assert "economics" not in profile["raw_payload"]


def test_handle_post_request_prepares_supplier_discovery_queries_when_missing(tmp_path) -> None:
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
                raw_payload={"supplier_catalog_preset_ids": []},
            )
        ],
    )

    response = handle_post_request(
        store.database_path,
        "/api/tenders/mosreg_market/3668200/product-profiles/1/supplier-discovery/run",
        {},
    )

    assert response.status == 400
    assert response.payload["error"] == "Новых кандидатов поставщиков не найдено."
    profile = response.payload["product_profiles"][0]
    assert profile["position_index"] == 1
    supplier_search = profile["raw_payload"]["supplier_search"]
    assert supplier_search["status"] == "ready"
    assert [query["query"] for query in supplier_search["queries"]] == ["Office paper A4"]


def test_handle_post_request_reports_supplier_discovery_no_new_candidates(tmp_path) -> None:
    store = _store_with_tender(tmp_path)
    empty_page = quote("<html><h1>No offer here</h1></html>", safe="")
    store.upsert_product_profiles(
        "mosreg_market",
        "3668200",
        [
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="3668200",
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
                                    {"label": "Supplier page", "url": f"data:text/html,{empty_page}"},
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

    assert response.status == 400
    assert response.payload["error"] == "Новых кандидатов поставщиков не найдено."
    discovery = response.payload["product_profiles"][0]["raw_payload"]["supplier_discovery"]
    assert discovery["status"] == "no_candidates"
    diagnostics = {item["provider"]: item for item in discovery["collector_diagnostics"]}
    assert diagnostics["schema_org_product"]["pages_fetched"] == 1
    assert diagnostics["schema_org_product"]["candidates_found"] == 0
    assert discovery["candidates"] == []


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


def test_handle_post_request_routes_product_profile_price_candidate_confirm(tmp_path) -> None:
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
    saved = store.upsert_price_candidates(
        "mosreg_market",
        "3668200",
        1,
        [{"provider": "komus", "name": "Office paper", "url": "https://example.com/paper", "unit_price": 900.0}],
        origin="supplier_discovery",
    )

    response = handle_post_request(
        store.database_path,
        f"/api/tenders/mosreg_market/3668200/product-profiles/1/price-candidates/{saved[0]['id']}/confirm",
        {},
    )

    profile = response.payload["product_profiles"][0]
    assert response.status == 200
    assert response.payload["price_candidate_review"]["review_status"] == "confirmed"
    assert response.payload["price_candidate_review"]["supplier_option_index"] == 0
    assert profile["profile_status"] == "priced"
    assert profile["raw_payload"]["economics"]["unit_cost"] == 900.0
    assert profile["raw_payload"]["economics_price_source"]["source"] == "price_candidate"
    assert response.payload["economics"]["supplier_cost"] == 9000.0


def test_handle_post_request_routes_product_profile_price_candidate_reject(tmp_path) -> None:
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
    saved = store.upsert_price_candidates(
        "mosreg_market",
        "3668200",
        1,
        [{"provider": "bad", "name": "Wrong item", "unit_price": 10.0}],
        origin="supplier_discovery",
    )

    response = handle_post_request(
        store.database_path,
        f"/api/tenders/mosreg_market/3668200/product-profiles/1/price-candidates/{saved[0]['id']}/reject",
        {},
    )

    profile = response.payload["product_profiles"][0]
    candidates = store.list_price_candidates("mosreg_market", "3668200", 1)
    assert response.status == 200
    assert response.payload["price_candidate_review"]["review_status"] == "rejected"
    assert candidates[0]["review_status"] == "rejected"
    assert "economics" not in profile["raw_payload"]


def test_handle_post_request_routes_ready_price_candidate_bulk_confirm(tmp_path) -> None:
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
            ),
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="3668200",
                position_index=2,
                product_name="Cable",
                quantity=20,
                unit="шт",
            ),
        ],
    )
    store.upsert_price_candidates(
        "mosreg_market",
        "3668200",
        1,
        [
            {
                "provider": "komus",
                "name": "Office paper",
                "url": "https://example.com/paper",
                "unit_price": 900.0,
                "currency": "RUB",
                "vat_mode": "vat_included",
                "availability": "in_stock",
                "confidence": "high",
                "delivery_note": "Delivery included",
                "pack_quantity": 1,
                "unit": "pack",
                "minimum_order_quantity": 1,
            }
        ],
        origin="supplier_discovery",
    )
    store.upsert_price_candidates(
        "mosreg_market",
        "3668200",
        2,
        [{"provider": "manual", "name": "Cable", "unit_price": 10.0, "currency": "RUB", "confidence": "medium"}],
        origin="supplier_discovery",
    )

    response = handle_post_request(
        store.database_path,
        "/api/tenders/mosreg_market/3668200/price-candidates/ready/confirm",
        {},
    )

    assert response.status == 200
    assert response.payload["price_candidate_bulk_review"]["confirmed_count"] == 1
    assert response.payload["price_candidate_bulk_review"]["skipped_no_ready_candidate_count"] == 1
    profile = response.payload["product_profiles"][0]
    assert profile["raw_payload"]["economics"]["unit_cost"] == 900.0
    assert profile["raw_payload"]["economics_price_source"]["selection"] == "bulk_auto_eligible"
    assert response.payload["economics"]["items"][0]["total_cost"] == 9000.0
    assert response.payload["economics"]["supplier_cost"] is None
    assert response.payload["economics"]["status"] == "needs_costs"


def test_handle_post_request_routes_price_candidate_auto_stage(tmp_path) -> None:
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
                        {
                            "provider": "komus",
                            "name": "Office paper",
                            "url": "https://example.com/paper",
                            "unit_price": 900.0,
                            "currency": "RUB",
                            "vat_mode": "vat_included",
                            "availability": "in_stock",
                            "delivery_note": "Delivery included",
                            "pack_quantity": 1,
                            "unit": "pack",
                        }
                    ]
                },
            )
        ],
    )

    response = handle_post_request(store.database_path, "/api/tenders/mosreg_market/3668200/price-candidates/stage", {})

    profile = response.payload["product_profiles"][0]
    assert response.status == 200
    assert response.payload["price_candidate_stage"]["staged_count"] == 1
    assert response.payload["price_candidate_stage"]["ready_count"] == 1
    assert profile["price_candidates"][0]["provider"] == "komus"
    assert profile["price_candidates"][0]["quality_status"] == "ready"
    assert "economics" not in profile["raw_payload"]


def test_handle_post_request_routes_tender_price_book_feed_stage(tmp_path) -> None:
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
        "/api/tenders/mosreg_market/3668200/price-book/feed",
        {
            "feed_name": "Office suppliers",
            "rows": [
                {
                    "position_index": 1,
                    "supplier": "OfficeMag",
                    "name": "Office paper A4, 500 sheets",
                    "unit_price": 359,
                    "currency": "RUB",
                    "vat_mode": "vat_included",
                    "availability": "in_stock",
                    "delivery_note": "Delivery included",
                    "unit": "pack",
                    "pack_quantity": 1,
                }
            ],
        },
    )

    assert response.status == 200
    assert response.payload["price_book_feed"]["staged_count"] == 1
    candidate = response.payload["product_profiles"][0]["price_candidates"][0]
    assert candidate["origin"] == "price_book_feed"
    assert candidate["source_kind"] == "price_book_feed"
    assert candidate["pricing_passport"]["next_action"] == "ready_to_confirm"


def test_handle_post_request_routes_tender_auto_prices_and_refreshes_economics(tmp_path) -> None:
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
                        {
                            "provider": "komus",
                            "name": "Office paper",
                            "url": "https://example.com/paper",
                            "unit_price": 900.0,
                            "currency": "RUB",
                            "vat_mode": "vat_included",
                            "availability": "in_stock",
                            "delivery_note": "Delivery included",
                            "pack_quantity": 1,
                            "unit": "pack",
                        }
                    ]
                },
            ),
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="3668200",
                position_index=2,
                product_name="Folders",
                quantity=5,
                unit="pack",
            ),
        ],
    )

    response = handle_post_request(store.database_path, "/api/tenders/mosreg_market/3668200/price-candidates/auto-apply", {})

    assert response.status == 200
    assert response.payload["price_auto_apply"]["stage"]["staged_count"] == 1
    assert response.payload["price_auto_apply"]["ready_review"]["confirmed_count"] == 1
    assert response.payload["price_auto_apply"]["priced_count"] == 1
    assert response.payload["price_auto_apply"]["missing_cost_positions"] == [2]
    assert response.payload["product_profiles"][0]["raw_payload"]["economics"]["unit_cost"] == 900.0
    assert response.payload["economics"]["items"][0]["total_cost"] == 9000.0
    assert response.payload["economics"]["missing_cost_inputs"] == ["Folders"]


def test_handle_post_request_starts_tender_price_discovery_job(tmp_path, monkeypatch) -> None:
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
    calls = []

    def fake_start(database_path, source, external_id):
        calls.append((database_path, source, external_id))
        return {
            "job_id": "job-1",
            "status": "queued",
            "source": source,
            "external_id": external_id,
            "total_profiles": 1,
            "searched_count": 0,
            "limited_count": 0,
            "partial": False,
        }

    monkeypatch.setattr("tender_killer.api_handlers.start_tender_price_discovery_job", fake_start)

    response = handle_post_request(store.database_path, "/api/tenders/mosreg_market/3668200/price-discovery/run", {})

    assert response.status == 200
    assert calls == [(store.database_path, "mosreg_market", "3668200")]
    assert response.payload["price_discovery_job"]["job_id"] == "job-1"
    assert response.payload["price_discovery_job"]["status"] == "queued"
    assert response.payload["price_discovery_run"]["job_id"] == "job-1"
    assert response.payload["product_profiles"][0]["position_index"] == 1


def test_handle_get_request_routes_tender_price_discovery_job_status(tmp_path, monkeypatch) -> None:
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

    def fake_get(job_id, database_path):
        assert job_id == "job-1"
        assert database_path == store.database_path
        return {
            "job_id": "job-1",
            "status": "running",
            "source": "mosreg_market",
            "external_id": "3668200",
            "total_profiles": 3,
            "searched_count": 1,
            "limited_count": 2,
            "partial": True,
        }

    monkeypatch.setattr("tender_killer.api_handlers.get_tender_price_discovery_job", fake_get)

    response = handle_get_request(store.database_path, "/api/price-discovery/jobs/job-1", {})

    assert response.status == 200
    assert response.payload["price_discovery_job"]["job_id"] == "job-1"
    assert response.payload["price_discovery_job"]["searched_count"] == 1
    assert response.payload["tender"]["external_id"] == "3668200"


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


def test_handle_post_request_routes_bulk_best_supplier_option_select(tmp_path) -> None:
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
            ),
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="3668200",
                position_index=2,
                product_name="Folders",
                quantity=5,
                unit="pack",
                raw_payload={"supplier_options": [{"name": "No price", "status": "candidate"}]},
            ),
        ],
    )

    response = handle_post_request(
        store.database_path,
        "/api/tenders/mosreg_market/3668200/product-profiles/supplier-options/best/select",
        {},
    )

    assert response.status == 200
    assert response.payload["supplier_selection"] == {
        "ok": True,
        "selected_count": 1,
        "skipped_count": 1,
        "selected_positions": [1],
        "skipped_positions": [2],
    }
    assert response.payload["product_profiles"][0]["raw_payload"]["economics"]["unit_cost"] == 900.0
    assert response.payload["economics"]["items"][0]["total_cost"] == 9000.0
    assert response.payload["economics"]["missing_cost_inputs"] == ["Folders"]


def test_handle_request_reports_invalid_tender_route(tmp_path) -> None:
    response = handle_get_request(tmp_path / "tenders.sqlite", "/api/tenders/mosreg_market/3668200/extra", {})

    assert response.status == 400
    assert response.payload == {"error": "invalid tender path"}
