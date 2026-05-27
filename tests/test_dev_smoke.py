from __future__ import annotations

from tender_killer.dev_smoke import check_dev_site


def _mojibake(text: str) -> str:
    return text.encode("utf-8").decode("cp1251")


def test_check_dev_site_verifies_api_frontend_proxy_and_ui_text(tmp_path):
    app_source = tmp_path / "App.jsx"
    app_source.write_text("Панель закупок\nНа странице\nЗакупок на странице\n", encoding="utf-8")

    def fetcher(url: str, timeout: float):
        if url == "http://127.0.0.1:8000/api/health":
            return 200, (
                '{"ok": true, "capabilities": '
                '["supplier_search_prepare", "supplier_catalog_presets", "supplier_catalog_health", "supplier_discovery_url"]}'
            )
        if url == "http://127.0.0.1:8000/api/sources/status":
            return 200, '{"sources": []}'
        if url == "http://127.0.0.1:8000/api/supplier-catalogs/health":
            return 200, '{"ok": true, "catalogs": []}'
        if url == "http://127.0.0.1:5173/":
            return 200, '<html><body><div id="root"></div><script type="module" src="/src/App.jsx"></script></body></html>'
        if url == "http://127.0.0.1:5173/api/health":
            return 200, (
                '{"ok": true, "capabilities": '
                '["supplier_search_prepare", "supplier_catalog_presets", "supplier_catalog_health", "supplier_discovery_url"]}'
            )
        if url == "http://127.0.0.1:5173/api/sources/status":
            return 200, '{"sources": []}'
        if url == "http://127.0.0.1:5173/api/supplier-catalogs/health":
            return 200, '{"ok": true, "catalogs": []}'
        raise AssertionError(url)

    payload = check_dev_site(
        api_base_url="http://127.0.0.1:8000",
        web_base_url="http://127.0.0.1:5173",
        app_source_path=app_source,
        fetcher=fetcher,
    )

    assert payload["ok"] is True
    assert [check["name"] for check in payload["checks"]] == [
        "api_direct",
        "frontend_html",
        "vite_proxy_health",
        "vite_proxy_sources",
        "vite_proxy_supplier_catalogs",
        "ui_text",
    ]


def test_check_dev_site_reports_missing_page_size_label(tmp_path):
    app_source = tmp_path / "App.jsx"
    app_source.write_text("Панель закупок\n" + _mojibake("На странице") + "\n", encoding="utf-8")

    def fetcher(url: str, timeout: float):
        if url.endswith("/api/health"):
            return 200, (
                '{"ok": true, "capabilities": '
                '["supplier_search_prepare", "supplier_catalog_presets", "supplier_catalog_health", "supplier_discovery_url"]}'
            )
        if url.endswith("/api/sources/status"):
            return 200, '{"sources": []}'
        if url.endswith("/api/supplier-catalogs/health"):
            return 200, '{"ok": true, "catalogs": []}'
        return 200, '<div id="root"></div>'

    payload = check_dev_site(
        api_base_url="http://127.0.0.1:8000",
        web_base_url="http://127.0.0.1:5173",
        app_source_path=app_source,
        fetcher=fetcher,
    )

    assert payload["ok"] is False
    ui_check = payload["checks"][-1]
    assert ui_check["name"] == "ui_text"
    assert "На странице" in ui_check["error"]
