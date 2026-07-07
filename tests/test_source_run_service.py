from __future__ import annotations

from datetime import UTC, datetime

from tender_killer.source_run_service import list_source_runs_payload
from tender_killer.storage import TenderStore


def test_list_source_runs_payload_returns_known_sources_and_checkpoint_state(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.record_source_success(
        "mosreg_market",
        last_seen_published_at=datetime(2026, 5, 21, 9, 15, tzinfo=UTC),
    )
    store.record_source_error("moscow_supplier_portal", "HTTP 500")

    payload = list_source_runs_payload(store.database_path)

    by_source = {row["source"]: row for row in payload["sources"]}
    assert set(by_source) == {"moscow_supplier_portal", "mosreg_market"}
    assert by_source["mosreg_market"]["label"]
    assert by_source["mosreg_market"]["last_seen_published_at"] == "2026-05-21T09:15:00+00:00"
    assert by_source["moscow_supplier_portal"]["last_error"] == "HTTP 500"
    assert by_source["moscow_supplier_portal"]["last_error_at"]
