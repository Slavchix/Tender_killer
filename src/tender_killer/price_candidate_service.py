from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Any

from tender_killer.price_candidate_common import (
    MIN_ORDER_AMOUNT_FIELDS,
    MIN_ORDER_QUANTITY_FIELDS,
    PACK_QUANTITY_FIELDS,
    SUPPLIER_PREORDER_FIELDS,
    SUPPLIER_STOCK_FIELDS,
    copy_price_break_fields as _copy_price_break_fields,
    first_number as _first_number,
    number_or_none as _number,
    price_breaks as _price_breaks,
    raw_payload as _raw_payload,
    string_list as _string_list,
    token as _token,
    units_compatible as _units_compatible,
)
from tender_killer.price_candidate_normalization import normalize_price_candidate
from tender_killer.price_candidate_passport import build_pricing_passport
from tender_killer.price_candidate_quality import (
    candidate_score as _candidate_score,
    ensure_candidate_confirmable as _ensure_candidate_confirmable,
    evaluate_price_candidate_quality,
)
from tender_killer.product_profile_service import ensure_product_profiles
from tender_killer.storage import TenderStore


REVIEW_STATUSES = {"confirmed", "rejected"}
PRICE_MATCH_TOKEN_RE = re.compile(r"[\w]+", re.UNICODE)
PRICE_MATCH_STOP_WORDS = {
    "для",
    "товар",
    "товара",
    "товары",
    "работа",
    "работы",
    "услуга",
    "услуги",
    "офисной",
    "офисная",
    "техники",
    "техника",
    "office",
    "for",
    "the",
}


