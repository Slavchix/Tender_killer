from tender_killer.models import ProductProfile, Tender, TenderItem
from tender_killer.price_candidate_service import apply_tender_auto_prices
from tender_killer.price_candidate_service import confirm_ready_price_candidates
from tender_killer.price_candidate_service import normalize_price_candidate
from tender_killer.price_candidate_service import rank_profile_price_candidates
from tender_killer.price_candidate_service import review_profile_price_candidate
from tender_killer.price_candidate_service import stage_tender_price_candidates
from tender_killer.storage import TenderStore
from tender_killer.tender_detail_service import get_tender_payload


def test_rank_profile_price_candidates_prefers_reviewed_and_high_signal_candidates() -> None:
    profile = {
        "position_index": 1,
        "price_candidates": [
            {
                "id": 1,
                "provider": "unknown",
                "product_name": "Paper A4",
                "unit_price": 900.0,
                "confidence": "low",
                "review_status": "pending",
            },
            {
                "id": 2,
                "provider": "komus",
                "product_name": "Paper A4",
                "source_url": "https://supplier.example/paper",
                "unit_price": 880.0,
                "availability": "in_stock",
                "confidence": "high",
                "confidence_reasons": ["has_price", "has_url"],
                "review_status": "pending",
            },
            {
                "id": 3,
                "provider": "manual",
                "product_name": "Paper A4",
                "unit_price": 950.0,
                "confidence": "medium",
                "review_status": "confirmed",
            },
            {
                "id": 4,
                "provider": "bad",
                "product_name": "Wrong item",
                "unit_price": 100.0,
                "confidence": "high",
                "review_status": "rejected",
            },
        ],
    }

    ranked = rank_profile_price_candidates(profile)

    assert [candidate["id"] for candidate in ranked] == [3, 2, 1, 4]
    assert ranked[0]["score"] > ranked[1]["score"]
    assert "confirmed" in ranked[0]["score_reasons"]
    assert "source_url" in ranked[1]["score_reasons"]
    assert ranked[-1]["review_status"] == "rejected"


def test_rank_profile_price_candidates_marks_auto_ready_candidate() -> None:
    profile = {
        "position_index": 1,
        "quantity": 10,
        "unit": "pack",
        "price_candidates": [
            {
                "id": 1,
                "provider": "komus",
                "product_name": "Paper A4",
                "source_url": "https://supplier.example/unavailable",
                "unit_price": 700.0,
                "currency": "RUB",
                "vat_mode": "vat_included",
                "availability": "unavailable",
                "confidence": "high",
                "raw_payload": {
                    "delivery_note": "Delivery included",
                    "pack_quantity": 1,
                    "unit": "pack",
                    "minimum_order_quantity": 1,
                },
            },
            {
                "id": 2,
                "provider": "officemag",
                "product_name": "Paper A4",
                "source_url": "https://supplier.example/paper",
                "unit_price": 880.0,
                "currency": "RUB",
                "vat_mode": "vat_included",
                "availability": "in_stock",
                "confidence": "high",
                "raw_payload": {
                    "delivery_note": "Delivery included",
                    "pack_quantity": 1,
                    "unit": "pack",
                    "minimum_order_quantity": 1,
                },
            },
        ],
    }

    ranked = rank_profile_price_candidates(profile)

    assert [candidate["id"] for candidate in ranked] == [2, 1]
    assert ranked[0]["quality_status"] == "ready"
    assert ranked[0]["auto_eligible"] is True
    assert ranked[0]["quality_flags"] == []
    assert "quality_ready" in ranked[0]["score_reasons"]
    assert ranked[1]["quality_status"] == "blocked"
    assert ranked[1]["auto_eligible"] is False
    assert _flag_ids(ranked[1]) == {"availability_unavailable"}


