from __future__ import annotations

from collections.abc import Callable
from html.parser import HTMLParser
import re
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus
from urllib.parse import urljoin
from urllib.parse import urlparse

import httpx

from tender_killer.product_profile_service import ensure_product_profiles
from tender_killer.storage import TenderStore
from tender_killer.supplier_catalog_presets import supplier_catalog_presets_for_profile


LOCKED_PROFILE_STATUSES = {"matched", "priced", "rejected"}
FetchText = Callable[[str], str]
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
LENGTH_RE = re.compile(
    r"(?<!\d)(\d+(?:[,.]\d+)?)\s*(cm|mm|m|\u0441\u043c|\u043c\u043c|\u043c)"
    r"(?![0-9a-z\u0430-\u044f\u0451])",
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
    intent = build_supplier_search_intent(profile)
    base_query = _text(intent.get("base_query"))
    queries: list[dict[str, Any]] = []
    seen: set[str] = set()
    supplier_catalogs = _supplier_catalogs(profile)

    for preferred_query in _preferred_supplier_queries(profile, base_query, intent):
        _append_query(queries, seen, preferred_query, "catalog_hint", supplier_catalogs, intent)

    if base_query:
        kind = "normalized_name" if _text(profile.get("normalized_name")) else "product_name"
        _append_query(queries, seen, base_query, kind, supplier_catalogs, intent)

    for expanded_query in _expanded_supplier_queries(profile, base_query, intent):
        _append_query(queries, seen, expanded_query, "catalog_hint", supplier_catalogs, intent)

    for phrase in _text_items(profile.get("search_phrases")):
        _append_query(queries, seen, phrase, "search_phrase", supplier_catalogs, intent)

    classifier = _text(profile.get("okpd2")) or _text(profile.get("classifier_code"))
    if classifier:
        classifier_query = f"{classifier} {base_query}" if base_query else classifier
        _append_query(queries, seen, classifier_query, "classifier", supplier_catalogs, intent)

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


def build_supplier_search_intent(profile: dict[str, Any]) -> dict[str, Any]:
    base_query = _text(profile.get("normalized_name")) or _text(profile.get("product_name")) or ""
    product_text = _profile_product_text(profile, base_query)
    routing_text = _profile_routing_text(profile)
    combined_text = " ".join(part for part in (product_text, routing_text) if part)
    combined_tokens = TOKEN_RE.findall(combined_text.casefold())
    family = _search_family(combined_text, combined_tokens)
    attributes = _search_intent_attributes(product_text)
    required_terms = _required_search_terms(family, product_text)
    catalogs = _supplier_catalogs(profile)
    noise_terms = _routing_noise_terms(routing_text, product_text)
    query_candidates = _ranked_query_candidates(
        family,
        base_query,
        product_text,
        routing_text,
        required_terms,
        attributes,
        noise_terms,
    )
    best_query = _text(query_candidates[0]["query"]) if query_candidates else _best_intent_query(
        family,
        base_query,
        product_text,
        attributes,
    )

    return {
        "family": family,
        "base_query": base_query,
        "best_query": best_query,
        "product_text": product_text,
        "routing_text": routing_text,
        "noise_terms": noise_terms,
        "required_terms": required_terms,
        "attributes": attributes,
        "query_candidates": query_candidates,
        "catalog_providers": [catalog["provider"] for catalog in catalogs],
    }


def prepare_profile_supplier_search(
    database_path: str | Path,
    source: str,
    external_id: str,
    position_index: int,
    *,
    resolve_best_product_link: bool = False,
    fetch_text: FetchText | None = None,
) -> dict[str, Any]:
    store = TenderStore(database_path)
    store.initialize()
    profiles = ensure_product_profiles(database_path, source, external_id)

    target = _find_profile(profiles, position_index)
    if target is None:
        raise KeyError(f"Product profile position {position_index} not found.")

    search_intent = build_supplier_search_intent(target)
    queries = build_supplier_search_queries(target)
    if not queries:
        raise ValueError("No searchable product terms.")

    supplier_search = {
        "status": "ready",
        "search_intent": search_intent,
        "catalog_providers": search_intent["catalog_providers"],
        "queries": queries,
    }
    if resolve_best_product_link:
        best_product_link = build_best_supplier_product_link(
            supplier_search,
            fetch_text=fetch_text or _fetch_catalog_search_text,
        )
        if best_product_link:
            supplier_search["best_product_link"] = best_product_link
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


def build_best_supplier_product_link(
    supplier_search: dict[str, Any],
    *,
    fetch_text: FetchText | None = None,
) -> dict[str, Any] | None:
    selected = _first_catalog_search_link(supplier_search)
    if not selected:
        return None
    query, link = selected
    fallback = _best_product_link_fallback(link, query)
    if fetch_text is None:
        return fallback
    try:
        html = fetch_text(str(link["url"]))
    except Exception:
        return fallback
    best = _best_product_link_from_html(html, str(link["url"]), str(query), link)
    return best or fallback


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
    intent: dict[str, Any] | None = None,
) -> None:
    normalized = " ".join(query.split())
    if not normalized:
        return
    key = normalized.casefold()
    if key in seen:
        return
    seen.add(key)
    score = _score_supplier_query(normalized, kind, intent)
    queries.append(
        {
            "query": normalized,
            "kind": kind,
            "priority": len(queries) + 1,
            "query_score": score["score"],
            "query_quality": score["quality"],
            "score_reasons": score["reasons"],
            "intent_family": _text((intent or {}).get("family")) or "generic",
            "quick_links": build_supplier_search_links(normalized, supplier_catalogs),
        }
    )


