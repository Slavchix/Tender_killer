from __future__ import annotations

import math
import re
import sqlite3
from pathlib import Path
from typing import Any

from tender_killer.product_profile_service import ensure_product_profiles
from tender_killer.storage import TenderStore
from tender_killer.supplier_product_matcher import supplier_product_name_mismatch_reasons


REVIEW_STATUSES = {"confirmed", "rejected"}
UNAVAILABLE_VALUES = {"not_available", "unavailable", "out_of_stock", "sold_out"}
UNKNOWN_VALUES = {"", "unknown", "none", "null", "n/a", "not_specified", "неизвестно", "не указано"}
VAT_INCLUDED_VALUES = {"vat_included", "included", "with_vat", "nds_included", "ндс_включен"}
VAT_REVIEW_VALUES = {"vat_excluded", "excluded", "without_vat", "no_vat", "nds_excluded", "без_ндс"}
PICKUP_ONLY_MARKERS = ("pickup", "self pickup", "self-pickup", "самовывоз")
DELIVERY_INCLUDED_MARKERS = ("delivery included", "доставка включена", "с доставкой")
TRUSTED_SUPPLIER_VAT_NOTE = "НДС проверить: по умолчанию считаем цену поставщика с НДС."
TRUSTED_SUPPLIER_DELIVERY_RATE_PERCENT = 3.0
TRUSTED_SUPPLIER_MARKERS = (
    "officemag",
    "komus",
    "petrovich",
    "vseinstrumenti",
    "vseinstrument",
    "lemanapro",
    "lemana",
    "офисмаг",
    "комус",
    "петрович",
    "всеинструменты",
    "лемана",
)
PACK_QUANTITY_FIELDS = (
    "pack_quantity",
    "quantity_per_pack",
    "package_quantity",
    "items_per_pack",
    "items_in_pack",
)
MIN_ORDER_QUANTITY_FIELDS = ("minimum_order_quantity", "min_order_quantity", "minimum_quantity", "min_quantity")
MIN_ORDER_AMOUNT_FIELDS = ("minimum_order_amount", "min_order_amount")
SUPPLIER_STOCK_FIELDS = ("stock_quantity", "available_quantity", "stock")
SUPPLIER_PREORDER_FIELDS = ("preorder_quantity", "backorder_quantity", "on_order_quantity")
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
        ranked_candidate["pricing_passport"] = _pricing_passport(profile, ranked_candidate)
        ranked.append(ranked_candidate)
    return sorted(ranked, key=_rank_key)


