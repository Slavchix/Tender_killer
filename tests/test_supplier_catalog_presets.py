from __future__ import annotations

from tender_killer.supplier_catalog_presets import supplier_catalog_presets_for_profile
from tender_killer.supplier_catalog_presets import SUPPLIER_CATALOG_PRESETS


def test_supplier_catalog_presets_keep_real_cyrillic_keywords() -> None:
    keywords_by_provider = {
        str(preset["provider"]): tuple(str(keyword) for keyword in preset["match_keywords"])
        for preset in SUPPLIER_CATALOG_PRESETS
    }

    assert any("\u0431\u0443\u043c\u0430\u0433" in keyword for keyword in keywords_by_provider["officemag"])
    assert any("\u043a\u0430\u043d\u0446\u0435\u043b" in keyword for keyword in keywords_by_provider["komus"])
    assert any("\u0446\u0435\u043c\u0435\u043d\u0442" in keyword for keyword in keywords_by_provider["petrovich"])
    assert any("\u0448\u0443\u0440\u0443\u043f\u043e\u0432\u0435\u0440\u0442" in keyword for keyword in keywords_by_provider["vseinstrumenti"])


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
    assert [preset["provider"] for preset in building_presets] == ["petrovich", "vseinstrumenti", "lemanapro"]


def test_supplier_catalog_presets_match_real_russian_office_paper_without_okpd2() -> None:
    presets = supplier_catalog_presets_for_profile(
        {
            "product_name": "Бумага для офисной техники",
            "normalized_name": "Бумага офисная",
        }
    )

    assert [preset["provider"] for preset in presets] == ["officemag", "komus"]


def test_supplier_catalog_presets_match_printer_consumables_to_office_catalogs() -> None:
    presets = supplier_catalog_presets_for_profile(
        {
            "product_name": "Картридж для электрографических печатающих устройств",
            "normalized_name": "картридж для принтера",
            "okpd2": "28.23.25",
        }
    )

    assert [preset["provider"] for preset in presets] == ["officemag", "komus"]


def test_supplier_catalog_presets_do_not_match_building_inside_unrelated_words() -> None:
    presets = supplier_catalog_presets_for_profile(
        {
            "product_name": "Устройство коммутационное для лаборатории",
            "normalized_name": "электрографическое печатающее устройство",
        }
    )

    assert presets == []


def test_supplier_catalog_presets_match_okpd2_prefixes_without_keyword_text() -> None:
    office_presets = supplier_catalog_presets_for_profile({"product_name": "Лот 1", "okpd2": "28.23.25.000"})
    building_presets = supplier_catalog_presets_for_profile({"product_name": "Лот 2", "okpd2": "23.51.12.110"})

    assert [preset["provider"] for preset in office_presets] == ["officemag", "komus"]
    assert [preset["provider"] for preset in building_presets] == ["petrovich", "vseinstrumenti", "lemanapro"]


def test_supplier_catalog_presets_route_tools_to_tool_catalog_only() -> None:
    presets = supplier_catalog_presets_for_profile(
        {
            "product_name": "Аккумуляторный шуруповерт с набором бит",
            "normalized_name": "шуруповерт аккумуляторный",
        }
    )

    assert [preset["provider"] for preset in presets] == ["vseinstrumenti"]


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
