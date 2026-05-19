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


def list_tenders_payload(database_path: str | Path, query: dict[str, str]) -> dict[str, Any]:
    filters, params = _build_filters(query)
    sql = (
        "SELECT source, external_id, url, title, customer, region, price, currency, status, "
        "published_at, deadline_at, delivery_place, category, okpd2, documents_json, raw_payload_json, updated_at "
        "FROM tenders"
    )
    if filters:
        sql += " WHERE " + " AND ".join(filters)
    sql += " ORDER BY COALESCE(deadline_at, updated_at) DESC LIMIT ?"
    params.append(_int_query(query.get("limit"), 100))

    with _connect(database_path) as connection:
        rows = connection.execute(sql, params).fetchall()
    items = [_row_to_list_item(row) for row in rows]
    return {"total": len(items), "items": items}


def get_tender_payload(database_path: str | Path, source: str, external_id: str) -> dict[str, Any]:
    with _connect(database_path) as connection:
        row = connection.execute(
            """
            SELECT source, external_id, url, title, customer, region, price, currency, status,
                   published_at, deadline_at, delivery_place, category, okpd2,
                   documents_json, raw_payload_json, created_at, updated_at
            FROM tenders
            WHERE source = ? AND external_id = ?
            """,
            (source, external_id),
        ).fetchone()
    if row is None:
        raise KeyError(f"Tender {source}/{external_id} not found.")
    payload = dict(row)
    payload["documents"] = _json_list(payload.pop("documents_json"))
    return payload


def _build_filters(query: dict[str, str]) -> tuple[list[str], list[Any]]:
    filters: list[str] = []
    params: list[Any] = []

    if source := query.get("source"):
        filters.append("source = ?")
        params.append(source)
    if region := query.get("region"):
        filters.append("LOWER(COALESCE(region, '')) LIKE ?")
        params.append(f"%{region.lower()}%")
    if status := query.get("status"):
        filters.append("LOWER(COALESCE(status, '')) LIKE ?")
        params.append(f"%{status.lower()}%")
    if okpd2 := query.get("okpd2"):
        filters.append("COALESCE(okpd2, '') LIKE ?")
        params.append(f"{okpd2}%")
    if law := _law_query(query.get("law")):
        filters.append("LOWER(COALESCE(raw_payload_json, '')) LIKE ?")
        params.append(f"%{law}%")
    if min_price := _float_query(query.get("min_price")):
        filters.append("price >= ?")
        params.append(min_price)
    if max_price := _float_query(query.get("max_price")):
        filters.append("price <= ?")
        params.append(max_price)
    if search := query.get("q"):
        filters.append(
            "(LOWER(title) LIKE ? OR LOWER(COALESCE(customer, '')) LIKE ? OR LOWER(COALESCE(raw_payload_json, '')) LIKE ?)"
        )
        needle = f"%{search.lower()}%"
        params.extend([needle, needle, needle])
    return filters, params


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

    def do_OPTIONS(self) -> None:  # noqa: N802 - stdlib API name.
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()

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
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
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
