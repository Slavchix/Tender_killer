from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus
from urllib.parse import urlparse

from tender_killer.product_profile_service import ensure_product_profiles
from tender_killer.storage import TenderStore
from tender_killer.supplier_catalog_presets import supplier_catalog_presets_for_profile


LOCKED_PROFILE_STATUSES = {"matched", "priced", "rejected"}
SUPPLIER_SEARCH_TARGETS = (
    ("Google", "https://www.google.com/search?q={query}"),
    ("Yandex", "https://yandex.ru/search/?text={query}"),
)
DIMENSION_RE = re.compile(
    r"(?<!\d)(\d+(?:[,.]\d+)?)\s*(?:x|\u0445|\u00d7)\s*"
    r"(\d+(?:[,.]\d+)?)(?:\s*(?:x|\u0445|\u00d7)\s*(\d+(?:[,.]\d+)?))?",
    re.IGNORECASE,
)
PIECE_PACK_COUNT_RE = re.compile(
    r"(?<!\d)(\d{1,5})\s*(pcs?|pieces?|pc\.?|"
    r"\u0448\u0442\.?|\u0448\u0442\u0443\u043a(?:\u0438|a)?|"
    r"\u0435\u0434\.?|\u0435\u0434\u0438\u043d\u0438\u0446(?:\u0430|\u044b)?)(?![a-z\u0430-\u044f\u0451])",
    re.IGNORECASE,
)
WEIGHT_RE = re.compile(
    r"(?<!\d)(\d+(?:[,.]\d+)?)\s*(kg|g|mg|\u043a\u0433|"
    r"\u0433\u0440?\.?|\u0433\u0440\u0430\u043c\u043c(?:\u0430|\u043e\u0432)?)"
    r"(?!\s*/\s*(?:m2|m\^2|m\u00b2|\u043c2|\u043c\^2|\u043c\u00b2))"
    r"(?![a-z\u0430-\u044f\u0451])",
    re.IGNORECASE,
)
VOLUME_RE = re.compile(
    r"(?<!\d)(\d+(?:[,.]\d+)?)\s*(ml|l|liters?|litres?|"
    r"\u043c\u043b|"
    r"\u043b\.?|\u043b\u0438\u0442\u0440(?:\u0430|\u043e\u0432)?)(?![a-z\u0430-\u044f\u0451])",
    re.IGNORECASE,
)
GENERIC_QUERY_STOP_WORDS = {
    "supply",
    "delivery",
    "purchase",
    "procurement",
    "pack",
    "kg",
    "g",
    "mg",
    "l",
    "ml",
    "pcs",
    "pc",
    "pieces",
    "piece",
    "of",
    "for",
    "and",
    "the",
    "\u043f\u043e\u0441\u0442\u0430\u0432\u043a\u0430",
    "\u043f\u043e\u0441\u0442\u0430\u0432\u043a\u0438",
    "\u043f\u0430\u0447\u043a\u0430",
    "\u0443\u043f\u0430\u043a\u043e\u0432\u043a\u0430",
    "\u043a\u0433",
    "\u0433",
    "\u0433\u0440",
    "\u043b",
    "\u043c\u043b",
    "\u0448\u0442",
    "\u0448\u0442\u0443\u043a",
    "\u0434\u043b\u044f",
    "\u0438",
}
TOKEN_RE = re.compile(r"[0-9a-zа-яё]+", re.IGNORECASE)


def build_supplier_search_queries(profile: dict[str, Any]) -> list[dict[str, Any]]:
    base_query = _text(profile.get("normalized_name")) or _text(profile.get("product_name"))
    queries: list[dict[str, Any]] = []
    seen: set[str] = set()
    supplier_catalogs = _supplier_catalogs(profile)

    if base_query:
        kind = "normalized_name" if _text(profile.get("normalized_name")) else "product_name"
        _append_query(queries, seen, base_query, kind, supplier_catalogs)

    for expanded_query in _expanded_supplier_queries(profile, base_query):
        _append_query(queries, seen, expanded_query, "catalog_hint", supplier_catalogs)

    for phrase in _text_items(profile.get("search_phrases")):
        _append_query(queries, seen, phrase, "search_phrase", supplier_catalogs)

    classifier = _text(profile.get("okpd2")) or _text(profile.get("classifier_code"))
    if classifier:
        classifier_query = f"{classifier} {base_query}" if base_query else classifier
        _append_query(queries, seen, classifier_query, "classifier", supplier_catalogs)

    return queries


