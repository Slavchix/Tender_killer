from __future__ import annotations

import json
from typing import Any

from tender_killer.normalization import first_present
from tender_killer.normalization import parse_float

MOSCOW_PUBLIC_BID_STEP_RATIO = 0.005
MOSCOW_ACTIVE_STATE_ID = 19000002


def extract_market_state(tender: dict[str, Any]) -> dict[str, Any]:
    raw_payload = _raw_payload(tender)
    detail = raw_payload.get("__detail") if isinstance(raw_payload.get("__detail"), dict) else {}
    imported = (
        raw_payload.get("__market_state_import")
        if isinstance(raw_payload.get("__market_state_import"), dict)
        else {}
    )
    nmc_price = _first_positive_number(tender, raw_payload, detail, ("price", "InitialPrice", "startPrice", "startCost"))
    source = str(tender.get("source") or "")
    participant_count = _participant_count(raw_payload, detail, imported)
    bid_count = _bid_count(raw_payload, detail, imported)
    public_bid_count = _public_moscow_bid_count(raw_payload, detail, imported) if source == "moscow_supplier_portal" else None
    current_offer_price, price_source = _current_offer_price(
        raw_payload,
        detail,
        imported,
        source=source,
        public_bid_count=bid_count or public_bid_count,
    )
    if price_source == "moscow_public_step_estimate" and (bid_count is None or bid_count == 0):
        bid_count = public_bid_count
    next_bid_price = _first_positive_number(imported, detail, raw_payload, ("nextCost", "auctionNextPrice", "next_bid_price"))
    last_offer_supplier = _last_offer_supplier(imported) or _last_offer_supplier(detail)

    if current_offer_price is not None:
        status = "has_current_offer"
        has_participants = True
    elif participant_count == 0:
        status = "no_participants"
        has_participants = False
    elif participant_count and participant_count > 0:
        status = "participants_without_public_price"
        has_participants = True
    else:
        status = "unknown"
        has_participants = None

    return {
        "status": status,
        "participant_count": participant_count,
        "bid_count": bid_count,
        "has_participants": has_participants,
        "current_offer_price": current_offer_price,
        "next_bid_price": next_bid_price,
        "nmc_price": nmc_price,
        "price_source": price_source,
        "last_offer_supplier": last_offer_supplier,
    }


def _raw_payload(tender: dict[str, Any]) -> dict[str, Any]:
    raw_payload = tender.get("raw_payload")
    if isinstance(raw_payload, dict):
        return raw_payload
    raw_payload_json = tender.get("raw_payload_json")
    if isinstance(raw_payload_json, str) and raw_payload_json.strip():
        try:
            data = json.loads(raw_payload_json)
        except json.JSONDecodeError:
            return {}
        return data if isinstance(data, dict) else {}
    return {}


def _participant_count(
    raw_payload: dict[str, Any],
    detail: dict[str, Any],
    imported: dict[str, Any] | None = None,
) -> int | None:
    count_values: list[int] = []
    for payload, keys in (
        (imported or {}, ("uniqueSupplierCount", "participantCount", "offerCount")),
        (detail, ("uniqueSupplierCount", "participantCount", "offerCount", "ApplicationsCount")),
        (raw_payload, ("ApplicationsCount", "uniqueSupplierCount", "participantCount", "offerCount")),
    ):
        for key in keys:
            value = _int_value(payload.get(key))
            if value is not None:
                count_values.append(value)
    bets = detail.get("bets")
    if isinstance(bets, list) and bets:
        suppliers = {
            str(first_present(bet, "supplier.id", "supplier.name") or "")
            for bet in bets
            if isinstance(bet, dict)
        }
        suppliers.discard("")
        if suppliers:
            count_values.append(len(suppliers))
    if count_values:
        return max(count_values)
    return None


def _bid_count(
    raw_payload: dict[str, Any],
    detail: dict[str, Any],
    imported: dict[str, Any] | None = None,
) -> int | None:
    count_values: list[int] = []
    if imported:
        bets_diff = imported.get("betsDiff")
        if isinstance(bets_diff, list) and bets_diff:
            return len(bets_diff)
        for key in ("bidCount", "betCount", "offerCount"):
            value = _int_value(imported.get(key))
            if value is not None:
                count_values.append(value)
        participant_count = _int_value(imported.get("uniqueSupplierCount"))
        if _positive_number(imported.get("lastBetCost")) is not None:
            count_values.append(max(1, participant_count or 1))
    for payload in (detail, raw_payload):
        bets = payload.get("bets")
        if isinstance(bets, list) and bets:
            priced_bets = _priced_bet_count(bets)
            if priced_bets > 0:
                return priced_bets
    for payload, keys in (
        (detail, ("bidCount", "betCount", "offerCount")),
        (raw_payload, ("bidCount", "betCount", "offerCount", "ApplicationsCount")),
    ):
        for key in keys:
            value = _int_value(payload.get(key))
            if value is not None:
                count_values.append(value)
    if count_values:
        return max(count_values)
    for payload in (detail, raw_payload):
        bets = payload.get("bets")
        if isinstance(bets, list):
            return _priced_bet_count(bets)
    return None


