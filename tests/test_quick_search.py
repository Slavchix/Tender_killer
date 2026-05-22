from tender_killer.filter_store import FilterProfileStore
from tender_killer.quick_search import (
    QUICK_SEARCH_PROFILE_ID,
    format_quick_search_confirmation,
    parse_quick_search_text,
    save_quick_search_profile,
)


def test_parse_quick_search_text_extracts_region_law_price_and_keywords():
    draft = parse_quick_search_text("строительные материалы в Москве и Московской области до 2 млн 44-ФЗ")

    assert draft.original_text == "строительные материалы в Москве и Московской области до 2 млн 44-ФЗ"
    assert draft.title == "строительные материалы"
    assert draft.profile.keywords == ("строительные материалы",)
    assert draft.profile.regions == ("Москва", "Московская область")
    assert draft.profile.laws == ("44-ФЗ",)
    assert draft.profile.max_price == 2_000_000
    assert draft.profile.min_price is None
    assert draft.profile.only_active is True


def test_parse_quick_search_text_extracts_okpd2_and_source_words():
    draft = parse_quick_search_text("кабель 27.32.13 только МО 223-ФЗ от 100 тыс до 1 млн")

    assert draft.profile.keywords == ("кабель",)
    assert draft.profile.regions == ("Московская область",)
    assert draft.profile.laws == ("223-ФЗ",)
    assert draft.profile.okpd2 == ("27.32.13",)
    assert draft.profile.min_price == 100_000
    assert draft.profile.max_price == 1_000_000


def test_save_quick_search_profile_upserts_without_removing_existing_profiles(tmp_path):
    store = FilterProfileStore(tmp_path / "filters.json")
    existing = store.add_profile("Бумага", keywords=("бумага",), regions=("Москва",))
    draft = parse_quick_search_text("медицинские маски Москва до 500 тыс 44-ФЗ")

    quick = save_quick_search_profile(store, draft)
    updated = save_quick_search_profile(store, parse_quick_search_text("кабель МО до 1 млн"))
    collection = store.load_collection()

    assert quick.id == QUICK_SEARCH_PROFILE_ID
    assert updated.id == QUICK_SEARCH_PROFILE_ID
    assert existing.id in {profile.id for profile in collection.profiles}
    assert QUICK_SEARCH_PROFILE_ID in {profile.id for profile in collection.profiles}
    assert existing.id in collection.active_profile_ids
    assert QUICK_SEARCH_PROFILE_ID in collection.active_profile_ids
    assert len([profile for profile in collection.profiles if profile.id == QUICK_SEARCH_PROFILE_ID]) == 1
    assert updated.profile.keywords == ("кабель",)


def test_format_quick_search_confirmation_shows_parsed_profile(tmp_path):
    store = FilterProfileStore(tmp_path / "filters.json")
    draft = parse_quick_search_text("строительные материалы Москва МО до 2 млн 44-ФЗ")
    profile = save_quick_search_profile(store, draft)

    text = format_quick_search_confirmation(profile, draft)

    assert "Быстрый вход сохранен" in text
    assert "Запрос: строительные материалы Москва МО до 2 млн 44-ФЗ" in text
    assert "Ключевые слова: строительные материалы" in text
    assert "Регионы: Москва, Московская область" in text
    assert "Цена: любая - 2 000 000" in text
    assert "Запустить быстрый поиск" in text