def test_rank_profile_price_candidates_adds_operator_pricing_passport() -> None:
    profile = {
        "position_index": 1,
        "product_name": "Paper A4",
        "quantity": 12,
        "unit": "pack",
        "price_candidates": [
            {
                "id": 1,
                "provider": "officemag",
                "product_name": "Paper A4 500 sheets",
                "source_url": "https://www.officemag.ru/catalog/goods/110532/",
                "source_kind": "catalog_product",
                "observed_at": "2026-06-21T09:00:00",
                "unit_price": 359.0,
                "currency": "RUB",
                "vat_mode": "vat_included",
                "availability": "in_stock",
                "delivery_note": "Delivery included",
                "unit": "pack",
                "pack_quantity": 1,
                "stock_quantity": 14194,
                "confidence": "high",
                "match_reasons": ["profile_intent_match", "price_break_selected"],
            }
        ],
    }

    candidate = rank_profile_price_candidates(profile)[0]

    assert candidate["pricing_passport"] == {
        "provider": "officemag",
        "supplier_name": None,
        "product_name": "Paper A4 500 sheets",
        "source_url": "https://www.officemag.ru/catalog/goods/110532/",
        "source_kind": "catalog_product",
        "source_label": "officemag · catalog_product",
        "observed_at": "2026-06-21T09:00:00",
        "freshness_label": "2026-06-21T09:00:00",
        "match_confidence": "high",
        "match_reasons": ["profile_intent_match", "price_break_selected"],
        "unit_pack_label": "12 pack · упак. 1",
        "vat_label": "НДС включен",
        "delivery_label": "доставка ясна",
        "evidence_url": "https://www.officemag.ru/catalog/goods/110532/",
        "evidence_label": "карточка товара",
        "unit_price": 359.0,
        "total_price": 4308.0,
        "quantity": 12.0,
        "unit": "pack",
        "currency": "RUB",
        "availability": "in_stock",
        "vat_mode": "vat_included",
        "delivery_note": "Delivery included",
        "stock_quantity": 14194.0,
        "preorder_quantity": None,
        "pack_quantity": 1.0,
        "minimum_order_quantity": None,
        "quality_status": "ready",
        "auto_eligible": True,
        "confidence": "high",
        "positive_checks": ["source_url", "unit_price", "availability", "vat", "delivery", "pack_quantity"],
        "review_checks": [],
        "block_checks": [],
        "next_action": "ready_to_confirm",
        "summary": "Цена готова к подтверждению: есть ссылка, цена, наличие, НДС и доставка.",
    }


def test_rank_profile_price_candidates_prefers_strict_catalog_query_over_generic_fallback() -> None:
    profile = {
        "position_index": 1,
        "product_name": "self drilling screw 4.2x19 zinc 200 pcs",
        "quantity": 1,
        "unit": "pack",
        "price_candidates": [
            {
                "id": 1,
                "provider": "vseinstrumenti",
                "product_name": "FastenPro self drilling screw 4.2x19 zinc pack 200 pcs",
                "source_url": "https://www.vseinstrumenti.ru/product/generic/",
                "source_query": "self drilling screw",
                "source_kind": "search_phrase",
                "unit_price": 390.0,
                "currency": "RUB",
                "vat_mode": "vat_included",
                "availability": "in_stock",
                "confidence": "high",
                "match_reasons": ["profile_intent_match"],
                "raw_payload": {"delivery_note": "Delivery included", "unit": "pack"},
            },
            {
                "id": 2,
                "provider": "vseinstrumenti",
                "product_name": "FastenPro self drilling screw 4.2x19 zinc pack 200 pcs",
                "source_url": "https://www.vseinstrumenti.ru/product/strict/",
                "source_query": "self drilling screw 4.2x19 zinc 200 pcs",
                "source_kind": "catalog_hint",
                "unit_price": 399.0,
                "currency": "RUB",
                "vat_mode": "vat_included",
                "availability": "in_stock",
                "confidence": "high",
                "match_reasons": ["profile_intent_match"],
                "raw_payload": {"delivery_note": "Delivery included", "unit": "pack"},
            },
        ],
    }

    ranked = rank_profile_price_candidates(profile)

    assert [candidate["id"] for candidate in ranked] == [2, 1]
    assert "strict_source_query" in ranked[0]["score_reasons"]
    assert "profile_intent_match" in ranked[0]["score_reasons"]


