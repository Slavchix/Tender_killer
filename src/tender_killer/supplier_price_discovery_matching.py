from __future__ import annotations

import re
from typing import Any

from tender_killer.supplier_price_discovery_diagnostics import MAX_INTENT_REJECTION_SAMPLES
from tender_killer.supplier_price_discovery_diagnostics import _extend_intent_rejection_samples
from tender_killer.supplier_price_discovery_queries import _supplier_search_queries
from tender_killer.supplier_price_discovery_utils import CATALOG_QUERY_STOP_WORDS
from tender_killer.supplier_price_discovery_utils import CATALOG_TOKEN_RE
from tender_killer.supplier_price_discovery_utils import _catalog_product_name_matches_query
from tender_killer.supplier_price_discovery_utils import _dedupe_text_items
from tender_killer.supplier_price_discovery_utils import _dict_items
from tender_killer.supplier_price_discovery_utils import _number
from tender_killer.supplier_price_discovery_utils import _text
from tender_killer.supplier_price_discovery_utils import _text_items
from tender_killer.supplier_product_matcher import supplier_product_name_match_reasons
from tender_killer.supplier_product_matcher import supplier_product_name_mismatch_reasons


def _supplier_candidate_rank_key(profile: dict[str, Any], candidate: dict[str, Any]) -> tuple[float, float, str]:
    unit_price = _number(candidate.get("unit_price"))
    normalized_price = unit_price if unit_price is not None else float("inf")
    name_key = _text(candidate.get("name") or candidate.get("product_name")) or ""
    return (-_supplier_candidate_relevance_score(profile, candidate), normalized_price, name_key.casefold())


def _supplier_candidate_relevance_score(profile: dict[str, Any], candidate: dict[str, Any]) -> float:
    product_name = _candidate_intent_text(candidate)
    profile_text = _profile_intent_text(profile, candidate)
    score = _number(candidate.get("score")) or 0.0
    if product_name and profile_text and _catalog_product_name_matches_query(product_name, profile_text):
        score += 60
    profile_tokens = _rank_tokens(profile_text)
    candidate_tokens = _rank_tokens(
        " ".join(
            part
            for part in (
                product_name,
                _text(candidate.get("brand")) or "",
                _text(candidate.get("manufacturer")) or "",
                _text(candidate.get("supplier_name")) or "",
            )
            if part
        )
    )
    overlap = profile_tokens.intersection(candidate_tokens)
    score += min(len(overlap), 12) * 4
    brand_tokens = _rank_tokens(_text(candidate.get("brand")) or _text(candidate.get("manufacturer")) or "")
    if brand_tokens and brand_tokens.issubset(profile_tokens.union(candidate_tokens)):
        score += 25
    confidence = (_text(candidate.get("confidence")) or "").casefold()
    score += {"high": 20, "medium": 10, "needs_review": 2, "low": 2}.get(confidence, 0)
    if _number(candidate.get("unit_price")) is not None:
        score += 10
    availability = (_text(candidate.get("availability")) or "").casefold()
    if availability in {"in_stock", "available", "instock"}:
        score += 5
    source_kind = (_text(candidate.get("source_kind")) or "").casefold()
    if source_kind in {"catalog_hint", "normalized_name", "manual_product_url"}:
        score += 8
    if candidate.get("url") or candidate.get("source_url"):
        score += 4
    return score


def _rank_tokens(text: str | None) -> set[str]:
    tokens: set[str] = set()
    for token in CATALOG_TOKEN_RE.findall(str(text or "").casefold()):
        if len(token) < 2 or token in CATALOG_QUERY_STOP_WORDS:
            continue
        tokens.add(token)
    return tokens


def _candidate_matches_profile_intent(profile: dict[str, Any], candidate: dict[str, Any]) -> bool:
    product_name = _candidate_intent_text(candidate)
    profile_text = _profile_intent_text(profile, candidate)
    if not product_name or not profile_text:
        return True
    return _catalog_product_name_matches_query(product_name, profile_text)


def _candidate_profile_intent_rejection_reasons(profile: dict[str, Any], candidate: dict[str, Any]) -> list[str]:
    product_name = _candidate_intent_text(candidate)
    profile_text = _profile_intent_text(profile, candidate)
    if not product_name or not profile_text:
        return []
    return supplier_product_name_mismatch_reasons(profile_text, product_name)


