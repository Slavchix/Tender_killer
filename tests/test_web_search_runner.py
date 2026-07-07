from __future__ import annotations

from tender_killer.pipeline import PipelineStats
from tender_killer.web_search_runner import WebAutoSearchScheduler
from tender_killer.web_search_runner import WebSearchRunner


class FakeSettings:
    telegram_bot_token = ""
    telegram_chat_id = ""


def test_web_search_runner_skips_overlapping_runs() -> None:
    captured: dict[str, object] = {}

    def fake_pipeline_runner(settings, collection):
        captured["nested"] = search_runner.run(trigger="manual")
        return PipelineStats(fetched=7, saved=3, matched=2, notified=0, failed_sources=0)

    search_runner = WebSearchRunner(
        settings_factory=lambda: FakeSettings(),
        pipeline_runner=fake_pipeline_runner,
    )

    payload = search_runner.run(trigger="manual")

    assert payload["ok"] is True
    assert payload["running"] is False
    assert payload["trigger"] == "manual"
    assert payload["stats"]["fetched"] == 7
    assert captured["nested"] == {
        "ok": False,
        "running": True,
        "status": "already_running",
        "message": "Поиск уже идет. Дождитесь завершения обновления.",
    }


def test_web_auto_search_scheduler_runs_shared_runner_when_due() -> None:
    calls: list[tuple[object, str]] = []
    current_time = [100.0]

    class FakeRunner:
        def run(self, filters_payload=None, trigger="manual"):
            calls.append((filters_payload, trigger))
            return {"ok": True, "trigger": trigger}

    scheduler = WebAutoSearchScheduler(
        search_runner=FakeRunner(),
        interval_seconds=3600,
        clock=lambda: current_time[0],
    )

    assert scheduler.run_if_due() == {"ran": False}
    current_time[0] = 3700.0

    assert scheduler.run_if_due() == {"ran": True, "payload": {"ok": True, "trigger": "auto"}}
    assert calls == [(None, "auto")]
