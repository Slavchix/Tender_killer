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


def test_supplier_catalog_presets_route_flooring_profiles_to_building_catalogs() -> None:
    laminate_presets = supplier_catalog_presets_for_profile(
        {
            "product_name": "\u041b\u0430\u043c\u0438\u043d\u0430\u0442 \u00ab\u0414\u0443\u0431 \u041a\u0435\u043c\u0435\u0440\u00bb 33 \u043a\u043b\u0430\u0441\u0441 \u0442\u043e\u043b\u0449\u0438\u043d\u0430 12 \u043c\u043c",
            "normalized_name": "\u041b\u0430\u043c\u0438\u043d\u0430\u0442 \u0414\u0443\u0431 \u041a\u0435\u043c\u0435\u0440 12 \u043c\u043c",
        }
    )
    plinth_presets = supplier_catalog_presets_for_profile(
        {
            "product_name": "\u0421\u043e\u0435\u0434\u0438\u043d\u0438\u0442\u0435\u043b\u044c \u0434\u043b\u044f \u043f\u043b\u0438\u043d\u0442\u0443\u0441\u0430 \u00ab\u0414\u0443\u0431 \u0414\u0436\u0435\u0440\u0441\u0438\u00bb, \u0432\u044b\u0441\u043e\u0442\u0430 80 \u043c\u043c",
            "normalized_name": "\u0421\u043e\u0435\u0434\u0438\u043d\u0438\u0442\u0435\u043b\u044c \u0434\u043b\u044f \u043f\u043b\u0438\u043d\u0442\u0443\u0441\u0430 \u0414\u0443\u0431 \u0414\u0436\u0435\u0440\u0441\u0438 80 \u043c\u043c",
        }
    )

    assert [preset["provider"] for preset in laminate_presets] == ["petrovich", "vseinstrumenti", "lemanapro"]
    assert [preset["provider"] for preset in plinth_presets] == ["petrovich", "vseinstrumenti", "lemanapro"]


def test_supplier_catalog_presets_route_cable_accessories_to_tool_and_diy_catalogs() -> None:
    clamp_presets = supplier_catalog_presets_for_profile(
        {
            "product_name": "\u0425\u043e\u043c\u0443\u0442 REXANT nylon 4.0x300 \u043c\u043c 100 \u0448\u0442 black",
            "details": "\u041a\u043e\u043c\u043f\u043b\u0435\u043a\u0442\u0443\u044e\u0449\u0438\u0435 \u0434\u043b\u044f \u043a\u0430\u0431\u0435\u043b\u044c\u043d\u044b\u0445 \u0438\u0437\u0434\u0435\u043b\u0438\u0439",
            "classifier_code": "\u0410\u0440\u043c\u0430\u0442\u0443\u0440\u0430 \u043a\u0430\u0431\u0435\u043b\u044c\u043d\u0430\u044f",
        }
    )
    plug_presets = supplier_catalog_presets_for_profile(
        {
            "product_name": "\u0412\u0438\u043b\u043a\u0430 \u0448\u0442\u0435\u043f\u0441\u0435\u043b\u044c\u043d\u0430\u044f \u0441\u0438\u043b\u043e\u0432\u0430\u044f \u0418\u042d\u041a 16 \u0410",
            "details": "\u041a\u043e\u043c\u043f\u043b\u0435\u043a\u0442\u0443\u044e\u0449\u0438\u0435 \u0434\u043b\u044f \u043a\u0430\u0431\u0435\u043b\u044c\u043d\u044b\u0445 \u0438\u0437\u0434\u0435\u043b\u0438\u0439",
        }
    )

    assert [preset["provider"] for preset in clamp_presets] == ["vseinstrumenti", "lemanapro"]
    assert [preset["provider"] for preset in plug_presets] == ["vseinstrumenti", "lemanapro"]


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
