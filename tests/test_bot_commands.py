import asyncio
from types import SimpleNamespace

from tender_killer.bot import (
    MENU,
    apply_filter_command,
    apply_profile_edit,
    create_profile_from_template,
    format_filter_profile,
    format_tender_analysis_reply,
    format_tender_documents_reply,
    format_profile_details,
    format_profiles,
    format_search_summary,
    format_test_search_summary,
    format_sources_status,
    parse_csv_args,
    text_menu_handler,
)
from tender_killer.filter_store import FilterProfileCollection, FilterProfileStore, NamedFilterProfile
from tender_killer.filters import FilterProfile
from tender_killer.pipeline import PipelineStats
from tender_killer.quick_search import QUICK_SEARCH_PROFILE_ID
from tender_killer.telegram_chat_service import get_remembered_telegram_chat_id


def test_parse_csv_args_accepts_spaces_and_commas():
    assert parse_csv_args("Москва, Московская область") == ("Москва", "Московская область")


def test_menu_does_not_show_legacy_slash_filter_buttons():
    labels = [
        button.text
        for row in MENU.keyboard
        for button in row
    ]

    assert "/sources moscow, mosreg" not in labels
    assert "/region Москва, Московская область" not in labels
    assert "/price 10000 500000" not in labels
    assert "/okpd2 17.12, 27.32.13" not in labels


def test_menu_is_notification_only():
    labels = [
        button.text
        for row in MENU.keyboard
        for button in row
    ]

    assert labels == ["Статус источников"]


def test_apply_filter_command_updates_region_price_okpd2_sources_and_active(tmp_path):
    store = FilterProfileStore(tmp_path / "filters.json")

    apply_filter_command(store, "region", "Москва, Московская область")
    apply_filter_command(store, "price", "10000 500000")
    apply_filter_command(store, "okpd2", "17.12, 27.32.13")
    apply_filter_command(store, "sources", "moscow")
    apply_filter_command(store, "active", "on")

    profile = store.load()
    assert profile.regions == ("Москва", "Московская область")
    assert profile.min_price == 10_000
    assert profile.max_price == 500_000
    assert profile.okpd2 == ("17.12", "27.32.13")
    assert profile.sources == ("moscow",)
    assert profile.only_active is True


def test_format_filter_profile_shows_sources_and_core_filters(tmp_path):
    store = FilterProfileStore(tmp_path / "filters.json")
    profile = store.update(
        regions=("Москва",),
        min_price=10_000,
        max_price=500_000,
        okpd2=("17.12",),
        sources=("moscow", "mosreg"),
        only_active=True,
        keywords=(),
    )

    text = format_filter_profile(profile)

    assert "Регион: Москва" in text
    assert "Цена: 10 000 - 500 000" in text
    assert "ОКПД2: 17.12" in text
    assert "Площадки: Москва: zakupki.mos.ru; МО: market.mosreg.ru" in text
    assert "Только активные: да" in text


def test_format_search_summary_shows_failed_source_names():
    text = format_search_summary(
        PipelineStats(
            fetched=126,
            saved=25,
            matched=46,
            matched_new=24,
            matched_existing=22,
            notified=5,
            failed_sources=1,
            failed_source_names=("moscow_supplier_portal",),
            failed_source_errors=("moscow_supplier_portal: HTTP Error 500",),
            source_counts=(("moscow_supplier_portal", 24), ("mosreg_market", 22)),
            law_counts=(("44-ФЗ", 26), ("223-ФЗ", 12), ("Запрос цен", 8)),
            region_counts=(("Москва", 22), ("Московская область", 21)),
        )
    )

    assert "Просмотрено: 126" in text
    assert "Новых в базе: 25" in text
    assert "Релевантных: 46" in text
    assert "Новые релевантные: 24" in text
    assert "Уже известных релевантных: 22" in text
    assert "44-ФЗ: 26" in text
    assert "Москва: 22" in text
    assert "Москва: zakupki.mos.ru: 24" in text
    assert "Упали источники: moscow_supplier_portal" in text
    assert "moscow_supplier_portal: HTTP Error 500" in text


def test_format_test_search_summary_explains_preview_mode():
    text = format_test_search_summary(
        PipelineStats(fetched=50, saved=0, matched=2, matched_new=0, matched_existing=2, notified=2, failed_sources=0)
    )

    assert "Тест поиска" in text
    assert "подходящие карточки отправлены повторно" in text


def test_format_profiles_shows_active_and_disabled_profiles():
    collection = FilterProfileCollection(
        profiles=(
            NamedFilterProfile("paper", "Бумага", FilterProfile(keywords=("бумага",))),
            NamedFilterProfile("cable", "Кабель", FilterProfile(keywords=("кабель",))),
        ),
        active_profile_ids=("paper",),
    )

    text = format_profiles(collection)

    assert "on Бумага [paper]" in text
    assert "off Кабель [cable]" in text


def test_format_sources_status_shows_last_stats_and_errors():
    text = format_sources_status(
        PipelineStats(
            fetched=0,
            saved=0,
            matched=0,
            notified=0,
            failed_sources=1,
            failed_source_errors=("moscow_supplier_portal: HTTP Error 500",),
        )
    )

    assert "Последний запуск" in text
    assert "moscow_supplier_portal: HTTP Error 500" in text


