from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from tender_killer import supplier_browser_fetcher as browser_fetcher


def test_browser_fetcher_runs_configured_helper(monkeypatch, tmp_path) -> None:
    script = tmp_path / "browser-fetch.mjs"
    script.write_text("// fake helper", encoding="utf-8")
    captured: dict[str, object] = {}

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured.update(kwargs)
        return subprocess.CompletedProcess(command, 0, stdout="<html>ok</html>", stderr="")

    monkeypatch.setenv("TENDER_KILLER_SUPPLIER_BROWSER_FETCH", "1")
    monkeypatch.setenv("TENDER_KILLER_SUPPLIER_BROWSER_FETCH_PROVIDERS", "officemag")
    monkeypatch.setenv("TENDER_KILLER_BROWSER_NODE_PATH", "node-test.exe")
    monkeypatch.setenv("TENDER_KILLER_BROWSER_SCRIPT_PATH", str(script))
    monkeypatch.setattr(browser_fetcher.subprocess, "run", fake_run)

    html = browser_fetcher.fetch_text("https://www.officemag.ru/search/?q=paper", provider="officemag")

    assert html == "<html>ok</html>"
    assert captured["command"] == [
        "node-test.exe",
        str(script),
        "https://www.officemag.ru/search/?q=paper",
    ]
    assert captured["text"] is True
    assert captured["encoding"] == "utf-8"


def test_browser_fetcher_uses_explicit_timeout_for_helper(monkeypatch, tmp_path) -> None:
    script = tmp_path / "browser-fetch.mjs"
    script.write_text("// fake helper", encoding="utf-8")
    captured: dict[str, object] = {}

    def fake_run(command, **kwargs):
        captured.update(kwargs)
        return subprocess.CompletedProcess(command, 0, stdout="<html>ok</html>", stderr="")

    monkeypatch.setenv("TENDER_KILLER_SUPPLIER_BROWSER_FETCH", "1")
    monkeypatch.setenv("TENDER_KILLER_BROWSER_NODE_PATH", "node-test.exe")
    monkeypatch.setenv("TENDER_KILLER_BROWSER_SCRIPT_PATH", str(script))
    monkeypatch.setattr(browser_fetcher.subprocess, "run", fake_run)

    browser_fetcher.fetch_text(
        "https://www.officemag.ru/search/?q=paper",
        provider="officemag",
        timeout_seconds=1.25,
    )

    assert captured["timeout"] == 6.25


def test_browser_fetcher_defaults_to_browser_supported_catalogs(monkeypatch) -> None:
    monkeypatch.delenv("TENDER_KILLER_SUPPLIER_BROWSER_FETCH", raising=False)
    monkeypatch.delenv("TENDER_KILLER_SUPPLIER_BROWSER_FETCH_PROVIDERS", raising=False)

    assert browser_fetcher.is_enabled_for_provider("officemag") is True
    assert browser_fetcher.is_enabled_for_provider("komus") is True
    assert browser_fetcher.is_enabled_for_provider("petrovich") is True
    assert browser_fetcher.is_enabled_for_provider("vseinstrumenti") is True
    assert browser_fetcher.is_enabled_for_provider("lemanapro") is True


def test_browser_fetch_script_has_lemanapro_dom_markers() -> None:
    script = Path("scripts/browser-fetch.mjs").read_text(encoding="utf-8")

    assert "provider === 'lemanapro'" in script
    assert "INITIAL_STATE" in script


def test_browser_fetcher_can_be_disabled_explicitly(monkeypatch) -> None:
    monkeypatch.setenv("TENDER_KILLER_SUPPLIER_BROWSER_FETCH", "0")

    assert browser_fetcher.is_enabled_for_provider("officemag") is False


def test_browser_fetcher_skips_unlisted_providers(monkeypatch) -> None:
    monkeypatch.setenv("TENDER_KILLER_SUPPLIER_BROWSER_FETCH", "1")
    monkeypatch.setenv("TENDER_KILLER_SUPPLIER_BROWSER_FETCH_PROVIDERS", "officemag")

    assert browser_fetcher.is_enabled_for_provider("officemag") is True
    assert browser_fetcher.is_enabled_for_provider("komus") is False


