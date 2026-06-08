from __future__ import annotations

from pathlib import Path


WEB_SRC = Path("web/src")


def test_supplier_catalog_frontend_reads_connection_state() -> None:
    dashboard_source = (WEB_SRC / "Dashboard.jsx").read_text(encoding="utf-8")

    assert "catalog.connection_state" in dashboard_source
    assert "no_cards" in dashboard_source
    assert "parser_broken" in dashboard_source
