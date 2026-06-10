from __future__ import annotations

import os
import re
from typing import Any
from urllib.parse import urlparse

from tender_killer.supplier_catalog_fetcher import fetch_catalog_text
from tender_killer.supplier_catalog_fetcher import fetch_public_text
from tender_killer.supplier_product_matcher import supplier_product_name_matches_query


SEARCH_ENGINE_HOSTS = ("google.", "yandex.")
NUMBER_SPACE_RE = re.compile(r"[\s\u00a0\u202f]+")
CATALOG_TOKEN_RE = re.compile(r"[\w]+", re.UNICODE)
CATALOG_QUERY_STOP_WORDS = {
    "\u0434\u043b\u044f",
    "\u0442\u043e\u0432\u0430\u0440",
    "\u0442\u043e\u0432\u0430\u0440\u0430",
    "\u0442\u043e\u0432\u0430\u0440\u044b",
    "\u0440\u0430\u0431\u043e\u0442\u0430",
    "\u0440\u0430\u0431\u043e\u0442\u044b",
    "\u0443\u0441\u043b\u0443\u0433\u0430",
    "\u0443\u0441\u043b\u0443\u0433\u0438",
    "\u043e\u0444\u0438\u0441\u043d\u043e\u0439",
    "\u043e\u0444\u0438\u0441\u043d\u0430\u044f",
    "\u0442\u0435\u0445\u043d\u0438\u043a\u0438",
    "\u0442\u0435\u0445\u043d\u0438\u043a\u0430",
    "office",
    "for",
    "the",
}


def _positive_env_int(name: str, default: int) -> int:
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default
    try:
        value = int(raw_value)
    except ValueError:
        return default
    return value if value > 0 else default


def _append_unique_url(urls: list[str], seen: set[str], url: str) -> None:
    key = url.casefold()
    if key in seen:
        return
    seen.add(key)
    urls.append(url)


def _fetch_public_text(url: str) -> str:
    return fetch_public_text(url)


def _fetch_catalog_text(url: str, provider: str, *, allow_browser_fetch: bool = False) -> str:
    return fetch_catalog_text(url, provider, allow_browser_fetch=allow_browser_fetch)


def _is_public_product_page_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme == "data":
        return True
    if parsed.scheme not in {"http", "https"}:
        return False
    host = parsed.netloc.casefold()
    return not any(marker in host for marker in SEARCH_ENGINE_HOSTS)


def _is_same_public_site(source_url: str, target_url: str) -> bool:
    source = urlparse(source_url)
    target = urlparse(target_url)
    if source.scheme == "data" or target.scheme == "data":
        return True
    return source.netloc.casefold() == target.netloc.casefold()


def _provider_from_url(url: str) -> str | None:
    host = urlparse(url).netloc.casefold()
    if "officemag.ru" in host:
        return "officemag"
    if "komus.ru" in host:
        return "komus"
    if "petrovich.ru" in host:
        return "petrovich"
    if "vseinstrumenti.ru" in host:
        return "vseinstrumenti"
    if "lemanapro.ru" in host:
        return "lemanapro"
    return None


def _catalog_provider_label(provider: str) -> str:
    labels = {
        "officemag": "OfficeMag",
        "komus": "Komus",
        "petrovich": "Petrovich",
        "vseinstrumenti": "Vseinstrumenti",
        "lemanapro": "Lemana Pro",
    }
    return labels.get(provider.casefold(), provider.replace("_", " ").title())


def _catalog_product_name_matches_query(product_name: str, query_text: str) -> bool:
    return supplier_product_name_matches_query(query_text, product_name)


def _catalog_token_stems(text: str, *, remove_stop_words: bool) -> set[str]:
    stems: set[str] = set()
    for token in CATALOG_TOKEN_RE.findall(str(text or "").casefold()):
        if token.isdigit() or len(token) < 4:
            continue
        if remove_stop_words and token in CATALOG_QUERY_STOP_WORDS:
            continue
        stems.add(token[:5])
    return stems


def _positive_number(value: Any) -> int | None:
    number = _number(value)
    if number is None or number <= 0:
        return None
    return int(number)


def _format_decimal(value: Any) -> str:
    number = _number(value)
    if number is None:
        return ""
    return f"{number:.2f}".rstrip("0").rstrip(".")


def _is_provider_product_detail_url(provider: str, url: str) -> bool:
    parsed = urlparse(url)
    path = parsed.path.casefold()
    provider_key = provider.casefold()
    if provider_key == "officemag":
        return "/catalog/goods/" in path
    if provider_key == "komus":
        return "/p/" in path
    if provider_key == "petrovich":
        return path.startswith("/product/") or path.startswith("/catalog/")
    if provider_key == "vseinstrumenti":
        return "/product/" in path
    if provider_key == "lemanapro":
        return "/product/" in path
    return False


def _dict_items(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]


def _text_items(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    items: list[str] = []
    for item in value:
        text = _text(item)
        if text:
            items.append(text)
    return items


def _dedupe_text_items(items: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        text = _text(item)
        if not text:
            continue
        key = text.casefold()
        if key in seen:
            continue
        seen.add(key)
        result.append(text)
    return result


def _unique_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unique: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for candidate in candidates:
        url = (_text(candidate.get("url")) or "").casefold()
        name = (_text(candidate.get("name") or candidate.get("product_name")) or "").casefold()
        key = (url, name)
        if key in seen:
            continue
        seen.add(key)
        unique.append(candidate)
    return unique


def _candidate_key(candidate: dict[str, Any]) -> tuple[str, str]:
    url = _text(candidate.get("url"))
    source_query = _text(candidate.get("source_query"))
    return (
        (_text(candidate.get("provider")) or "").casefold(),
        (url or source_query or "").casefold(),
    )


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _number(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        number = float(NUMBER_SPACE_RE.sub("", str(value)).replace(",", "."))
    except (TypeError, ValueError):
        return None
    return number if number >= 0 else None
