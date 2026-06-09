from __future__ import annotations

import time
from pathlib import Path

from tender_killer import supplier_catalog_health_service as health
from tender_killer.supplier_catalog_health_service import get_cached_supplier_catalog_health_payload
from tender_killer.supplier_catalog_health_service import get_supplier_catalog_health_payload


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "supplier_catalog_health"


def _fixture_body(provider: str) -> str:
    return (FIXTURES_DIR / f"{provider}_search.html").read_text(encoding="utf-8")


def _fixture_body_for_url(url: str) -> str:
    for provider in ("officemag", "komus", "petrovich", "vseinstrumenti", "lemanapro"):
        if provider in url:
            return _fixture_body(provider)
    raise AssertionError(url)


def _workspace_tmp_path(name: str) -> Path:
    path = Path("logs") / "supplier-catalog-health-tests" / f"{name}-{time.time_ns()}"
    path.mkdir(parents=True, exist_ok=False)
    return path


def test_supplier_catalog_health_lists_configured_builtin_catalogs_without_network() -> None:
    payload = get_supplier_catalog_health_payload()

    assert payload["ok"] is True
    assert payload["live"] is False
    assert [catalog["provider"] for catalog in payload["catalogs"]] == [
        "officemag",
        "komus",
        "petrovich",
        "vseinstrumenti",
        "lemanapro",
    ]
    assert [catalog["status"] for catalog in payload["catalogs"]] == [
        "configured",
        "configured",
        "configured",
        "configured",
        "configured",
    ]
    assert [catalog["connection_state"] for catalog in payload["catalogs"]] == [
        "configured",
        "configured",
        "configured",
        "configured",
        "configured",
    ]
    assert [catalog["search_mode"] for catalog in payload["catalogs"]] == [
        "active_small_search",
        "active_small_search",
        "active_small_search",
        "active_small_search",
        "active_small_search",
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
        if "officemag" in url:
            return 200, "<html><body><li class='js-productListItem'>Office paper A4</li></body></html>"
        if "komus" in url:
            return 403, "<html><body>.container { display: flex; } .load { color: grey; }</body></html>"
        if "petrovich" in url:
            return 503, "<html><head><style>body{display:block}</style></head><body><main>maintenance</main></body></html>"
        if "vseinstrumenti" in url:
            raise RuntimeError("timed out")
        if "lemanapro" in url:
            return 200, _fixture_body("lemanapro")
        raise AssertionError(url)

    payload = get_supplier_catalog_health_payload(live=True, timeout=1.5, fetcher=fetcher)

    assert payload["ok"] is False
    assert payload["live"] is True
    assert [call[0] for call in calls] == [
        "https://www.officemag.ru/search/?q=office+paper+a4",
        "https://www.komus.ru/search/?text=office+paper+a4",
        "https://petrovich.ru/search/?q=cement+mix",
        "https://www.vseinstrumenti.ru/search/?what=%D1%81%D0%B0%D0%BC%D0%BE%D1%80%D0%B5%D0%B7%D1%8B+4%2C2x19",
        "https://lemanapro.ru/search/?q=%D1%86%D0%B5%D0%BC%D0%B5%D0%BD%D1%82+50+%D0%BA%D0%B3",
    ]
    assert all(call[1] == 1.5 for call in calls)
    statuses = {catalog["provider"]: catalog for catalog in payload["catalogs"]}
    assert statuses["officemag"]["status"] == "ok"
    assert statuses["officemag"]["connection_state"] == "reachable"
    assert statuses["officemag"]["small_tender_active_search"] is True
    assert statuses["komus"]["status"] == "error"
    assert statuses["komus"]["connection_state"] == "blocked"
    assert statuses["komus"]["http_status"] == 403
    assert statuses["komus"]["error_kind"] == "access_blocked"
    assert statuses["petrovich"]["status"] == "error"
    assert statuses["petrovich"]["connection_state"] == "blocked"
    assert statuses["petrovich"]["http_status"] == 503
    assert statuses["petrovich"]["error"] == "expected HTTP 2xx/3xx, got 503"
    assert statuses["petrovich"]["error_kind"] == "access_blocked"
    assert statuses["petrovich"]["body_preview"] == "maintenance"
    assert statuses["vseinstrumenti"]["status"] == "error"
    assert statuses["vseinstrumenti"]["connection_state"] == "timeout"
    assert statuses["vseinstrumenti"]["http_status"] is None
    assert statuses["vseinstrumenti"]["error"] == "timed out"
    assert statuses["vseinstrumenti"]["error_kind"] == "network_error"
    assert statuses["vseinstrumenti"]["body_preview"] == ""
    assert statuses["lemanapro"]["status"] == "ok"
    assert statuses["lemanapro"]["connection_state"] == "reachable"
    assert statuses["lemanapro"]["small_tender_active_search"] is True


def test_supplier_catalog_health_checks_small_search_catalogs_without_browser_fallback(monkeypatch) -> None:
    calls: list[tuple[str, float]] = []
    browser_calls: list[tuple[str, str | None, float | None]] = []

    def fetcher(url: str, timeout: float) -> tuple[int, str]:
        calls.append((url, timeout))
        return 200, _fixture_body_for_url(url)

    def fake_browser_fetch(
        url: str,
        *,
        provider: str | None = None,
        timeout_seconds: float | None = None,
    ) -> str:
        browser_calls.append((url, provider, timeout_seconds))
        return "<html><body><li class='js-productListItem'>OfficeMag ok</li></body></html>"

    monkeypatch.delenv("TENDER_KILLER_SUPPLIER_BROWSER_FETCH", raising=False)
    monkeypatch.delenv("TENDER_KILLER_SUPPLIER_BROWSER_FETCH_PROVIDERS", raising=False)
    monkeypatch.setattr(health.supplier_browser_fetcher, "fetch_text", fake_browser_fetch)

    payload = get_supplier_catalog_health_payload(live=True, timeout=1.5, fetcher=fetcher)

    statuses = {catalog["provider"]: catalog for catalog in payload["catalogs"]}
    assert [call[0] for call in calls] == [
        "https://www.officemag.ru/search/?q=office+paper+a4",
        "https://www.komus.ru/search/?text=office+paper+a4",
        "https://petrovich.ru/search/?q=cement+mix",
        "https://www.vseinstrumenti.ru/search/?what=%D1%81%D0%B0%D0%BC%D0%BE%D1%80%D0%B5%D0%B7%D1%8B+4%2C2x19",
        "https://lemanapro.ru/search/?q=%D1%86%D0%B5%D0%BC%D0%B5%D0%BD%D1%82+50+%D0%BA%D0%B3",
    ]
    assert browser_calls == []
    assert statuses["officemag"]["status"] == "ok"
    assert statuses["officemag"]["connection_state"] == "reachable"
    assert statuses["officemag"]["access_mode"] == "http"
    assert statuses["officemag"]["error"] == ""
    assert statuses["officemag"]["body_preview"] == ""
    assert payload["ok"] is True


def test_supplier_catalog_health_does_not_browser_fetch_active_catalog_blocks(monkeypatch) -> None:
    browser_calls: list[tuple[str, str | None, float | None]] = []

    def fetcher(url: str, timeout: float) -> tuple[int, str]:
        if "vseinstrumenti" in url:
            return 503, "<html><body>browser verification required</body></html>"
        return 200, _fixture_body_for_url(url)

    def fake_browser_fetch(
        url: str,
        *,
        provider: str | None = None,
        timeout_seconds: float | None = None,
    ) -> str:
        browser_calls.append((url, provider, timeout_seconds))
        return "<html><body>browser verification required</body></html>"

    monkeypatch.delenv("TENDER_KILLER_SUPPLIER_BROWSER_FETCH", raising=False)
    monkeypatch.delenv("TENDER_KILLER_SUPPLIER_BROWSER_FETCH_PROVIDERS", raising=False)
    monkeypatch.setattr(health.supplier_browser_fetcher, "fetch_text", fake_browser_fetch)

    payload = get_supplier_catalog_health_payload(live=True, timeout=1.5, fetcher=fetcher)

    statuses = {catalog["provider"]: catalog for catalog in payload["catalogs"]}
    assert browser_calls == []
    assert payload["ok"] is False
    assert statuses["vseinstrumenti"]["status"] == "error"
    assert statuses["vseinstrumenti"]["connection_state"] == "blocked"
    assert statuses["vseinstrumenti"]["access_mode"] == "http"
    assert statuses["vseinstrumenti"]["error_kind"] == "access_blocked"
    assert "browser_error" not in statuses["vseinstrumenti"]


def test_supplier_catalog_health_rejects_active_http_success_without_product_cards(monkeypatch) -> None:
    def fetcher(url: str, timeout: float) -> tuple[int, str]:
        if "vseinstrumenti" in url:
            return 200, "<html><body>empty search page without products</body></html>"
        return 200, _fixture_body_for_url(url)

    payload = get_supplier_catalog_health_payload(live=True, timeout=1.5, fetcher=fetcher)

    statuses = {catalog["provider"]: catalog for catalog in payload["catalogs"]}
    assert payload["ok"] is False
    assert statuses["vseinstrumenti"]["status"] == "error"
    assert statuses["vseinstrumenti"]["connection_state"] == "no_cards"
    assert statuses["vseinstrumenti"]["http_status"] == 200
    assert statuses["vseinstrumenti"]["error_kind"] == "access_blocked"
    assert statuses["vseinstrumenti"]["error"] == "HTTP 200 did not contain parseable ВсеИнструменты product cards"


def test_supplier_catalog_health_does_not_try_browser_for_http_success_without_cards(monkeypatch) -> None:
    browser_calls: list[tuple[str, str | None, float | None]] = []

    def fetcher(url: str, timeout: float) -> tuple[int, str]:
        if "vseinstrumenti" in url:
            return 200, "<html><body>browser verification required</body></html>"
        return 200, _fixture_body_for_url(url)

    def fake_browser_fetch(
        url: str,
        *,
        provider: str | None = None,
        timeout_seconds: float | None = None,
    ) -> str:
        browser_calls.append((url, provider, timeout_seconds))
        return _fixture_body("officemag")

    monkeypatch.delenv("TENDER_KILLER_SUPPLIER_BROWSER_FETCH", raising=False)
    monkeypatch.delenv("TENDER_KILLER_SUPPLIER_BROWSER_FETCH_PROVIDERS", raising=False)
    monkeypatch.setattr(health.supplier_browser_fetcher, "fetch_text", fake_browser_fetch)

    payload = get_supplier_catalog_health_payload(live=True, timeout=1.5, fetcher=fetcher)

    statuses = {catalog["provider"]: catalog for catalog in payload["catalogs"]}
    assert browser_calls == []
    assert statuses["vseinstrumenti"]["status"] == "error"
    assert statuses["vseinstrumenti"]["connection_state"] == "blocked"
    assert statuses["vseinstrumenti"]["access_mode"] == "http"


def test_supplier_catalog_health_classifies_captcha_response(monkeypatch) -> None:
    def fetcher(url: str, timeout: float) -> tuple[int, str]:
        if "petrovich" in url:
            return 403, "<html><body>captcha required</body></html>"
        return 200, _fixture_body_for_url(url)

    monkeypatch.setenv("TENDER_KILLER_SUPPLIER_BROWSER_FETCH", "0")

    payload = get_supplier_catalog_health_payload(live=True, timeout=1.5, fetcher=fetcher)

    statuses = {catalog["provider"]: catalog for catalog in payload["catalogs"]}
    assert statuses["petrovich"]["status"] == "error"
    assert statuses["petrovich"]["connection_state"] == "captcha"
    assert statuses["petrovich"]["error_kind"] == "access_blocked"


def test_supplier_catalog_health_uses_catalog_fixtures_for_parseability() -> None:
    for provider in ("officemag", "komus", "petrovich", "vseinstrumenti", "lemanapro"):
        html = (FIXTURES_DIR / f"{provider}_search.html").read_text(encoding="utf-8")
        assert health._catalog_body_has_parseable_content(provider, html) is True

    blocked_html = (FIXTURES_DIR / "blocked.html").read_text(encoding="utf-8")
    for provider in ("officemag", "komus", "petrovich", "vseinstrumenti", "lemanapro"):
        assert health._catalog_body_has_parseable_content(provider, blocked_html) is False


def test_supplier_catalog_health_live_result_is_cached_for_dashboard(monkeypatch) -> None:
    tmp_path = _workspace_tmp_path("cache")
    database_path = tmp_path / "tenders.sqlite"
    calls: list[str] = []

    def fetcher(url: str, timeout: float) -> tuple[int, str]:
        calls.append(url)
        if "vseinstrumenti" in url:
            return 503, "<html><body>browser verification required</body></html>"
        return 200, _fixture_body_for_url(url)

    monkeypatch.setenv("TENDER_KILLER_SUPPLIER_BROWSER_FETCH", "0")

    live_payload = get_cached_supplier_catalog_health_payload(
        database_path,
        live=True,
        timeout=1.0,
        fetcher=fetcher,
        now_factory=lambda: "2026-06-07T10:00:00+00:00",
    )
    cached_payload = get_cached_supplier_catalog_health_payload(
        database_path,
        live=False,
        fetcher=lambda url, timeout: (_ for _ in ()).throw(AssertionError("cache should avoid network")),
    )

    live_statuses = {catalog["provider"]: catalog for catalog in live_payload["catalogs"]}
    cached_statuses = {catalog["provider"]: catalog for catalog in cached_payload["catalogs"]}
    assert calls == [
        "https://www.officemag.ru/search/?q=office+paper+a4",
        "https://www.komus.ru/search/?text=office+paper+a4",
        "https://petrovich.ru/search/?q=cement+mix",
        "https://www.vseinstrumenti.ru/search/?what=%D1%81%D0%B0%D0%BC%D0%BE%D1%80%D0%B5%D0%B7%D1%8B+4%2C2x19",
        "https://lemanapro.ru/search/?q=%D1%86%D0%B5%D0%BC%D0%B5%D0%BD%D1%82+50+%D0%BA%D0%B3",
    ]
    assert live_payload["cached"] is False
    assert live_payload["checked_at"] == "2026-06-07T10:00:00+00:00"
    assert live_statuses["officemag"]["status"] == "ok"
    assert live_statuses["officemag"]["connection_state"] == "reachable"
    assert live_statuses["vseinstrumenti"]["status"] == "error"
    assert live_statuses["vseinstrumenti"]["http_status"] == 503
    assert live_statuses["vseinstrumenti"]["error_kind"] == "access_blocked"
    assert cached_payload["cached"] is True
    assert cached_payload["live"] is False
    assert cached_payload["checked_at"] == "2026-06-07T10:00:00+00:00"
    assert cached_statuses["officemag"]["connection_state"] == "reachable"
    assert cached_statuses["vseinstrumenti"]["http_status"] == 503