def rank_profile_price_candidates(profile: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = profile.get("price_candidates") if isinstance(profile.get("price_candidates"), list) else []
    ranked: list[dict[str, Any]] = []
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        candidate = _rankable_price_candidate(profile, candidate)
        quality = evaluate_price_candidate_quality(profile, candidate)
        score, reasons = _candidate_score(candidate, quality)
        ranked_candidate = {**candidate, **quality, "score": score, "score_reasons": reasons}
        ranked_candidate["pricing_passport"] = build_pricing_passport(profile, ranked_candidate)
        ranked.append(ranked_candidate)
    return sorted(ranked, key=_rank_key)


def _rankable_price_candidate(profile: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    raw_payload = _raw_payload(candidate)
    if _number(candidate.get("unit_price") or raw_payload.get("unit_price")) is None:
        return {**candidate}
    return normalize_price_candidate(profile, candidate)


def stage_tender_price_candidates(
    database_path: str | Path,
    source: str,
    external_id: str,
) -> dict[str, Any]:
    store = TenderStore(database_path)
    store.initialize()
    profiles = _ensure_profiles_with_item_fallback(database_path, source, external_id)
    staged_count = 0
    ready_count = 0
    review_count = 0
    blocked_count = 0
    skipped_no_candidate_source_count = 0
    positions: list[dict[str, Any]] = []

    for profile in profiles:
        position_index = int(profile.get("position_index") or 0)
        candidates = _profile_candidate_sources(profile)
        if not candidates:
            skipped_no_candidate_source_count += 1
            positions.append({"position_index": position_index, "staged_count": 0, "status": "no_candidate_source"})
            continue

        normalized_candidates = [normalize_price_candidate(profile, candidate) for candidate in candidates]
        saved_candidates = store.upsert_price_candidates(
            source,
            external_id,
            position_index,
            normalized_candidates,
            origin="auto_stage",
        )
        staged_count += len(saved_candidates)

        status_counts = {"ready": 0, "review": 0, "blocked": 0}
        for candidate in saved_candidates:
            status = str(evaluate_price_candidate_quality(profile, candidate).get("quality_status") or "review")
            if status in status_counts:
                status_counts[status] += 1
        ready_count += status_counts["ready"]
        review_count += status_counts["review"]
        blocked_count += status_counts["blocked"]
        positions.append(
            {
                "position_index": position_index,
                "staged_count": len(saved_candidates),
                "ready_count": status_counts["ready"],
                "review_count": status_counts["review"],
                "blocked_count": status_counts["blocked"],
            }
        )

    return {
        "ok": True,
        "total_profiles": len(profiles),
        "profiles_with_candidates_count": len(profiles) - skipped_no_candidate_source_count,
        "staged_count": staged_count,
        "ready_count": ready_count,
        "review_count": review_count,
        "blocked_count": blocked_count,
        "skipped_no_candidate_source_count": skipped_no_candidate_source_count,
        "positions": positions,
    }


def review_profile_price_candidate(
    database_path: str | Path,
    source: str,
    external_id: str,
    position_index: int,
    candidate_id: int,
    *,
    review_status: str,
) -> dict[str, Any]:
    status = _review_status(review_status)
    store = TenderStore(database_path)
    store.initialize()
    profiles = _ensure_profiles_with_item_fallback(database_path, source, external_id)
    target = _find_profile(profiles, position_index)
    candidate = _find_candidate(store, source, external_id, position_index, candidate_id)

    supplier_option_index: int | None = None
    propagated: list[dict[str, int | None]] = []
    if status == "confirmed":
        _ensure_candidate_confirmable(target, candidate)
        supplier_option_index = _apply_confirmed_candidate(target, candidate)
        propagated = _propagate_confirmed_candidate_to_matching_profiles(profiles, target, candidate)
        store.upsert_product_profiles(source, external_id, profiles)
        from tender_killer.price_memory_service import remember_confirmed_price_candidate

        remember_confirmed_price_candidate(
            store.database_path,
            source,
            external_id,
            target,
            {**candidate, "review_status": "confirmed"},
        )

    store.update_price_candidate_review(
        source,
        external_id,
        position_index,
        candidate,
        review_status=status,
        supplier_option_index=supplier_option_index,
    )
    result = {
        "ok": True,
        "position_index": int(position_index),
        "candidate_id": int(candidate_id),
        "review_status": status,
        "supplier_option_index": supplier_option_index,
    }
    if propagated:
        result["propagated_count"] = len(propagated)
        result["propagated"] = propagated
    return result


def confirm_ready_price_candidates(
    database_path: str | Path,
    source: str,
    external_id: str,
) -> dict[str, Any]:
    store = TenderStore(database_path)
    store.initialize()
    profiles = _ensure_profiles_with_item_fallback(database_path, source, external_id)

    confirmed: list[dict[str, int | None]] = []
    propagated: list[dict[str, int | None]] = []
    review_updates: list[tuple[int, dict[str, Any], int | None]] = []
    skipped_existing_cost_count = 0
    skipped_no_ready_candidate_count = 0

    for profile in profiles:
        position_index = int(profile.get("position_index") or 0)
        if _profile_has_positive_cost(profile):
            skipped_existing_cost_count += 1
            continue

        candidate = _first_ready_candidate(profile)
        if candidate is None:
            skipped_no_ready_candidate_count += 1
            continue

        supplier_option_index = _apply_confirmed_candidate(profile, candidate, selection="bulk_auto_eligible")
        confirmed.append(
            {
                "position_index": position_index,
                "candidate_id": int(candidate["id"]),
                "supplier_option_index": supplier_option_index,
            }
        )
        review_updates.append((position_index, candidate, supplier_option_index))
        propagated.extend(_propagate_confirmed_candidate_to_matching_profiles(profiles, profile, candidate))

    if confirmed:
        store.upsert_product_profiles(source, external_id, profiles)
        for position_index, candidate, supplier_option_index in review_updates:
            store.update_price_candidate_review(
                source,
                external_id,
                position_index,
                candidate,
                review_status="confirmed",
                supplier_option_index=supplier_option_index,
            )
            profile = _find_profile(profiles, position_index)
            from tender_killer.price_memory_service import remember_confirmed_price_candidate

            remember_confirmed_price_candidate(
                store.database_path,
                source,
                external_id,
                profile,
                {**candidate, "review_status": "confirmed"},
            )

    skipped_count = skipped_existing_cost_count + skipped_no_ready_candidate_count
    result = {
        "ok": True,
        "total_profiles": len(profiles),
        "confirmed_count": len(confirmed),
        "skipped_count": skipped_count,
        "skipped_existing_cost_count": skipped_existing_cost_count,
        "skipped_no_ready_candidate_count": skipped_no_ready_candidate_count,
        "confirmed": confirmed,
    }
    if propagated:
        result["propagated_count"] = len(propagated)
        result["propagated"] = propagated
    return result


def apply_tender_auto_prices(
    database_path: str | Path,
    source: str,
    external_id: str,
) -> dict[str, Any]:
    stage = stage_tender_price_candidates(database_path, source, external_id)
    ready_review = confirm_ready_price_candidates(database_path, source, external_id)
    profiles = _ensure_profiles_with_item_fallback(database_path, source, external_id)

    priced_positions: list[int] = []
    missing_cost_positions: list[int] = []
    for profile in profiles:
        position_index = int(profile.get("position_index") or 0)
        if _profile_has_positive_cost(profile):
            priced_positions.append(position_index)
        else:
            missing_cost_positions.append(position_index)

    return {
        "ok": True,
        "total_profiles": len(profiles),
        "stage": stage,
        "ready_review": ready_review,
        "applied_count": int(ready_review.get("confirmed_count") or 0),
        "priced_count": len(priced_positions),
        "missing_cost_count": len(missing_cost_positions),
        "priced_positions": priced_positions,
        "missing_cost_positions": missing_cost_positions,
    }


def _rank_key(candidate: dict[str, Any]) -> tuple[float, float, int]:
    price = _number(candidate.get("unit_price"))
    normalized_price = price if price is not None else float("inf")
    return (-float(candidate.get("score") or 0), normalized_price, int(candidate.get("id") or 0))


def _apply_confirmed_candidate(
    profile: dict[str, Any],
    candidate: dict[str, Any],
    *,
    selection: str = "manual_confirmed",
) -> int | None:
    unit_price = _number(candidate.get("unit_price"))
    if unit_price is None:
        raise ValueError("Price candidate has no unit price.")

    raw_payload = dict(profile.get("raw_payload") or {})
    supplier_options = _supplier_options(raw_payload.get("supplier_options"))
    option = _supplier_option_from_candidate(candidate)
    option_index = _matching_supplier_option_index(supplier_options, option)
    if option_index is None:
        supplier_options.append(option)
        option_index = len(supplier_options) - 1

    for index, supplier_option in enumerate(supplier_options):
        if index == option_index:
            supplier_option["status"] = "selected"
        elif supplier_option.get("status") == "selected":
            supplier_option["status"] = "candidate"

    economics = dict(raw_payload.get("economics") or {})
    economics["unit_cost"] = unit_price
    raw_payload["economics"] = economics
    raw_payload["supplier_options"] = supplier_options
    raw_payload["selected_supplier_option_index"] = option_index
    quality = evaluate_price_candidate_quality(profile, candidate)
    raw_payload["economics_price_source"] = _economics_price_source(candidate, unit_price, quality, selection=selection)
    profile["raw_payload"] = raw_payload
    profile["profile_status"] = "priced"
    return option_index


def _propagate_confirmed_candidate_to_matching_profiles(
    profiles: list[dict[str, Any]],
    source_profile: dict[str, Any],
    candidate: dict[str, Any],
) -> list[dict[str, int | None]]:
    source_index = int(source_profile.get("position_index") or 0)
    source_key = _profile_price_reuse_key(source_profile)
    source_unit = _token(source_profile.get("unit"))
    if not source_key or not source_unit:
        return []

    propagated: list[dict[str, int | None]] = []
    for profile in profiles:
        position_index = int(profile.get("position_index") or 0)
        if position_index == source_index or _profile_has_positive_cost(profile):
            continue
        if _profile_price_reuse_key(profile) != source_key:
            continue
        target_unit = _token(profile.get("unit"))
        if not target_unit or not _units_compatible(source_unit, target_unit):
            continue
        option_index = _apply_confirmed_candidate(profile, candidate, selection="reused_from_position")
        raw_payload = dict(profile.get("raw_payload") or {})
        price_source = dict(raw_payload.get("economics_price_source") or {})
        price_source["reused_from_position_index"] = source_index
        raw_payload["economics_price_source"] = price_source
        profile["raw_payload"] = raw_payload
        propagated.append({"position_index": position_index, "supplier_option_index": option_index})
    return propagated


def _profile_price_reuse_key(profile: dict[str, Any]) -> str:
    name = str(profile.get("normalized_name") or profile.get("product_name") or "").casefold()
    tokens = [token for token in PRICE_MATCH_TOKEN_RE.findall(name) if token and token not in PRICE_MATCH_STOP_WORDS]
    return " ".join(tokens)


def _economics_price_source(
    candidate: dict[str, Any],
    unit_price: float,
    quality: dict[str, Any],
    *,
    selection: str,
) -> dict[str, Any]:
    raw_payload = _raw_payload(candidate)
    source = {
        "source": "price_candidate",
        "selection": selection,
        "candidate_id": int(candidate["id"]),
        "provider": candidate.get("provider"),
        "product_name": candidate.get("product_name"),
        "supplier_name": candidate.get("supplier_name"),
        "source_url": candidate.get("source_url"),
        "source_query": candidate.get("source_query"),
        "source_kind": candidate.get("source_kind"),
        "unit_price": unit_price,
        "currency": candidate.get("currency") or "RUB",
        "review_status": "confirmed",
        "quality_status": quality.get("quality_status"),
        "auto_eligible": bool(quality.get("auto_eligible")),
        "quality_flags": quality.get("quality_flags") or [],
    }
    for field, fields in {
        "stock_quantity": SUPPLIER_STOCK_FIELDS,
        "preorder_quantity": SUPPLIER_PREORDER_FIELDS,
        "minimum_order_quantity": MIN_ORDER_QUANTITY_FIELDS,
        "pack_quantity": PACK_QUANTITY_FIELDS,
    }.items():
        number = _first_number(candidate, raw_payload, fields)
        if number is not None:
            source[field] = number
    price_memory = candidate.get("price_memory") if isinstance(candidate.get("price_memory"), dict) else raw_payload.get("price_memory")
    if isinstance(price_memory, dict):
        source["price_memory"] = price_memory
    _copy_price_break_fields(source, candidate, raw_payload)
    return source


def _supplier_option_from_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    option: dict[str, Any] = {
        "name": candidate.get("supplier_name") or candidate.get("product_name") or "Supplier candidate",
        "unit_price": _number(candidate.get("unit_price")),
        "status": "selected",
    }
    field_map = {
        "source_url": "url",
        "provider": "provider",
        "confidence": "confidence",
        "currency": "currency",
        "vat_mode": "vat_mode",
        "availability": "availability",
        "source_query": "source_query",
        "source_kind": "source_kind",
    }
    for source_key, option_key in field_map.items():
        if candidate.get(source_key) not in (None, ""):
            option[option_key] = candidate[source_key]
    raw_payload = _raw_payload(candidate)
    number_field_map = {
        "stock_quantity": SUPPLIER_STOCK_FIELDS,
        "preorder_quantity": SUPPLIER_PREORDER_FIELDS,
        "minimum_order_quantity": MIN_ORDER_QUANTITY_FIELDS,
        "pack_quantity": PACK_QUANTITY_FIELDS,
    }
    for option_key, source_fields in number_field_map.items():
        number = _first_number(candidate, raw_payload, source_fields)
        if number is not None:
            option[option_key] = number
    _copy_price_break_fields(option, candidate, raw_payload)
    return {key: value for key, value in option.items() if value is not None}


def _first_ready_candidate(profile: dict[str, Any]) -> dict[str, Any] | None:
    for candidate in rank_profile_price_candidates(profile):
        review_status = str(candidate.get("review_status") or "pending").casefold()
        if candidate.get("auto_eligible") is True and review_status not in REVIEW_STATUSES:
            return candidate
    return None


def _profile_has_positive_cost(profile: dict[str, Any]) -> bool:
    raw_payload = profile.get("raw_payload")
    if not isinstance(raw_payload, dict):
        return False
    economics = raw_payload.get("economics")
    if not isinstance(economics, dict):
        return False
    unit_cost = _number(economics.get("unit_cost"))
    total_cost = _number(economics.get("total_cost"))
    return bool((unit_cost is not None and unit_cost > 0) or (total_cost is not None and total_cost > 0))


def _ensure_profiles_with_item_fallback(
    database_path: str | Path,
    source: str,
    external_id: str,
) -> list[dict[str, Any]]:
    profiles = ensure_product_profiles(database_path, source, external_id)
    item_fallbacks = _tender_items_by_position(database_path, source, external_id)
    if not item_fallbacks:
        return profiles
    return [
        _profile_with_item_fallback(profile, item_fallbacks.get(int(profile.get("position_index") or 0)))
        for profile in profiles
    ]


def _tender_items_by_position(
    database_path: str | Path,
    source: str,
    external_id: str,
) -> dict[int, dict[str, Any]]:
    with sqlite3.connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT position_index, quantity, unit
            FROM tender_items
            WHERE source = ? AND external_id = ?
            ORDER BY position_index
            """,
            (source, external_id),
        ).fetchall()
    return {
        int(row["position_index"]): dict(row)
        for row in rows
        if int(row["position_index"] or 0) > 0
    }


def _profile_with_item_fallback(profile: dict[str, Any], item: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(item, dict):
        return profile
    enriched = dict(profile)
    for key in ("quantity", "unit"):
        if enriched.get(key) in (None, "") and item.get(key) not in (None, ""):
            enriched[key] = item.get(key)
    return enriched


def _profile_candidate_sources(profile: dict[str, Any]) -> list[dict[str, Any]]:
    raw_payload = profile.get("raw_payload") if isinstance(profile.get("raw_payload"), dict) else {}
    candidates: list[dict[str, Any]] = []
    for option in _supplier_options(raw_payload.get("supplier_options")):
        candidate = _candidate_from_supplier_source(profile, option, source_kind="supplier_options")
        if candidate:
            candidates.append(candidate)

    discovery = raw_payload.get("supplier_discovery") if isinstance(raw_payload.get("supplier_discovery"), dict) else {}
    discovery_candidates = discovery.get("candidates") if isinstance(discovery.get("candidates"), list) else []
    for item in discovery_candidates:
        if not isinstance(item, dict):
            continue
        candidate = _candidate_from_supplier_source(profile, item, source_kind="supplier_discovery")
        if candidate:
            candidates.append(candidate)
    return candidates


def _candidate_from_supplier_source(
    profile: dict[str, Any],
    source_candidate: dict[str, Any],
    *,
    source_kind: str,
) -> dict[str, Any]:
    unit_price = _number(source_candidate.get("unit_price") or source_candidate.get("price"))
    if unit_price is None or unit_price <= 0:
        return {}
    raw_payload = {**source_candidate, "source_kind": source_kind}
    confidence = str(source_candidate.get("confidence") or "").strip().casefold()
    if not confidence:
        confidence = "high" if source_candidate.get("url") or source_candidate.get("source_url") else "medium"
    candidate = {
        "provider": source_candidate.get("provider") or source_candidate.get("catalog") or "manual",
        "product_name": source_candidate.get("product_name") or source_candidate.get("name") or profile.get("product_name"),
        "supplier_name": source_candidate.get("supplier_name"),
        "source_url": source_candidate.get("source_url") or source_candidate.get("url"),
        "source_query": source_candidate.get("source_query"),
        "source_kind": source_kind,
        "unit_price": unit_price,
        "currency": source_candidate.get("currency") or "RUB",
        "vat_mode": source_candidate.get("vat_mode"),
        "vat_rate_percent": source_candidate.get("vat_rate_percent"),
        "availability": source_candidate.get("availability"),
        "delivery_note": source_candidate.get("delivery_note"),
        "delivery_cost": source_candidate.get("delivery_cost"),
        "unit": source_candidate.get("unit") or source_candidate.get("uom") or profile.get("unit"),
        "price_breaks": _price_breaks(source_candidate.get("price_breaks")),
        "pack_quantity": _first_number(source_candidate, raw_payload, PACK_QUANTITY_FIELDS),
        "stock_quantity": _first_number(source_candidate, raw_payload, SUPPLIER_STOCK_FIELDS),
        "preorder_quantity": _first_number(source_candidate, raw_payload, SUPPLIER_PREORDER_FIELDS),
        "minimum_order_quantity": _first_number(source_candidate, raw_payload, MIN_ORDER_QUANTITY_FIELDS),
        "minimum_order_amount": _first_number(source_candidate, raw_payload, MIN_ORDER_AMOUNT_FIELDS),
        "confidence": confidence,
        "confidence_reasons": _string_list(source_candidate.get("confidence_reasons")),
        "match_reasons": _string_list(source_candidate.get("match_reasons")) + [f"from_{source_kind}"],
        "raw_payload": raw_payload,
    }
    return {key: value for key, value in candidate.items() if value not in (None, "")}


def _matching_supplier_option_index(supplier_options: list[dict[str, Any]], option: dict[str, Any]) -> int | None:
    option_url = str(option.get("url") or "").strip().casefold()
    for index, supplier_option in enumerate(supplier_options):
        supplier_url = str(supplier_option.get("url") or "").strip().casefold()
        if option_url and supplier_url == option_url:
            return index
        same_provider = str(supplier_option.get("provider") or "").casefold() == str(option.get("provider") or "").casefold()
        same_name = str(supplier_option.get("name") or "").casefold() == str(option.get("name") or "").casefold()
        same_price = _number(supplier_option.get("unit_price")) == _number(option.get("unit_price"))
        if same_provider and same_name and same_price:
            return index
    return None


def _find_candidate(
    store: TenderStore,
    source: str,
    external_id: str,
    position_index: int,
    candidate_id: int,
) -> dict[str, Any]:
    for candidate in store.list_price_candidates(source, external_id, position_index):
        if int(candidate.get("id") or 0) == int(candidate_id):
            return candidate
    raise KeyError(f"Price candidate {candidate_id} not found.")


def _find_profile(profiles: list[dict[str, Any]], position_index: int) -> dict[str, Any]:
    for profile in profiles:
        if int(profile.get("position_index") or 0) == int(position_index):
            return profile
    raise KeyError(f"Product profile position {position_index} not found.")


def _review_status(value: str) -> str:
    status = str(value or "").strip().casefold()
    if status not in REVIEW_STATUSES:
        raise ValueError("Price candidate review status must be confirmed or rejected.")
    return status


def _supplier_options(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]