def test_rank_profile_price_candidates_blocks_wrong_product_family() -> None:
    profile = {
        "position_index": 1,
        "product_name": "cartridge for electrophotographic printing devices",
        "quantity": 2,
        "unit": "piece",
        "price_candidates": [
            {
                "id": 1,
                "provider": "officemag",
                "product_name": "Office paper A4, 80 gsm, 500 sheets",
                "source_url": "https://www.officemag.ru/catalog/goods/112464/",
                "source_query": "cartridge for electrophotographic printing devices",
                "unit_price": 493.0,
                "currency": "RUB",
                "vat_mode": "vat_included",
                "availability": "in_stock",
                "confidence": "high",
                "raw_payload": {
                    "delivery_note": "Delivery included",
                    "pack_quantity": 1,
                    "unit": "piece",
                },
            }
        ],
    }

    ranked = rank_profile_price_candidates(profile)

    assert ranked[0]["quality_status"] == "blocked"
    assert ranked[0]["auto_eligible"] is False
    assert "product_name_mismatch" in _flag_ids(ranked[0])
    assert "product_family_mismatch" in _flag_ids(ranked[0])
    assert "product_family_mismatch" in ranked[0]["pricing_passport"]["block_checks"]


def test_rank_profile_price_candidates_flags_unknown_cost_drivers_before_auto_accept() -> None:
    profile = {
        "position_index": 1,
        "quantity": 20,
        "unit": "шт",
        "price_candidates": [
            {
                "id": 1,
                "provider": "manual",
                "product_name": "Cable",
                "unit_price": 100.0,
                "currency": "RUB",
                "confidence": "medium",
                "raw_payload": {},
            },
        ],
    }

    ranked = rank_profile_price_candidates(profile)

    assert ranked[0]["quality_status"] == "review"
    assert ranked[0]["auto_eligible"] is False
    assert _flag_ids(ranked[0]) == {
        "availability_unknown",
        "delivery_unknown",
        "pack_quantity_unknown",
        "vat_unknown",
    }
    assert "quality_review" in ranked[0]["score_reasons"]


def test_normalize_price_candidate_applies_vat_and_pack_conversion() -> None:
    profile = {
        "position_index": 1,
        "quantity": 20,
        "unit": "шт",
    }
    candidate = {
        "provider": "manual",
        "name": "Cable marker pack",
        "unit_price": 1200.0,
        "currency": "RUB",
        "vat_mode": "vat_excluded",
        "vat_rate_percent": 20,
        "availability": "в наличии",
        "delivery_note": "Delivery included",
        "unit": "pack",
        "pack_quantity": 10,
        "confidence": "high",
    }

    normalized = normalize_price_candidate(profile, candidate)

    assert normalized["unit_price"] == 144.0
    assert normalized["unit"] == "шт"
    assert normalized["vat_mode"] == "vat_included"
    assert normalized["availability"] == "in_stock"
    assert "pack_quantity_normalized" in normalized["match_reasons"]
    assert "vat_normalized" in normalized["match_reasons"]
    assert normalized["raw_payload"]["original_unit_price"] == 1200.0
    assert normalized["raw_payload"]["normalized_unit_price"] == 144.0
    assert normalized["raw_payload"]["normalization"]["pack_quantity"] == 10.0
    assert normalized["raw_payload"]["normalization"]["vat_rate_percent"] == 20.0


