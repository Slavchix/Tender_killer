from __future__ import annotations

import argparse
import json
import re
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

from tender_killer.config import Settings
from tender_killer.filter_store import FilterProfileCollection, FilterProfileStore, NamedFilterProfile
from tender_killer.filters import FilterProfile, MultiProfileTenderFilter
from tender_killer.pipeline import PipelineStats, TenderPipeline
from tender_killer.sources import build_adapters_for_collection, normalize_sources
from tender_killer.storage import TenderStore
from tender_killer.telegram import TelegramNotifier


WORKFLOW_STATUSES = frozenset(("new", "opened", "interesting", "in_progress", "skipped", "archive"))


def list_tenders_payload(database_path: str | Path, query: dict[str, str]) -> dict[str, Any]:
    filters, params = _build_filters(query)
    sql = (
        "SELECT tenders.source, tenders.external_id, url, title, customer, region, price, currency, status, "
        "published_at, deadline_at, delivery_place, category, okpd2, documents_json, raw_payload_json, "
        "tenders.updated_at, COALESCE(workflow.workflow_status, 'new') AS workflow_status, "
        "COALESCE(workflow.workflow_note, '') AS workflow_note "
        "FROM tenders "
        "LEFT JOIN tender_workflow AS workflow "
        "ON tenders.source = workflow.source AND tenders.external_id = workflow.external_id"
    )
    if filters:
        sql += " WHERE " + " AND ".join(filters)
    sql += " ORDER BY COALESCE(tenders.deadline_at, tenders.updated_at) DESC LIMIT ?"
    params.append(_int_query(query.get("limit"), 100))

    with _connect(database_path) as connection:
        _ensure_workflow_table(connection)
        rows = connection.execute(sql, params).fetchall()
    items = [_row_to_list_item(row) for row in rows]
    return {"total": len(items), "items": items}


def get_tender_payload(database_path: str | Path, source: str, external_id: str) -> dict[str, Any]:
    with _connect(database_path) as connection:
        _ensure_workflow_table(connection)
        row = connection.execute(
            """
            SELECT tenders.source, tenders.external_id, url, title, customer, region, price, currency, status,
                   published_at, deadline_at, delivery_place, category, okpd2,
                   documents_json, raw_payload_json, created_at, tenders.updated_at,
                   COALESCE(workflow.workflow_status, 'new') AS workflow_status,
                   COALESCE(workflow.workflow_note, '') AS workflow_note
            FROM tenders
            LEFT JOIN tender_workflow AS workflow
            ON tenders.source = workflow.source AND tenders.external_id = workflow.external_id
            WHERE tenders.source = ? AND tenders.external_id = ?
            """,
            (source, external_id),
        ).fetchone()
    if row is None:
        raise KeyError(f"Tender {source}/{external_id} not found.")
    payload = dict(row)
    payload["documents"] = _json_list(payload.pop("documents_json"))
    return payload


def update_tender_workflow(
    database_path: str | Path,
    source: str,
    external_id: str,
    data: dict[str, Any],
) -> dict[str, Any]:
    workflow_status = str(data.get("workflow_status") or "new").strip()
    workflow_note = str(data.get("workflow_note") or "").strip()
    if workflow_status not in WORKFLOW_STATUSES:
        raise ValueError(f"Unknown workflow status: {workflow_status}")
    with _connect(database_path) as connection:
        _ensure_workflow_table(connection)
        exists = connection.execute(
            "SELECT 1 FROM tenders WHERE source = ? AND external_id = ?",
            (source, external_id),
        ).fetchone()
        if exists is None:
            raise KeyError(f"Tender {source}/{external_id} not found.")
        connection.execute(
            """
            INSERT INTO tender_workflow (source, external_id, workflow_status, workflow_note)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(source, external_id) DO UPDATE SET
                workflow_status = excluded.workflow_status,
                workflow_note = excluded.workflow_note,
                updated_at = CURRENT_TIMESTAMP
            """,
            (source, external_id, workflow_status, workflow_note),
        )
    return get_tender_payload(database_path, source, external_id)


def run_search_payload(settings: Settings, runner=None, filters_payload: dict[str, Any] | None = None) -> dict[str, Any]:
    collection = build_search_collection(filters_payload) if filters_payload else None
    stats = runner(settings, collection) if runner else _run_search_from_settings(settings, collection)
    return {
        "ok": True,
        "notifications_enabled": bool(settings.telegram_bot_token and settings.telegram_chat_id),
        "stats": _stats_payload(stats),
    }


