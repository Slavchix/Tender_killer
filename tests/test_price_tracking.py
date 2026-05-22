from __future__ import annotations

from dataclasses import replace

from tender_killer.models import Tender
from tender_killer.storage import TenderStore


def test_store_records_price_snapshot_only_when_nmc_changes(tmp_path):
    store = TenderStore(tmp_path / "db.sqlite")
    store.initialize()

    tender = Tender(
        source="mosreg_market",
        external_id="price-1",
        url="https://example.test/price-1",
        title="Поставка топлива",
        price=100_000,
    )

    store.upsert_tender(tender)
    store.upsert_tender(tender)
    store.upsert_tender(replace(tender, price=95_000))

    with store._connect() as connection:
        rows = connection.execute(
            """
            SELECT price_kind, price
            FROM tender_price_snapshots
            WHERE source = ? AND external_id = ?
            ORDER BY id
            """,
            ("mosreg_market", "price-1"),
        ).fetchall()

    assert [(row["price_kind"], row["price"]) for row in rows] == [
        ("nmc", 100_000),
        ("nmc", 95_000),
    ]