def test_normalize_price_candidate_selects_price_break_by_profile_quantity() -> None:
    profile = {
        "position_index": 1,
        "product_name": "Office paper A4",
        "quantity": 60,
        "unit": "pack",
    }
    candidate = {
        "provider": "officemag",
        "name": "Office paper A4, 500 sheets",
        "unit_price": 364.0,
        "currency": "RUB",
        "vat_mode": "vat_included",
        "availability": "in_stock",
        "delivery_note": "Delivery included",
        "unit": "pack",
        "pack_quantity": 5,
        "confidence": "high",
        "price_breaks": [
            {"count": 1, "price": 364.0},
            {"count": 5, "price": 361.0},
            {"count": 10, "price": 359.0},
        ],
    }

    normalized = normalize_price_candidate(profile, candidate)

    assert normalized["unit_price"] == 359.0
    assert normalized["price_breaks"] == [
        {"count": 1, "price": 364.0},
        {"count": 5, "price": 361.0},
        {"count": 10, "price": 359.0},
    ]
    assert normalized["selected_price_break"] == {"count": 10, "price": 359.0}
    assert normalized["price_break_selection_quantity"] == 60.0
    assert normalized["raw_payload"]["normalization"]["selected_price_break"] == {"count": 10, "price": 359.0}
    assert normalized["raw_payload"]["normalization"]["price_break_selection_quantity"] == 60.0


def test_stage_price_candidates_uses_tender_item_quantity_for_legacy_profile(tmp_path) -> None:
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="legacy-profile-paper",
            url="https://market.mosreg.ru/Trade/ViewTrade/legacy-profile-paper",
            title="Paper tender",
            price=19890.0,
            items=[
                TenderItem(
                    name="Office paper A4",
                    quantity=60,
                    unit="pack",
                    unit_price=331.5,
                    total_price=19890.0,
                )
            ],
        )
    )
    store.upsert_product_profiles(
        "mosreg_market",
        "legacy-profile-paper",
        [
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="legacy-profile-paper",
                position_index=1,
                product_name="Paper tender title",
                raw_payload={
                    "supplier_discovery": {
                        "candidates": [
                            {
                                "provider": "officemag",
                                "name": "Office paper A4, 500 sheets",
                                "url": "https://www.officemag.ru/catalog/goods/110532/",
                                "unit_price": 364.0,
                                "currency": "RUB",
                                "vat_mode": "vat_included",
                                "availability": "in_stock",
                                "delivery_note": "Delivery included",
                                "unit": "pack",
                                "pack_quantity": 5,
                                "confidence": "high",
                                "price_breaks": [
                                    {"count": 1, "price": 364.0},
                                    {"count": 5, "price": 361.0},
                                    {"count": 10, "price": 359.0},
                                ],
                            }
                        ]
                    }
                },
            )
        ],
    )

    result = stage_tender_price_candidates(store.database_path, "mosreg_market", "legacy-profile-paper")

    assert result["staged_count"] == 1
    candidate = store.list_price_candidates("mosreg_market", "legacy-profile-paper", 1)[0]
    assert candidate["unit_price"] == 359.0
    assert candidate["selected_price_break"] == {"count": 10.0, "price": 359.0}
    assert candidate["price_break_selection_quantity"] == 60.0

    review_profile_price_candidate(
        store.database_path,
        "mosreg_market",
        "legacy-profile-paper",
        1,
        int(candidate["id"]),
        review_status="confirmed",
    )
    detail = get_tender_payload(store.database_path, "mosreg_market", "legacy-profile-paper")
    assert detail["economics"]["items"][0]["quantity"] == 60.0
    assert detail["economics"]["items"][0]["unit"] == "pack"
    assert detail["economics"]["items"][0]["unit_cost"] == 359.0
    assert detail["economics"]["items"][0]["total_cost"] == 21540.0


