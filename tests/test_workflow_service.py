from __future__ import annotations

import sqlite3

import pytest

from tender_killer.models import Tender
from tender_killer.storage import TenderStore
from tender_killer.workflow_service import save_tender_workflow


def test_save_tender_workflow_persists_status_and_note(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="3668200",
            url="https://example.test/3668200",
            title="Paper tender",
        )
    )

    payload = save_tender_workflow(
        store.database_path,
        "mosreg_market",
        "3668200",
        {"workflow_status": "interesting", "workflow_note": "Check margin."},
    )

    assert payload == {"workflow_status": "interesting", "workflow_note": "Check margin."}
    with sqlite3.connect(store.database_path) as connection:
        row = connection.execute(
            "SELECT workflow_status, workflow_note FROM tender_workflow WHERE source = ? AND external_id = ?",
            ("mosreg_market", "3668200"),
        ).fetchone()
    assert row == ("interesting", "Check margin.")


def test_save_tender_workflow_rejects_unknown_status(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="3668200",
            url="https://example.test/3668200",
            title="Paper tender",
        )
    )

    with pytest.raises(ValueError, match="Unknown workflow status"):
        save_tender_workflow(
            store.database_path,
            "mosreg_market",
            "3668200",
            {"workflow_status": "maybe"},
        )


def test_save_tender_workflow_rejects_missing_tender(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()

    with pytest.raises(KeyError, match="not found"):
        save_tender_workflow(
            store.database_path,
            "mosreg_market",
            "missing",
            {"workflow_status": "interesting"},
        )
