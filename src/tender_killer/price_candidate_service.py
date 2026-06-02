from __future__ import annotations

from pathlib import Path
from typing import Any

from tender_killer.product_profile_service import ensure_product_profiles
from tender_killer.storage import TenderStore


REVIEW_STATUSES = {"confirmed", "rejected"}
UNAVAILABLE_VALUES = {"not_available", "unavailable", "out_of_stock", "sold_out"}
UNKNOWN_VALUES = {"", "unknown", "none", "null", "n/a", "not_specified", "неизвестно", "не указано"}
VAT_INCLUDED_VALUES = {"vat_included", "included", "with_vat", "nds_included", "ндс_включен"}
VAT_REVIEW_VALUES = {"vat_excluded", "excluded", "without_vat", "no_vat", "nds_excluded", "без_ндс"}
PICKUP_ONLY_MARKERS = ("pickup", "self pickup", "self-pickup", "самовывоз")
DELIVERY_INCLUDED_MARKERS = ("delivery included", "доставка включена", "с доставкой")
PACK_QUANTITY_FIELDS = (
    "pack_quantity",
    "quantity_per_pack",
    "package_quantity",
    "items_per_pack",
    "items_in_pack",
)
MIN_ORDER_QUANTITY_FIELDS = ("minimum_order_quantity", "min_order_quantity", "minimum_quantity", "min_quantity")
MIN_ORDER_AMOUNT_FIELDS = ("minimum_order_amount", "min_order_amount")


def rank_profile_price_candidates(profile: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = profile.get("price_candidates") if isinstance(profile.get("price_candidates"), list) else []
    ranked: list[dict[str, Any]] = []
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        quality = evaluate_price_candidate_quality(profile, candidate)
        score, reasons = _candidate_score(candidate, quality)
        ranked.append({**candidate, **quality, "score": score, "score_reasons": reasons})
    return sorted(ranked, key=_rank_key)


def evaluate_price_candidate_quality(profile: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    flags: list[dict[str, str]] = []
    raw_payload = _raw_payload(candidate)

    unit_price = _number(candidate.get("unit_price"))
    if unit_price is None or unit_price <= 0:
        flags.append(_quality_flag("price_missing", "block", "No positive unit price", "Candidate cannot price the position."))

    review_status = str(candidate.get("review_status") or "pending").casefold()
    if review_status == "rejected":
        flags.append(_quality_flag("candidate_rejected", "block", "Rejected", "Operator already rejected this candidate."))

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
    profiles = ensure_product_profiles(database_path, source, external_id)
    target = _find_profile(profiles, position_index)
    candidate = _find_candidate(store, source, external_id, position_index, candidate_id)

    supplier_option_index: int | None = None
    if status == "confirmed":
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
    profiles = ensure_product_profiles(database_path, source, external_id)

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
    return {
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


def _token(value: Any) -> str:
    return str(value or "").strip().casefold().replace(" ", "_").replace("-", "_")


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


def _number(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        number = float(str(value).replace(" ", "").replace(",", "."))
    except (TypeError, ValueError):
        return None
    return number if number >= 0 else None