def test_format_tender_documents_reply_lists_saved_documents():
    text = format_tender_documents_reply(
        {
            "title": "Поставка бумаги",
            "url": "https://example.test/tender",
            "document_records": [
                {"name": "Извещение.docx", "url": "https://example.test/notice.docx"},
                {"name": "Проект договора.pdf", "url": "https://example.test/contract.pdf"},
            ],
        }
    )

    assert "Документы закупки" in text
    assert "Извещение.docx" in text
    assert "https://example.test/contract.pdf" in text


def test_format_tender_analysis_reply_shows_existing_checklist():
    text = format_tender_analysis_reply(
        {
            "title": "Поставка бумаги",
            "analysis": {
                "summary": "Срок поставки короткий, сертификаты нужны.",
                "checklist": [
                    {"label": "Проверить сертификаты", "severity": "high"},
                    {"label": "Уточнить доставку", "severity": "medium"},
                ],
            },
        }
    )

    assert "Анализ закупки" in text
    assert "Срок поставки короткий" in text
    assert "Проверить сертификаты" in text


def test_apply_profile_edit_updates_named_profile(tmp_path):
    store = FilterProfileStore(tmp_path / "filters.json")
    profile = store.add_profile("Бумага", keywords=("бумага",))

    updated = apply_profile_edit(store, profile.id, "okpd2", "17.12, 17.23")

    assert updated.profile.okpd2 == ("17.12", "17.23")


def test_apply_profile_edit_updates_law_and_stage(tmp_path):
    store = FilterProfileStore(tmp_path / "filters.json")
    profile = store.add_profile("Бумага", keywords=("бумага",))

    apply_profile_edit(store, profile.id, "law", "44-ФЗ")
    updated = apply_profile_edit(store, profile.id, "stage", "Подача заявок")

    assert updated.profile.laws == ("44-ФЗ",)
    assert updated.profile.statuses == ("прием предложений", "прием заявок", "active")
    assert updated.profile.only_active is True


def test_create_profile_from_template_sets_material_defaults(tmp_path):
    store = FilterProfileStore(tmp_path / "filters.json")

    profile = create_profile_from_template(store, "Бумага/канцелярия")

    assert profile.name == "Бумага/канцелярия"
    assert "бумаг" in profile.profile.keywords
    assert "услуги" in profile.profile.exclude_keywords
    assert profile.profile.sources == ("mosreg",)
    assert profile.id in store.load_collection().active_profile_ids


def test_format_profile_details_shows_law_stage_region_price_sources():
    profile = NamedFilterProfile(
        "paper",
        "Бумага",
        FilterProfile(
            keywords=("бумаг",),
            laws=("44-ФЗ",),
            statuses=("прием предложений",),
            regions=("Московская область",),
            sources=("mosreg",),
            min_price=10_000,
            max_price=500_000,
            okpd2=("17.12",),
        ),
    )

    text = format_profile_details(profile)

    assert "Закон: 44-ФЗ" in text
    assert "Этап: прием предложений" in text
    assert "Регионы: Московская область" in text
    assert "Цена: 10 000 - 500 000" in text
    assert "Площадки: МО: market.mosreg.ru" in text


def test_profile_toggle_command_disables_profile(tmp_path):
    store = FilterProfileStore(tmp_path / "filters.json")
    profile = store.add_profile("Бумага", keywords=("бумага",))

    store.set_profile_enabled(profile.id, False)
    collection = store.load_collection()

    assert profile.id not in collection.active_profile_ids


class FakeMessage:
    def __init__(self, text: str) -> None:
        self.text = text
        self.replies: list[str] = []

    async def reply_text(self, text: str, **kwargs) -> None:
        self.replies.append(text)


class FakeChat:
    id = 777


def test_text_menu_handler_accepts_quick_search_text_without_removing_filters(tmp_path):
    store = FilterProfileStore(tmp_path / "filters.json")
    existing = store.add_profile("Бумага", keywords=("бумага",))
    message = FakeMessage("строительные материалы Москва МО до 2 млн 44-ФЗ")
    update = SimpleNamespace(message=message)
    context = SimpleNamespace(
        user_data={},
        application=SimpleNamespace(bot_data={"filter_store": store}),
    )

    asyncio.run(text_menu_handler(update, context))
    collection = store.load_collection()
    quick_profile = next(profile for profile in collection.profiles if profile.id == QUICK_SEARCH_PROFILE_ID)

    assert existing.id in {profile.id for profile in collection.profiles}
    assert existing.id in collection.active_profile_ids
    assert QUICK_SEARCH_PROFILE_ID in collection.active_profile_ids
    assert quick_profile.profile.keywords == ("строительные материалы",)
    assert message.replies
    assert "Быстрый вход сохранен" in message.replies[0]
    assert "Запустить быстрый поиск" in message.replies[0]


def test_text_menu_handler_remembers_chat_id_for_site_notifications(tmp_path):
    store = FilterProfileStore(tmp_path / "filters.json")
    database_path = tmp_path / "tenders.sqlite"
    message = FakeMessage("строительные материалы Москва")
    update = SimpleNamespace(message=message, effective_chat=FakeChat())
    context = SimpleNamespace(
        user_data={},
        application=SimpleNamespace(
            bot_data={
                "filter_store": store,
                "settings": SimpleNamespace(database_path=database_path),
            }
        ),
    )

    asyncio.run(text_menu_handler(update, context))

    assert get_remembered_telegram_chat_id(database_path) == "777"
