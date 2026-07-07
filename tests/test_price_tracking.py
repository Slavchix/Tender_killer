from __future__ import annotations

from dataclasses import replace

from tender_killer.models import Tender
from tender_killer.price_tracking import latest_price_change
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


def test_latest_price_change_reports_decrease(tmp_path):
    store = TenderStore(tmp_path / "db.sqlite")
    store.initialize()
    tender = Tender(
        source="mosreg_market",
        external_id="price-2",
        url="https://example.test/price-2",
        title="Поставка топлива",
        price=100_000,
    )
    store.upsert_tender(tender)
    store.upsert_tender(replace(tender, price=93_500))

    change = latest_price_change(store.database_path, "mosreg_market", "price-2", "nmc")

    assert change == {
        "price_kind": "nmc",
        "direction": "decreased",
        "previous_price": 100_000.0,
        "current_price": 93_500.0,
        "delta": -6_500.0,
        "delta_percent": -6.5,
    }


def test_store_records_current_offer_snapshot_from_public_market_state(tmp_path):
    store = TenderStore(tmp_path / "db.sqlite")
    store.initialize()
    tender = Tender(
        source="moscow_supplier_portal",
        external_id="offer-1",
        url="https://zakupki.mos.ru/auction/offer-1",
        title="Auction with bets",
        price=100_000,
        raw_payload={"__detail": {"lastBetCost": 95_000.0, "uniqueSupplierCount": 2}},
    )

    store.upsert_tender(tender)
    store.upsert_tender(
        replace(
            tender,
            raw_payload={"__detail": {"lastBetCost": 90_000.0, "uniqueSupplierCount": 3}},
        )
    )

    change = latest_price_change(store.database_path, "moscow_supplier_portal", "offer-1", "current_offer")

    assert change == {
        "price_kind": "current_offer",
        "direction": "decreased",
        "previous_price": 95_000.0,
        "current_price": 90_000.0,
        "delta": -5_000.0,
        "delta_percent": -5.26,
    }
