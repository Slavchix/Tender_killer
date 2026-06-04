from __future__ import annotations

import argparse
import http.client
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote
from urllib.parse import urlsplit


def resolve_static_path(static_root: Path, request_path: str) -> Path:
    root = static_root.resolve()
    index_path = root / "index.html"
    path = unquote(urlsplit(request_path).path)
    relative_path = "index.html" if path in {"", "/"} else path.lstrip("/")
    candidate = (root / relative_path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return index_path
    if candidate.exists() and not candidate.is_dir():
        return candidate
    return index_path


def make_handler(static_root: Path, api_base_url: str) -> type[BaseHTTPRequestHandler]:
    root = static_root.resolve()
    api = urlsplit(api_base_url.rstrip("/"))
    api_host = api.hostname or "127.0.0.1"
    api_port = api.port or (443 if api.scheme == "https" else 80)
    connection_class = http.client.HTTPSConnection if api.scheme == "https" else http.client.HTTPConnection

    class StaticProxyHandler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
            return

        def _proxy_api(self) -> None:
            body = None
            if self.command in {"POST", "PUT", "PATCH", "DELETE"}:
                body = self.rfile.read(int(self.headers.get("Content-Length") or 0))
            headers = {
                key: value
                for key, value in self.headers.items()
                if key.lower() not in {"host", "connection", "transfer-encoding"}
            }
            api_path = self.path
            connection = connection_class(api_host, api_port, timeout=60)
            try:
                connection.request(self.command, api_path, body=body, headers=headers)
                response = connection.getresponse()
                data = response.read()
                self.send_response(response.status)
                for key, value in response.getheaders():
                    if key.lower() not in {"connection", "transfer-encoding"}:
                        self.send_header(key, value)
                self.end_headers()
                self.wfile.write(data)
            finally:
                connection.close()

        def _send_static(self) -> None:
            target = resolve_static_path(root, self.path)
            data = target.read_bytes()
            content_type = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self) -> None:
            if self.path.startswith("/api/"):
                self._proxy_api()
            else:
                self._send_static()

        def do_POST(self) -> None:
            if self.path.startswith("/api/"):
                self._proxy_api()
            else:
                self.send_error(404)

        def do_PUT(self) -> None:
            self.do_POST()

        def do_PATCH(self) -> None:
            self.do_POST()

        def do_DELETE(self) -> None:
            self.do_POST()

    return StaticProxyHandler


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tender-killer-dev-static-proxy")
    parser.add_argument("--root", type=Path, default=Path("web/dist"))
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5173)
    parser.add_argument("--api-base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    index_path = root / "index.html"
    if not index_path.exists():
        raise SystemExit(f"Static frontend build not found: {index_path}")

    handler = make_handler(root, args.api_base_url)
    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(f"Tender Killer static web proxy: http://{args.host}:{args.port} -> {args.api_base_url}")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
