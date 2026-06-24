from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from tender_killer.price_candidate_service import PRICE_MATCH_STOP_WORDS
from tender_killer.price_candidate_service import evaluate_price_candidate_quality
from tender_killer.price_candidate_service import normalize_price_candidate
from tender_killer.storage import TenderStore


TOKEN_RE = re.compile(r"[\w]+", re.UNICODE)


def remember_confirmed_price_candidate(
    database_path: str | Path,
    source: str,
    external_id: str,
    profile: dict[str, Any],
    candidate: dict[str, Any],
) -> dict[str, Any]:
    store = TenderStore(database_path)
    store.initialize()
    normalized = normalize_price_candidate(profile, candidate)
    quality = evaluate_price_candidate_quality(profile, normalized)
    entry = _entry_from_confirmed_candidate(source, external_id, profile, normalized, quality)
    if not entry:
        return {}
    return store.upsert_price_book_entry(entry)


def stage_price_memory_candidates(
    database_path: str | Path,
    source: str,
    external_id: str,
    *,
    limit_per_position: int = 1,
) -> dict[str, Any]:
    store = TenderStore(database_path)
    store.initialize()
    profiles = store.get_product_profiles(source, external_id)
    entries = store.list_price_book_entries(limit=500)
    staged_count = 0
    positions: list[dict[str, Any]] = []

    for profile in profiles:
        position_index = int(profile.get("position_index") or 0)
        if _profile_has_positive_cost(profile):
            positions.append({"position_index": position_index, "staged_count": 0, "status": "already_priced"})
            continue

        matches = _rank_memory_entries(profile, entries, source=source, external_id=external_id)
        selected = matches[: max(0, int(limit_per_position))]
        if not selected:
            positions.append({"position_index": position_index, "staged_count": 0, "status": "no_memory_match"})
            continue

        candidates = [normalize_price_candidate(profile, _candidate_from_entry(profile, entry, score=score)) for score, entry in selected]
        saved = store.upsert_price_candidates(
            source,
            external_id,
            position_index,
            candidates,
            origin="price_memory",
        )
        staged_count += len(saved)
        positions.append({"position_index": position_index, "staged_count": len(saved)})

    return {
        "ok": True,
        "total_profiles": len(profiles),
        "staged_count": staged_count,
        "positions": positions,
    }


def list_price_memory_payload(database_path: str | Path, *, limit: int = 50) -> dict[str, Any]:
    store = TenderStore(database_path)
    store.initialize()
    entries = store.list_price_book_entries(limit=limit, include_archived=True)
    return _price_memory_payload(entries)


def archive_price_memory_entry(
    database_path: str | Path,
    entry_id: int,
    *,
    reason: str | None = None,
) -> dict[str, Any]:
    store = TenderStore(database_path)
    store.initialize()
    store.archive_price_book_entry(entry_id, reason=reason)
    entries = store.list_price_book_entries(limit=50, include_archived=True)
    return _price_memory_payload(entries)


def _price_memory_payload(entries: list[dict[str, Any]]) -> dict[str, Any]:
    total_count = len(entries)
    active_count = sum(1 for entry in entries if str(entry.get("entry_status") or "active") == "active")
    archived_count = sum(1 for entry in entries if str(entry.get("entry_status") or "active") == "archived")
    return {
        "ok": True,
        "price_memory": {
            "summary": {
                "total_count": total_count,
                "active_count": active_count,
                "archived_count": archived_count,
            },
            "entries": entries,
        },
    }


def _entry_from_confirmed_candidate(
    source: str,
    external_id: str,
    profile: dict[str, Any],
    candidate: dict[str, Any],
    quality: dict[str, Any],
) -> dict[str, Any]:
    unit_price = _positive_number(candidate.get("unit_price"))
    product_name = str(candidate.get("product_name") or candidate.get("name") or profile.get("product_name") or "").strip()
    if unit_price is None or not product_name:
        return {}
    profile_name = str(profile.get("normalized_name") or profile.get("product_name") or "")
    tokens = _tokens(profile_name, product_name, candidate.get("source_query"))
    raw_payload = candidate.get("raw_payload") if isinstance(candidate.get("raw_payload"), dict) else {}
    position_index = int(profile.get("position_index") or candidate.get("position_index") or 0)
    return {
        "provider": candidate.get("provider"),
        "product_name": product_name,
        "supplier_name": candidate.get("supplier_name"),
        "normalized_name": profile_name.casefold() or product_name.casefold(),
        "tokens": tokens,
        "unit": candidate.get("unit") or profile.get("unit"),
        "unit_price": unit_price,
        "currency": candidate.get("currency") or "RUB",
        "vat_mode": candidate.get("vat_mode") or raw_payload.get("vat_mode"),
        "availability": candidate.get("availability") or raw_payload.get("availability"),
        "delivery_note": candidate.get("delivery_note") or raw_payload.get("delivery_note"),
        "source_url": candidate.get("source_url") or candidate.get("url") or raw_payload.get("source_url") or raw_payload.get("url"),
        "source_kind": candidate.get("source_kind") or raw_payload.get("source_kind") or "confirmed_candidate",
        "source_query": candidate.get("source_query") or raw_payload.get("source_query") or profile.get("product_name"),
        "source_tender_source": source,
        "source_tender_external_id": external_id,
        "source_position_index": position_index,
        "source_candidate_id": candidate.get("id"),
        "quality_status": quality.get("quality_status"),
        "confidence": candidate.get("confidence"),
        "pricing_passport": {
            "quality_status": quality.get("quality_status"),
            "quality_flags": quality.get("quality_flags") or [],
            "auto_eligible": quality.get("auto_eligible") is True,
        },
        "raw_payload": {
            "profile_product_name": profile.get("product_name"),
            "candidate": candidate,
            "quality": quality,
        },
        "observed_at": candidate.get("observed_at"),
    }