def test_browser_fetcher_reports_helper_failure(monkeypatch, tmp_path) -> None:
    script = tmp_path / "browser-fetch.mjs"
    script.write_text("// fake helper", encoding="utf-8")

    def fake_run(command, **kwargs):
        return subprocess.CompletedProcess(command, 2, stdout="", stderr="challenge failed")

    monkeypatch.setenv("TENDER_KILLER_SUPPLIER_BROWSER_FETCH", "1")
    monkeypatch.setenv("TENDER_KILLER_BROWSER_NODE_PATH", "node-test.exe")
    monkeypatch.setenv("TENDER_KILLER_BROWSER_SCRIPT_PATH", str(script))
    monkeypatch.setattr(browser_fetcher.subprocess, "run", fake_run)

    with pytest.raises(browser_fetcher.BrowserFetchError) as excinfo:
        browser_fetcher.fetch_text("https://www.officemag.ru/search/?q=paper", provider="officemag")

    assert "browser fetch failed" in str(excinfo.value)
    assert "challenge failed" in str(excinfo.value)


def test_browser_fetcher_discovers_bundled_codex_node(monkeypatch, tmp_path) -> None:
    local_app_data = tmp_path / "LocalAppData"
    node = local_app_data / "OpenAI" / "Codex" / "bin" / "runtime-id" / "node.exe"
    node.parent.mkdir(parents=True)
    node.write_text("", encoding="utf-8")

    monkeypatch.delenv("TENDER_KILLER_BROWSER_NODE_PATH", raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(local_app_data))
    monkeypatch.setattr(browser_fetcher.shutil, "which", lambda name: None)

    assert browser_fetcher.resolve_node_path() == str(node)


def test_browser_fetcher_skips_windowsapps_node_proxy(monkeypatch, tmp_path) -> None:
    local_app_data = tmp_path / "LocalAppData"
    bundled_node = local_app_data / "OpenAI" / "Codex" / "bin" / "runtime-id" / "node.exe"
    bundled_node.parent.mkdir(parents=True)
    bundled_node.write_text("", encoding="utf-8")
    windowsapps_node = (
        "C:\\Program Files\\WindowsApps\\OpenAI.Codex_26.601.2237.0_x64__2p2nqsd0c76g0"
        "\\app\\resources\\node.exe"
    )

    monkeypatch.setenv("TENDER_KILLER_BROWSER_NODE_PATH", windowsapps_node)
    monkeypatch.setenv("LOCALAPPDATA", str(local_app_data))
    monkeypatch.setattr(browser_fetcher.shutil, "which", lambda name: windowsapps_node)

    assert browser_fetcher.resolve_node_path() == str(bundled_node)


def test_browser_fetch_helper_uses_ephemeral_profile_by_default() -> None:
    script = Path("scripts/browser-fetch.mjs").read_text(encoding="utf-8")

    assert "supplier-fetch-runs" in script
    assert "os.tmpdir()" in script
    assert "process.cwd(), 'data'" not in script
    assert "fs.mkdtempSync" in script
    assert "detached: true" in script
    assert "function removeProfileDir" in script
    assert "fs.rmSync(profileDir, { recursive: true, force: true, maxRetries: 3, retryDelay: 200 })" in script
    assert "TENDER_KILLER_BROWSER_PROFILE_DIR" in script


def test_browser_fetch_helper_can_attach_to_existing_cdp_browser() -> None:
    script = Path("scripts/browser-fetch.mjs").read_text(encoding="utf-8")

    assert "TENDER_KILLER_BROWSER_CDP_URL" in script
    assert "resolveCdpBaseUrl" in script
    assert "attachToBrowser" in script
    assert "json/version" in script
    assert "json/new" in script
    assert "findReusableTarget" in script
    assert "rememberReusableTarget" in script
    assert "supplier-fetch-targets" in script
    assert "Boolean(${markerExpression()})" in script
    assert ".listItemsWrapper .js-productListItem" in script
    assert "input[name=\"SECTION\"]" in script
    assert "provider === 'komus'" in script
    assert "provider === 'petrovich'" in script
    assert "provider === 'vseinstrumenti'" in script
    assert "a[href*=\"/product/\"]" in script


def test_browser_bridge_launcher_exposes_cdp_url_hint() -> None:
    script = Path("scripts/browser-bridge.ps1").read_text(encoding="utf-8")

    assert "--remote-debugging-port=$Port" in script
    assert "data\\browser-bridge-profile" in script
    assert "https://www.vseinstrumenti.ru/" in script
    assert "TENDER_KILLER_BROWSER_CDP_URL" in script
    assert "cdp_url" in script
