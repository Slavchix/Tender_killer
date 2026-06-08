from __future__ import annotations

import os
from typing import Any
from urllib.parse import unquote

import httpx

from tender_killer import supplier_browser_fetcher
from tender_killer.supplier_catalog_health_service import http_error_kind
from tender_killer.supplier_catalog_health_service import response_body_preview


DEFAULT_PUBLIC_FETCH_TIMEOUT_SECONDS = 5.0


def fetch_public_text(url: str, *, timeout: float | None = None, headers: dict[str, str] | None = None) -> str:
    if url.startswith("data:text/html,"):
        return unquote(url.removeprefix("data:text/html,"))
    response = httpx.get(
        url,
        follow_redirects=True,
        timeout=timeout if timeout is not None else _positive_env_float(
            "TENDER_KILLER_PRICE_DISCOVERY_HTTP_TIMEOUT_SECONDS",
            DEFAULT_PUBLIC_FETCH_TIMEOUT_SECONDS,
        ),
        trust_env=False,
        headers=headers or {"User-Agent": "TenderKiller/0.1 public price discovery"},
    )
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise _status_error(url, response, exc) from exc
    return response.text


def fetch_catalog_text(url: str, provider: str) -> str:
    try:
        return fetch_public_text(url)
    except httpx.HTTPError as exc:
        if not supplier_browser_fetcher.is_enabled_for_provider(provider):
            raise
        try:
            return supplier_browser_fetcher.fetch_text(url, provider=provider)
        except supplier_browser_fetcher.BrowserFetchError as browser_exc:
            raise httpx.HTTPError(f"{exc}; browser_fetch_error: {browser_exc}") from browser_exc


def _status_error(url: str, response: httpx.Response, exc: httpx.HTTPStatusError) -> httpx.HTTPStatusError:
    kind = http_error_kind(int(response.status_code))
    preview = response_body_preview(response.text)
    message = f"{kind} HTTP {response.status_code} from {url}"
    if preview:
        message = f"{message}: {preview}"
    return httpx.HTTPStatusError(message, request=exc.request, response=exc.response)


def _positive_env_float(name: str, default: float) -> float:
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default
    try:
        value = float(raw_value)
    except ValueError:
        return default
    return value if value > 0 else default
