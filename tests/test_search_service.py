from __future__ import annotations

from tender_killer.pipeline import PipelineStats
from tender_killer.search_service import run_search_payload


def test_run_search_payload_passes_site_filter_collection_to_runner():
    class FakeSettings:
        telegram_bot_token = "token"
        telegram_chat_id = "123"

    captured = {}

    def fake_runner(settings, collection):
        captured["settings"] = settings
        captured["profile"] = collection.active_profiles()[0].profile
        return PipelineStats(
            fetched=3,
            saved=2,
            matched=1,
            notified=0,
            failed_sources=1,
            failed_source_names=("mosreg_market",),
            failed_source_errors=("mosreg_market: timeout",),
        )

    payload = run_search_payload(
        FakeSettings(),
        fake_runner,
        {"filters": {"source": "moscow_supplier_portal", "status": "active", "q": "paper"}},
    )

    assert payload["ok"] is True
    assert payload["notifications_enabled"] is True
    assert payload["stats"]["fetched"] == 3
    assert payload["stats"]["failed_source_names"] == ["mosreg_market"]
    assert captured["settings"].telegram_bot_token == "token"
    assert captured["profile"].sources == ("moscow",)
    assert captured["profile"].keywords == ("paper",)
