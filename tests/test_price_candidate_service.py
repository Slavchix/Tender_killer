from tender_killer.models import ProductProfile, Tender
from tender_killer.price_candidate_service import confirm_ready_price_candidates
from tender_killer.price_candidate_service import rank_profile_price_candidates
from tender_killer.price_candidate_service import review_profile_price_candidate
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
        "review_status": "confirmed",
        "quality_status": "ready",
        "auto_eligible": True,
        "quality_flags": [],
    }
    assert detail["economics"]["supplier_cost"] == 8800.0


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
