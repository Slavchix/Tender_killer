from __future__ import annotations

from tender_killer.supplier_provider_policy import get_supplier_provider_policy
from tender_killer.supplier_provider_policy import supplier_fetch_decision


REQUIRED_POLICY_FIELDS = {
    "provider",
    "label",
    "default_mode",
    "allow_quick_links",
    "allow_public_search_fetch",
    "allow_product_page_fetch",
    "allow_browser_fetch",
    "allow_internal_api",
    "recommended_flow",
    "risk_level",
    "operator_note",
}


def test_provider_policy_documents_required_supplier_modes() -> None:
    officemag = get_supplier_provider_policy("officemag")
    vseinstrumenti = get_supplier_provider_policy("vseinstrumenti")
    komus = get_supplier_provider_policy("komus")

    assert REQUIRED_POLICY_FIELDS.issubset(officemag.keys())
    assert officemag["default_mode"] == "limited_public_search"
    assert officemag["allow_quick_links"] is True
    assert officemag["allow_public_search_fetch"] is True
    assert officemag["public_search_max_positions"] == 5
    assert officemag["allow_product_page_fetch"] is True
    assert officemag["allow_browser_fetch"] is False
    assert officemag["allow_internal_api"] is False

    assert vseinstrumenti["allow_public_search_fetch"] is True
    assert vseinstrumenti["public_search_max_positions"] == 5
    assert vseinstrumenti["allow_product_page_fetch"] is True

    assert komus["allow_quick_links"] is True
    assert komus["allow_public_search_fetch"] is True
    assert komus["public_search_max_positions"] == 5
    assert komus["allow_product_page_fetch"] is True
    assert komus["recommended_flow"] == "limited_search_feed_quote"


def test_supplier_fetch_decision_separates_quick_links_from_collectors() -> None:
    quick_link = supplier_fetch_decision(
        "https://www.officemag.ru/search/?q=paper",
        provider="officemag",
        action="quick_link",
        tender_position_count=20,
    )
    small_search = supplier_fetch_decision(
        "https://www.officemag.ru/search/?q=paper",
        provider="officemag",
        action="public_search_fetch",
        tender_position_count=1,
    )
    large_search = supplier_fetch_decision(
        "https://www.officemag.ru/search/?q=paper",
        provider="officemag",
        action="public_search_fetch",
        tender_position_count=20,
    )
    manual_product = supplier_fetch_decision(
        "https://www.officemag.ru/catalog/goods/110532/",
        provider="officemag",
        action="product_page_fetch",
        tender_position_count=20,
    )

    assert quick_link["allowed"] is True
    assert small_search["allowed"] is True
    assert large_search["allowed"] is False
    assert large_search["reason"] == "large_tender_manual_required"
    assert manual_product["allowed"] is True


def test_supplier_fetch_decision_limits_active_search_to_small_tenders() -> None:
    small_tender = supplier_fetch_decision(
        "https://www.vseinstrumenti.ru/search/?what=cement",
        provider="vseinstrumenti",
        action="public_search_fetch",
        tender_position_count=5,
    )
    large_tender = supplier_fetch_decision(
        "https://www.vseinstrumenti.ru/search/?what=cement",
        provider="vseinstrumenti",
        action="public_search_fetch",
        tender_position_count=6,
    )

    assert small_tender["allowed"] is True
    assert large_tender["allowed"] is False
    assert large_tender["reason"] == "large_tender_manual_required"


def test_supplier_fetch_decision_blocks_private_or_internal_urls() -> None:
    unsafe_urls = [
        "https://petrovich.ru/login?token=secret",
        "https://petrovich.ru/api-common/product/get_price?id=1",
        "https://petrovich.ru/catalog/item/ajax/price",
        "https://petrovich.ru/graphql?query={price}",
        "https://petrovich.ru/orders/123",
        "https://petrovich.ru/catalog/item?session=abc",
    ]

    for url in unsafe_urls:
        decision = supplier_fetch_decision(
            url,
            provider="petrovich",
            action="product_page_fetch",
            tender_position_count=1,
        )
        assert decision["allowed"] is False
        assert decision["reason"] == "unsafe_url"

    safe_product = supplier_fetch_decision(
        "https://petrovich.ru/catalog/cement-25kg/",
        provider="petrovich",
        action="product_page_fetch",
        tender_position_count=12,
    )
    assert safe_product["allowed"] is True