def test_confirm_profile_price_candidate_applies_price_to_economics_and_marks_review(tmp_path) -> None:
    store = _store_with_profile(tmp_path)
    saved = store.upsert_price_candidates(
        "mosreg_market",
        "price-review",
        1,
        [
            {
                "provider": "komus",
                "name": "Paper A4",
                "url": "https://supplier.example/paper",
                "unit_price": 880.0,
                "currency": "RUB",
                "vat_mode": "vat_included",
                "availability": "in_stock",
                "confidence": "high",
                "delivery_note": "Delivery included",
                "pack_quantity": 1,
                "stock_quantity": 123,
                "preorder_quantity": 200,
                "unit": "pack",
                "minimum_order_quantity": 1,
                "source_query": "paper a4",
                "source_kind": "normalized_name",
            }
        ],
        origin="supplier_discovery",
    )

    result = review_profile_price_candidate(
        store.database_path,
        "mosreg_market",
        "price-review",
        1,
        int(saved[0]["id"]),
        review_status="confirmed",
    )

    detail = get_tender_payload(store.database_path, "mosreg_market", "price-review")
    profile = detail["product_profiles"][0]
    candidates = store.list_price_candidates("mosreg_market", "price-review", 1)
    assert result == {
        "ok": True,
        "position_index": 1,
        "candidate_id": saved[0]["id"],
        "review_status": "confirmed",
        "supplier_option_index": 0,
    }
    assert candidates[0]["review_status"] == "confirmed"
    assert candidates[0]["supplier_option_index"] == 0
    assert profile["profile_status"] == "priced"
    assert profile["raw_payload"]["economics"] == {"unit_cost": 880.0}
    assert profile["raw_payload"]["selected_supplier_option_index"] == 0
    assert profile["raw_payload"]["supplier_options"][0]["status"] == "selected"
    assert profile["raw_payload"]["supplier_options"][0]["stock_quantity"] == 123
    assert profile["raw_payload"]["supplier_options"][0]["preorder_quantity"] == 200
    assert profile["raw_payload"]["economics_price_source"] == {
        "source": "price_candidate",
        "selection": "manual_confirmed",
        "candidate_id": saved[0]["id"],
        "provider": "komus",
        "product_name": "Paper A4",
        "supplier_name": None,
        "source_url": "https://supplier.example/paper",
        "source_query": "paper a4",
        "source_kind": "normalized_name",
        "unit_price": 880.0,
        "currency": "RUB",
        "stock_quantity": 123,
        "preorder_quantity": 200,
        "minimum_order_quantity": 1,
        "pack_quantity": 1,
        "review_status": "confirmed",
        "quality_status": "ready",
        "auto_eligible": True,
        "quality_flags": [],
    }
    assert detail["economics"]["supplier_cost"] == 8800.0


def test_confirm_profile_price_candidate_rejects_blocked_product_mismatch(tmp_path) -> None:
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="price-review-blocked",
            url="https://market.mosreg.ru/Trade/ViewTrade/price-review-blocked",
            title="Blocked candidate",
        )
    )
    store.upsert_product_profiles(
        "mosreg_market",
        "price-review-blocked",
        [
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="price-review-blocked",
                position_index=1,
                product_name="cartridge for electrophotographic printing devices",
                quantity=2,
                unit="piece",
                raw_payload={
                    "supplier_options": [
                        {
                            "provider": "officemag",
                            "name": "Office paper A4, 80 gsm, 500 sheets",
                            "url": "https://www.officemag.ru/catalog/goods/112464/",
                            "unit_price": 493,
                            "currency": "RUB",
                            "vat_mode": "vat_included",
                            "availability": "in_stock",
                            "confidence": "high",
                            "delivery_note": "Delivery included",
                            "pack_quantity": 1,
                            "unit": "piece",
                            "source_query": "cartridge for electrophotographic printing devices",
                        }
                    ]
                },
            )
        ],
    )
    stage_tender_price_candidates(store.database_path, "mosreg_market", "price-review-blocked")
    profile = get_tender_payload(store.database_path, "mosreg_market", "price-review-blocked")["product_profiles"][0]
    candidate = profile["price_candidates"][0]

    try:
        review_profile_price_candidate(
            store.database_path,
            "mosreg_market",
            "price-review-blocked",
            1,
            int(candidate["id"]),
            review_status="confirmed",
        )
    except ValueError as exc:
        assert "blocked" in str(exc).casefold()
        assert "product_family_mismatch" in str(exc)
    else:
        raise AssertionError("blocked price candidate was confirmed")

    profile = get_tender_payload(store.database_path, "mosreg_market", "price-review-blocked")["product_profiles"][0]
    assert profile["raw_payload"].get("economics", {}) == {}
    assert profile["profile_status"] != "priced"
    assert profile["price_candidates"][0]["review_status"] == "pending"


