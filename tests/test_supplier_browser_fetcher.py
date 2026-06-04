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


def test_browser_fetcher_defaults_to_officemag_only(monkeypatch) -> None:
    monkeypatch.delenv("TENDER_KILLER_SUPPLIER_BROWSER_FETCH", raising=False)
    monkeypatch.delenv("TENDER_KILLER_SUPPLIER_BROWSER_FETCH_PROVIDERS", raising=False)

    assert browser_fetcher.is_enabled_for_provider("officemag") is True
    assert browser_fetcher.is_enabled_for_provider("komus") is False


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
