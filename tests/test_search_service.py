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
            matched_new=1,
            matched_existing=0,
            notified=0,
            failed_sources=1,
            failed_source_names=("mosreg_market",),
            failed_source_errors=("mosreg_market: timeout",),
            source_counts=(("moscow_supplier_portal", 1),),
            law_counts=(("44-ФЗ", 1),),
            region_counts=(("Москва", 1),),
        )

    payload = run_search_payload(
        FakeSettings(),
        fake_runner,
        {"filters": {"source": "moscow_supplier_portal", "status": "active", "q": "paper"}},
    )

    assert payload["ok"] is True
    assert payload["notifications_enabled"] is True
    assert payload["stats"]["fetched"] == 3
    assert payload["stats"]["matched_new"] == 1
    assert payload["stats"]["source_counts"] == [{"value": "moscow_supplier_portal", "count": 1}]
    assert payload["stats"]["law_counts"] == [{"value": "44-ФЗ", "count": 1}]
    assert payload["stats"]["region_counts"] == [{"value": "Москва", "count": 1}]
    assert payload["stats"]["failed_source_names"] == ["mosreg_market"]
    assert captured["settings"].telegram_bot_token == "token"
    assert captured["profile"].sources == ("moscow",)
    assert captured["profile"].keywords == ("paper",)