def build_supplier_search_links(query: str, supplier_catalogs: list[dict[str, str]] | None = None) -> list[dict[str, str]]:
    encoded_query = quote_plus(query)
    links = [
        {"label": label, "url": url_template.format(query=encoded_query)}
        for label, url_template in SUPPLIER_SEARCH_TARGETS
    ]
    for catalog in supplier_catalogs or []:
        if link := _supplier_catalog_link(catalog, encoded_query):
            links.append(link)
    return links


def prepare_profile_supplier_search(
    database_path: str | Path,
    source: str,
    external_id: str,
    position_index: int,
) -> dict[str, Any]:
    store = TenderStore(database_path)
    store.initialize()
    profiles = ensure_product_profiles(database_path, source, external_id)

    target = _find_profile(profiles, position_index)
    if target is None:
        raise KeyError(f"Product profile position {position_index} not found.")

    queries = build_supplier_search_queries(target)
    if not queries:
        raise ValueError("No searchable product terms.")

    supplier_search = {"status": "ready", "queries": queries}
    raw_payload = dict(target.get("raw_payload") or {})
    raw_payload["supplier_search"] = supplier_search
    target["raw_payload"] = raw_payload
    if str(target.get("profile_status") or "") not in LOCKED_PROFILE_STATUSES:
        target["profile_status"] = "searching"

    store.upsert_product_profiles(source, external_id, profiles)
    return {
        "ok": True,
        "position_index": position_index,
        "supplier_search": supplier_search,
    }


def _find_profile(profiles: list[dict[str, Any]], position_index: int) -> dict[str, Any] | None:
    for profile in profiles:
        if int(profile.get("position_index") or 0) == position_index:
            return profile
    return None


def _append_query(
    queries: list[dict[str, Any]],
    seen: set[str],
    query: str,
    kind: str,
    supplier_catalogs: list[dict[str, str]],
) -> None:
    normalized = " ".join(query.split())
    if not normalized:
        return
    key = normalized.casefold()
    if key in seen:
        return
    seen.add(key)
    queries.append(
        {
            "query": normalized,
            "kind": kind,
            "priority": len(queries) + 1,
            "quick_links": build_supplier_search_links(normalized, supplier_catalogs),
        }
    )


def _expanded_supplier_queries(profile: dict[str, Any], base_query: str | None) -> list[str]:
    profile_text = _profile_search_text(profile, base_query)
    tokens = TOKEN_RE.findall(profile_text.casefold())
    if _looks_like_office_paper(profile_text, tokens):
        paper_format = _office_paper_format(tokens)
        return _unique_texts(
            [
                f"бумага офисная белая {paper_format} 80 г/м2 500 листов",
                f"бумага офисная {paper_format} 80 г/м2 500 листов",
                "бумага офисная",
                f"бумага офисная {paper_format}",
                "бумага для принтера",
            ]
        )

    if _looks_like_cartridge(profile_text, tokens):
        return _unique_texts(
            [
                "картридж лазерный",
                "картридж для принтера",
            ]
        )

    return _constrained_supplier_queries(profile_text)


def _profile_search_text(profile: dict[str, Any], base_query: str | None) -> str:
    parts: list[str] = []
    if base_query:
        parts.append(base_query)
    for field in ("product_name", "normalized_name", "category", "okpd2", "classifier_code", "details"):
        if text := _text(profile.get(field)):
            parts.append(text)
    parts.extend(_text_items(profile.get("search_phrases")))
    return " ".join(parts)


def _looks_like_office_paper(profile_text: str, tokens: list[str]) -> bool:
    has_paper = any(token.startswith("бумаг") for token in tokens)
    has_office_context = any(
        token.startswith(("офис", "принтер", "оргтехник"))
        for token in tokens
    )
    return has_paper and (has_office_context or "17.12" in profile_text)


def _looks_like_cartridge(profile_text: str, tokens: list[str]) -> bool:
    has_cartridge = any(
        token.startswith(("картридж", "тонер", "фотобарабан"))
        or token in {"cartridge", "toner", "drum"}
        for token in tokens
    )
    has_print_context = any(
        token.startswith(("принтер", "печата", "мфу", "laserjet", "printer"))
        for token in tokens
    )
    return has_cartridge or ("28.23" in profile_text and has_print_context)


def _constrained_supplier_queries(profile_text: str) -> list[str]:
    constraints = [
        *_dimension_fragments(profile_text),
        *_piece_pack_count_fragments(profile_text),
        *_weight_fragments(profile_text),
        *_volume_fragments(profile_text),
    ]
    if not constraints:
        return []
    terms = _generic_query_terms(profile_text)
    if not terms:
        return []
    return _unique_texts([" ".join([*terms[:6], *constraints])])


