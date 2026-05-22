from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from tender_killer.schema import ensure_price_snapshots_table


def latest_price_change(
    database_path: str | Path,
    source: str,
    external_id: str,
    price_kind: str = "nmc",
) -> dict[str, Any] | None:
    with sqlite3.connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        ensure_price_snapshots_table(connection)
        rows = connection.execute(
            """
            SELECT price_kind, price, observed_at
            FROM tender_price_snapshots
            WHERE source = ? AND external_id = ? AND price_kind = ?
            ORDER BY observed_at DESC, id DESC
            LIMIT 2
            """,
            (source, external_id, price_kind),
        ).fetchall()
    if len(rows) < 2:
        return None

    current, previous = rows[0], rows[1]
    current_price = float(current["price"])
    previous_price = float(previous["price"])
    delta = round(current_price - previous_price, 2)
    if delta < 0:
        direction = "decreased"
    elif delta > 0:
        direction = "increased"
    else:
        direction = "unchanged"
    delta_percent = round((delta / previous_price) * 100, 2) if previous_price else None
    return {
        "price_kind": str(current["price_kind"]),
        "direction": direction,
        "previous_price": previous_price,
        "current_price": current_price,
        "delta": delta,
        "delta_percent": delta_percent,
    }
