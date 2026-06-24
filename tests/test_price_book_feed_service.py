from tender_killer.models import ProductProfile, Tender
from tender_killer.price_book_feed_service import stage_tender_price_book_feed
from tender_killer.storage import TenderStore
from tender_killer.tender_detail_service import get_tender_payload


def test_stage_tender_price_book_feed_turns_feed_rows_into_review_candidates(tmp_path) -> None:
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="price-book-feed",
            url="https://market.mosreg.ru/Trade/ViewTrade/price-book-feed",
            title="Office paper tender",
            price=100000.0,
        )
    )
    store.upsert_product_profiles(
        "mosreg_market",
        "price-book-feed",
        [
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="price-book-feed",
                position_index=1,
                product_name="Office paper A4",
                quantity=20,
                unit="pack",
            ),
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="price-book-feed",
                position_index=2,
                product_name="Folder A4",
                quantity=5,
                unit="pack",
            ),
        ],
    )

    result = stage_tender_price_book_feed(
        store.database_path,
        "mosreg_market",
        "price-book-feed",
        [
            {
                "position_index": 1,
                "supplier": "OfficeMag",
                "sku": "110532",
                "name": "Office paper A4, 500 sheets",
                "unit_price": "359,50",
                "currency": "RUB",
                "vat_mode": "vat_included",
                "availability": "in_stock",
                "delivery_note": "Delivery included",
                "unit": "pack",
                "pack_quantity": 1,
                "stock_quantity": 120,
                "source_url": "https://www.officemag.ru/catalog/goods/110532/",
                "valid_until": "2026-07-01",
            },
            {
                "product_name": "Folder A4",
                "supplier_name": "Komus",
                "unit_price": 44,
                "vat_mode": "vat_included",
                "availability": "in_stock",
                "delivery_note": "Delivery included",
                "unit": "pack",
                "pack_quantity": 1,
            },
            {"name": "No matching product", "unit_price": 10},
        ],
        feed_name="June price book",
    )

    detail = get_tender_payload(store.database_path, "mosreg_market", "price-book-feed")
    profiles = {profile["position_index"]: profile for profile in detail["product_profiles"]}

    assert result["ok"] is True
    assert result["feed_name"] == "June price book"
    assert result["stage_mode"] == "all"
    assert result["rows_count"] == 3
    assert result["matched_count"] == 2
    assert result["staged_count"] == 2
    assert result["skipped_count"] == 1
    assert result["positions"] == [
        {"position_index": 1, "staged_count": 1},
        {"position_index": 2, "staged_count": 1},
    ]
    assert result["quality_report"]["summary"]["exact_position_count"] == 1
    assert result["quality_report"]["summary"]["name_match_count"] == 1
    assert result["quality_report"]["summary"]["review_count"] == 1
    first_candidate = profiles[1]["price_candidates"][0]
    assert first_candidate["origin"] == "price_book_feed"
    assert first_candidate["source_kind"] == "price_book_feed"
    assert first_candidate["provider"] == "officemag"
    assert first_candidate["unit_price"] == 359.5
    assert first_candidate["quality_status"] == "ready"
    assert first_candidate["auto_eligible"] is True
    assert first_candidate["raw_payload"]["feed_name"] == "June price book"
    assert first_candidate["raw_payload"]["sku"] == "110532"
    assert first_candidate["pricing_passport"]["next_action"] == "ready_to_confirm"
    assert profiles[2]["price_candidates"][0]["provider"] == "komus"


def test_stage_tender_price_book_feed_reports_quality_and_stages_confident_rows_only(tmp_path) -> None:
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="price-book-quality",
            url="https://market.mosreg.ru/Trade/ViewTrade/price-book-quality",
            title="Office supplies",
            price=100000.0,
        )
    )
    store.upsert_product_profiles(
        "mosreg_market",
        "price-book-quality",
        [
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="price-book-quality",
                position_index=1,
                product_name="Office paper A4",
                quantity=20,
                unit="pack",
            ),
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="price-book-quality",
                position_index=2,
                product_name="Folder A4",
                quantity=5,
                unit="pack",
            ),
        ],
    )

    result = stage_tender_price_book_feed(
        store.database_path,
        "mosreg_market",
        "price-book-quality",
        [
            {"position_index": 1, "name": "Office paper A4", "unit_price": 359},
            {"product_name": "Folder A4 blue", "unit_price": 44},
            {"product_name": "Unknown clips", "unit_price": 10},
            {"position_index": 2, "name": "Folder A4 without price"},
        ],
        feed_name="June price book",
        stage_mode="confident",
    )

    assert result["stage_mode"] == "confident"
    assert result["quality_report"]["summary"] == {
        "rows_count": 4,
        "exact_position_count": 1,
        "name_match_count": 1,
        "review_count": 1,
        "error_count": 1,
        "stageable_count": 2,
        "selected_count": 1,
    }
    assert result["quality_report"]["rows"][0]["status"] == "exact_position"
    assert result["quality_report"]["rows"][0]["stage_action"] == "staged"
    assert result["quality_report"]["rows"][1]["status"] == "name_match"
    assert result["quality_report"]["rows"][1]["stage_action"] == "left_for_review"
    assert result["quality_report"]["rows"][2]["status"] == "review"
    assert result["quality_report"]["rows"][2]["reason"] == "no_matching_position"
    assert result["quality_report"]["rows"][3]["status"] == "error"
    assert result["quality_report"]["rows"][3]["reason"] == "missing_unit_price"
    assert result["staged_count"] == 1
    assert result["skipped_count"] == 3

    detail = get_tender_payload(store.database_path, "mosreg_market", "price-book-quality")
    profiles = {profile["position_index"]: profile for profile in detail["product_profiles"]}
    assert len(profiles[1]["price_candidates"]) == 1
    assert profiles[2].get("price_candidates", []) == []