def _expanded_supplier_queries(
    profile: dict[str, Any],
    base_query: str | None,
    intent: dict[str, Any],
) -> list[str]:
    product_text = _text(intent.get("product_text")) or _profile_product_text(profile, base_query)
    routing_text = _text(intent.get("routing_text")) or _profile_routing_text(profile)
    profile_text = " ".join(part for part in (product_text, routing_text) if part)
    tokens = TOKEN_RE.findall(profile_text.casefold())
    if _looks_like_flexible_water_connector(profile_text, tokens):
        length = _first_length_fragment(profile_text)
        suffix = f" {length}" if length else ""
        return _unique_texts(
            [
                f"\u043f\u043e\u0434\u0432\u043e\u0434\u043a\u0430 \u0433\u0438\u0431\u043a\u0430\u044f \u0434\u043b\u044f \u0441\u043c\u0435\u0441\u0438\u0442\u0435\u043b\u044f{suffix}",
            ]
        )

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

    return _constrained_supplier_queries(product_text)


def _preferred_supplier_queries(
    profile: dict[str, Any],
    base_query: str | None,
    intent: dict[str, Any],
) -> list[str]:
    if intent.get("family") != "flexible_water_connector":
        return []
    return _unique_texts([_text(intent.get("best_query")) or ""])


def _profile_search_text(profile: dict[str, Any], base_query: str | None) -> str:
    parts: list[str] = []
    if base_query:
        parts.append(base_query)
    for field in ("product_name", "normalized_name", "category", "okpd2", "classifier_code", "details"):
        if text := _text(profile.get(field)):
            parts.append(text)
    parts.extend(_text_items(profile.get("search_phrases")))
    return " ".join(parts)


def _profile_product_text(profile: dict[str, Any], base_query: str | None) -> str:
    parts: list[str] = []
    if base_query:
        parts.append(base_query)
    for field in ("product_name", "normalized_name", "details"):
        if text := _text(profile.get(field)):
            parts.append(text)
    parts.extend(_text_items(profile.get("search_phrases")))
    return " ".join(_unique_texts(parts))


def _profile_routing_text(profile: dict[str, Any]) -> str:
    parts: list[str] = []
    for field in ("category", "okpd2", "classifier_code", "classifier_type"):
        if text := _text(profile.get(field)):
            parts.append(text)
    return " ".join(_unique_texts(parts))


def _search_family(profile_text: str, tokens: list[str]) -> str:
    if _looks_like_flexible_water_connector(profile_text, tokens):
        return "flexible_water_connector"
    if _looks_like_office_paper(profile_text, tokens):
        return "office_paper"
    if _looks_like_cartridge(profile_text, tokens):
        return "printer_cartridge"
    if _looks_like_fastener(tokens):
        return "fastener"
    return "generic"


def _search_intent_attributes(product_text: str) -> dict[str, Any]:
    attributes: dict[str, Any] = {}
    if lengths := _length_fragments(product_text):
        attributes["length"] = lengths[0]
    if dimensions := _dimension_fragments(product_text):
        attributes["dimensions"] = dimensions
    if pack_counts := _piece_pack_count_fragments(product_text):
        attributes["pack_count"] = pack_counts[0]
    if weights := _weight_fragments(product_text):
        attributes["weight"] = weights[0]
    if volumes := _volume_fragments(product_text):
        attributes["volume"] = volumes[0]
    return attributes


