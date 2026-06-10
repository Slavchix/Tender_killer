from __future__ import annotations

from tender_killer.eis_reference_service import build_eis_reference


def test_build_eis_reference_prepares_official_lookup_links_without_fetching() -> None:
    reference = build_eis_reference(
        {
            "source": "mosreg_market",
            "external_id": "local-1",
            "title": "Paper supply",
            "law": "44-\u0424\u0417",
            "customer": "School",
            "customer_inn": "5047152960",
            "raw_payload": {"purchaseNumber": "0373200000126000012"},
        }
    )

    assert reference["version"] == 1
    assert reference["status"] == "ready"
    assert reference["network_fetch_enabled"] is False
    assert reference["identifiers"] == {
        "purchase_number": "0373200000126000012",
        "customer_inn": "5047152960",
        "law": "44-\u0424\u0417",
    }
    assert reference["queries"] == [
        {"kind": "purchase_number", "value": "0373200000126000012"},
        {"kind": "customer_inn", "value": "5047152960"},
    ]
    assert [link["id"] for link in reference["links"]] == [
        "eis_purchase_search",
        "eis_contracts_by_customer",
        "eis_complaints_by_customer",
        "eis_rnp_by_customer",
        "eis_home",
    ]
    assert "searchString=0373200000126000012" in reference["links"][0]["url"]
    assert "searchString=5047152960" in reference["links"][1]["url"]


def test_build_eis_reference_falls_back_to_title_search_when_no_official_ids() -> None:
    reference = build_eis_reference(
        {
            "source": "moscow_supplier_portal",
            "external_id": "Auction102",
            "title": "Decorative panels for cabinets",
            "raw_payload": {},
        }
    )

    assert reference["status"] == "manual_lookup"
    assert reference["identifiers"]["purchase_number"] is None
    assert reference["identifiers"]["customer_inn"] is None
    assert reference["queries"] == [{"kind": "title", "value": "Decorative panels for cabinets"}]
    assert reference["links"][0]["id"] == "eis_purchase_search"
    assert "Decorative+panels+for+cabinets" in reference["links"][0]["url"]