def _profile_intent_text(profile: dict[str, Any], candidate: dict[str, Any]) -> str:
    parts: list[str] = []
    for field in ("product_name", "normalized_name"):
        value = _text(profile.get(field))
        if value:
            parts.append(value)
    for phrase in _text_items(profile.get("search_phrases")):
        parts.append(phrase)
    raw_payload = profile.get("raw_payload") if isinstance(profile.get("raw_payload"), dict) else {}
    for query in _supplier_search_queries(raw_payload.get("supplier_search")):
        if _text(query.get("kind")) == "catalog_hint" and (query_text := _text(query.get("query"))):
            parts.append(query_text)
    source_query = _text(candidate.get("source_query"))
    if source_query:
        parts.append(source_query)
    return " ".join(parts)


def _candidate_with_profile_match(profile: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    updated = dict(candidate)
    reasons = _text_items(candidate.get("match_reasons"))
    reasons.extend(supplier_product_name_match_reasons(_profile_intent_text(profile, candidate), _candidate_intent_text(candidate)))
    reasons.extend(_candidate_brand_match_reasons(candidate))
    if "profile_intent_match" not in reasons:
        reasons.append("profile_intent_match")
    updated["match_reasons"] = _dedupe_text_items(reasons)
    return updated


def _candidate_intent_text(candidate: dict[str, Any]) -> str:
    parts: list[str] = []
    for field in ("name", "product_name", "brand", "manufacturer", "supplier_name", "unit"):
        if text := _text(candidate.get(field)):
            parts.append(text)
    for attribute in _dict_items(candidate.get("product_attributes")):
        name = _text(attribute.get("name"))
        value = _text(attribute.get("value"))
        if not name or not value:
            continue
        parts.append(f"{name} {value}")
        parts.append(f"{value} {name}")
        if unit_hint := _attribute_unit_hint(name):
            if unit_hint not in value.casefold():
                parts.append(f"{value} {unit_hint}")
    return " ".join(parts)


def _candidate_brand_match_reasons(candidate: dict[str, Any]) -> list[str]:
    brand_tokens = _rank_tokens(_text(candidate.get("brand")) or _text(candidate.get("manufacturer")) or "")
    if not brand_tokens:
        return []
    source_tokens = _rank_tokens(_text(candidate.get("source_query")) or "")
    name_tokens = _rank_tokens(_text(candidate.get("name") or candidate.get("product_name")) or "")
    return ["brand_match"] if brand_tokens.intersection(source_tokens.union(name_tokens)) else []


def _attribute_unit_hint(name: str) -> str | None:
    normalized = name.casefold()
    if "kg" in normalized or "\u043a\u0433" in normalized:
        return "kg"
    if "ml" in normalized or "\u043c\u043b" in normalized:
        return "ml"
    if "mm" in normalized or "\u043c\u043c" in normalized:
        return "mm"
    if re.search(r"(?<![a-z])g(?![a-z])", normalized) or "\u0433" in normalized:
        return "g"
    if re.search(r"(?<![a-z])l(?![a-z])", normalized) or "\u043b" in normalized:
        return "l"
    return None


def _provider_catalog_candidates_matching_query(
    candidates: list[dict[str, Any]],
    query_text: str,
) -> tuple[list[dict[str, Any]], int, list[dict[str, Any]]]:
    accepted: list[dict[str, Any]] = []
    rejected_count = 0
    rejection_samples: list[dict[str, Any]] = []
    for candidate in candidates:
        product_name = _candidate_intent_text(candidate)
        if not product_name or not query_text or _catalog_product_name_matches_query(product_name, query_text):
            accepted.append(candidate)
            continue
        rejected_count += 1
        if len(rejection_samples) < MAX_INTENT_REJECTION_SAMPLES:
            rejection_samples.append(_intent_rejection_sample(candidate, query_text))
    return accepted, rejected_count, rejection_samples


def _add_rejected_by_intent(
    diagnostics: dict[str, Any],
    rejected_count: int,
    rejection_samples: list[dict[str, Any]] | None = None,
) -> None:
    if rejected_count <= 0:
        return
    diagnostics["candidates_rejected_by_intent"] = (
        int(diagnostics.get("candidates_rejected_by_intent") or 0) + rejected_count
    )
    if rejection_samples:
        _extend_intent_rejection_samples(diagnostics, rejection_samples)


def _intent_rejection_sample(candidate: dict[str, Any], query_text: str) -> dict[str, Any]:
    sample = {
        "name": _text(candidate.get("name") or candidate.get("product_name")) or "",
        "url": _text(candidate.get("url")) or "",
        "reasons": supplier_product_name_mismatch_reasons(query_text, _candidate_intent_text(candidate)),
    }
    return {key: value for key, value in sample.items() if value not in ("", [], None)}
