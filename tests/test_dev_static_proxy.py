from __future__ import annotations

import shutil
from pathlib import Path

from tender_killer.dev_static_proxy import resolve_static_path


def test_resolve_static_path_serves_index_for_root_and_spa_routes() -> None:
    root = _workspace_tmp("routes")
    try:
        (root / "index.html").write_text("<div id=\"root\"></div>", encoding="utf-8")
        (root / "assets").mkdir()
        (root / "assets" / "app.js").write_text("console.log('ok')", encoding="utf-8")

        assert resolve_static_path(root, "/") == root / "index.html"
        assert resolve_static_path(root, "/tenders/mosreg/123") == root / "index.html"
        assert resolve_static_path(root, "/assets/app.js") == root / "assets" / "app.js"
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_resolve_static_path_rejects_traversal() -> None:
    root = _workspace_tmp("traversal")
    try:
        (root / "index.html").write_text("<div id=\"root\"></div>", encoding="utf-8")

        assert resolve_static_path(root, "/../README.md") == root / "index.html"
    finally:
        shutil.rmtree(root, ignore_errors=True)


def _workspace_tmp(name: str) -> Path:
    root = Path.cwd() / "pytest-cache-dev-static-proxy" / name
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    return root
