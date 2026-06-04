from __future__ import annotations

import os
import threading
import time
import uuid
from pathlib import Path
from typing import Any

from tender_killer.supplier_price_discovery_service import run_tender_supplier_price_discovery


JOB_STATUS_QUEUED = "queued"
JOB_STATUS_RUNNING = "running"
JOB_STATUS_SUCCEEDED = "succeeded"
JOB_STATUS_FAILED = "failed"
ACTIVE_JOB_STATUSES = {JOB_STATUS_QUEUED, JOB_STATUS_RUNNING}
DEFAULT_PRICE_DISCOVERY_JOB_MAX_POSITIONS = 50

_JOBS: dict[str, dict[str, Any]] = {}
_LOCK = threading.Lock()


def start_tender_price_discovery_job(database_path: str | Path, source: str, external_id: str) -> dict[str, Any]:
    existing = _active_job_for_tender(source, external_id)
    if existing is not None:
        return existing

    job_id = uuid.uuid4().hex
    now = time.time()
    job = {
        "job_id": job_id,
        "status": JOB_STATUS_QUEUED,
        "source": source,
        "external_id": external_id,
        "total_profiles": 0,
        "searched_count": 0,
        "limited_count": 0,
        "partial": False,
        "positions": [],
        "created_at": now,
        "updated_at": now,
    }
    with _LOCK:
        _JOBS[job_id] = job

    thread = threading.Thread(
        target=_run_price_discovery_job,
        args=(job_id, str(database_path), source, external_id),
        name=f"price-discovery-{job_id[:8]}",
        daemon=True,
    )
    thread.start()
    return get_tender_price_discovery_job(job_id)


def get_tender_price_discovery_job(job_id: str) -> dict[str, Any]:
    with _LOCK:
        job = _JOBS.get(job_id)
        if job is None:
            raise KeyError(f"Price discovery job {job_id} not found.")
        return _job_snapshot(job)


def _active_job_for_tender(source: str, external_id: str) -> dict[str, Any] | None:
    with _LOCK:
        for job in _JOBS.values():
            if (
                job.get("source") == source
                and job.get("external_id") == external_id
                and job.get("status") in ACTIVE_JOB_STATUSES
            ):
                return _job_snapshot(job)
    return None


def _run_price_discovery_job(job_id: str, database_path: str, source: str, external_id: str) -> None:
    _update_job(job_id, {"status": JOB_STATUS_RUNNING})
    try:
        result = run_tender_supplier_price_discovery(
            database_path,
            source,
            external_id,
            max_positions=_job_max_positions(),
            progress_callback=lambda progress: _update_job(job_id, progress),
        )
    except Exception as exc:
        _update_job(job_id, {"status": JOB_STATUS_FAILED, "error": str(exc)})
        return
    _update_job(job_id, {**result, "status": JOB_STATUS_SUCCEEDED, "result": result})


def _update_job(job_id: str, updates: dict[str, Any]) -> None:
    with _LOCK:
        job = _JOBS.get(job_id)
        if job is None:
            return
        job.update(updates)
        job["updated_at"] = time.time()


def _job_snapshot(job: dict[str, Any]) -> dict[str, Any]:
    snapshot = dict(job)
    result = snapshot.get("result")
    if isinstance(result, dict):
        snapshot["result"] = dict(result)
    positions = snapshot.get("positions")
    if isinstance(positions, list):
        snapshot["positions"] = [dict(item) if isinstance(item, dict) else item for item in positions]
    return snapshot


def _job_max_positions() -> int:
    raw_value = os.environ.get("TENDER_KILLER_PRICE_DISCOVERY_JOB_MAX_POSITIONS")
    if raw_value is None:
        return DEFAULT_PRICE_DISCOVERY_JOB_MAX_POSITIONS
    try:
        value = int(raw_value)
    except ValueError:
        return DEFAULT_PRICE_DISCOVERY_JOB_MAX_POSITIONS
    return value if value > 0 else DEFAULT_PRICE_DISCOVERY_JOB_MAX_POSITIONS
