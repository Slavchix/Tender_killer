from __future__ import annotations

import json
import shutil
from pathlib import Path

from tender_killer.dev_smoke import REQUIRED_UI_TEXT
from tender_killer.dev_smoke import check_dev_site


def _mojibake(text: str) -> str:
    return text.encode("utf-8").decode("cp1251")


def _workspace_tmp(name: str) -> Path:
    root = Path.cwd() / "pytest-cache-dev-smoke" / name
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    return root


def test_check_dev_site_verifies_api_frontend_proxy_and_ui_text():
    app_source = _workspace_tmp("ok") / "App.jsx"
    app_source.write_text(
        "Tender Killer\nЗакупки\nФильтры\nНа странице\nЗакупок на странице\n",
        encoding="utf-8",
    )

    def fetcher(url: str, timeout: float):
        if url == "http://127.0.0.1:8000/api/health":
            return 200, (
                '{"ok": true, "capabilities": '
                '["supplier_search_prepare", "supplier_catalog_presets", "supplier_catalog_health", "supplier_discovery_url", "web_auto_search", "market_state_import", "dashboard_queues", "price_candidate_auto_stage", "price_auto_apply", "price_discovery_run", "price_discovery_jobs"]}'
            )
        if url == "http://127.0.0.1:8000/api/sources/status":
            return 200, '{"sources": []}'
        if url == "http://127.0.0.1:8000/api/supplier-catalogs/health":
            return 200, '{"ok": true, "catalogs": []}'
        if url == "http://127.0.0.1:5175/":
            return 200, '<html><body><div id="root"></div><script type="module" src="/src/App.jsx"></script></body></html>'
        if url == "http://127.0.0.1:5175/api/health":
            return 200, (
                '{"ok": true, "capabilities": '
                '["supplier_search_prepare", "supplier_catalog_presets", "supplier_catalog_health", "supplier_discovery_url", "web_auto_search", "market_state_import", "dashboard_queues", "price_candidate_auto_stage", "price_auto_apply", "price_discovery_run", "price_discovery_jobs"]}'
            )
        if url == "http://127.0.0.1:5175/api/sources/status":
            return 200, '{"sources": []}'
        if url == "http://127.0.0.1:5175/api/supplier-catalogs/health":
            return 200, '{"ok": true, "catalogs": []}'
        raise AssertionError(url)

    payload = check_dev_site(
        api_base_url="http://127.0.0.1:8000",
        web_base_url="http://127.0.0.1:5175",
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


def test_check_dev_site_accepts_blocked_supplier_catalog_diagnostics():
    app_source = _workspace_tmp("blocked-catalogs") / "App.jsx"
    app_source.write_text(
        "\n".join(REQUIRED_UI_TEXT) + "\n",
        encoding="utf-8",
    )

    def fetcher(url: str, timeout: float):
        if url.endswith("/api/health"):
            return 200, (
                '{"ok": true, "capabilities": '
                '["supplier_search_prepare", "supplier_catalog_presets", "supplier_catalog_health", "supplier_discovery_url", "web_auto_search", "market_state_import", "dashboard_queues", "price_candidate_auto_stage", "price_auto_apply", "price_discovery_run", "price_discovery_jobs"]}'
            )
        if url.endswith("/api/sources/status"):
            return 200, '{"sources": []}'
        if url.endswith("/api/supplier-catalogs/health"):
            return 200, '{"ok": false, "catalogs": [{"provider": "officemag", "status": "error"}]}'
        return 200, '<html><body><div id="root"></div></body></html>'

    payload = check_dev_site(
        api_base_url="http://127.0.0.1:8000",
        web_base_url="http://127.0.0.1:5175",
        app_source_path=app_source,
        fetcher=fetcher,
    )

    assert payload["ok"] is True


def test_visual_smoke_script_covers_key_frontend_surfaces():
    package = json.loads(Path("package.json").read_text(encoding="utf-8"))
    script = Path("scripts/visual-smoke.mjs").read_text(encoding="utf-8")

    assert package["scripts"]["dev:visual"] == "node scripts/visual-smoke.mjs"
    assert "Page.captureScreenshot" in script
    assert ".dashboard-queue-board" in script
    assert ".tender-list .rows" in script
    assert ".tender-row" in script
    assert ".fullscreen-workspace.analysis" in script
    assert ".fullscreen-workspace.economics" in script
    assert "No tender rows available in the current dev database." in script


def test_visual_smoke_script_supports_tz_scope_without_economics_workspace():
    script = Path("scripts/visual-smoke.mjs").read_text(encoding="utf-8")

    assert "--scope" in script
    assert "VALID_SCOPES" in script
    assert "scope: parsed.scope || 'full'" in script
    assert "SURFACE_SCOPES" in script
    assert "tz: ['dashboard', 'tender-list', 'analysis-workspace']" in script
    assert "full: ['dashboard', 'tender-list', 'analysis-workspace', 'economics-workspace']" in script


def test_visual_smoke_script_captures_browser_errors_and_strict_surface_selectors():
    script = Path("scripts/visual-smoke.mjs").read_text(encoding="utf-8")

    assert "const browserEvents = createBrowserEventLog()" in script
    assert "Runtime.exceptionThrown" in script
    assert "Log.entryAdded" in script
    assert "browser_events" in script
    assert "assertNoNewBrowserErrors" in script
    assert "resetBrowserEvents" in script

    assert "dashboard-queue-columns" in script
    assert ".dashboard-queue-column" in script
    assert ".dashboard-queue-items" in script
    assert "tender-list-rows" in script
    assert ".tender-row .row-insights" in script
    assert "analysis-workspace-core" in script
    assert ".analysis-decision-brief" in script
    assert ".analysis-passport" in script


def test_visual_smoke_script_waits_for_browser_exit_before_profile_cleanup():
    script = Path("scripts/visual-smoke.mjs").read_text(encoding="utf-8")

    assert "await stopBrowser(browser)" in script
    assert "await removeUserDataDir(userDataDir)" in script
    assert "function stopBrowser" in script
    assert "function removeUserDataDir" in script
    assert "EBUSY" in script
    assert "EPERM" in script


def test_visual_smoke_script_handles_empty_tender_list_and_benign_browser_noise():
    script = Path("scripts/visual-smoke.mjs").read_text(encoding="utf-8")

    assert "minHeight" in script
    assert "minWidth" in script
    assert "isIgnoredBrowserLogEntry" in script
    assert "favicon.ico" in script
    assert "entry.url" in script


def test_check_dev_site_reports_missing_page_size_label():
    app_source = _workspace_tmp("missing-label") / "App.jsx"
    app_source.write_text(
        "Tender Killer\nЗакупки\nФильтры\n" + _mojibake("На странице") + "\n",
        encoding="utf-8",
    )

    def fetcher(url: str, timeout: float):
        if url.endswith("/api/health"):
            return 200, (
                '{"ok": true, "capabilities": '
                '["supplier_search_prepare", "supplier_catalog_presets", "supplier_catalog_health", "supplier_discovery_url", "web_auto_search", "market_state_import", "dashboard_queues", "price_candidate_auto_stage", "price_auto_apply", "price_discovery_run", "price_discovery_jobs"]}'
            )
        if url.endswith("/api/sources/status"):
            return 200, '{"sources": []}'
        if url.endswith("/api/supplier-catalogs/health"):
            return 200, '{"ok": true, "catalogs": []}'
        return 200, '<div id="root"></div>'

    payload = check_dev_site(
        api_base_url="http://127.0.0.1:8000",
        web_base_url="http://127.0.0.1:5175",
        app_source_path=app_source,
        fetcher=fetcher,
    )

    assert payload["ok"] is False
    ui_check = payload["checks"][-1]
    assert ui_check["name"] == "ui_text"
    assert "На странице" in ui_check["error"]
