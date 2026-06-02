from __future__ import annotations

from pathlib import Path

from tender_killer.dev_health import check_api_health


def test_check_api_health_requires_health_and_source_status_endpoints():
    def fetcher(url: str, timeout: float):
        if url.endswith("/api/health"):
            return 200, {
                "ok": True,
                "capabilities": [
                    "supplier_search_prepare",
                    "supplier_catalog_presets",
                    "supplier_catalog_health",
                    "supplier_discovery_url",
                    "web_auto_search",
                    "market_state_import",
                    "dashboard_queues",
                ],
            }
        if url.endswith("/api/sources/status"):
            return 200, {"sources": []}
        if url.endswith("/api/supplier-catalogs/health"):
            return 200, {"ok": True, "catalogs": []}
        raise AssertionError(url)

    payload = check_api_health("http://127.0.0.1:8000", fetcher=fetcher)

    assert payload["ok"] is True
    assert [check["path"] for check in payload["checks"]] == [
        "/api/health",
        "/api/sources/status",
        "/api/supplier-catalogs/health",
    ]


def test_check_api_health_reports_stale_backend_missing_supplier_capabilities():
    def fetcher(url: str, timeout: float):
        if url.endswith("/api/health"):
            return 200, {"ok": True}
        if url.endswith("/api/sources/status"):
            return 200, {"sources": []}
        raise AssertionError(url)

    payload = check_api_health("http://127.0.0.1:8000", fetcher=fetcher)

    assert payload["ok"] is False
    health = payload["checks"][0]
    assert health["path"] == "/api/health"
    assert "supplier_catalog_presets" in health["error"]
    assert "supplier_search_prepare" in health["error"]
    assert "supplier_catalog_health" in health["error"]
    assert "supplier_discovery_url" in health["error"]
    assert "web_auto_search" in health["error"]
    assert "market_state_import" in health["error"]
    assert "dashboard_queues" in health["error"]


def test_check_api_health_reports_stale_backend_missing_source_status():
    def fetcher(url: str, timeout: float):
        if url.endswith("/api/health"):
            return 200, {
                "ok": True,
                "capabilities": [
                    "supplier_search_prepare",
                    "supplier_catalog_presets",
                    "supplier_catalog_health",
                    "supplier_discovery_url",
                    "web_auto_search",
                    "market_state_import",
                    "dashboard_queues",
                ],
            }
        if url.endswith("/api/sources/status"):
            return 404, {"error": "not found"}
        if url.endswith("/api/supplier-catalogs/health"):
            return 200, {"ok": True, "catalogs": []}
        raise AssertionError(url)

    payload = check_api_health("http://127.0.0.1:8000", fetcher=fetcher)

    assert payload["ok"] is False
    source_status = payload["checks"][1]
    assert source_status["path"] == "/api/sources/status"
    assert source_status["status"] == 404
    assert "expected HTTP 2xx" in source_status["error"]


def test_check_api_health_reports_stale_backend_missing_supplier_catalog_health():
    def fetcher(url: str, timeout: float):
        if url.endswith("/api/health"):
            return 200, {
                "ok": True,
                "capabilities": [
                    "supplier_search_prepare",
                    "supplier_catalog_presets",
                    "supplier_catalog_health",
                    "supplier_discovery_url",
                    "web_auto_search",
                    "market_state_import",
                    "dashboard_queues",
                ],
            }
        if url.endswith("/api/sources/status"):
            return 200, {"sources": []}
        if url.endswith("/api/supplier-catalogs/health"):
            return 404, {"error": "not found"}
        raise AssertionError(url)

    payload = check_api_health("http://127.0.0.1:8000", fetcher=fetcher)

    assert payload["ok"] is False
    catalog_health = payload["checks"][2]
    assert catalog_health["path"] == "/api/supplier-catalogs/health"
    assert catalog_health["status"] == 404
    assert "expected HTTP 2xx" in catalog_health["error"]


def test_dev_web_script_runs_api_health_check_before_frontend():
    script = Path("scripts/dev-web.ps1").read_text(encoding="utf-8")

    assert "tender_killer.dev_health" in script
    assert "capabilities" in script
    assert "Port 8000 is already in use" in script
    assert "TENDER_KILLER_PDF_OCR_COMMAND" in script
    assert "ocr-pdf.ps1" in script


def test_ocr_pdf_script_wraps_local_ocr_backends_for_pdf_text_fallback():
    script = Path("scripts/ocr-pdf.ps1").read_text(encoding="utf-8")

    assert "TENDER_KILLER_PDF_OCR_COMMAND" in script
    assert "ocrmypdf" in script
    assert "tesseract" in script
    assert "pdftoppm" in script
    assert "Tesseract-OCR" in script
    assert "WinGet\\Packages" in script
    assert "OCR backend not found" in script
    assert "Fail-Ocr" in script
    assert "[Console]::OutputEncoding" in script
