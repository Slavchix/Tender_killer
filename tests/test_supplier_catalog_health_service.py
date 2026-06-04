from __future__ import annotations

from tender_killer import supplier_catalog_health_service as health
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


def test_supplier_catalog_health_fetch_bypasses_system_proxy_env(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class Response:
        status_code = 200
        text = "<html></html>"

    def fake_get(url: str, **kwargs: object) -> Response:
        captured["url"] = url
        captured.update(kwargs)
        return Response()

    monkeypatch.setattr(health.httpx, "get", fake_get)

    status, body = health._fetch_catalog_status("https://example.test/search", 7.5)

    assert status == 200
    assert body == "<html></html>"
    assert captured["url"] == "https://example.test/search"
    assert captured["timeout"] == 7.5
    assert captured["follow_redirects"] is True
    assert captured["trust_env"] is False


def test_supplier_catalog_health_live_mode_records_provider_errors() -> None:
    calls: list[tuple[str, float]] = []

    def fetcher(url: str, timeout: float) -> tuple[int, str]:
        calls.append((url, timeout))
        if "komus" in url:
            return 403, "<html><body>.container { display: flex; } .load { color: grey; }</body></html>"
        if "petrovich" in url:
            return 503, "<html><head><style>body{display:block}</style></head><body><main>maintenance</main></body></html>"
        if "vseinstrumenti" in url:
            raise RuntimeError("timed out")
        return 200, "<html><body><li class='js-productListItem'>Office paper A4</li></body></html>"

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
    assert statuses["komus"]["status"] == "error"
    assert statuses["komus"]["http_status"] == 403
    assert statuses["komus"]["error_kind"] == "access_blocked"
    assert statuses["komus"]["body_preview"] == "HTML response without readable text"
    assert statuses["petrovich"]["status"] == "error"
    assert statuses["petrovich"]["http_status"] == 503
    assert statuses["petrovich"]["error"] == "expected HTTP 2xx/3xx, got 503"
    assert statuses["petrovich"]["error_kind"] == "access_blocked"
    assert statuses["petrovich"]["body_preview"] == "maintenance"
    assert statuses["vseinstrumenti"]["status"] == "error"
    assert statuses["vseinstrumenti"]["http_status"] is None
    assert statuses["vseinstrumenti"]["error"] == "timed out"
    assert statuses["vseinstrumenti"]["error_kind"] == "network_error"
    assert statuses["vseinstrumenti"]["body_preview"] == ""


def test_supplier_catalog_health_uses_browser_fallback_for_officemag_access_block(monkeypatch) -> None:
    calls: list[tuple[str, float]] = []
    browser_calls: list[tuple[str, str | None]] = []

    def fetcher(url: str, timeout: float) -> tuple[int, str]:
        calls.append((url, timeout))
        if "officemag" in url:
            return 503, "<html><body>Ваш браузер не смог пройти проверку.</body></html>"
        return 200, "<html></html>"

    def fake_browser_fetch(url: str, *, provider: str | None = None) -> str:
        browser_calls.append((url, provider))
        return "<html><body><li class='js-productListItem'>OfficeMag ok</li></body></html>"

    monkeypatch.delenv("TENDER_KILLER_SUPPLIER_BROWSER_FETCH", raising=False)
    monkeypatch.delenv("TENDER_KILLER_SUPPLIER_BROWSER_FETCH_PROVIDERS", raising=False)
    monkeypatch.setattr(health.supplier_browser_fetcher, "fetch_text", fake_browser_fetch)

    payload = get_supplier_catalog_health_payload(live=True, timeout=1.5, fetcher=fetcher)

    statuses = {catalog["provider"]: catalog for catalog in payload["catalogs"]}
    assert browser_calls == [("https://www.officemag.ru/search/?q=office+paper+a4", "officemag")]
    assert statuses["officemag"]["status"] == "ok"
    assert statuses["officemag"]["access_mode"] == "browser"
    assert statuses["officemag"]["error"] == ""
    assert statuses["officemag"]["body_preview"] == ""
    assert payload["ok"] is True


def test_supplier_catalog_health_rejects_officemag_browser_check_without_product_cards(monkeypatch) -> None:
    def fetcher(url: str, timeout: float) -> tuple[int, str]:
        if "officemag" in url:
            return 503, "<html><body>browser verification required</body></html>"
        return 200, "<html></html>"

    def fake_browser_fetch(url: str, *, provider: str | None = None) -> str:
        return "<html><body>browser verification required</body></html>"

    monkeypatch.delenv("TENDER_KILLER_SUPPLIER_BROWSER_FETCH", raising=False)
    monkeypatch.delenv("TENDER_KILLER_SUPPLIER_BROWSER_FETCH_PROVIDERS", raising=False)
    monkeypatch.setattr(health.supplier_browser_fetcher, "fetch_text", fake_browser_fetch)

    payload = get_supplier_catalog_health_payload(live=True, timeout=1.5, fetcher=fetcher)

    statuses = {catalog["provider"]: catalog for catalog in payload["catalogs"]}
    assert payload["ok"] is False
    assert statuses["officemag"]["status"] == "error"
    assert statuses["officemag"]["access_mode"] == "browser"
    assert statuses["officemag"]["error_kind"] == "access_blocked"
    assert statuses["officemag"]["browser_error"] == "browser fetch returned no parseable OfficeMag product cards"


def test_supplier_catalog_health_rejects_officemag_http_success_without_product_cards() -> None:
    def fetcher(url: str, timeout: float) -> tuple[int, str]:
        if "officemag" in url:
            return 200, "<html><body>browser verification required</body></html>"
        return 200, "<html></html>"

    payload = get_supplier_catalog_health_payload(live=True, timeout=1.5, fetcher=fetcher)

    statuses = {catalog["provider"]: catalog for catalog in payload["catalogs"]}
    assert payload["ok"] is False
    assert statuses["officemag"]["status"] == "error"
    assert statuses["officemag"]["http_status"] == 200
    assert statuses["officemag"]["error_kind"] == "access_blocked"
    assert statuses["officemag"]["error"] == "HTTP 200 did not contain parseable OfficeMag product cards"
