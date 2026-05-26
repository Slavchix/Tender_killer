from __future__ import annotations

from tender_killer.supplier_catalog_health_service import get_supplier_catalog_health_payload


def test_supplier_catalog_health_lists_configured_builtin_catalogs_without_network() -> None:
    payload = get_supplier_catalog_health_payload()

    assert payload["ok"] is True
    assert payload["live"] is False
    assert [catalog["provider"] for catalog in payload["catalogs"]] == [
        "officemag",
        "komus",
        "petrovich",
        "vseinstrumenti",
    ]
    assert [catalog["status"] for catalog in payload["catalogs"]] == [
        "configured",
        "configured",
        "configured",
        "configured",
    ]
    assert payload["catalogs"][0]["sample_url"] == "https://www.officemag.ru/search/?q=office+paper+a4"


def test_supplier_catalog_health_live_mode_records_provider_errors() -> None:
    calls: list[tuple[str, float]] = []

    def fetcher(url: str, timeout: float) -> tuple[int, str]:
        calls.append((url, timeout))
        if "petrovich" in url:
            return 503, "maintenance"
        if "vseinstrumenti" in url:
            raise RuntimeError("timed out")
        return 200, "<html></html>"

    payload = get_supplier_catalog_health_payload(live=True, timeout=1.5, fetcher=fetcher)

    assert payload["ok"] is False
    assert payload["live"] is True
    assert [call[0] for call in calls] == [
        "https://www.officemag.ru/search/?q=office+paper+a4",
        "https://www.komus.ru/search/?text=office+paper+a4",
        "https://petrovich.ru/search/?q=cement+mix",
        "https://www.vseinstrumenti.ru/search/?q=cement+mix",
    ]
    assert all(call[1] == 1.5 for call in calls)
    statuses = {catalog["provider"]: catalog for catalog in payload["catalogs"]}
    assert statuses["officemag"]["status"] == "ok"
    assert statuses["officemag"]["http_status"] == 200
    assert statuses["petrovich"]["status"] == "error"
    assert statuses["petrovich"]["http_status"] == 503
    assert statuses["petrovich"]["error"] == "expected HTTP 2xx/3xx, got 503"
    assert statuses["vseinstrumenti"]["status"] == "error"
    assert statuses["vseinstrumenti"]["http_status"] is None
    assert statuses["vseinstrumenti"]["error"] == "timed out"
