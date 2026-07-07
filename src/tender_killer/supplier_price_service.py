from __future__ import annotations

from typing import Any


BLOCKED_SUPPLIER_STATUSES = {"rejected"}
BLOCKED_SUPPLIER_AVAILABILITIES = {"not_available"}


def best_supplier_price(profile: dict[str, Any]) -> dict[str, Any] | None:
    raw_payload = profile.get("raw_payload") if isinstance(profile.get("raw_payload"), dict) else {}
    supplier_options = _supplier_options(raw_payload.get("supplier_options"))
    selected_index = _integer(raw_payload.get("selected_supplier_option_index"))
    if selected_index is not None and 0 <= selected_index < len(supplier_options):
        selected_option = supplier_options[selected_index]
        if _number(selected_option.get("unit_price")) is not None:
            return supplier_price_source(selected_option, selected_index, "manual_selected")

    eligible: list[tuple[int, dict[str, Any]]] = []
    for index, option in enumerate(supplier_options):
        if _is_eligible_supplier_option(option):
            eligible.append((index, option))
    if not eligible:
        return None

    selected_index, selected_option = min(
        eligible,
        key=lambda item: (
            _number(item[1].get("unit_price")) or 0.0,
            _availability_rank(item[1].get("availability")),
            _status_rank(item[1].get("status")),
            item[0],
        ),
    )
    return supplier_price_source(selected_option, selected_index, "auto_best")


def supplier_price_source(option: dict[str, Any], option_index: int, selection: str) -> dict[str, Any]:
    unit_price = _number(option.get("unit_price"))
    if unit_price is None:
        raise ValueError("Supplier option has no unit price.")
    return {
        "source": "supplier_option",
        "selection": selection,
        "option_index": option_index,
        "supplier_name": _text(option.get("name")),
        "supplier_url": _text(option.get("url")),
        "unit_price": unit_price,
        "availability": _text(option.get("availability")) or "unknown",
        "status": _text(option.get("status")) or "candidate",
        "confidence": _confidence(option, selection),
    }


def _is_eligible_supplier_option(option: dict[str, Any]) -> bool:
    if _number(option.get("unit_price")) is None:
        return False
    status = str(option.get("status") or "candidate").strip()
    availability = str(option.get("availability") or "unknown").strip()
    return status not in BLOCKED_SUPPLIER_STATUSES and availability not in BLOCKED_SUPPLIER_AVAILABILITIES


def _confidence(option: dict[str, Any], selection: str) -> str:
    if selection == "manual_selected":
        return "confirmed"
    status = str(option.get("status") or "").strip()
    availability = str(option.get("availability") or "unknown").strip()
    if status == "suitable" and availability == "in_stock":
        return "high"
    if status == "suitable" or availability in {"in_stock", "on_request"}:
        return "medium"
    return "needs_review"


def _availability_rank(value: Any) -> int:
    return {
        "in_stock": 0,
        "on_request": 1,
        "unknown": 2,
    }.get(str(value or "unknown").strip(), 3)


def _status_rank(value: Any) -> int:
    return {
        "selected": 0,
        "suitable": 1,
        "candidate": 2,
    }.get(str(value or "candidate").strip(), 3)


def _supplier_options(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _number(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        number = float(str(value).replace(" ", "").replace(",", "."))
    except (TypeError, ValueError):
        return None
    return number if number >= 0 else None


def _integer(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
