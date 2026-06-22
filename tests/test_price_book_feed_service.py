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

    assert result == {
        "ok": True,
        "feed_name": "June price book",
        "rows_count": 3,
        "matched_count": 2,
        "staged_count": 2,
        "skipped_count": 1,
        "positions": [
            {"position_index": 1, "staged_count": 1},
            {"position_index": 2, "staged_count": 1},
        ],
    }
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