def _ranked_query_candidates(
    family: str,
    base_query: str,
    product_text: str,
    routing_text: str,
    required_terms: list[str],
    attributes: dict[str, Any],
    noise_terms: list[str],
) -> list[dict[str, Any]]:
    intent = {
        "family": family,
        "best_query": "",
        "product_text": product_text,
        "routing_text": routing_text,
        "required_terms": required_terms,
        "attributes": attributes,
        "noise_terms": noise_terms,
    }
    ranked: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, candidate in enumerate(_raw_query_candidates(family, base_query, product_text, attributes)):
        query = _text(candidate.get("query"))
        if not query:
            continue
        key = query.casefold()
        if key in seen:
            continue
        seen.add(key)
        kind = _text(candidate.get("kind")) or "catalog_hint"
        score = _score_supplier_query(query, kind, intent)
        ranked.append(
            {
                "query": query,
                "kind": kind,
                "query_score": score["score"],
                "query_quality": score["quality"],
                "score_reasons": score["reasons"],
                "_index": index,
            }
        )
    ranked.sort(key=lambda item: (-int(item["query_score"]), int(item["_index"])))
    for item in ranked:
        item.pop("_index", None)
    return ranked


def _raw_query_candidates(
    family: str,
    base_query: str,
    product_text: str,
    attributes: dict[str, Any],
) -> list[dict[str, str]]:
    candidates: list[dict[str, str]] = []
    best_query = _best_intent_query(family, base_query, product_text, attributes)
    if best_query:
        candidates.append(
            {
                "query": best_query,
                "kind": "catalog_hint" if family != "generic" else "normalized_name",
            }
        )
    if base_query:
        candidates.append({"query": base_query, "kind": "normalized_name"})
    if family == "flexible_water_connector":
        length = _text(attributes.get("length"))
        suffix = f" {length}" if length else ""
        candidates.append(
            {
                "query": f"\u043f\u043e\u0434\u0432\u043e\u0434\u043a\u0430 \u0433\u0438\u0431\u043a\u0430\u044f \u0434\u043b\u044f \u0441\u043c\u0435\u0441\u0438\u0442\u0435\u043b\u044f{suffix}",
                "kind": "catalog_hint",
            }
        )
    for query in _constrained_supplier_queries(product_text):
        candidates.append({"query": query, "kind": "catalog_hint"})
    return candidates


def _routing_noise_terms(routing_text: str, product_text: str) -> list[str]:
    product_terms = set(_generic_query_terms(product_text))
    noise_terms = [
        term
        for term in _generic_query_terms(routing_text)
        if term not in product_terms and len(term) > 3
    ]
    return _unique_texts(noise_terms)[:12]


def _required_search_terms(family: str, product_text: str) -> list[str]:
    if family == "flexible_water_connector":
        return ["\u043f\u043e\u0434\u0432\u043e\u0434\u043a\u0430", "\u0433\u0438\u0431\u043a\u0430\u044f"]
    if family == "office_paper":
        return ["\u0431\u0443\u043c\u0430\u0433\u0430"]
    if family == "printer_cartridge":
        return ["\u043a\u0430\u0440\u0442\u0440\u0438\u0434\u0436"]
    if family == "fastener":
        for token in TOKEN_RE.findall(product_text.casefold()):
            if token.startswith(("\u0431\u043e\u043b\u0442", "\u0433\u0430\u0439\u043a", "\u0432\u0438\u043d\u0442", "\u0448\u0443\u0440\u0443\u043f", "\u0441\u0430\u043c\u043e\u0440\u0435\u0437")):
                return [token]
        return ["\u043a\u0440\u0435\u043f\u0435\u0436"]
    return []


def _best_intent_query(
    family: str,
    base_query: str,
    product_text: str,
    attributes: dict[str, Any],
) -> str:
    if family == "flexible_water_connector":
        length = _text(attributes.get("length"))
        suffix = f" {length}" if length else ""
        return f"\u043f\u043e\u0434\u0432\u043e\u0434\u043a\u0430 \u0433\u0438\u0431\u043a\u0430\u044f \u0434\u043b\u044f \u0432\u043e\u0434\u044b{suffix}"
    if base_query:
        return base_query
    terms = _generic_query_terms(product_text)
    return " ".join(terms[:6])


def _looks_like_fastener(tokens: list[str]) -> bool:
    return any(
        token.startswith(
            (
                "fastener",
                "bolt",
                "nut",
                "washer",
                "screw",
                "\u043a\u0440\u0435\u043f\u0435\u0436",
                "\u043a\u0440\u0435\u043f\u0451\u0436",
                "\u0431\u043e\u043b\u0442",
                "\u0433\u0430\u0439\u043a",
                "\u0432\u0438\u043d\u0442",
                "\u0448\u0430\u0439\u0431",
                "\u0441\u0430\u043c\u043e\u0440\u0435\u0437",
            )
        )
        for token in tokens
    )


