from __future__ import annotations

from typing import Any

from tender_killer.price_candidate_common import (
    DELIVERY_INCLUDED_MARKERS,
    MIN_ORDER_AMOUNT_FIELDS,
    MIN_ORDER_QUANTITY_FIELDS,
    PACK_QUANTITY_FIELDS,
    PICKUP_ONLY_MARKERS,
    UNKNOWN_VALUES,
    UNAVAILABLE_VALUES,
    VAT_INCLUDED_VALUES,
    VAT_REVIEW_VALUES,
    first_number,
    number_or_none,
    raw_payload,
    string_list,
    token,
    units_compatible,
)
from tender_killer.price_candidate_types import PriceCandidateQuality, PriceCandidateQualityFlag
from tender_killer.supplier_product_matcher import supplier_product_name_mismatch_reasons


def evaluate_price_candidate_quality(profile: dict[str, Any], candidate: dict[str, Any]) -> PriceCandidateQuality:
    flags: list[PriceCandidateQualityFlag] = []
    payload = raw_payload(candidate)

    unit_price = number_or_none(candidate.get("unit_price"))
    if unit_price is None or unit_price <= 0:
        flags.append(_quality_flag("price_missing", "block", "No positive unit price", "Candidate cannot price the position."))

    review_status = str(candidate.get("review_status") or "pending").casefold()
    if review_status == "rejected":
        flags.append(_quality_flag("candidate_rejected", "block", "Rejected", "Operator already rejected this candidate."))

    mismatch_reasons = _candidate_name_mismatch_reasons(profile, candidate, payload)
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

    availability = token(candidate.get("availability") or payload.get("availability"))
    if availability in UNAVAILABLE_VALUES:
        flags.append(_quality_flag("availability_unavailable", "block", "Unavailable", "Supplier marks the offer as unavailable."))
    elif availability in UNKNOWN_VALUES:
        flags.append(_quality_flag("availability_unknown", "review", "Availability unknown", "Check stock before using this price."))

    currency = str(candidate.get("currency") or payload.get("currency") or "RUB").strip().upper()
    if currency and currency != "RUB":
        flags.append(_quality_flag("currency_non_rub", "review", "Non-RUB price", "Normalize currency before using this price."))

    vat_mode = token(candidate.get("vat_mode") or payload.get("vat_mode"))
    if vat_mode in UNKNOWN_VALUES:
        flags.append(_quality_flag("vat_unknown", "review", "VAT unknown", "Check whether VAT is included before comparing prices."))
    elif vat_mode not in VAT_INCLUDED_VALUES:
        flag_id = "vat_not_included" if vat_mode in VAT_REVIEW_VALUES else "vat_unknown"
        flags.append(_quality_flag(flag_id, "review", "VAT needs review", "Normalize VAT before auto-accepting this price."))

    delivery_note = str(candidate.get("delivery_note") or payload.get("delivery_note") or "").strip()
    delivery_token = delivery_note.casefold()
    if not delivery_token or delivery_token in UNKNOWN_VALUES:
        flags.append(_quality_flag("delivery_unknown", "review", "Delivery unknown", "Check delivery cost and terms before using this price."))
    elif any(marker in delivery_token for marker in PICKUP_ONLY_MARKERS):
        flags.append(_quality_flag("delivery_pickup_only", "review", "Pickup only", "Add delivery cost or reject the candidate."))
    elif not any(marker in delivery_token for marker in DELIVERY_INCLUDED_MARKERS):
        flags.append(_quality_flag("delivery_needs_review", "review", "Delivery needs review", "Delivery text is present but not clearly included."))

    profile_quantity = number_or_none(profile.get("quantity"))
    profile_unit = token(profile.get("unit"))
    candidate_unit = token(candidate.get("unit") or payload.get("unit") or payload.get("uom"))
    pack_quantity = first_number(candidate, payload, PACK_QUANTITY_FIELDS)
    if profile_quantity and profile_quantity > 1 and pack_quantity is None:
        flags.append(_quality_flag("pack_quantity_unknown", "review", "Pack quantity unknown", "Check unit and package conversion before auto-pricing."))
    elif pack_quantity is not None and pack_quantity <= 0:
        flags.append(_quality_flag("pack_quantity_invalid", "review", "Pack quantity invalid", "Check package conversion before using this candidate."))
    if profile_unit and candidate_unit and not units_compatible(profile_unit, candidate_unit):
        flags.append(_quality_flag("unit_mismatch", "review", "Unit mismatch", "Supplier unit differs from tender position unit."))

    min_order_quantity = first_number(candidate, payload, MIN_ORDER_QUANTITY_FIELDS)
    if min_order_quantity is not None and profile_quantity is not None and min_order_quantity > profile_quantity:
        flags.append(_quality_flag("minimum_order_quantity", "review", "Minimum order too high", "Supplier minimum order exceeds tender quantity."))
    min_order_amount = first_number(candidate, payload, MIN_ORDER_AMOUNT_FIELDS)
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


def ensure_candidate_confirmable(profile: dict[str, Any], candidate: dict[str, Any]) -> None:
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


def candidate_score(candidate: dict[str, Any], quality: PriceCandidateQuality) -> tuple[int, list[str]]:
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
    if number_or_none(candidate.get("unit_price")) is not None:
        score += 25
        reasons.append("unit_price")
    if candidate.get("source_url"):
        score += 15
        reasons.append("source_url")
    match_reasons = string_list(candidate.get("match_reasons"))
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


def _candidate_name_mismatch_reasons(
    profile: dict[str, Any],
    candidate: dict[str, Any],
    payload: dict[str, Any],
) -> list[str]:
    candidate_name = str(
        candidate.get("product_name")
        or candidate.get("name")
        or payload.get("product_name")
        or payload.get("name")
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
            payload.get("source_query"),
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


def _quality_flag(flag_id: str, severity: str, label: str, detail: str) -> PriceCandidateQualityFlag:
    return {"id": flag_id, "severity": severity, "label": label, "detail": detail}
