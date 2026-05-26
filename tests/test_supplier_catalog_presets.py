from __future__ import annotations

from tender_killer.supplier_catalog_presets import supplier_catalog_presets_for_profile


def test_supplier_catalog_presets_match_office_and_building_profiles() -> None:
    office_presets = supplier_catalog_presets_for_profile(
        {
            "product_name": "Office paper A4 80 g/m2",
            "normalized_name": "office paper a4",
            "okpd2": "17.12.14.110",
        }
    )
    building_presets = supplier_catalog_presets_for_profile(
        {
            "product_name": "Cement M500",
            "category": "building materials",
        }
    )

    assert [preset["provider"] for preset in office_presets] == ["officemag", "komus"]
    assert [preset["preset_id"] for preset in office_presets] == [
        "officemag_office_supplies",
        "komus_office_supplies",
    ]
    assert [preset["provider"] for preset in building_presets] == ["petrovich", "vseinstrumenti"]


def test_supplier_catalog_presets_can_be_selected_or_disabled_by_payload() -> None:
    selected = supplier_catalog_presets_for_profile(
        {
            "product_name": "Office paper A4",
            "raw_payload": {"supplier_catalog_preset_ids": ["petrovich_building_materials"]},
        }
    )
    disabled = supplier_catalog_presets_for_profile(
        {
            "product_name": "Office paper A4",
            "raw_payload": {"supplier_catalog_preset_ids": []},
        }
    )

    assert [preset["provider"] for preset in selected] == ["petrovich"]
    assert disabled == []
