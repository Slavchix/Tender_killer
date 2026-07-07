from __future__ import annotations

import time
import threading
from pathlib import Path

from tender_killer import price_discovery_job_service as jobs


def test_start_tender_price_discovery_job_tracks_background_progress(monkeypatch) -> None:
    with jobs._LOCK:
        jobs._JOBS.clear()
    database_path = Path("pytest_tmp_price_discovery_job.sqlite")
    database_path.unlink(missing_ok=True)

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

    started = jobs.start_tender_price_discovery_job(database_path, "moscow_supplier_portal", "Auction1")
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
            "database_path": str(database_path),
            "source": "moscow_supplier_portal",
            "external_id": "Auction1",
            "max_positions": jobs.DEFAULT_PRICE_DISCOVERY_JOB_MAX_POSITIONS,
        }
    ]


def test_price_discovery_job_status_survives_memory_cache_reset(monkeypatch) -> None:
    with jobs._LOCK:
        jobs._JOBS.clear()
    database_path = Path("pytest_tmp_price_discovery_persisted.sqlite")
    database_path.unlink(missing_ok=True)

    def fake_run(
        database_path: str | Path,
        source: str,
        external_id: str,
        *,
        max_positions: int | None = None,
        progress_callback=None,
    ) -> dict[str, object]:
        if progress_callback is not None:
            progress_callback({"searched_count": 1, "positions": [{"position_index": 1, "status": "staged"}]})
        return {
            "ok": True,
            "total_profiles": 1,
            "searched_count": 1,
            "limited_count": 0,
            "partial": False,
            "staged_count": 1,
            "ready_count": 1,
            "review_count": 0,
            "blocked_count": 0,
            "no_candidates_count": 0,
            "error_count": 0,
            "positions": [{"position_index": 1, "status": "staged"}],
        }

    monkeypatch.setattr(jobs, "run_tender_supplier_price_discovery", fake_run)

    started = jobs.start_tender_price_discovery_job(database_path, "mosreg_market", "persisted-job")
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline:
        current = jobs.get_tender_price_discovery_job(started["job_id"], database_path)
        if current["status"] == jobs.JOB_STATUS_SUCCEEDED:
            break
        time.sleep(0.01)

    with jobs._LOCK:
        jobs._JOBS.clear()

    restored = jobs.get_tender_price_discovery_job(started["job_id"], database_path)

    assert restored["status"] == jobs.JOB_STATUS_SUCCEEDED
    assert restored["source"] == "mosreg_market"
    assert restored["external_id"] == "persisted-job"
    assert restored["searched_count"] == 1
    assert restored["positions"] == [{"position_index": 1, "status": "staged"}]
    assert restored["result"]["ready_count"] == 1


def test_price_discovery_active_job_lookup_uses_sqlite_when_memory_cache_is_empty(monkeypatch) -> None:
    with jobs._LOCK:
        jobs._JOBS.clear()
    database_path = Path("pytest_tmp_price_discovery_active.sqlite")
    database_path.unlink(missing_ok=True)
    release = threading.Event()
    started = threading.Event()
    calls: list[str] = []

    def fake_run(
        database_path: str | Path,
        source: str,
        external_id: str,
        *,
        max_positions: int | None = None,
        progress_callback=None,
    ) -> dict[str, object]:
        calls.append(external_id)
        started.set()
        release.wait(timeout=2)
        return {
            "ok": True,
            "total_profiles": 1,
            "searched_count": 1,
            "limited_count": 0,
            "partial": False,
            "positions": [],
        }

    monkeypatch.setattr(jobs, "run_tender_supplier_price_discovery", fake_run)

    first = jobs.start_tender_price_discovery_job(database_path, "mosreg_market", "active-job")
    assert started.wait(timeout=2)
    with jobs._LOCK:
        jobs._JOBS.clear()
    second = jobs.start_tender_price_discovery_job(database_path, "mosreg_market", "active-job")
    release.set()

    assert second["job_id"] == first["job_id"]
    assert second["status"] in {jobs.JOB_STATUS_QUEUED, jobs.JOB_STATUS_RUNNING}
    assert calls == ["active-job"]


def test_price_discovery_start_replaces_active_job_from_previous_process(monkeypatch) -> None:
    with jobs._LOCK:
        jobs._JOBS.clear()
    database_path = Path("pytest_tmp_price_discovery_orphaned.sqlite")
    database_path.unlink(missing_ok=True)
    now = time.time()
    jobs._store_job(
        database_path,
        {
            "job_id": "old-job",
            "status": jobs.JOB_STATUS_RUNNING,
            "source": "mosreg_market",
            "external_id": "orphaned-job",
            "total_profiles": 3,
            "searched_count": 1,
            "limited_count": 0,
            "partial": True,
            "positions": [],
            "created_at": now,
            "updated_at": now,
            "_owner_token": "previous-process",
        },
    )
    monkeypatch.setattr(jobs, "_PROCESS_TOKEN", "current-process")
    calls: list[str] = []

    def fake_run(
        database_path: str | Path,
        source: str,
        external_id: str,
        *,
        max_positions: int | None = None,
        progress_callback=None,
    ) -> dict[str, object]:
        calls.append(external_id)
        return {
            "ok": True,
            "total_profiles": 1,
            "searched_count": 1,
            "limited_count": 0,
            "partial": False,
            "positions": [],
        }

    monkeypatch.setattr(jobs, "run_tender_supplier_price_discovery", fake_run)

    started = jobs.start_tender_price_discovery_job(database_path, "mosreg_market", "orphaned-job")

    assert started["job_id"] != "old-job"
    old_job = jobs.get_tender_price_discovery_job("old-job", database_path)
    assert old_job["status"] == jobs.JOB_STATUS_FAILED
    assert "interrupted" in old_job["error"]
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline:
        current = jobs.get_tender_price_discovery_job(started["job_id"], database_path)
        if current["status"] == jobs.JOB_STATUS_SUCCEEDED:
            break
        time.sleep(0.01)
    assert calls == ["orphaned-job"]