def build_search_collection(payload: dict[str, Any] | None) -> FilterProfileCollection:
    data = payload.get("filters", payload) if isinstance(payload, dict) else {}
    data = data if isinstance(data, dict) else {}
    status = str(data.get("status") or "").strip()
    only_active = not status or _is_active_status_query(status)
    statuses = () if only_active else _single_value_tuple(status)
    keywords = _keywords_from_query(str(data.get("q") or ""))
    profile = FilterProfile(
        keywords=keywords or FilterProfile.DEFAULT_KEYWORDS,
        regions=_single_value_tuple(data.get("region")),
        sources=normalize_sources(_single_value_tuple(data.get("source"))),
        laws=_single_value_tuple(data.get("law")),
        statuses=statuses,
        okpd2=_single_value_tuple(data.get("okpd2")),
        min_price=_float_query(data.get("min_price")),
        max_price=_float_query(data.get("max_price")),
        only_active=only_active,
        include_without_price=True,
        include_without_deadline=True,
    )
    return FilterProfileCollection(
        profiles=(NamedFilterProfile(id="site", name="Сайт", profile=profile),),
        active_profile_ids=("site",),
    )


def _run_search_from_settings(settings: Settings, collection: FilterProfileCollection | None = None) -> PipelineStats:
    if collection is None:
        filter_path = settings.filter_profile_path or Path("filters.json")
        filter_store = FilterProfileStore(filter_path)
        collection = filter_store.load_collection()
    pipeline = TenderPipeline(
        adapters=build_adapters_for_collection(collection, settings),
        store=TenderStore(settings.database_path),
        material_filter=MultiProfileTenderFilter(collection),
        notifier=TelegramNotifier(settings.telegram_bot_token, settings.telegram_chat_id, dry_run=settings.dry_run),
        notify_mode="new_only",
    )
    return pipeline.run()


def _stats_payload(stats: PipelineStats) -> dict[str, Any]:
    return {
        "fetched": stats.fetched,
        "saved": stats.saved,
        "matched": stats.matched,
        "notified": stats.notified,
        "failed_sources": stats.failed_sources,
        "failed_source_names": list(stats.failed_source_names),
        "failed_source_errors": list(stats.failed_source_errors),
    }


def _build_filters(query: dict[str, str]) -> tuple[list[str], list[Any]]:
    filters: list[str] = []
    params: list[Any] = []

    if source := query.get("source"):
        filters.append("tenders.source = ?")
        params.append(source)
    if region := query.get("region"):
        region_filters, region_params = _text_like_any("tenders.region", region)
        filters.append(region_filters)
        params.extend(region_params)
    if status := query.get("status"):
        if _is_active_status_query(status):
            filters.append(
                "("
                + " OR ".join(
                    [
                        "COALESCE(tenders.status, '') LIKE ?",
                        "COALESCE(tenders.status, '') LIKE ?",
                        "COALESCE(tenders.status, '') LIKE ?",
                        "COALESCE(tenders.status, '') LIKE ?",
                    ]
                )
                + ")"
            )
            params.extend(["%Актив%", "%актив%", "%Прием%", "%Приём%"])
        else:
            status_filters, status_params = _text_like_any("tenders.status", status)
            filters.append(status_filters)
            params.extend(status_params)
    if okpd2 := query.get("okpd2"):
        filters.append("COALESCE(tenders.okpd2, '') LIKE ?")
        params.append(f"{okpd2}%")
    if law := _law_query(query.get("law")):
        filters.append("LOWER(COALESCE(tenders.raw_payload_json, '')) LIKE ?")
        params.append(f"%{law}%")
    if min_price := _float_query(query.get("min_price")):
        filters.append("tenders.price >= ?")
        params.append(min_price)
    if max_price := _float_query(query.get("max_price")):
        filters.append("tenders.price <= ?")
        params.append(max_price)
    if search := query.get("q"):
        filters.append(
            "(LOWER(tenders.title) LIKE ? OR LOWER(COALESCE(tenders.customer, '')) LIKE ? "
            "OR LOWER(COALESCE(tenders.raw_payload_json, '')) LIKE ?)"
        )
        needle = f"%{search.lower()}%"
        params.extend([needle, needle, needle])
    return filters, params


def _keywords_from_query(value: str) -> tuple[str, ...]:
    parts = re.split(r"[,;\n]+", value)
    return tuple(part.strip() for part in parts if part.strip())


def _single_value_tuple(value: Any) -> tuple[str, ...]:
    text = str(value or "").strip()
    return (text,) if text else ()


def _is_active_status_query(value: str) -> bool:
    normalized = value.strip().casefold().replace("ё", "е")
    return normalized in {"active", "актив", "активные", "прием", "прием заявок", "прием предложений"}


def _text_like_any(field: str, value: str) -> tuple[str, list[Any]]:
    variants = _text_variants(value)
    clause = "(" + " OR ".join([f"COALESCE({field}, '') LIKE ?" for _ in variants]) + ")"
    return clause, [f"%{variant}%" for variant in variants]


def _text_variants(value: str) -> tuple[str, ...]:
    text = value.strip()
    if not text:
        return ("",)
    variants = []
    for candidate in (text, text.casefold(), text.upper(), text[:1].upper() + text[1:].casefold()):
        if candidate and candidate not in variants:
            variants.append(candidate)
    return tuple(variants)


