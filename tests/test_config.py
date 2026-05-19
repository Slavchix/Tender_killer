from pathlib import Path

from tender_killer.config import Settings


def test_settings_reads_filter_profile_path(monkeypatch):
    monkeypatch.setenv("TENDER_KILLER_FILTERS", "filters.json")
    monkeypatch.delenv("TENDER_KILLER_AUTO_SEARCH_MINUTES", raising=False)

    settings = Settings.from_env()

    assert settings.filter_profile_path == Path("filters.json")
    assert settings.bot_auto_search_minutes == 0


def test_settings_has_no_filter_profile_by_default(monkeypatch):
    monkeypatch.delenv("TENDER_KILLER_FILTERS", raising=False)

    settings = Settings.from_env()

    assert settings.filter_profile_path is None


def test_settings_reads_bot_auto_search_minutes(monkeypatch):
    monkeypatch.setenv("TENDER_KILLER_AUTO_SEARCH_MINUTES", "15")

    settings = Settings.from_env()

    assert settings.bot_auto_search_minutes == 15
