from __future__ import annotations

from typing import Any

from tender_killer.price_candidate_types import PriceCandidatePassport


UNAVAILABLE_VALUES = {"not_available", "unavailable", "out_of_stock", "sold_out"}
UNKNOWN_VALUES = {"", "unknown", "none", "null", "n/a", "not_specified", "неизвестно", "не указано"}
VAT_INCLUDED_VALUES = {"vat_included", "included", "with_vat", "nds_included", "ндс_включен"}
VAT_REVIEW_VALUES = {"vat_excluded", "excluded", "without_vat", "no_vat", "nds_excluded", "без_ндс"}
TRUSTED_SUPPLIER_RULE_NOTE = (
    "Правило поставщика: НДС считаем включенным, доставку добавляем 3%. "
    "НДС все равно проверь по карточке/КП."
)
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
SUPPLIER_STOCK_FIELDS = ("stock_quantity", "available_quantity", "stock")
SUPPLIER_PREORDER_FIELDS = ("preorder_quantity", "backorder_quantity", "on_order_quantity")


def build_pricing_passport(profile: dict[str, Any], candidate: dict[str, Any]) -> PriceCandidatePassport:
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
    trusted_supplier_rule = _pricing_passport_trusted_supplier_rule(candidate, raw_payload)
    price_memory = candidate.get("price_memory") if isinstance(candidate.get("price_memory"), dict) else raw_payload.get("price_memory")
    reuse_context = price_memory.get("reuse") if isinstance(price_memory, dict) and isinstance(price_memory.get("reuse"), dict) else None

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
        **({"trusted_supplier_rule": trusted_supplier_rule} if trusted_supplier_rule else {}),
        **({"rule_label": _pricing_passport_rule_label(trusted_supplier_rule)} if trusted_supplier_rule else {}),
        **({"reuse": reuse_context} if reuse_context else {}),
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
        "funnel_steps": _pricing_passport_funnel_steps(quality_status, positive_checks, review_checks, block_checks),
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


def _pricing_passport_trusted_supplier_rule(
    candidate: dict[str, Any],
    raw_payload: dict[str, Any],
) -> dict[str, Any]:
    marker = _trusted_supplier_marker(candidate, raw_payload)
    if not marker:
        return {}
    match_reasons = set(_string_list(candidate.get("match_reasons")) + _string_list(raw_payload.get("match_reasons")))
    has_vat_rule = "supplier_default_vat_included" in match_reasons
    has_delivery_rule = "supplier_default_delivery" in match_reasons
    if not has_vat_rule and not has_delivery_rule:
        return {}
    delivery_rate = _number(candidate.get("delivery_rate_percent") or raw_payload.get("delivery_rate_percent"))
    delivery_cost = _number(candidate.get("delivery_cost_per_unit") or raw_payload.get("delivery_cost_per_unit"))
    return {
        "enabled": True,
        "provider": marker,
        "vat_mode": "vat_included_by_rule" if has_vat_rule else _token(candidate.get("vat_mode") or raw_payload.get("vat_mode")),
        "delivery_rate_percent": delivery_rate,
        "delivery_cost_per_unit": delivery_cost,
        "operator_note": TRUSTED_SUPPLIER_RULE_NOTE,
    }


def _pricing_passport_rule_label(rule: dict[str, Any]) -> str:
    if not rule:
        return ""
    parts: list[str] = []
    if rule.get("vat_mode") == "vat_included_by_rule":
        parts.append("НДС включен")
    delivery_rate = _number(rule.get("delivery_rate_percent"))
    if delivery_rate is not None:
        parts.append(f"доставка +{_format_number(delivery_rate)}%")
    return f"правило поставщика: {', '.join(parts)}" if parts else "правило поставщика"


def _pricing_passport_funnel_steps(
    quality_status: str,
    positive_checks: list[str],
    review_checks: list[str],
    block_checks: list[str],
) -> list[dict[str, str]]:
    positive = set(positive_checks)
    review = set(review_checks)
    block = set(block_checks)
    match_blockers = {
        "brand_mismatch",
        "color_mismatch",
        "dimension_mismatch",
        "family_modifier_mismatch",
        "material_mismatch",
        "paper_format_mismatch",
        "paper_sheet_count_mismatch",
        "piece_pack_count_mismatch",
        "product_family_mismatch",
        "product_name_mismatch",
        "volume_mismatch",
        "weight_mismatch",
    }
    terms_review = {
        "availability_unknown",
        "currency_non_rub",
        "delivery_needs_review",
        "delivery_pickup_only",
        "delivery_unknown",
        "minimum_order_amount",
        "minimum_order_quantity",
        "pack_quantity_invalid",
        "pack_quantity_unknown",
        "unit_mismatch",
        "vat_not_included",
        "vat_unknown",
    }
    return [
        {
            "id": "source",
            "label": "найдена",
            "status": "ok" if "source_url" in positive else "review",
        },
        {
            "id": "match",
            "label": "товар подходит" if not (block & match_blockers) else "товар проверить",
            "status": "block" if block & match_blockers else "ok",
        },
        {
            "id": "price",
            "label": "цена понятна" if "price_missing" not in block else "нет цены",
            "status": "block" if "price_missing" in block else "ok" if "unit_price" in positive else "review",
        },
        {
            "id": "terms",
            "label": "условия понятны" if not (review & terms_review) else "условия проверить",
            "status": "review" if review & terms_review else "ok",
        },
        {
            "id": "decision",
            "label": _pricing_passport_funnel_decision_label(quality_status),
            "status": _pricing_passport_funnel_decision_status(quality_status),
        },
    ]


def _pricing_passport_funnel_decision_label(quality_status: str) -> str:
    status = str(quality_status or "").casefold()
    if status == "ready":
        return "можно принять"
    if status == "blocked":
        return "нельзя брать"
    return "нужна проверка"


def _pricing_passport_funnel_decision_status(quality_status: str) -> str:
    status = str(quality_status or "").casefold()
    if status == "ready":
        return "ok"
    if status == "blocked":
        return "block"
    return "review"


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


def _trusted_supplier_marker(candidate: dict[str, Any], raw_payload: dict[str, Any]) -> str | None:
    values = [
        candidate.get("provider"),
        candidate.get("supplier_name"),
        raw_payload.get("provider"),
        raw_payload.get("supplier_name"),
        raw_payload.get("source_url"),
        candidate.get("source_url"),
    ]
    for value in values:
        token = str(value or "").casefold()
        if any(marker in token for marker in TRUSTED_SUPPLIER_MARKERS):
            return token
    return None


def _raw_payload(candidate: dict[str, Any]) -> dict[str, Any]:
    return dict(candidate.get("raw_payload") or {}) if isinstance(candidate.get("raw_payload"), dict) else {}


def _first_number(candidate: dict[str, Any], raw_payload: dict[str, Any], fields: tuple[str, ...]) -> float | None:
    for field in fields:
        number = _number(candidate.get(field))
        if number is not None:
            return number
        number = _number(raw_payload.get(field))
        if number is not None:
            return number
    return None


def _string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if item not in (None, "")]
    if value in (None, ""):
        return []
    return [str(value)]


def _token(value: Any) -> str:
    return str(value or "").strip().casefold()


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
