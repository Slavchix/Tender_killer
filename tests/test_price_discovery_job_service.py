from __future__ import annotations

import time
from pathlib import Path

from tender_killer import price_discovery_job_service as jobs


def test_start_tender_price_discovery_job_tracks_background_progress(tmp_path, monkeypatch) -> None:
    with jobs._LOCK:
        jobs._JOBS.clear()

    calls: list[dict[str, object]] = []

    def fake_run(
        database_path: str | Path,
        source: str,
        external_id: str,
        *,
        max_positions: int | None = None,
        progress_callback=None,
    ) -> dict[str, object]:
        calls.append(
            {
                "database_path": str(database_path),
                "source": source,
                "external_id": external_id,
                "max_positions": max_positions,
            }
        )
        if progress_callback is not None:
            progress_callback(
                {
                    "total_profiles": 2,
                    "searched_count": 1,
                    "limited_count": 1,
                    "partial": True,
                    "positions": [{"position_index": 1, "status": "staged", "staged_count": 1}],
                }
            )
        return {
            "ok": True,
            "total_profiles": 2,
            "searched_count": 2,
            "limited_count": 0,
            "partial": False,
            "staged_count": 1,
            "ready_count": 1,
            "review_count": 0,
            "blocked_count": 0,
            "no_candidates_count": 0,
            "error_count": 0,
            "positions": [{"position_index": 1, "status": "staged", "staged_count": 1}],
        }

    monkeypatch.setattr(jobs, "run_tender_supplier_price_discovery", fake_run)

    started = jobs.start_tender_price_discovery_job(tmp_path / "db.sqlite", "moscow_supplier_portal", "Auction1")
    deadline = time.monotonic() + 2
    final = started
    while time.monotonic() < deadline:
        final = jobs.get_tender_price_discovery_job(started["job_id"])
        if final["status"] == jobs.JOB_STATUS_SUCCEEDED:
            break
        time.sleep(0.01)

    assert final["status"] == jobs.JOB_STATUS_SUCCEEDED
    assert final["searched_count"] == 2
    assert final["staged_count"] == 1
    assert final["result"]["ready_count"] == 1
    assert calls == [
        {
            "database_path": str(tmp_path / "db.sqlite"),
            "source": "moscow_supplier_portal",
            "external_id": "Auction1",
            "max_positions": jobs.DEFAULT_PRICE_DISCOVERY_JOB_MAX_POSITIONS,
        }
    ]
