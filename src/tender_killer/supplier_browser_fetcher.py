from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any


class BrowserFetchError(RuntimeError):
    pass


def is_enabled_for_provider(provider: str | None) -> bool:
    enabled_value = os.environ.get("TENDER_KILLER_SUPPLIER_BROWSER_FETCH")
    if enabled_value is not None and enabled_value.strip().casefold() not in {"1", "true", "yes", "on"}:
        return False
    provider_name = (provider or "").casefold().strip()
    allowed = {
        item.strip().casefold()
        for item in os.environ.get("TENDER_KILLER_SUPPLIER_BROWSER_FETCH_PROVIDERS", "officemag").split(",")
        if item.strip()
    }
    return "*" in allowed or provider_name in allowed


def fetch_text(url: str, *, provider: str | None = None) -> str:
    if not is_enabled_for_provider(provider):
        raise BrowserFetchError(f"browser fetch is not enabled for provider {provider or '<unknown>'}")

    script_path = resolve_script_path()
    if not script_path.exists():
        raise BrowserFetchError(f"browser fetch helper not found: {script_path}")

    command = [resolve_node_path(), str(script_path), str(url)]
    env = os.environ.copy()
    if provider:
        env["TENDER_KILLER_BROWSER_PROVIDER"] = provider

    timeout = _positive_env_float("TENDER_KILLER_BROWSER_TIMEOUT_SECONDS", 30.0) + 5.0
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=timeout,
            env=env,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise BrowserFetchError(f"browser fetch failed: {exc}") from exc

    if result.returncode != 0:
        details = (result.stderr or result.stdout or "").strip()
        raise BrowserFetchError(f"browser fetch failed with exit code {result.returncode}: {details}")
    html = result.stdout or ""
    if not html.strip():
        raise BrowserFetchError("browser fetch returned an empty response")
    return html


def resolve_node_path() -> str:
    if value := _text(os.environ.get("TENDER_KILLER_BROWSER_NODE_PATH")):
        return value
    if bundled_node := _bundled_codex_node_path():
        return str(bundled_node)
    if node_path := shutil.which("node"):
        return node_path
    return "node"


def resolve_script_path() -> Path:
    if value := _text(os.environ.get("TENDER_KILLER_BROWSER_SCRIPT_PATH")):
        return Path(value)
    return Path(__file__).resolve().parents[2] / "scripts" / "browser-fetch.mjs"


def _bundled_codex_node_path() -> Path | None:
    local_app_data = _text(os.environ.get("LOCALAPPDATA"))
    if not local_app_data:
        return None
    root = Path(local_app_data) / "OpenAI" / "Codex" / "bin"
    if not root.exists():
        return None
    candidates = [path for path in root.glob("*/node.exe") if path.exists()]
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def _positive_env_float(name: str, default: float) -> float:
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default
    try:
        value = float(raw_value)
    except ValueError:
        return default
    return value if value > 0 else default


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