def test_confirm_profile_price_candidate_applies_price_break_total_by_quantity(tmp_path) -> None:
    store = _store_with_profile(tmp_path)
    store.upsert_product_profiles(
        "mosreg_market",
        "price-review",
        [
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="price-review",
                position_index=1,
                product_name="Office paper A4",
                quantity=60,
                unit="pack",
            )
        ],
    )
    saved = store.upsert_price_candidates(
        "mosreg_market",
        "price-review",
        1,
        [
            normalize_price_candidate(
                {
                    "position_index": 1,
                    "product_name": "Office paper A4",
                    "quantity": 60,
                    "unit": "pack",
                },
                {
                    "provider": "officemag",
                    "name": "Office paper A4, 500 sheets",
                    "url": "https://www.officemag.ru/catalog/goods/110532/",
                    "unit_price": 364.0,
                    "currency": "RUB",
                    "vat_mode": "vat_included",
                    "availability": "in_stock",
                    "confidence": "high",
                    "delivery_note": "Delivery included",
                    "unit": "pack",
                    "pack_quantity": 5,
                    "stock_quantity": 14194,
                    "price_breaks": [
                        {"count": 1, "price": 364.0},
                        {"count": 5, "price": 361.0},
                        {"count": 10, "price": 359.0},
                    ],
                },
            )
        ],
        origin="supplier_discovery",
    )

    review_profile_price_candidate(
        store.database_path,
        "mosreg_market",
        "price-review",
        1,
        int(saved[0]["id"]),
        review_status="confirmed",
    )

    detail = get_tender_payload(store.database_path, "mosreg_market", "price-review")
    profile = detail["product_profiles"][0]
    candidate = profile["price_candidates"][0]
    assert candidate["unit_price"] == 359.0
    assert candidate["selected_price_break"] == {"count": 10, "price": 359.0}
    assert profile["raw_payload"]["economics"] == {"unit_cost": 359.0}
    assert profile["raw_payload"]["economics_price_source"]["selected_price_break"] == {"count": 10, "price": 359.0}
    assert detail["economics"]["items"][0]["quantity"] == 60.0
    assert detail["economics"]["items"][0]["unit_cost"] == 359.0
    assert detail["economics"]["items"][0]["total_cost"] == 21540.0
    assert detail["economics"]["supplier_cost"] == 21540.0


def test_stage_tender_price_candidates_from_saved_sources_normalizes_quality(tmp_path) -> None:
    store = _store_with_profile(tmp_path)
    store.upsert_product_profiles(
        "mosreg_market",
        "price-review",
        [
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="price-review",
                position_index=1,
                product_name="Paper A4",
                quantity=10,
                unit="pack",
                raw_payload={
                    "supplier_options": [
                        {
                            "provider": "komus",
                            "name": "Paper A4",
                            "url": "https://supplier.example/paper",
                            "unit_price": 880.0,
                            "currency": "RUB",
                            "vat_mode": "vat_included",
                            "availability": "in_stock",
                            "delivery_note": "Delivery included",
                            "unit": "pack",
                            "pack_quantity": 1,
                            "source_query": "paper a4",
                        }
                    ]
                },
            ),
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="price-review",
                position_index=2,
                product_name="Cable marker",
                quantity=20,
                unit="шт",
                raw_payload={
                    "supplier_discovery": {
                        "candidates": [
                            {
                                "provider": "officemag",
                                "name": "Cable marker pack",
                                "url": "https://supplier.example/marker-pack",
                                "unit_price": 1200.0,
                                "currency": "RUB",
                                "vat_mode": "vat_excluded",
                                "vat_rate_percent": 20,
                                "availability": "в наличии",
                                "delivery_note": "Delivery included",
                                "unit": "pack",
                                "pack_quantity": 10,
                                "confidence": "high",
                                "source_query": "cable marker",
                            }
                        ]
                    }
                },
            ),
        ],
    )

    result = stage_tender_price_candidates(store.database_path, "mosreg_market", "price-review")

    detail = get_tender_payload(store.database_path, "mosreg_market", "price-review")
    profiles = {profile["position_index"]: profile for profile in detail["product_profiles"]}
    assert result["ok"] is True
    assert result["total_profiles"] == 2
    assert result["staged_count"] == 2
    assert result["ready_count"] == 2
    assert result["skipped_no_candidate_source_count"] == 0
    assert profiles[1]["price_candidates"][0]["unit_price"] == 880.0
    assert profiles[1]["price_candidates"][0]["quality_status"] == "ready"
    assert profiles[2]["price_candidates"][0]["unit_price"] == 144.0
    assert profiles[2]["price_candidates"][0]["unit"] == "шт"
    assert profiles[2]["price_candidates"][0]["quality_status"] == "ready"
    assert profiles[2]["price_candidates"][0]["raw_payload"]["normalization"]["source"] == "supplier_discovery"


