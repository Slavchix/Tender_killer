from __future__ import annotations

import os
import json
import sqlite3
import threading
import time
import uuid
from pathlib import Path
from typing import Any

from tender_killer.schema import initialize_schema
from tender_killer.supplier_price_discovery_service import run_tender_supplier_price_discovery
from tender_killer.supplier_price_discovery_service import tender_price_discovery_policy_for_tender


JOB_STATUS_QUEUED = "queued"
JOB_STATUS_RUNNING = "running"
JOB_STATUS_SUCCEEDED = "succeeded"
JOB_STATUS_FAILED = "failed"
ACTIVE_JOB_STATUSES = {JOB_STATUS_QUEUED, JOB_STATUS_RUNNING}
DEFAULT_PRICE_DISCOVERY_JOB_MAX_POSITIONS = 50

_PROCESS_TOKEN = uuid.uuid4().hex
_JOBS: dict[str, dict[str, Any]] = {}
_LOCK = threading.Lock()


def start_tender_price_discovery_job(database_path: str | Path, source: str, external_id: str) -> dict[str, Any]:
    database_path = Path(database_path)
    existing = _active_job_for_tender(database_path, source, external_id)
    if existing is not None:
        return existing

    try:
        policy = tender_price_discovery_policy_for_tender(database_path, source, external_id)
    except Exception:
        policy = {"ok": True, "status": "active_discovery_allowed"}
    if policy.get("status") == "manual_required":
        now = time.time()
        return {
            "job_id": "",
            "status": "manual_required",
            "source": source,
            "external_id": external_id,
            "created_at": now,
            "updated_at": now,
            **policy,
        }

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
        "_database_path": str(database_path),
        "_owner_token": _PROCESS_TOKEN,
    }
    _store_job(database_path, job)
    with _LOCK:
        _JOBS[job_id] = job

    thread = threading.Thread(
        target=_run_price_discovery_job,
        args=(job_id, str(database_path), source, external_id),
        name=f"price-discovery-{job_id[:8]}",
        daemon=True,
    )
    thread.start()
    return get_tender_price_discovery_job(job_id, database_path)


def get_tender_price_discovery_job(job_id: str, database_path: str | Path | None = None) -> dict[str, Any]:
    with _LOCK:
        job = _JOBS.get(job_id)
        if job is not None:
            return _job_snapshot(job)
    if database_path is not None:
        loaded = _load_job(Path(database_path), job_id)
        if loaded is not None:
            return loaded
    raise KeyError(f"Price discovery job {job_id} not found.")


def _active_job_for_tender(database_path: Path, source: str, external_id: str) -> dict[str, Any] | None:
    with _LOCK:
        for job in _JOBS.values():
            if (
                job.get("source") == source
                and job.get("external_id") == external_id
                and job.get("status") in ACTIVE_JOB_STATUSES
            ):
                return _job_snapshot(job)
    return _load_active_job_for_tender(database_path, source, external_id)


def _run_price_discovery_job(job_id: str, database_path: str, source: str, external_id: str) -> None:
    _update_job(job_id, {"status": JOB_STATUS_RUNNING}, database_path=database_path)
    try:
        result = run_tender_supplier_price_discovery(
            database_path,
            source,
            external_id,
            max_positions=_job_max_positions(),
            progress_callback=lambda progress: _update_job(job_id, progress, database_path=database_path),
        )
    except Exception as exc:
        _update_job(job_id, {"status": JOB_STATUS_FAILED, "error": str(exc)}, database_path=database_path)
        return
    _update_job(job_id, {**result, "status": JOB_STATUS_SUCCEEDED, "result": result}, database_path=database_path)


def _update_job(job_id: str, updates: dict[str, Any], *, database_path: str | Path | None = None) -> None:
    now = time.time()
    job_snapshot: dict[str, Any] | None = None
    resolved_database_path = Path(database_path) if database_path is not None else None
    with _LOCK:
        job = _JOBS.get(job_id)
        if job is not None:
            job.update(updates)
            job["updated_at"] = now
            if resolved_database_path is None and job.get("_database_path"):
                resolved_database_path = Path(str(job["_database_path"]))
            job_snapshot = dict(job)
    if resolved_database_path is None:
        return
    if job_snapshot is None:
        existing = _load_job(resolved_database_path, job_id, include_private=True)
        if existing is None:
            return
        existing.update(updates)
        existing["updated_at"] = now
        job_snapshot = existing
    _store_job(resolved_database_path, job_snapshot)


def _job_snapshot(job: dict[str, Any]) -> dict[str, Any]:
    snapshot = {key: value for key, value in job.items() if not str(key).startswith("_")}
    result = snapshot.get("result")
    if isinstance(result, dict):
        snapshot["result"] = dict(result)
    positions = snapshot.get("positions")
    if isinstance(positions, list):
        snapshot["positions"] = [dict(item) if isinstance(item, dict) else item for item in positions]
    return snapshot


def _connect(database_path: Path) -> sqlite3.Connection:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    initialize_schema(connection)
    return connection


