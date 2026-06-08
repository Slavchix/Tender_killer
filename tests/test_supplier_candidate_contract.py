from __future__ import annotations

from tender_killer.supplier_candidate_contract import normalize_supplier_candidate


def test_normalize_supplier_candidate_preserves_shared_contract_fields() -> None:
    candidate = normalize_supplier_candidate(
        {
            "product_name": "Aziya Cement M500 50 kg",
            "source_url": "https://lemanapro.ru/product/cement-85606184/",
            "unit_price": "522",
            "price_breaks": [
                {"count": "10", "price": "500"},
                {"count": "1", "price": "522"},
            ],
            "match_reasons": ["brand_match", "brand_match"],
        },
        provider="lemanapro",
        source_query="Aziya Cement M500 50 kg",
        source_kind="catalog_hint",
    )

    assert candidate["name"] == "Aziya Cement M500 50 kg"
    assert candidate["product_name"] == "Aziya Cement M500 50 kg"
    assert candidate["url"] == "https://lemanapro.ru/product/cement-85606184/"
    assert candidate["source_url"] == "https://lemanapro.ru/product/cement-85606184/"
    assert candidate["unit_price"] == 522.0
    assert candidate["provider"] == "lemanapro"
    assert candidate["source_query"] == "Aziya Cement M500 50 kg"
    assert candidate["source_kind"] == "catalog_hint"
    assert candidate["price_breaks"] == [
        {"count": 1.0, "price": 522.0},
        {"count": 10.0, "price": 500.0},
    ]
    assert candidate["match_reasons"] == ["brand_match"]