def test_confirm_ready_price_candidates_applies_only_auto_eligible_missing_prices(tmp_path) -> None:
    store = _store_with_profile(tmp_path)
    store.upsert_product_profiles(
        "mosreg_market",
        "price-review",
        [
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="price-review",
                position_index=1,
                product_name="Paper A4",
                quantity=10,
                unit="pack",
            ),
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="price-review",
                position_index=2,
                product_name="Folder",
                quantity=5,
                unit="pack",
                raw_payload={"economics": {"unit_cost": 55.0}},
            ),
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="price-review",
                position_index=3,
                product_name="Cable",
                quantity=20,
                unit="шт",
            ),
        ],
    )
    ready_candidate = {
        "provider": "officemag",
        "name": "Paper A4",
        "url": "https://supplier.example/paper",
        "unit_price": 100.0,
        "currency": "RUB",
        "vat_mode": "vat_included",
        "availability": "in_stock",
        "confidence": "high",
        "delivery_note": "Delivery included",
        "pack_quantity": 1,
        "unit": "pack",
        "minimum_order_quantity": 1,
    }
    store.upsert_price_candidates("mosreg_market", "price-review", 1, [ready_candidate], origin="supplier_discovery")
    store.upsert_price_candidates("mosreg_market", "price-review", 2, [ready_candidate], origin="supplier_discovery")
    store.upsert_price_candidates(
        "mosreg_market",
        "price-review",
        3,
        [{"provider": "manual", "name": "Cable", "unit_price": 25.0, "currency": "RUB", "confidence": "medium"}],
        origin="supplier_discovery",
    )

    result = confirm_ready_price_candidates(store.database_path, "mosreg_market", "price-review")

    detail = get_tender_payload(store.database_path, "mosreg_market", "price-review")
    profiles = {profile["position_index"]: profile for profile in detail["product_profiles"]}
    assert result == {
        "ok": True,
        "total_profiles": 3,
        "confirmed_count": 1,
        "skipped_count": 2,
        "skipped_existing_cost_count": 1,
        "skipped_no_ready_candidate_count": 1,
        "confirmed": [{"position_index": 1, "candidate_id": profiles[1]["price_candidates"][0]["id"], "supplier_option_index": 0}],
    }
    assert profiles[1]["raw_payload"]["economics"] == {"unit_cost": 100.0}
    assert profiles[1]["raw_payload"]["economics_price_source"]["selection"] == "bulk_auto_eligible"
    assert profiles[1]["price_candidates"][0]["review_status"] == "confirmed"
    assert profiles[2]["raw_payload"]["economics"] == {"unit_cost": 55.0}
    assert profiles[2]["price_candidates"][0]["review_status"] == "pending"
    assert "economics" not in profiles[3]["raw_payload"]
    assert profiles[3]["price_candidates"][0]["quality_status"] == "review"