def _dimension_fragments(value: str) -> list[str]:
    fragments: list[str] = []
    for match in DIMENSION_RE.finditer(value.casefold()):
        parts = [_normalized_decimal(part) for part in match.groups() if part is not None]
        if len(parts) >= 2:
            fragments.append("x".join(parts))
    return _unique_texts(fragments)


def _piece_pack_count_fragments(value: str) -> list[str]:
    fragments: list[str] = []
    for match in PIECE_PACK_COUNT_RE.finditer(value.casefold()):
        unit = match.group(2)
        unit_text = "\u0448\u0442" if any("\u0430" <= char <= "\u044f" for char in unit) else "pcs"
        fragments.append(f"{int(match.group(1))} {unit_text}")
    return _unique_texts(fragments)


def _weight_fragments(value: str) -> list[str]:
    fragments: list[str] = []
    for match in WEIGHT_RE.finditer(value.casefold()):
        unit = match.group(2)
        unit_text = "kg" if unit in {"kg", "\u043a\u0433"} else "g"
        fragments.append(f"{_normalized_decimal(match.group(1))} {unit_text}")
    return _unique_texts(fragments)


def _volume_fragments(value: str) -> list[str]:
    fragments: list[str] = []
    for match in VOLUME_RE.finditer(value.casefold()):
        unit = match.group(2)
        unit_text = "ml" if unit in {"ml", "\u043c\u043b"} else "l"
        fragments.append(f"{_normalized_decimal(match.group(1))} {unit_text}")
    return _unique_texts(fragments)


def _generic_query_terms(value: str) -> list[str]:
    terms: list[str] = []
    for token in TOKEN_RE.findall(value.casefold()):
        if token.isdigit() or any(char.isdigit() for char in token):
            continue
        if token in GENERIC_QUERY_STOP_WORDS or len(token) < 2:
            continue
        terms.append(token)
    return _unique_texts(terms)


def _normalized_decimal(value: str) -> str:
    number = value.replace(",", ".")
    if "." not in number:
        return str(int(number))
    return f"{float(number):g}"


def _office_paper_format(tokens: list[str]) -> str:
    for paper_format in ("а3", "a3", "а5", "a5", "а4", "a4"):
        if paper_format in tokens:
            return paper_format.replace("a", "а")
    return "а4"


def _unique_texts(values: list[str]) -> list[str]:
    unique: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = " ".join(value.split())
        key = normalized.casefold()
        if not normalized or key in seen:
            continue
        seen.add(key)
        unique.append(normalized)
    return unique


def _supplier_catalogs(profile: dict[str, Any]) -> list[dict[str, str]]:
    raw_payload = profile.get("raw_payload") if isinstance(profile.get("raw_payload"), dict) else {}
    catalogs = raw_payload.get("supplier_catalogs")
    manual_catalogs = [] if not isinstance(catalogs, list) else [
        catalog
        for item in catalogs
        if isinstance(item, dict) and (catalog := _supplier_catalog(item)) is not None
    ]
    preset_catalogs = [
        catalog
        for item in supplier_catalog_presets_for_profile(profile)
        if (catalog := _supplier_catalog(item)) is not None
    ]
    return _unique_supplier_catalogs([*manual_catalogs, *preset_catalogs])


def _supplier_catalog(item: dict[str, Any]) -> dict[str, str] | None:
    template = _text(item.get("url_template")) or _text(item.get("search_url_template"))
    if not template or "{query}" not in template:
        return None
    label = _text(item.get("label")) or _text(item.get("provider")) or "Supplier catalog"
    provider = _text(item.get("provider")) or label
    catalog = {"label": label, "provider": provider, "url_template": template}
    if preset_id := _text(item.get("preset_id")):
        catalog["preset_id"] = preset_id
    return catalog


def _unique_supplier_catalogs(catalogs: list[dict[str, str]]) -> list[dict[str, str]]:
    unique: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for catalog in catalogs:
        key = (catalog["provider"].casefold(), catalog["url_template"].casefold())
        if key in seen:
            continue
        seen.add(key)
        unique.append(catalog)
    return unique


def _supplier_catalog_link(catalog: dict[str, str], encoded_query: str) -> dict[str, str] | None:
    try:
        url = catalog["url_template"].format(query=encoded_query)
    except (KeyError, ValueError):
        return None
    if not _is_http_url(url):
        return None
    link = {
        "label": catalog["label"],
        "url": url,
        "provider": catalog["provider"],
        "link_kind": "catalog_search",
    }
    if preset_id := catalog.get("preset_id"):
        link["preset_id"] = preset_id
    return link


def _is_http_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _text_items(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [text for item in value if (text := _text(item))]


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