def _current_offer_price(
    raw_payload: dict[str, Any],
    detail: dict[str, Any],
    imported: dict[str, Any],
    *,
    source: str,
    public_bid_count: int | None,
) -> tuple[float | None, str | None]:
    imported_price = _positive_number(
        first_present(imported, "lastBetCost", "currentOfferPrice", "auctionCurrentPrice", "currentCost")
    )
    if imported_price is not None:
        return imported_price, "moscow_get_bet_update_import"

    bets = detail.get("bets")
    bet_prices: list[float] = []
    if isinstance(bets, list):
        bet_prices = [
            value
            for bet in bets
            if isinstance(bet, dict)
            for value in (_positive_number(first_present(bet, "cost", "price", "amount")),)
            if value is not None
        ]
        if len(bet_prices) > 1:
            return min(bet_prices), "moscow_bets_min"

    for key, price_source in (
        ("lastBetCost", "moscow_last_bet"),
        ("auctionCurrentPrice", "moscow_current_price"),
        ("currentOfferPrice", "current_offer"),
    ):
        value = _positive_number(first_present(detail, key) or first_present(raw_payload, key))
        if value is not None:
            return value, price_source

    if bet_prices:
        return bet_prices[0], "moscow_bets"
    if source == "moscow_supplier_portal" and _is_active_moscow_session(raw_payload, detail):
        estimated = _estimated_moscow_public_bid_price(raw_payload, detail, public_bid_count)
        if estimated is not None:
            return estimated, "moscow_public_step_estimate"
    return None, None


def _public_moscow_bid_count(
    raw_payload: dict[str, Any],
    detail: dict[str, Any],
    imported: dict[str, Any] | None = None,
) -> int | None:
    if not _is_active_moscow_session(raw_payload, detail):
        return None
    imported_count = _int_value((imported or {}).get("uniqueSupplierCount"))
    if imported_count is not None:
        return imported_count
    for payload, keys in (
        (detail, ("bidCount", "betCount", "offerCount", "uniqueSupplierCount")),
        (raw_payload, ("bidCount", "betCount", "offerCount", "uniqueSupplierCount")),
    ):
        for key in keys:
            value = _int_value(payload.get(key))
            if value is not None:
                return value
    return None


def _is_active_moscow_session(raw_payload: dict[str, Any], detail: dict[str, Any]) -> bool:
    state_id = _int_value(first_present(detail, "state.id") or first_present(raw_payload, "stateId"))
    if state_id == MOSCOW_ACTIVE_STATE_ID:
        return True
    state_name = str(first_present(detail, "state.name") or first_present(raw_payload, "stateName") or "").casefold()
    return "\u0430\u043a\u0442\u0438\u0432" in state_name


def _estimated_moscow_public_bid_price(
    raw_payload: dict[str, Any],
    detail: dict[str, Any],
    public_bid_count: int | None,
) -> float | None:
    if public_bid_count is None or public_bid_count <= 0:
        return None
    start_price = _first_positive_number(detail, raw_payload, {}, ("startCost", "startPrice", "price"))
    if start_price is None:
        return None
    current_price = start_price * (1 - MOSCOW_PUBLIC_BID_STEP_RATIO * public_bid_count)
    return round(max(0.0, current_price), 2)


def _first_positive_number(
    primary: dict[str, Any],
    secondary: dict[str, Any],
    tertiary: dict[str, Any],
    keys: tuple[str, ...],
) -> float | None:
    for payload in (primary, secondary, tertiary):
        for key in keys:
            value = _positive_number(first_present(payload, key))
            if value is not None:
                return value
    return None


def _positive_number(value: Any) -> float | None:
    number = parse_float(value)
    if number is None or number <= 0:
        return None
    return number


def _priced_bet_count(bets: list[Any]) -> int:
    return sum(
        1
        for bet in bets
        if isinstance(bet, dict)
        and _positive_number(first_present(bet, "cost", "price", "amount")) is not None
    )


def _last_offer_supplier(detail: dict[str, Any]) -> str | None:
    supplier = detail.get("lastBetSupplier")
    if isinstance(supplier, dict):
        value = first_present(supplier, "name", "title")
        return str(value) if value else None
    return None


def _int_value(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(float(str(value).replace(" ", "").replace(",", ".")))
    except (TypeError, ValueError):
        return None
