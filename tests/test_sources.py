from tender_killer.config import Settings
from tender_killer.filter_store import FilterProfileCollection, NamedFilterProfile
from tender_killer.filters import FilterProfile
from tender_killer.sources import build_adapters, build_adapters_for_collection


def settings(tmp_path):
    return Settings(
        database_path=tmp_path / "db.sqlite",
        telegram_bot_token=None,
        telegram_chat_id=None,
        dry_run=True,
        moscow_url="https://moscow.test/api",
        mosreg_url="https://mosreg.test/api",
        filter_profile_path=None,
        request_timeout_seconds=7,
        bot_auto_search_minutes=30,
    )


def test_build_adapters_uses_selected_sources(tmp_path):
    adapters = build_adapters(FilterProfile(keywords=(), sources=("mosreg",)), settings(tmp_path))

    assert [adapter.source for adapter in adapters] == ["mosreg_market"]
    assert adapters[0].url == "https://mosreg.test/api"


def test_build_adapters_uses_all_sources_by_default(tmp_path):
    adapters = build_adapters(FilterProfile.default(), settings(tmp_path))

    assert [adapter.source for adapter in adapters] == ["moscow_supplier_portal", "mosreg_market"]


def test_build_adapters_for_collection_uses_union_of_active_profile_sources(tmp_path):
    collection = FilterProfileCollection(
        profiles=(
            NamedFilterProfile("paper", "Бумага", FilterProfile(keywords=(), sources=("moscow",))),
            NamedFilterProfile("cable", "Кабель", FilterProfile(keywords=(), sources=("mosreg",))),
            NamedFilterProfile("disabled", "Выкл", FilterProfile(keywords=(), sources=("moscow",))),
        ),
        active_profile_ids=("paper", "cable"),
    )

    adapters = build_adapters_for_collection(collection, settings(tmp_path))

    assert [adapter.source for adapter in adapters] == ["moscow_supplier_portal", "mosreg_market"]


def test_build_adapters_for_collection_skips_sources_when_no_active_profiles(tmp_path):
    collection = FilterProfileCollection(
        profiles=(
            NamedFilterProfile("paper", "Бумага", FilterProfile(keywords=(), sources=("moscow",))),
        ),
        active_profile_ids=(),
    )

    adapters = build_adapters_for_collection(collection, settings(tmp_path))

    assert adapters == []