def _score_supplier_query(query: str, kind: str, intent: dict[str, Any] | None) -> dict[str, Any]:
    intent = intent or {}
    score = 40
    reasons: list[str] = ["base_terms"]
    query_text = query.casefold()

    best_query = _text(intent.get("best_query"))
    if best_query and query_text == best_query.casefold():
        score += 30
        reasons.append("best_intent_query")

    if kind == "catalog_hint":
        score += 12
        reasons.append("catalog_hint")
    elif kind in {"normalized_name", "product_name"}:
        score += 8
        reasons.append("profile_name")
    elif kind == "classifier":
        score -= 25
        reasons.append("classifier_is_routing")

    required_terms = [
        term.casefold()
        for term in intent.get("required_terms", [])
        if isinstance(term, str) and term.strip()
    ]
    matched_required = [term for term in required_terms if term in query_text]
    score += len(matched_required) * 8
    if matched_required:
        reasons.append("required_terms")
    missing_required = set(required_terms) - set(matched_required)
    if missing_required:
        score -= len(missing_required) * 15
        reasons.append("missing_required_terms")

    matched_attributes = _matched_intent_attributes(query_text, intent.get("attributes"))
    score += len(matched_attributes) * 6
    if matched_attributes:
        reasons.append("product_attributes")

    if _query_uses_routing_noise(query_text, intent):
        score -= 30
        reasons.append("routing_noise")
    else:
        score += 8
        reasons.append("routing_kept_out")

    token_count = len(TOKEN_RE.findall(query_text))
    if token_count > 9:
        score -= min(20, (token_count - 9) * 3)
        reasons.append("long_query")

    score = max(0, min(120, score))
    if score >= 60:
        quality = "good"
    elif score >= 35:
        quality = "review"
    else:
        quality = "weak"
    return {"score": score, "quality": quality, "reasons": _unique_texts(reasons)}


def _matched_intent_attributes(query_text: str, raw_attributes: Any) -> list[str]:
    if not isinstance(raw_attributes, dict):
        return []
    matched: list[str] = []
    for key, value in raw_attributes.items():
        values = value if isinstance(value, list) else [value]
        for item in values:
            text = _text(item)
            if text and text.casefold() in query_text:
                matched.append(str(key))
                break
    return _unique_texts(matched)


def _query_uses_routing_noise(query_text: str, intent: dict[str, Any]) -> bool:
    routing_text = _text(intent.get("routing_text")) or ""
    product_text = _text(intent.get("product_text")) or ""
    if not routing_text:
        return False
    product_terms = set(_generic_query_terms(product_text))
    routing_terms = [
        term
        for term in _generic_query_terms(routing_text)
        if term not in product_terms and len(term) > 3
    ]
    matched_noise = [term for term in routing_terms if term in query_text]
    return len(matched_noise) >= 2


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


def _looks_like_flexible_water_connector(profile_text: str, tokens: list[str]) -> bool:
    has_connector = any(token.startswith("\u043f\u043e\u0434\u0432\u043e\u0434") for token in tokens)
    has_flexible = any(token.startswith("\u0433\u0438\u0431\u043a") for token in tokens)
    has_plumbing_context = any(
        token.startswith(
            (
                "\u0441\u0430\u043d\u0442\u0435\u0445",
                "\u0441\u043c\u0435\u0441\u0438\u0442",
                "\u0440\u0430\u043a\u043e\u0432",
                "\u0443\u043d\u0438\u0442\u0430\u0437",
                "\u0432\u043e\u0434",
            )
        )
        for token in tokens
    )
    return has_connector and (has_flexible or has_plumbing_context or "\u0441\u0430\u043d\u0442\u0435\u0445" in profile_text.casefold())


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


def _first_length_fragment(value: str) -> str | None:
    fragments = _length_fragments(value)
    return fragments[0] if fragments else None


def _length_fragments(value: str) -> list[str]:
    fragments: list[str] = []
    for match in LENGTH_RE.finditer(value.casefold()):
        unit = match.group(2)
        unit_text = {
            "cm": "\u0441\u043c",
            "\u0441\u043c": "\u0441\u043c",
            "mm": "\u043c\u043c",
            "\u043c\u043c": "\u043c\u043c",
            "m": "\u043c",
            "\u043c": "\u043c",
        }.get(unit, unit)
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