def _rankable_price_candidate(profile: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    raw_payload = _raw_payload(candidate)
    if _number(candidate.get("unit_price") or raw_payload.get("unit_price")) is None:
        return {**candidate}
    return normalize_price_candidate(profile, candidate)


def evaluate_price_candidate_quality(profile: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    flags: list[dict[str, str]] = []
    raw_payload = _raw_payload(candidate)

    unit_price = _number(candidate.get("unit_price"))
    if unit_price is None or unit_price <= 0:
        flags.append(_quality_flag("price_missing", "block", "No positive unit price", "Candidate cannot price the position."))

    review_status = str(candidate.get("review_status") or "pending").casefold()
    if review_status == "rejected":
        flags.append(_quality_flag("candidate_rejected", "block", "Rejected", "Operator already rejected this candidate."))

    mismatch_reasons = _candidate_name_mismatch_reasons(profile, candidate, raw_payload)
    if mismatch_reasons:
        flags.append(
            _quality_flag(
                "product_name_mismatch",
                "block",
                "Product name mismatch",
                "Supplier product title does not match the tender position.",
            )
        )
        for reason in mismatch_reasons:
            if reason == "product_name_mismatch":
                continue
            flags.append(
                _quality_flag(
                    reason,
                    "block",
                    _quality_mismatch_label(reason),
                    "Supplier product title conflicts with the tender position.",
                )
            )

    availability = _token(candidate.get("availability") or raw_payload.get("availability"))
    if availability in UNAVAILABLE_VALUES:
        flags.append(_quality_flag("availability_unavailable", "block", "Unavailable", "Supplier marks the offer as unavailable."))
    elif availability in UNKNOWN_VALUES:
        flags.append(_quality_flag("availability_unknown", "review", "Availability unknown", "Check stock before using this price."))

    currency = str(candidate.get("currency") or raw_payload.get("currency") or "RUB").strip().upper()
    if currency and currency != "RUB":
        flags.append(_quality_flag("currency_non_rub", "review", "Non-RUB price", "Normalize currency before using this price."))

    vat_mode = _token(candidate.get("vat_mode") or raw_payload.get("vat_mode"))
    if vat_mode in UNKNOWN_VALUES:
        flags.append(_quality_flag("vat_unknown", "review", "VAT unknown", "Check whether VAT is included before comparing prices."))
    elif vat_mode not in VAT_INCLUDED_VALUES:
        flag_id = "vat_not_included" if vat_mode in VAT_REVIEW_VALUES else "vat_unknown"
        flags.append(_quality_flag(flag_id, "review", "VAT needs review", "Normalize VAT before auto-accepting this price."))

    delivery_note = str(candidate.get("delivery_note") or raw_payload.get("delivery_note") or "").strip()
    delivery_token = delivery_note.casefold()
    if not delivery_token or delivery_token in UNKNOWN_VALUES:
        flags.append(_quality_flag("delivery_unknown", "review", "Delivery unknown", "Check delivery cost and terms before using this price."))
    elif any(marker in delivery_token for marker in PICKUP_ONLY_MARKERS):
        flags.append(_quality_flag("delivery_pickup_only", "review", "Pickup only", "Add delivery cost or reject the candidate."))
    elif not any(marker in delivery_token for marker in DELIVERY_INCLUDED_MARKERS):
        flags.append(_quality_flag("delivery_needs_review", "review", "Delivery needs review", "Delivery text is present but not clearly included."))

    profile_quantity = _number(profile.get("quantity"))
    profile_unit = _token(profile.get("unit"))
    candidate_unit = _token(candidate.get("unit") or raw_payload.get("unit") or raw_payload.get("uom"))
    pack_quantity = _first_number(candidate, raw_payload, PACK_QUANTITY_FIELDS)
    if profile_quantity and profile_quantity > 1 and pack_quantity is None:
        flags.append(_quality_flag("pack_quantity_unknown", "review", "Pack quantity unknown", "Check unit and package conversion before auto-pricing."))
    elif pack_quantity is not None and pack_quantity <= 0:
        flags.append(_quality_flag("pack_quantity_invalid", "review", "Pack quantity invalid", "Check package conversion before using this candidate."))
    if profile_unit and candidate_unit and not _units_compatible(profile_unit, candidate_unit):
        flags.append(_quality_flag("unit_mismatch", "review", "Unit mismatch", "Supplier unit differs from tender position unit."))

    min_order_quantity = _first_number(candidate, raw_payload, MIN_ORDER_QUANTITY_FIELDS)
    if min_order_quantity is not None and profile_quantity is not None and min_order_quantity > profile_quantity:
        flags.append(_quality_flag("minimum_order_quantity", "review", "Minimum order too high", "Supplier minimum order exceeds tender quantity."))
    min_order_amount = _first_number(candidate, raw_payload, MIN_ORDER_AMOUNT_FIELDS)
    if min_order_amount is not None and unit_price is not None and profile_quantity is not None:
        if min_order_amount > unit_price * profile_quantity:
            flags.append(_quality_flag("minimum_order_amount", "review", "Minimum order amount", "Supplier minimum order amount exceeds this position value."))

    severities = {flag["severity"] for flag in flags}
    if "block" in severities:
        status = "blocked"
    elif flags:
        status = "review"
    else:
        status = "ready"

    confidence = str(candidate.get("confidence") or "").casefold()
    return {
        "quality_status": status,
        "auto_eligible": status == "ready" and confidence == "high",
        "quality_flags": flags,
    }


def normalize_price_candidate(profile: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    normalized = {**candidate}
    raw_payload = _raw_payload(candidate)
    profile_quantity = _number(profile.get("quantity"))
    profile_unit = _token(profile.get("unit"))
    candidate_unit = _token(candidate.get("unit") or raw_payload.get("unit") or raw_payload.get("uom"))
    pack_quantity = _first_number(candidate, raw_payload, PACK_QUANTITY_FIELDS)
    price_breaks = _price_breaks(candidate.get("price_breaks") or raw_payload.get("price_breaks"))
    price_break_quantity = _price_break_selection_quantity(profile_quantity, profile_unit, candidate_unit, pack_quantity)
    selected_price_break = _select_price_break(price_breaks, price_break_quantity)
    original_unit_price = _number(candidate.get("unit_price") or raw_payload.get("unit_price"))
    if selected_price_break:
        original_unit_price = _number(selected_price_break.get("price"))
    if original_unit_price is None:
        original_unit_price = 0.0
    unit_price = original_unit_price
    match_reasons = _string_list(candidate.get("match_reasons"))
    normalization: dict[str, Any] = {
        "original_unit_price": original_unit_price,
        "source": candidate.get("source_kind") or raw_payload.get("source_kind"),
    }

    if price_breaks:
        normalized["price_breaks"] = price_breaks
        raw_payload["price_breaks"] = price_breaks
    if selected_price_break:
        normalized["selected_price_break"] = selected_price_break
        raw_payload["selected_price_break"] = selected_price_break
        normalization["selected_price_break"] = selected_price_break
        match_reasons.append("price_break_selected")
    if price_break_quantity is not None:
        normalized["price_break_selection_quantity"] = price_break_quantity
        raw_payload["price_break_selection_quantity"] = price_break_quantity
        normalization["price_break_selection_quantity"] = price_break_quantity

    if _is_pack_unit(candidate_unit) and _is_piece_unit(profile_unit) and pack_quantity and pack_quantity > 0:
        unit_price = unit_price / pack_quantity
        normalized["unit"] = profile.get("unit")
        normalization["pack_quantity"] = pack_quantity
        match_reasons.append("pack_quantity_normalized")
    elif candidate.get("unit") not in (None, ""):
        normalized["unit"] = candidate.get("unit")
    elif profile.get("unit") not in (None, ""):
        normalized["unit"] = profile.get("unit")

    vat_mode = _token(candidate.get("vat_mode") or raw_payload.get("vat_mode"))
    vat_rate = _number(candidate.get("vat_rate_percent") or raw_payload.get("vat_rate_percent"))
    supplier_defaults = _trusted_supplier_pricing_defaults(candidate, raw_payload)
    if vat_mode in VAT_REVIEW_VALUES and vat_rate and vat_rate > 0:
        unit_price = unit_price * (1 + vat_rate / 100)
        normalized["vat_mode"] = "vat_included"
        normalized["vat_rate_percent"] = vat_rate
        normalization["vat_rate_percent"] = vat_rate
        match_reasons.append("vat_normalized")
    elif vat_mode in VAT_REVIEW_VALUES and supplier_defaults:
        normalized["vat_mode"] = "vat_included"
        normalized["vat_note"] = supplier_defaults["vat_note"]
        normalization["supplier_default_vat_note"] = supplier_defaults["vat_note"]
        match_reasons.append("supplier_default_vat_included")
    elif vat_mode in UNKNOWN_VALUES and supplier_defaults:
        normalized["vat_mode"] = "vat_included"
        normalized["vat_note"] = supplier_defaults["vat_note"]
        normalization["supplier_default_vat_note"] = supplier_defaults["vat_note"]
        match_reasons.append("supplier_default_vat_included")
    elif vat_mode:
        normalized["vat_mode"] = "vat_included" if vat_mode in VAT_INCLUDED_VALUES else vat_mode
        if vat_rate is not None:
            normalized["vat_rate_percent"] = vat_rate

    availability = _normalize_availability(candidate.get("availability") or raw_payload.get("availability"))
    if availability:
        normalized["availability"] = availability
    stock_quantity = _first_number(candidate, raw_payload, SUPPLIER_STOCK_FIELDS)
    if stock_quantity is not None:
        normalized["stock_quantity"] = stock_quantity
    preorder_quantity = _first_number(candidate, raw_payload, SUPPLIER_PREORDER_FIELDS)
    if preorder_quantity is not None:
        normalized["preorder_quantity"] = preorder_quantity

    delivery_note = str(candidate.get("delivery_note") or raw_payload.get("delivery_note") or "").strip()
    delivery_token = delivery_note.casefold()
    if not delivery_note and _number(candidate.get("delivery_cost") or raw_payload.get("delivery_cost")) == 0:
        delivery_note = "Delivery included"
        delivery_token = delivery_note.casefold()
    elif supplier_defaults and _delivery_needs_supplier_default(delivery_token):
        delivery_rate = _number(candidate.get("delivery_rate_percent") or raw_payload.get("delivery_rate_percent"))
        if delivery_rate is None or delivery_rate <= 0:
            delivery_rate = supplier_defaults["delivery_rate_percent"]
        delivery_cost_per_unit = unit_price * delivery_rate / 100
        unit_price += delivery_cost_per_unit
        normalized["delivery_rate_percent"] = delivery_rate
        normalized["delivery_cost_per_unit"] = round(delivery_cost_per_unit, 2)
        delivery_note = f"Delivery included by supplier default ({_format_number(delivery_rate)}%)"
        normalization["supplier_default_delivery_rate_percent"] = delivery_rate
        normalization["supplier_default_delivery_cost_per_unit"] = round(delivery_cost_per_unit, 2)
        match_reasons.append("supplier_default_delivery")
    if delivery_note:
        normalized["delivery_note"] = delivery_note

    normalized["unit_price"] = round(unit_price, 2)
    normalized["currency"] = str(candidate.get("currency") or raw_payload.get("currency") or "RUB").strip().upper() or "RUB"
    normalized["confidence"] = str(candidate.get("confidence") or raw_payload.get("confidence") or "high").strip().casefold()
    if candidate.get("provider") not in (None, ""):
        normalized["provider"] = candidate.get("provider")
    if candidate.get("source_url") in (None, "") and candidate.get("url"):
        normalized["source_url"] = candidate.get("url")
    if candidate.get("product_name") in (None, "") and candidate.get("name"):
        normalized["product_name"] = candidate.get("name")

    normalization["normalized_unit_price"] = normalized["unit_price"]
    raw_payload.update(
        {
            "original_unit_price": original_unit_price,
            "normalized_unit_price": normalized["unit_price"],
            "normalization": {key: value for key, value in normalization.items() if value not in (None, "")},
        }
    )
    normalized["original_unit_price"] = original_unit_price
    normalized["normalized_unit_price"] = normalized["unit_price"]
    normalized["normalization"] = raw_payload["normalization"]
    normalized["raw_payload"] = raw_payload
    normalized["match_reasons"] = _dedupe_strings(match_reasons)
    return normalized


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
    if status == "confirmed":
        _ensure_candidate_confirmable(target, candidate)
        supplier_option_index = _apply_confirmed_candidate(target, candidate)
        store.upsert_product_profiles(source, external_id, profiles)

    store.update_price_candidate_review(
        source,
        external_id,
        position_index,
        candidate,
        review_status=status,
        supplier_option_index=supplier_option_index,
    )
    return {
        "ok": True,
        "position_index": int(position_index),
        "candidate_id": int(candidate_id),
        "review_status": status,
        "supplier_option_index": supplier_option_index,
    }


def confirm_ready_price_candidates(
    database_path: str | Path,
    source: str,
    external_id: str,
) -> dict[str, Any]:
    store = TenderStore(database_path)
    store.initialize()
    profiles = _ensure_profiles_with_item_fallback(database_path, source, external_id)

    confirmed: list[dict[str, int | None]] = []
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

    skipped_count = skipped_existing_cost_count + skipped_no_ready_candidate_count
    return {
        "ok": True,
        "total_profiles": len(profiles),
        "confirmed_count": len(confirmed),
        "skipped_count": skipped_count,
        "skipped_existing_cost_count": skipped_existing_cost_count,
        "skipped_no_ready_candidate_count": skipped_no_ready_candidate_count,
        "confirmed": confirmed,
    }


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


def _candidate_name_mismatch_reasons(
    profile: dict[str, Any],
    candidate: dict[str, Any],
    raw_payload: dict[str, Any],
) -> list[str]:
    candidate_name = str(
        candidate.get("product_name")
        or candidate.get("name")
        or raw_payload.get("product_name")
        or raw_payload.get("name")
        or ""
    ).strip()
    if not candidate_name:
        return []

    profile_text = " ".join(
        str(value).strip()
        for value in (
            profile.get("product_name"),
            profile.get("normalized_name"),
            candidate.get("source_query"),
            raw_payload.get("source_query"),
        )
        if value not in (None, "")
    )
    if not profile_text.strip():
        return []
    return supplier_product_name_mismatch_reasons(profile_text, candidate_name)


def _quality_mismatch_label(reason: str) -> str:
    return {
        "brand_mismatch": "Brand mismatch",
        "color_mismatch": "Color mismatch",
        "dimension_mismatch": "Dimension mismatch",
        "family_modifier_mismatch": "Product modifier mismatch",
        "material_mismatch": "Material mismatch",
        "paper_format_mismatch": "Paper format mismatch",
        "paper_sheet_count_mismatch": "Paper sheet count mismatch",
        "piece_pack_count_mismatch": "Pack quantity mismatch",
        "product_family_mismatch": "Product family mismatch",
        "product_name_mismatch": "Product name mismatch",
        "volume_mismatch": "Volume mismatch",
        "weight_mismatch": "Weight mismatch",
    }.get(reason, "Product mismatch")


def _ensure_candidate_confirmable(profile: dict[str, Any], candidate: dict[str, Any]) -> None:
    quality = evaluate_price_candidate_quality(profile, candidate)
    if str(quality.get("quality_status") or "").casefold() != "blocked":
        return
    block_reasons = [
        str(flag.get("id"))
        for flag in quality.get("quality_flags") or []
        if isinstance(flag, dict) and flag.get("severity") == "block" and flag.get("id")
    ]
    reason_text = ", ".join(block_reasons) if block_reasons else "quality_blocked"
    raise ValueError(f"Price candidate is blocked and cannot be confirmed: {reason_text}")


def _price_match_stems(text: str, *, remove_stop_words: bool) -> set[str]:
    stems: set[str] = set()
    for token in PRICE_MATCH_TOKEN_RE.findall(str(text or "").casefold()):
        if token.isdigit() or len(token) < 4:
            continue
        if remove_stop_words and token in PRICE_MATCH_STOP_WORDS:
            continue
        stems.add(token[:5])
    return stems


def _candidate_score(candidate: dict[str, Any], quality: dict[str, Any]) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []
    review_status = str(candidate.get("review_status") or "pending")
    if review_status == "rejected":
        return -1000, ["rejected", "quality_blocked"]
    if review_status == "confirmed":
        score += 100
        reasons.append("confirmed")
    elif review_status == "imported":
        score += 50
        reasons.append("imported")

    confidence = str(candidate.get("confidence") or "").casefold()
    confidence_score = {"high": 35, "medium": 20, "low": 5}.get(confidence, 0)
    if confidence_score:
        score += confidence_score
        reasons.append(f"confidence_{confidence}")
    if _number(candidate.get("unit_price")) is not None:
        score += 25
        reasons.append("unit_price")
    if candidate.get("source_url"):
        score += 15
        reasons.append("source_url")
    match_reasons = _string_list(candidate.get("match_reasons"))
    if "profile_intent_match" in match_reasons:
        score += 10
        reasons.append("profile_intent_match")
    source_kind = str(candidate.get("source_kind") or "").casefold()
    if source_kind in {"catalog_hint", "normalized_name", "manual_product_url"}:
        score += 15
        reasons.append("strict_source_query")
    if candidate.get("availability") and str(candidate.get("availability")).casefold() not in {"unavailable", "out_of_stock"}:
        score += 5
        reasons.append("availability")
    if candidate.get("provider") or candidate.get("supplier_name"):
        score += 5
        reasons.append("supplier_identity")
    quality_status = str(quality.get("quality_status") or "")
    if quality_status == "ready":
        score += 30
        reasons.append("quality_ready")
    elif quality_status == "review":
        score -= 20
        reasons.append("quality_review")
    elif quality_status == "blocked":
        score -= 300
        reasons.append("quality_blocked")
    return score, reasons or ["weak_signal"]


def _rank_key(candidate: dict[str, Any]) -> tuple[float, float, int]:
    price = _number(candidate.get("unit_price"))
    normalized_price = price if price is not None else float("inf")
    return (-float(candidate.get("score") or 0), normalized_price, int(candidate.get("id") or 0))


def _pricing_passport(profile: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    raw_payload = _raw_payload(candidate)
    unit_price = _number(candidate.get("unit_price"))
    quantity = _number(profile.get("quantity"))
    total_price = _round_money(unit_price * quantity) if unit_price is not None and quantity is not None else None
    flags = [flag for flag in candidate.get("quality_flags") or [] if isinstance(flag, dict)]
    flag_ids = {str(flag.get("id") or "") for flag in flags}
    availability = _token(candidate.get("availability") or raw_payload.get("availability"))
    vat_mode = _token(candidate.get("vat_mode") or raw_payload.get("vat_mode"))
    delivery_note = str(candidate.get("delivery_note") or raw_payload.get("delivery_note") or "").strip()
    pack_quantity = _first_number(candidate, raw_payload, PACK_QUANTITY_FIELDS)
    provider = candidate.get("provider")
    supplier_name = candidate.get("supplier_name")
    source_url = candidate.get("source_url") or raw_payload.get("source_url") or candidate.get("url") or raw_payload.get("url")
    source_kind = candidate.get("source_kind") or raw_payload.get("source_kind")
    observed_at = (
        candidate.get("observed_at")
        or raw_payload.get("observed_at")
        or raw_payload.get("collected_at")
        or candidate.get("updated_at")
        or raw_payload.get("updated_at")
    )
    confidence = candidate.get("confidence")
    match_reasons = _string_list(candidate.get("match_reasons")) or _string_list(raw_payload.get("match_reasons"))

    positive_checks: list[str] = []
    if source_url:
        positive_checks.append("source_url")
    if unit_price is not None and unit_price > 0:
        positive_checks.append("unit_price")
    if availability and availability not in UNKNOWN_VALUES and availability not in UNAVAILABLE_VALUES:
        positive_checks.append("availability")
    if vat_mode in VAT_INCLUDED_VALUES:
        positive_checks.append("vat")
    if delivery_note and not any(flag_id.startswith("delivery_") for flag_id in flag_ids):
        positive_checks.append("delivery")
    if pack_quantity is not None and pack_quantity > 0 and "pack_quantity_invalid" not in flag_ids:
        positive_checks.append("pack_quantity")

    review_checks = [str(flag.get("id")) for flag in flags if flag.get("severity") == "review" and flag.get("id")]
    block_checks = [str(flag.get("id")) for flag in flags if flag.get("severity") == "block" and flag.get("id")]
    quality_status = str(candidate.get("quality_status") or "review")

    return {
        "provider": provider,
        "supplier_name": supplier_name,
        "product_name": candidate.get("product_name"),
        "source_url": source_url,
        "source_kind": source_kind,
        "source_label": _pricing_passport_source_label(provider, supplier_name, source_kind),
        "observed_at": observed_at,
        "freshness_label": _pricing_passport_freshness_label(observed_at),
        "match_confidence": confidence or "needs_review",
        "match_reasons": match_reasons,
        "unit_pack_label": _pricing_passport_unit_pack_label(quantity, candidate.get("unit") or profile.get("unit"), pack_quantity),
        "vat_label": _pricing_passport_vat_label(vat_mode),
        "delivery_label": _pricing_passport_delivery_label(delivery_note, flag_ids),
        "evidence_url": source_url,
        "evidence_label": _pricing_passport_evidence_label(source_url),
        "unit_price": _round_money(unit_price) if unit_price is not None else None,
        "total_price": total_price,
        "quantity": _round_money(quantity) if quantity is not None else None,
        "unit": candidate.get("unit") or profile.get("unit"),
        "currency": candidate.get("currency") or "RUB",
        "availability": candidate.get("availability") or raw_payload.get("availability"),
        "vat_mode": candidate.get("vat_mode") or raw_payload.get("vat_mode"),
        **({"vat_note": candidate.get("vat_note") or raw_payload.get("vat_note")} if candidate.get("vat_note") or raw_payload.get("vat_note") else {}),
        "delivery_note": delivery_note or None,
        "stock_quantity": _first_number(candidate, raw_payload, SUPPLIER_STOCK_FIELDS),
        "preorder_quantity": _first_number(candidate, raw_payload, SUPPLIER_PREORDER_FIELDS),
        "pack_quantity": pack_quantity,
        "minimum_order_quantity": _first_number(candidate, raw_payload, MIN_ORDER_QUANTITY_FIELDS),
        "quality_status": quality_status,
        "auto_eligible": bool(candidate.get("auto_eligible")),
        "confidence": confidence,
        "positive_checks": positive_checks,
        "review_checks": review_checks,
        "block_checks": block_checks,
        "next_action": _pricing_passport_next_action(candidate),
        "summary": _pricing_passport_summary(quality_status, positive_checks, review_checks, block_checks),
    }


def _pricing_passport_source_label(provider: Any, supplier_name: Any, source_kind: Any) -> str:
    source = _passport_text(provider) or _passport_text(supplier_name) or "источник"
    kind = _passport_text(source_kind)
    return f"{source} · {kind}" if kind else source


def _pricing_passport_freshness_label(observed_at: Any) -> str:
    return _passport_text(observed_at) or "нет даты"


def _pricing_passport_unit_pack_label(quantity: float | None, unit: Any, pack_quantity: float | None) -> str:
    parts: list[str] = []
    if quantity is not None:
        parts.append(f"{_format_number(quantity)} {_passport_text(unit) or 'ед.'}".strip())
    elif unit:
        parts.append(_passport_text(unit))
    if pack_quantity is not None:
        parts.append(f"упак. {_format_number(pack_quantity)}")
    return " · ".join(part for part in parts if part) or "единица не ясна"


def _pricing_passport_vat_label(vat_mode: str) -> str:
    if vat_mode in VAT_INCLUDED_VALUES:
        return "НДС включен"
    if vat_mode == "no_vat":
        return "без НДС"
    if vat_mode in VAT_REVIEW_VALUES:
        return "НДС сверху"
    return "НДС уточнить"


def _pricing_passport_delivery_label(delivery_note: str, flag_ids: set[str]) -> str:
    if "delivery_pickup_only" in flag_ids:
        return "самовывоз"
    if not delivery_note or any(flag_id.startswith("delivery_") for flag_id in flag_ids):
        return "доставку уточнить"
    return "доставка ясна"


def _pricing_passport_evidence_label(source_url: Any) -> str:
    return "карточка товара" if _passport_text(source_url) else "доказательство нужно"


def _format_number(value: float) -> str:
    return str(int(value)) if float(value).is_integer() else str(round(float(value), 2)).replace(".", ",")


def _passport_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _pricing_passport_next_action(candidate: dict[str, Any]) -> str:
    review_status = str(candidate.get("review_status") or "pending").casefold()
    if review_status == "confirmed":
        return "already_confirmed"
    if review_status == "rejected":
        return "rejected"
    quality_status = str(candidate.get("quality_status") or "review").casefold()
    if quality_status == "ready":
        return "ready_to_confirm"
    if quality_status == "blocked":
        return "do_not_accept"
    return "review_required"


def _pricing_passport_summary(
    quality_status: str,
    positive_checks: list[str],
    review_checks: list[str],
    block_checks: list[str],
) -> str:
    if block_checks or quality_status == "blocked":
        return "Цена не готова: есть блокирующие признаки, нужен другой источник или ручная проверка."
    if review_checks or quality_status == "review":
        return "Цена требует проверки: уточни НДС, доставку, упаковку или наличие перед расчетом."
    if {"source_url", "unit_price", "availability", "vat", "delivery"} <= set(positive_checks):
        return "Цена готова к подтверждению: есть ссылка, цена, наличие, НДС и доставка."
    return "Цена выглядит пригодной, но перед расчетом проверь источник и условия поставки."


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


def _normalize_availability(value: Any) -> str:
    token = _token(value)
    in_stock_values = {
        "in_stock",
        "available",
        "instock",
        "https://schema.org/instock",
        "в_наличии",
        "на_складе",
    }
    unavailable_values = {
        "not_available",
        "unavailable",
        "out_of_stock",
        "sold_out",
        "https://schema.org/outofstock",
        "нет",
        "нет_в_наличии",
    }
    if token in in_stock_values:
        return "in_stock"
    if token in unavailable_values:
        return "unavailable"
    if token in UNKNOWN_VALUES:
        return "unknown"
    return token or "unknown"


def _trusted_supplier_pricing_defaults(candidate: dict[str, Any], raw_payload: dict[str, Any]) -> dict[str, Any]:
    if not _trusted_supplier_marker(candidate, raw_payload):
        return {}
    return {
        "vat_note": TRUSTED_SUPPLIER_VAT_NOTE,
        "delivery_rate_percent": TRUSTED_SUPPLIER_DELIVERY_RATE_PERCENT,
    }


def _trusted_supplier_marker(candidate: dict[str, Any], raw_payload: dict[str, Any]) -> str:
    text = " ".join(
        str(value)
        for value in (
            candidate.get("provider"),
            raw_payload.get("provider"),
            candidate.get("supplier_name"),
            raw_payload.get("supplier_name"),
            candidate.get("source_url"),
            raw_payload.get("source_url"),
            candidate.get("url"),
            raw_payload.get("url"),
            raw_payload.get("catalog"),
        )
        if value not in (None, "")
    ).casefold()
    compact = re.sub(r"[^a-z0-9]+", "", text)
    for marker in TRUSTED_SUPPLIER_MARKERS:
        if marker in text or marker in compact:
            return marker
    return ""


def _delivery_needs_supplier_default(delivery_token: str) -> bool:
    if not delivery_token or delivery_token in UNKNOWN_VALUES:
        return True
    if any(marker in delivery_token for marker in PICKUP_ONLY_MARKERS):
        return False
    if any(marker in delivery_token for marker in DELIVERY_INCLUDED_MARKERS):
        return False
    return True


def _raw_payload(candidate: dict[str, Any]) -> dict[str, Any]:
    payload = candidate.get("raw_payload")
    return dict(payload) if isinstance(payload, dict) else {}


def _quality_flag(flag_id: str, severity: str, label: str, detail: str) -> dict[str, str]:
    return {"id": flag_id, "severity": severity, "label": label, "detail": detail}


def _first_number(candidate: dict[str, Any], raw_payload: dict[str, Any], fields: tuple[str, ...]) -> float | None:
    for field in fields:
        value = candidate.get(field)
        if value in (None, ""):
            value = raw_payload.get(field)
        number = _number(value)
        if number is not None:
            return number
    return None


def _price_breaks(value: Any) -> list[dict[str, float]]:
    if not isinstance(value, list):
        return []
    breaks: list[dict[str, float]] = []
    seen: set[tuple[float, float]] = set()
    for item in value:
        if not isinstance(item, dict):
            continue
        count = _number(item.get("count") or item.get("quantity") or item.get("min_quantity"))
        price = _number(item.get("price") or item.get("unit_price"))
        if count is None or count <= 0 or price is None or price <= 0:
            continue
        key = (float(count), float(price))
        if key in seen:
            continue
        seen.add(key)
        breaks.append({"count": float(count), "price": float(price)})
    return sorted(breaks, key=lambda item: (item["count"], item["price"]))


def _price_break_selection_quantity(
    profile_quantity: float | None,
    profile_unit: str,
    candidate_unit: str,
    pack_quantity: float | None,
) -> float | None:
    if profile_quantity is None or profile_quantity <= 0:
        return None
    if _is_pack_unit(candidate_unit) and _is_piece_unit(profile_unit) and pack_quantity and pack_quantity > 0:
        return float(math.ceil(profile_quantity / pack_quantity))
    return float(profile_quantity)


def _select_price_break(price_breaks: list[dict[str, float]], selection_quantity: float | None) -> dict[str, float] | None:
    if not price_breaks:
        return None
    if selection_quantity is None or selection_quantity <= 0:
        return min(price_breaks, key=lambda item: item["price"])
    eligible = [item for item in price_breaks if item["count"] <= selection_quantity]
    if eligible:
        return max(eligible, key=lambda item: (item["count"], -item["price"]))
    return min(price_breaks, key=lambda item: item["count"])


def _copy_price_break_fields(target: dict[str, Any], candidate: dict[str, Any], raw_payload: dict[str, Any]) -> None:
    price_breaks = _price_breaks(candidate.get("price_breaks") or raw_payload.get("price_breaks"))
    if price_breaks:
        target["price_breaks"] = price_breaks
    selected = candidate.get("selected_price_break") or raw_payload.get("selected_price_break")
    if isinstance(selected, dict):
        selected_break = _select_price_break(_price_breaks([selected]), _number(selected.get("count")))
        if selected_break:
            target["selected_price_break"] = selected_break
    selection_quantity = _number(candidate.get("price_break_selection_quantity") or raw_payload.get("price_break_selection_quantity"))
    if selection_quantity is not None:
        target["price_break_selection_quantity"] = selection_quantity


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if item not in (None, "")]


def _dedupe_strings(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _token(value: Any) -> str:
    return str(value or "").strip().casefold().replace(" ", "_").replace("-", "_")


def _is_piece_unit(unit: str) -> bool:
    return unit in {"шт", "штука", "ед", "pcs", "piece", "unit", "item"}


def _is_pack_unit(unit: str) -> bool:
    return unit in {"уп", "упак", "упаковка", "pack", "package", "box"}


def _units_compatible(profile_unit: str, candidate_unit: str) -> bool:
    unit_groups = [
        {"шт", "штука", "ед", "pcs", "piece", "unit"},
        {"уп", "упак", "упаковка", "pack", "package"},
        {"м", "meter", "metre", "m"},
        {"кг", "kg"},
        {"л", "l", "liter", "litre"},
    ]
    for group in unit_groups:
        if profile_unit in group and candidate_unit in group:
            return True
    return profile_unit == candidate_unit


def _normalize_availability(value: Any) -> str:
    token = _token(value)
    in_stock_values = {
        "in_stock",
        "available",
        "instock",
        "https://schema.org/instock",
        "\u0432_\u043d\u0430\u043b\u0438\u0447\u0438\u0438",
        "\u043d\u0430_\u0441\u043a\u043b\u0430\u0434\u0435",
    }
    unavailable_values = {
        "not_available",
        "unavailable",
        "out_of_stock",
        "sold_out",
        "https://schema.org/outofstock",
        "\u043d\u0435\u0442",
        "\u043d\u0435\u0442_\u0432_\u043d\u0430\u043b\u0438\u0447\u0438\u0438",
    }
    if token in in_stock_values:
        return "in_stock"
    if token in unavailable_values:
        return "unavailable"
    if token in UNKNOWN_VALUES:
        return "unknown"
    return token or "unknown"


def _is_piece_unit(unit: str) -> bool:
    return unit in {"\u0448\u0442", "\u0448\u0442\u0443\u043a\u0430", "\u0435\u0434", "pcs", "piece", "unit", "item"}


def _is_pack_unit(unit: str) -> bool:
    return unit in {"\u0443\u043f", "\u0443\u043f\u0430\u043a", "\u0443\u043f\u0430\u043a\u043e\u0432\u043a\u0430", "pack", "package", "box"}


def _number(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        number = float(str(value).replace(" ", "").replace(",", "."))
    except (TypeError, ValueError):
        return None
    return number if number >= 0 else None


def _round_money(value: float) -> float:
    return round(float(value), 2)
