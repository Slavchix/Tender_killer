from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from tender_killer.market_state import extract_market_state
from tender_killer.normalization import parse_datetime
from tender_killer.normalization import parse_float
from tender_killer.schema import initialize_schema
from tender_killer.tender_detail_service import get_tender_payload
from tender_killer.tender_metadata import normalize_status

MOSCOW_GET_BET_UPDATE_SOURCE = "zakupki_mos_get_bet_update"
MARKET_IMPORT_KEY = "__market_state_import"

_SENSITIVE_KEY_MARKERS = (
    "authorization",
    "cookie",
    "set-cookie",
    "access-token",
    "refresh-token",
    "id-token",
    "password",
    "secret",
)


def import_tender_market_state(
    database_path: str | Path,
    source: str,
    external_id: str,
    data: dict[str, Any],
) -> dict[str, Any]:
    if source != "moscow_supplier_portal":
        raise ValueError("Market state import is currently supported only for Moscow supplier portal tenders.")
    if not isinstance(data, dict):
        raise ValueError("Market state import payload must be a JSON object.")

    _reject_sensitive_fields(data)
    imported = normalize_moscow_get_bet_update_payload(data)

    with _connect(database_path) as connection:
        initialize_schema(connection)
        row = connection.execute(
            """
            SELECT source, external_id, price, currency, raw_payload_json
            FROM tenders
            WHERE source = ? AND external_id = ?
            """,
            (source, external_id),
        ).fetchone()
        if row is None:
            raise KeyError(f"Tender {source}/{external_id} not found.")

        raw_payload = _json_object(row["raw_payload_json"])
        raw_payload[MARKET_IMPORT_KEY] = imported
        state_name = _state_name(imported)
        deadline_at = parse_datetime(imported.get("endDate"))
        status_normalized = normalize_status(state_name) if state_name else None

        connection.execute(
            """
            UPDATE tenders
            SET raw_payload_json = ?,
                status = COALESCE(?, status),
                status_normalized = COALESCE(?, status_normalized),
                deadline_at = COALESCE(?, deadline_at),
                updated_at = CURRENT_TIMESTAMP
            WHERE source = ? AND external_id = ?
            """,
            (
                json.dumps(raw_payload, ensure_ascii=False),
                state_name,
                status_normalized,
                deadline_at.isoformat() if deadline_at else None,
                source,
                external_id,
            ),
        )
        market_state = extract_market_state(
            {
                "source": source,
                "external_id": external_id,
                "price": row["price"],
                "raw_payload": raw_payload,
            }
        )
        _record_price_snapshot(
            connection,
            source,
            external_id,
            row["currency"] or "RUB",
            market_state.get("current_offer_price"),
            raw_payload,
        )

    return get_tender_payload(database_path, source, external_id)


def normalize_moscow_get_bet_update_payload(data: dict[str, Any]) -> dict[str, Any]:
    imported: dict[str, Any] = {
        "source": MOSCOW_GET_BET_UPDATE_SOURCE,
        "imported_at": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    for key in ("endDate", "rowVersion"):
        value = data.get(key)
        if value not in (None, ""):
            imported[key] = value
    for key in ("nextCost", "lastBetCost"):
        value = parse_float(data.get(key))
        if value is not None:
            imported[key] = value
    supplier_count = _int_value(data.get("uniqueSupplierCount"))
    if supplier_count is not None:
        imported["uniqueSupplierCount"] = supplier_count
    state = data.get("state")
    if isinstance(state, dict):
        safe_state: dict[str, Any] = {}
        if state.get("name") not in (None, ""):
            safe_state["name"] = str(state["name"])
        state_id = _int_value(state.get("id"))
        if state_id is not None:
            safe_state["id"] = state_id
        if safe_state:
            imported["state"] = safe_state
    supplier = data.get("lastBetSupplier")
    if isinstance(supplier, dict):
        safe_supplier: dict[str, Any] = {}
        if supplier.get("name") not in (None, ""):
            safe_supplier["name"] = str(supplier["name"])
        if supplier.get("id") not in (None, ""):
            safe_supplier["id"] = supplier["id"]
        if safe_supplier:
            imported["lastBetSupplier"] = safe_supplier
    bets_diff = data.get("betsDiff")
    if isinstance(bets_diff, list):
        imported["betsDiff"] = [_safe_bet_diff(item) for item in bets_diff if isinstance(item, dict)]

    if "lastBetCost" not in imported and "nextCost" not in imported and "uniqueSupplierCount" not in imported:
        raise ValueError("Market state import payload does not contain recognizable bid fields.")
    return imported


def _reject_sensitive_fields(value: Any, path: tuple[str, ...] = ()) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            key_text = str(key)
            if _is_sensitive_key(key_text):
                dotted_path = ".".join((*path, key_text))
                raise ValueError(f"Market state import payload contains sensitive field: {dotted_path}")
            _reject_sensitive_fields(nested, (*path, key_text))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            _reject_sensitive_fields(nested, (*path, str(index)))


def _is_sensitive_key(key: str) -> bool:
    normalized = key.strip().casefold().replace("_", "-")
    if normalized == "token" or normalized.endswith("-token"):
        return True
    return any(marker in normalized for marker in _SENSITIVE_KEY_MARKERS)


def _safe_bet_diff(item: dict[str, Any]) -> dict[str, Any]:
    safe: dict[str, Any] = {}
    for key in ("num", "number", "date", "time"):
        if item.get(key) not in (None, ""):
            safe[key] = item[key]
    cost = parse_float(item.get("cost") or item.get("price") or item.get("amount"))
    if cost is not None:
        safe["cost"] = cost
    supplier = item.get("supplier") or item.get("betSupplier")
    if isinstance(supplier, dict):
        safe_supplier: dict[str, Any] = {}
        if supplier.get("name") not in (None, ""):
            safe_supplier["name"] = str(supplier["name"])
        if supplier.get("id") not in (None, ""):
            safe_supplier["id"] = supplier["id"]
        if safe_supplier:
            safe["supplier"] = safe_supplier
    return safe


def _state_name(imported: dict[str, Any]) -> str | None:
    state = imported.get("state")
    if isinstance(state, dict) and state.get("name") not in (None, ""):
        return str(state["name"])
    return None


def _record_price_snapshot(
    connection: sqlite3.Connection,
    source: str,
    external_id: str,
    currency: str,
    price: Any,
    raw_payload: dict[str, Any],
) -> None:
    current_price = parse_float(price)
    if current_price is None:
        return
    latest = connection.execute(
        """
        SELECT price
        FROM tender_price_snapshots
        WHERE source = ? AND external_id = ? AND price_kind = ?
        ORDER BY observed_at DESC, id DESC
        LIMIT 1
        """,
        (source, external_id, "current_offer"),
    ).fetchone()
    if latest is not None and float(latest["price"]) == float(current_price):
        return
    connection.execute(
        """
        INSERT INTO tender_price_snapshots (
            source, external_id, price_kind, price, currency, raw_payload_json
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            source,
            external_id,
            "current_offer",
            float(current_price),
            currency or "RUB",
            json.dumps(raw_payload, ensure_ascii=False),
        ),
    )


def _json_object(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    try:
        data = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _int_value(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(float(str(value).replace(" ", "").replace(",", ".")))
    except (TypeError, ValueError):
        return None


def _connect(database_path: str | Path) -> sqlite3.Connection:
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    return connection