def test_apply_tender_auto_prices_stages_ready_candidates_and_updates_economics(tmp_path) -> None:
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="auto-prices",
            url="https://market.mosreg.ru/Trade/ViewTrade/auto-prices",
            title="Paper tender",
            price=100000.0,
        )
    )
    store.upsert_product_profiles(
        "mosreg_market",
        "auto-prices",
        [
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="auto-prices",
                position_index=1,
                product_name="Paper A4",
                quantity=10,
                unit="pack",
                raw_payload={
                    "supplier_options": [
                        {
                            "provider": "komus",
                            "name": "Paper A4",
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
                tender_external_id="auto-prices",
                position_index=2,
                product_name="Pens",
                quantity=5,
                unit="pack",
                raw_payload={
                    "economics": {"unit_cost": 55.0},
                    "supplier_options": [
                        {
                            "provider": "manual",
                            "name": "Pens",
                            "url": "https://example.com/pens",
                            "unit_price": 10.0,
                            "currency": "RUB",
                            "vat_mode": "vat_included",
                            "availability": "in_stock",
                            "delivery_note": "Delivery included",
                            "pack_quantity": 1,
                            "unit": "pack",
                        }
                    ],
                },
            ),
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="auto-prices",
                position_index=3,
                product_name="Folders",
                quantity=3,
                unit="pack",
            ),
        ],
    )

    result = apply_tender_auto_prices(store.database_path, "mosreg_market", "auto-prices")

    assert result["ok"] is True
    assert result["stage"]["staged_count"] == 2
    assert result["ready_review"]["confirmed_count"] == 1
    assert result["ready_review"]["skipped_existing_cost_count"] == 1
    assert result["priced_count"] == 2
    assert result["missing_cost_count"] == 1
    assert result["missing_cost_positions"] == [3]
    detail = get_tender_payload(store.database_path, "mosreg_market", "auto-prices")
    profiles = {profile["position_index"]: profile for profile in detail["product_profiles"]}
    assert profiles[1]["raw_payload"]["economics"]["unit_cost"] == 900.0
    assert profiles[1]["raw_payload"]["economics_price_source"]["selection"] == "bulk_auto_eligible"
    assert profiles[2]["raw_payload"]["economics"]["unit_cost"] == 55.0
    assert detail["economics"]["items"][0]["total_cost"] == 9000.0
    assert detail["economics"]["items"][1]["total_cost"] == 275.0
    assert detail["economics"]["missing_cost_inputs"] == ["Folders"]


def test_reject_profile_price_candidate_marks_review_without_pricing(tmp_path) -> None:
    store = _store_with_profile(tmp_path)
    saved = store.upsert_price_candidates(
        "mosreg_market",
        "price-review",
        1,
        [{"provider": "bad", "name": "Wrong paper", "unit_price": 10.0}],
        origin="supplier_discovery",
    )

    result = review_profile_price_candidate(
        store.database_path,
        "mosreg_market",
        "price-review",
        1,
        int(saved[0]["id"]),
        review_status="rejected",
    )

    detail = get_tender_payload(store.database_path, "mosreg_market", "price-review")
    profile = detail["product_profiles"][0]
    candidates = store.list_price_candidates("mosreg_market", "price-review", 1)
    assert result == {
        "ok": True,
        "position_index": 1,
        "candidate_id": saved[0]["id"],
        "review_status": "rejected",
        "supplier_option_index": None,
    }
    assert candidates[0]["review_status"] == "rejected"
    assert "economics" not in profile["raw_payload"]
    assert "supplier_options" not in profile["raw_payload"]
    assert detail["economics"]["status"] == "needs_costs"


def _store_with_profile(tmp_path) -> TenderStore:
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="price-review",
            url="https://market.mosreg.ru/Trade/ViewTrade/price-review",
            title="Paper tender",
            price=100000.0,
        )
    )
    store.upsert_product_profiles(
        "mosreg_market",
        "price-review",
        [
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="price-review",
                position_index=1,
                product_name="Paper A4",
                quantity=10,
                unit="pack",
            )
        ],
    )
    return store


def _flag_ids(candidate: dict) -> set[str]:
    return {str(flag["id"]) for flag in candidate.get("quality_flags", [])}