def _first_catalog_search_link(supplier_search: dict[str, Any]) -> tuple[str, dict[str, Any]] | None:
    queries = supplier_search.get("queries")
    if not isinstance(queries, list):
        return None
    selected: tuple[int, int, int, str, dict[str, Any]] | None = None
    for query_index, query in enumerate(queries):
        if not isinstance(query, dict):
            continue
        query_text = _text(query.get("query"))
        quick_links = query.get("quick_links")
        if not query_text or not isinstance(quick_links, list):
            continue
        query_score = _query_selection_score(query, query_index)
        for link_index, link in enumerate(quick_links):
            if (
                isinstance(link, dict)
                and link.get("link_kind") == "catalog_search"
                and _text(link.get("url"))
            ):
                candidate = (query_score, -query_index, -link_index, query_text, link)
                if selected is None or candidate[:3] > selected[:3]:
                    selected = candidate
    if selected is None:
        return None
    return selected[3], selected[4]


def _query_selection_score(query: dict[str, Any], query_index: int) -> int:
    if "query_score" not in query:
        return max(0, 100 - query_index)
    try:
        return int(query.get("query_score") or 0)
    except (TypeError, ValueError):
        return max(0, 100 - query_index)


def _best_product_link_fallback(link: dict[str, Any], query: str) -> dict[str, Any]:
    label = _text(link.get("label")) or _text(link.get("provider")) or "каталоге"
    provider = _text(link.get("provider")) or label
    url = _text(link.get("url")) or ""
    return {
        "status": "fallback_search",
        "provider": provider,
        "label": label,
        "title": f"Открыть поиск в {label}",
        "url": url,
        "search_url": url,
        "source_query": query,
        "message": "Сайт не дал выбрать карточку автоматически. Открой поиск вручную.",
    }


def _best_product_link_from_html(
    html: str,
    search_url: str,
    query: str,
    catalog_link: dict[str, Any],
) -> dict[str, Any] | None:
    parser = _SearchResultLinkParser(search_url)
    parser.feed(html or "")
    candidates = [
        candidate
        for candidate in parser.links
        if _looks_like_product_link(candidate["url"], search_url)
    ]
    scored = [
        {
            **candidate,
            "match_score": _product_link_match_score(query, candidate["title"]),
        }
        for candidate in candidates
    ]
    scored = [candidate for candidate in scored if candidate["match_score"] > 0]
    if not scored:
        return None
    best = max(scored, key=lambda candidate: (candidate["match_score"], len(candidate["title"])))
    label = _text(catalog_link.get("label")) or _text(catalog_link.get("provider")) or "Каталог"
    provider = _text(catalog_link.get("provider")) or label
    return {
        "status": "product_link",
        "provider": provider,
        "label": label,
        "title": best["title"],
        "url": best["url"],
        "search_url": search_url,
        "source_query": query,
        "match_score": best["match_score"],
    }


class _SearchResultLinkParser(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__()
        self.base_url = base_url
        self.links: list[dict[str, str]] = []
        self._active_href: str | None = None
        self._active_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        href = dict(attrs).get("href")
        if not href:
            return
        self._active_href = urljoin(self.base_url, href)
        self._active_text = []

    def handle_data(self, data: str) -> None:
        if self._active_href:
            self._active_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() != "a" or not self._active_href:
            return
        title = " ".join(" ".join(self._active_text).split())
        if title:
            self.links.append({"url": self._active_href, "title": title})
        self._active_href = None
        self._active_text = []


def _looks_like_product_link(url: str, search_url: str) -> bool:
    parsed = urlparse(url)
    search = urlparse(search_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False
    if parsed.netloc.casefold() != search.netloc.casefold():
        return False
    path = parsed.path.casefold()
    if not path or path == "/":
        return False
    blocked_fragments = ("/search", "/cart", "/basket", "/login", "/auth", "/compare", "/favorite")
    return not any(fragment in path for fragment in blocked_fragments)


def _product_link_match_score(query: str, title: str) -> int:
    query_tokens = [
        token
        for token in TOKEN_RE.findall(query.casefold())
        if token not in GENERIC_QUERY_STOP_WORDS and len(token) > 1
    ]
    title_tokens = set(TOKEN_RE.findall(title.casefold()))
    if not query_tokens or not title_tokens:
        return 0
    score = sum(3 for token in query_tokens if token in title_tokens)
    score += sum(1 for token in query_tokens if any(title_token.startswith(token) for title_token in title_tokens))
    if query.casefold() in title.casefold():
        score += 8
    return score


def _fetch_catalog_search_text(url: str) -> str:
    response = httpx.get(
        url,
        follow_redirects=True,
        timeout=4.0,
        headers={
            "User-Agent": "Mozilla/5.0 TenderKiller/1.0",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    response.raise_for_status()
    return response.text


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
