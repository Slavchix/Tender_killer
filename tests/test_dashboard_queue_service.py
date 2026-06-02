from __future__ import annotations

from datetime import UTC, datetime, timedelta

from tender_killer.dashboard_queue_service import build_dashboard_queues_payload
from tender_killer.models import ProductProfile, Tender, TenderDocument
from tender_killer.storage import TenderStore


def test_dashboard_queue_service_builds_decision_owned_work_queues(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="queue-1",
            url="https://example.test/queue-1",
            title="Queue tender",
            customer="School",
            price=120000.0,
            status="Active",
            deadline_at=datetime.now(UTC) + timedelta(days=2),
            document_records=[
                TenderDocument(url="https://example.test/spec.docx", name="spec.docx"),
                TenderDocument(url="https://example.test/contract.pdf", name="contract.pdf"),
            ],
        )
    )
    with store._connect() as connection:
        connection.execute(
            """
            UPDATE tender_documents
            SET text_status = 'ok', text_content = 'extracted text'
            WHERE source = ? AND external_id = ? AND url = ?
            """,
            ("mosreg_market", "queue-1", "https://example.test/spec.docx"),
        )
    store.upsert_product_profiles(
        "mosreg_market",
        "queue-1",
        [
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="queue-1",
                position_index=1,
                product_name="Paper",
                quantity=10,
            )
        ],
    )

    payload = build_dashboard_queues_payload(store.database_path, {"status": "active"})
    queues = {queue["id"]: queue for queue in payload["queues"]}

    assert payload["ok"] is True
    assert payload["summary"]["total"] == 1
    assert payload["summary"]["scanned"] == 1
    assert queues["missing_prices"]["count"] == 1
    assert queues["documents_review"]["count"] == 1
    assert queues["missing_prices"]["items"][0]["external_id"] == "queue-1"
    assert queues["missing_prices"]["items"][0]["decision"]["status"] == "missing_prices"
