from __future__ import annotations

import argparse
import json
from dataclasses import replace
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from tender_killer.api_handlers import ApiResponse
from tender_killer.api_handlers import handle_get_request
from tender_killer.api_handlers import handle_post_request
from tender_killer.config import Settings
from tender_killer.web_search_runner import WebAutoSearchScheduler
from tender_killer.web_search_runner import WebSearchRunner


class TenderApiHandler(BaseHTTPRequestHandler):
    database_path: Path
    search_runner: WebSearchRunner | None = None
    settings_factory = staticmethod(Settings.from_env)

    def do_GET(self) -> None:  # noqa: N802 - stdlib API name.
        parsed = urlparse(self.path)
        query = {key: values[-1] for key, values in parse_qs(parsed.query).items()}
        try:
            self._send_api_response(handle_get_request(self.database_path, parsed.path, query))
        except KeyError as exc:
            self._send_json({"error": str(exc)}, status=404)
        except Exception as exc:  # noqa: BLE001 - API must return JSON errors in local dev.
            self._send_json({"error": str(exc)}, status=500)

    def do_POST(self) -> None:  # noqa: N802 - stdlib API name.
        parsed = urlparse(self.path)
        try:
            self._send_api_response(
                handle_post_request(
                    self.database_path,
                    parsed.path,
                    self._read_json_body(),
                    settings_factory=self.settings_factory,
                    search_runner=self.search_runner,
                )
            )
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

    def _send_api_response(self, response: ApiResponse) -> None:
        if response.kind == "binary":
            self._send_binary(response.payload, status=response.status)
            return
        self._send_json(response.payload, status=response.status)

    def _send_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")


def run_server(host: str, port: int, database_path: Path) -> None:
    def settings_factory() -> Settings:
        return replace(Settings.from_env(), database_path=database_path)

    search_runner = WebSearchRunner(settings_factory=settings_factory)
    auto_search = WebAutoSearchScheduler(
        search_runner=search_runner,
        interval_seconds=settings_factory().web_auto_search_minutes * 60,
    )
    auto_search.start()
    handler = type(
        "ConfiguredTenderApiHandler",
        (TenderApiHandler,),
        {
            "database_path": database_path,
            "search_runner": search_runner,
            "settings_factory": staticmethod(settings_factory),
        },
    )
    server = ThreadingHTTPServer((host, port), handler)
    print(f"Tender Killer API: http://{host}:{port}")
    print(f"SQLite: {database_path}")
    print(f"Auto search: every {settings_factory().web_auto_search_minutes} minute(s)")
    try:
        server.serve_forever()
    finally:
        auto_search.stop()


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