def _rank_memory_entries(
    profile: dict[str, Any],
    entries: list[dict[str, Any]],
    *,
    source: str,
    external_id: str,
) -> list[tuple[float, dict[str, Any]]]:
    profile_tokens = set(_tokens(profile.get("normalized_name"), profile.get("product_name"), profile.get("details")))
    if not profile_tokens:
        return []
    profile_unit = _unit_token(profile.get("unit"))
    ranked: list[tuple[float, dict[str, Any]]] = []
    for entry in entries:
        if _is_same_position(entry, source=source, external_id=external_id, position_index=int(profile.get("position_index") or 0)):
            continue
        entry_tokens = set(_tokens(*(entry.get("tokens") or []), entry.get("normalized_name"), entry.get("product_name")))
        if not entry_tokens:
            continue
        overlap = profile_tokens & entry_tokens
        if len(overlap) < _minimum_overlap(profile_tokens):
            continue
        entry_unit = _unit_token(entry.get("unit"))
        unit_bonus = 0.5 if not profile_unit or not entry_unit or profile_unit == entry_unit else -1.0
        if unit_bonus < 0:
            continue
        score = len(overlap) + unit_bonus + _quality_bonus(entry)
        ranked.append((score, entry))
    return sorted(ranked, key=lambda item: (-item[0], -int(item[1].get("id") or 0)))


def _candidate_from_entry(profile: dict[str, Any], entry: dict[str, Any], *, score: float) -> dict[str, Any]:
    price_memory = {
        "entry_id": entry.get("id"),
        "confirmed_at": entry.get("confirmed_at"),
        "updated_at": entry.get("updated_at"),
        "source_tender_source": entry.get("source_tender_source"),
        "source_tender_external_id": entry.get("source_tender_external_id"),
        "source_position_index": entry.get("source_position_index"),
        "source_candidate_id": entry.get("source_candidate_id"),
        "quality_status": entry.get("quality_status"),
    }
    return {
        "provider": entry.get("provider") or "price_memory",
        "product_name": entry.get("product_name"),
        "supplier_name": entry.get("supplier_name"),
        "source_url": entry.get("source_url"),
        "source_query": profile.get("product_name"),
        "source_kind": "price_memory",
        "unit_price": entry.get("unit_price"),
        "currency": entry.get("currency") or "RUB",
        "vat_mode": entry.get("vat_mode"),
        "availability": entry.get("availability"),
        "delivery_note": entry.get("delivery_note"),
        "unit": entry.get("unit") or profile.get("unit"),
        "confidence": "medium",
        "confidence_reasons": ["price_memory", f"memory_score:{score:g}", "review_only"],
        "match_reasons": ["price_memory", "token_match", "operator_confirmed_before"],
        "review_status": "pending",
        "price_memory": price_memory,
        "raw_payload": {
            "price_memory": price_memory
        },
    }


def _tokens(*parts: Any) -> list[str]:
    tokens: list[str] = []
    for part in parts:
        if part is None:
            continue
        if isinstance(part, (list, tuple, set)):
            tokens.extend(_tokens(*part))
            continue
        for token in TOKEN_RE.findall(str(part).casefold()):
            if len(token) > 1 and token not in PRICE_MATCH_STOP_WORDS:
                tokens.append(token)
    return sorted(set(tokens))


def _minimum_overlap(tokens: set[str]) -> int:
    if len(tokens) <= 2:
        return len(tokens)
    return 2


def _quality_bonus(entry: dict[str, Any]) -> float:
    quality = str(entry.get("quality_status") or "").casefold()
    confidence = str(entry.get("confidence") or "").casefold()
    return (0.4 if quality == "ready" else 0.0) + (0.2 if confidence == "high" else 0.0)


def _is_same_position(entry: dict[str, Any], *, source: str, external_id: str, position_index: int) -> bool:
    return (
        str(entry.get("source_tender_source") or "") == source
        and str(entry.get("source_tender_external_id") or "") == external_id
        and int(entry.get("source_position_index") or 0) == position_index
    )


def _profile_has_positive_cost(profile: dict[str, Any]) -> bool:
    raw_payload = profile.get("raw_payload")
    if not isinstance(raw_payload, dict):
        return False
    economics = raw_payload.get("economics")
    if not isinstance(economics, dict):
        return False
    return _positive_number(economics.get("unit_cost")) is not None or _positive_number(economics.get("total_cost")) is not None


def _positive_number(value: Any) -> float | None:
    try:
        number = float(str(value).replace(" ", "").replace(",", "."))
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def _unit_token(value: Any) -> str:
    return "".join(character if character.isalnum() else "_" for character in str(value or "").casefold()).strip("_")
