from tender_killer.bot import (
    apply_filter_command,
    format_filter_profile,
    format_search_summary,
    parse_csv_args,
)
from tender_killer.filter_store import FilterProfileStore
from tender_killer.pipeline import PipelineStats


def test_parse_csv_args_accepts_spaces_and_commas():
    assert parse_csv_args("Москва, Московская область") == ("Москва", "Московская область")


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
            fetched=25,
            saved=25,
            matched=1,
            notified=1,
            failed_sources=1,
            failed_source_names=("moscow_supplier_portal",),
        )
    )

    assert "FailedSources=1" in text
    assert "Упали источники: moscow_supplier_portal" in text
