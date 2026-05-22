from pathlib import Path

from tender_killer.config import Settings


def test_settings_reads_filter_profile_path(monkeypatch):
    monkeypatch.setenv("TENDER_KILLER_FILTERS", "filters.json")
    monkeypatch.delenv("TENDER_KILLER_AUTO_SEARCH_MINUTES", raising=False)

    settings = Settings.from_env()

    assert settings.filter_profile_path == Path("filters.json")
    assert settings.bot_auto_search_minutes == 0


def test_settings_reads_local_dotenv_when_environment_missing(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    (tmp_path / ".env").write_text(
        "TELEGRAM_BOT_TOKEN=token-from-dotenv\nTELEGRAM_CHAT_ID=777\n",
        encoding="utf-8",
    )

    settings = Settings.from_env()

    assert settings.telegram_bot_token == "token-from-dotenv"
    assert settings.telegram_chat_id == "777"


def test_settings_has_no_filter_profile_by_default(monkeypatch):
    monkeypatch.delenv("TENDER_KILLER_FILTERS", raising=False)

    settings = Settings.from_env()

    assert settings.filter_profile_path is None


def test_settings_reads_bot_auto_search_minutes(monkeypatch):
    monkeypatch.setenv("TENDER_KILLER_AUTO_SEARCH_MINUTES", "15")

    settings = Settings.from_env()

    assert settings.bot_auto_search_minutes == 15


def test_settings_reads_source_max_pages(monkeypatch):
    monkeypatch.setenv("TENDER_KILLER_SOURCE_MAX_PAGES", "5")

    settings = Settings.from_env()

    assert settings.source_max_pages == 5


def test_settings_reads_source_incremental_overlap_minutes(monkeypatch):
    monkeypatch.setenv("TENDER_KILLER_SOURCE_OVERLAP_MINUTES", "90")

    settings = Settings.from_env()

    assert settings.source_incremental_overlap_minutes == 90