def _store_job(database_path: Path, job: dict[str, Any]) -> None:
    with _connect(database_path) as connection:
        connection.execute(
            """
            INSERT INTO price_discovery_jobs (
                job_id, source, external_id, status, total_profiles, searched_count,
                limited_count, partial, positions_json, result_json, error, created_at, updated_at, owner_token
            )
            VALUES (
                :job_id, :source, :external_id, :status, :total_profiles, :searched_count,
                :limited_count, :partial, :positions_json, :result_json, :error, :created_at, :updated_at, :owner_token
            )
            ON CONFLICT(job_id) DO UPDATE SET
                source = excluded.source,
                external_id = excluded.external_id,
                status = excluded.status,
                total_profiles = excluded.total_profiles,
                searched_count = excluded.searched_count,
                limited_count = excluded.limited_count,
                partial = excluded.partial,
                positions_json = excluded.positions_json,
                result_json = excluded.result_json,
                error = excluded.error,
                updated_at = excluded.updated_at,
                owner_token = excluded.owner_token
            """,
            _serialize_job(job),
        )


def _load_job(database_path: Path, job_id: str, *, include_private: bool = False) -> dict[str, Any] | None:
    with _connect(database_path) as connection:
        row = connection.execute(
            """
            SELECT job_id, source, external_id, status, total_profiles, searched_count,
                   limited_count, partial, positions_json, result_json, error, created_at, updated_at, owner_token
            FROM price_discovery_jobs
            WHERE job_id = ?
            """,
            (job_id,),
        ).fetchone()
    return _deserialize_job(row, include_private=include_private) if row is not None else None


def _load_active_job_for_tender(database_path: Path, source: str, external_id: str) -> dict[str, Any] | None:
    placeholders = ", ".join(["?"] * len(ACTIVE_JOB_STATUSES))
    with _connect(database_path) as connection:
        row = connection.execute(
            f"""
            SELECT job_id, source, external_id, status, total_profiles, searched_count,
                   limited_count, partial, positions_json, result_json, error, created_at, updated_at, owner_token
            FROM price_discovery_jobs
            WHERE source = ?
              AND external_id = ?
              AND status IN ({placeholders})
            ORDER BY updated_at DESC
            LIMIT 1
            """,
            (source, external_id, *sorted(ACTIVE_JOB_STATUSES)),
        ).fetchone()
        if row is not None and row["owner_token"] != _PROCESS_TOKEN:
            connection.execute(
                f"""
                UPDATE price_discovery_jobs
                SET status = ?,
                    error = ?,
                    updated_at = ?
                WHERE source = ?
                  AND external_id = ?
                  AND status IN ({placeholders})
                  AND owner_token != ?
                """,
                (
                    JOB_STATUS_FAILED,
                    "Price discovery job interrupted by API restart.",
                    time.time(),
                    source,
                    external_id,
                    *sorted(ACTIVE_JOB_STATUSES),
                    _PROCESS_TOKEN,
                ),
            )
            return None
    return _deserialize_job(row) if row is not None else None


def _serialize_job(job: dict[str, Any]) -> dict[str, Any]:
    return {
        "job_id": str(job["job_id"]),
        "source": str(job.get("source") or ""),
        "external_id": str(job.get("external_id") or ""),
        "status": str(job.get("status") or JOB_STATUS_QUEUED),
        "total_profiles": int(job.get("total_profiles") or 0),
        "searched_count": int(job.get("searched_count") or 0),
        "limited_count": int(job.get("limited_count") or 0),
        "partial": 1 if job.get("partial") else 0,
        "positions_json": json.dumps(job.get("positions") or [], ensure_ascii=False),
        "result_json": json.dumps(job.get("result"), ensure_ascii=False) if isinstance(job.get("result"), dict) else None,
        "error": str(job.get("error")) if job.get("error") not in (None, "") else None,
        "created_at": float(job.get("created_at") or time.time()),
        "updated_at": float(job.get("updated_at") or time.time()),
        "owner_token": str(job.get("_owner_token") or job.get("owner_token") or ""),
    }


def _deserialize_job(row: sqlite3.Row, *, include_private: bool = False) -> dict[str, Any]:
    result_json = row["result_json"]
    result = json.loads(result_json) if result_json else None
    job: dict[str, Any] = {
        "job_id": row["job_id"],
        "status": row["status"],
        "source": row["source"],
        "external_id": row["external_id"],
        "total_profiles": int(row["total_profiles"] or 0),
        "searched_count": int(row["searched_count"] or 0),
        "limited_count": int(row["limited_count"] or 0),
        "partial": bool(row["partial"]),
        "positions": json.loads(row["positions_json"] or "[]"),
        "created_at": float(row["created_at"]),
        "updated_at": float(row["updated_at"]),
    }
    if row["error"]:
        job["error"] = row["error"]
    if include_private:
        job["_owner_token"] = row["owner_token"]
    if isinstance(result, dict):
        job["result"] = result
        for key, value in result.items():
            job.setdefault(key, value)
    return job


def _job_max_positions() -> int:
    raw_value = os.environ.get("TENDER_KILLER_PRICE_DISCOVERY_JOB_MAX_POSITIONS")
    if raw_value is None:
        return DEFAULT_PRICE_DISCOVERY_JOB_MAX_POSITIONS
    try:
        value = int(raw_value)
    except ValueError:
        return DEFAULT_PRICE_DISCOVERY_JOB_MAX_POSITIONS
    return value if value > 0 else DEFAULT_PRICE_DISCOVERY_JOB_MAX_POSITIONS