def _row_to_list_item(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    documents = _json_list(payload.pop("documents_json"))
    raw_payload_json = payload.pop("raw_payload_json", None)
    payload["documents_count"] = len(documents)
    payload["law"] = _law_label(raw_payload_json)
    return payload


def _json_list(value: str | None) -> list[Any]:
    if not value:
        return []
    try:
        data = json.loads(value)
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


def _connect(database_path: str | Path) -> sqlite3.Connection:
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    return connection


def _ensure_workflow_table(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS tender_workflow (
            source TEXT NOT NULL,
            external_id TEXT NOT NULL,
            workflow_status TEXT NOT NULL DEFAULT 'new',
            workflow_note TEXT NOT NULL DEFAULT '',
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (source, external_id)
        )
        """
    )


def _int_query(value: str | None, default: int) -> int:
    try:
        return int(value) if value else default
    except ValueError:
        return default


def _float_query(value: str | None) -> float | None:
    try:
        return float(value) if value not in (None, "") else None
    except ValueError:
        return None


def _law_query(value: str | None) -> str | None:
    if not value:
        return None
    digits = re.sub(r"\D+", "", value)
    if "223" in digits:
        return "223"
    if "44" in digits:
        return "44"
    return value.lower()


def _law_label(raw_payload_json: str | None) -> str | None:
    if not raw_payload_json:
        return None
    digits = re.sub(r"\D+", "", raw_payload_json)
    if "223" in digits:
        return "223-ФЗ"
    if "44" in digits:
        return "44-ФЗ"
    return None


class TenderApiHandler(BaseHTTPRequestHandler):
    database_path: Path

    def do_GET(self) -> None:  # noqa: N802 - stdlib API name.
        parsed = urlparse(self.path)
        query = {key: values[-1] for key, values in parse_qs(parsed.query).items()}
        try:
            if parsed.path == "/api/tenders":
                self._send_json(list_tenders_payload(self.database_path, query))
                return
            if parsed.path.startswith("/api/tenders/"):
                parts = parsed.path.split("/")
                if len(parts) != 5:
                    self._send_json({"error": "invalid tender path"}, status=400)
                    return
                source, external_id = parts[3], parts[4]
                self._send_json(get_tender_payload(self.database_path, unquote(source), unquote(external_id)))
                return
            if parsed.path == "/api/health":
                self._send_json({"ok": True})
                return
            self._send_json({"error": "not found"}, status=404)
        except KeyError as exc:
            self._send_json({"error": str(exc)}, status=404)
        except Exception as exc:  # noqa: BLE001 - API must return JSON errors in local dev.
            self._send_json({"error": str(exc)}, status=500)

    def do_POST(self) -> None:  # noqa: N802 - stdlib API name.
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/api/search":
                self._send_json(run_search_payload(Settings.from_env(), filters_payload=self._read_json_body()))
                return
            if parsed.path.startswith("/api/tenders/") and parsed.path.endswith("/workflow"):
                parts = parsed.path.split("/")
                if len(parts) != 6:
                    self._send_json({"error": "invalid workflow path"}, status=400)
                    return
                source, external_id = unquote(parts[3]), unquote(parts[4])
                payload = self._read_json_body()
                self._send_json(update_tender_workflow(self.database_path, source, external_id, payload))
                return
            self._send_json({"error": "not found"}, status=404)
        except ValueError as exc:
            self._send_json({"error": str(exc)}, status=400)
        except KeyError as exc:
            self._send_json({"error": str(exc)}, status=404)
        except Exception as exc:  # noqa: BLE001 - API must return JSON errors in local dev.
            self._send_json({"error": str(exc)}, status=500)

    def do_OPTIONS(self) -> None:  # noqa: N802 - stdlib API name.
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()

    def _read_json_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            return {}
        if length > 65536:
            raise ValueError("Request body is too large.")
        data = json.loads(self.rfile.read(length).decode("utf-8"))
        if not isinstance(data, dict):
            raise ValueError("Request body must be a JSON object.")
        return data

    def _send_json(self, payload: dict[str, Any], status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self._send_cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")


def run_server(host: str, port: int, database_path: Path) -> None:
    handler = type("ConfiguredTenderApiHandler", (TenderApiHandler,), {"database_path": database_path})
    server = ThreadingHTTPServer((host, port), handler)
    print(f"Tender Killer API: http://{host}:{port}")
    print(f"SQLite: {database_path}")
    server.serve_forever()


def main() -> None:
    parser = argparse.ArgumentParser(prog="tender-killer-api")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--db", type=Path)
    args = parser.parse_args()

    settings = Settings.from_env()
    run_server(args.host, args.port, args.db or settings.database_path)


if __name__ == "__main__":
    main()
