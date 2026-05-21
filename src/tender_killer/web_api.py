from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

from tender_killer.analysis_service import analyze_tender_payload
from tender_killer.config import Settings
from tender_killer.database_view_service import get_database_table_payload
from tender_killer.database_view_service import list_database_tables_payload
from tender_killer.document_service import download_tender_documents_payload
from tender_killer.document_service import extract_tender_document_text_payload
from tender_killer.notification_service import send_tender_notification_payload
from tender_killer.product_profile_service import rebuild_product_profiles as rebuild_product_profiles_from_payload
from tender_killer.report_service import build_tender_report_response as build_tender_report_download_response
from tender_killer.search_service import run_search_payload
from tender_killer.source_run_service import list_source_runs_payload
from tender_killer.tender_detail_service import get_tender_payload
from tender_killer.tender_detail_service import refresh_tender_detail_payload
from tender_killer.tender_query_service import build_search_collection
from tender_killer.tender_query_service import list_tenders_payload
from tender_killer.workflow_service import save_tender_workflow


def rebuild_product_profiles(database_path: str | Path, source: str, external_id: str) -> dict[str, Any]:
    tender = get_tender_payload(database_path, source, external_id, include_product_profiles=False)
    return rebuild_product_profiles_from_payload(database_path, source, external_id, tender)


def build_tender_report_response(database_path: str | Path, source: str, external_id: str) -> dict[str, Any]:
    tender = get_tender_payload(database_path, source, external_id)
    return build_tender_report_download_response(tender)


def update_tender_workflow(
    database_path: str | Path,
    source: str,
    external_id: str,
    data: dict[str, Any],
) -> dict[str, Any]:
    save_tender_workflow(database_path, source, external_id, data)
    return get_tender_payload(database_path, source, external_id)


class TenderApiHandler(BaseHTTPRequestHandler):
    database_path: Path

    def do_GET(self) -> None:  # noqa: N802 - stdlib API name.
        parsed = urlparse(self.path)
        query = {key: values[-1] for key, values in parse_qs(parsed.query).items()}
        try:
            if parsed.path == "/api/db/tables":
                self._send_json(list_database_tables_payload(self.database_path))
                return
            if parsed.path.startswith("/api/db/tables/"):
                parts = parsed.path.split("/")
                if len(parts) != 5:
                    self._send_json({"error": "invalid database table path"}, status=400)
                    return
                self._send_json(get_database_table_payload(self.database_path, unquote(parts[4]), query))
                return
            if parsed.path == "/api/sources/status":
                self._send_json(list_source_runs_payload(self.database_path))
                return
            if parsed.path == "/api/tenders":
                self._send_json(list_tenders_payload(self.database_path, query))
                return
            if parsed.path.startswith("/api/tenders/") and parsed.path.endswith("/report.docx"):
                parts = parsed.path.split("/")
                if len(parts) != 6:
                    self._send_json({"error": "invalid report path"}, status=400)
                    return
                source, external_id = unquote(parts[3]), unquote(parts[4])
                self._send_binary(build_tender_report_response(self.database_path, source, external_id))
                return
            if parsed.path.startswith("/api/tenders/") and parsed.path.endswith("/product-profiles"):
                parts = parsed.path.split("/")
                if len(parts) != 6:
                    self._send_json({"error": "invalid product profiles path"}, status=400)
                    return
                source, external_id = unquote(parts[3]), unquote(parts[4])
                detail = get_tender_payload(self.database_path, source, external_id)
                self._send_json(
                    {
                        "ok": True,
                        "summary": detail["product_profile_summary"],
                        "product_profiles": detail["product_profiles"],
                    }
                )
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
            if parsed.path.startswith("/api/tenders/") and parsed.path.endswith("/notify"):
                parts = parsed.path.split("/")
                if len(parts) != 6:
                    self._send_json({"error": "invalid notify path"}, status=400)
                    return
                source, external_id = unquote(parts[3]), unquote(parts[4])
                self._send_json(
                    send_tender_notification_payload(
                        self.database_path,
                        source,
                        external_id,
                        Settings.from_env(),
                    )
                )
                return
            if parsed.path.startswith("/api/tenders/") and parsed.path.endswith("/documents/download"):
                parts = parsed.path.split("/")
                if len(parts) != 7:
                    self._send_json({"error": "invalid documents download path"}, status=400)
                    return
                source, external_id = unquote(parts[3]), unquote(parts[4])
                self._send_json(download_tender_documents_payload(self.database_path, source, external_id))
                return
            if parsed.path.startswith("/api/tenders/") and parsed.path.endswith("/documents/extract-text"):
                parts = parsed.path.split("/")
                if len(parts) != 7:
                    self._send_json({"error": "invalid documents extract path"}, status=400)
                    return
                source, external_id = unquote(parts[3]), unquote(parts[4])
                self._send_json(extract_tender_document_text_payload(self.database_path, source, external_id))
                return
            if parsed.path.startswith("/api/tenders/") and parsed.path.endswith("/analysis/run"):
                parts = parsed.path.split("/")
                if len(parts) != 7:
                    self._send_json({"error": "invalid analysis path"}, status=400)
                    return
                source, external_id = unquote(parts[3]), unquote(parts[4])
                self._send_json(analyze_tender_payload(self.database_path, source, external_id))
                return
            if parsed.path.startswith("/api/tenders/") and parsed.path.endswith("/details/refresh"):
                parts = parsed.path.split("/")
                if len(parts) != 7:
                    self._send_json({"error": "invalid detail refresh path"}, status=400)
                    return
                source, external_id = unquote(parts[3]), unquote(parts[4])
                self._send_json(refresh_tender_detail_payload(self.database_path, source, external_id))
                return
            if parsed.path.startswith("/api/tenders/") and parsed.path.endswith("/product-profiles/rebuild"):
                parts = parsed.path.split("/")
                if len(parts) != 7:
                    self._send_json({"error": "invalid product profiles rebuild path"}, status=400)
                    return
                source, external_id = unquote(parts[3]), unquote(parts[4])
                self._send_json(rebuild_product_profiles(self.database_path, source, external_id))
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

    def _send_binary(self, payload: dict[str, Any], status: int = 200) -> None:
        body = payload["body"]
        self.send_response(status)
        self._send_cors_headers()
        self.send_header("Content-Type", payload["content_type"])
        self.send_header("Content-Disposition", f'attachment; filename="{payload["filename"]}"')
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
