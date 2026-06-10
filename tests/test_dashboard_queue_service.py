from __future__ import annotations

from datetime import UTC, datetime, timedelta

from tender_killer.dashboard_queue_service import _has_current_offer
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


def test_dashboard_queue_service_counts_only_positive_current_offer():
    assert _has_current_offer({"market_state": {"current_offer_price": 1000}}) is True
    assert _has_current_offer({"market_state": {"current_offer_price": 0}}) is False
    assert _has_current_offer({"market_state": {"current_offer_price": ""}}) is False


def test_dashboard_queue_service_surfaces_customer_review_queue(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    for external_id in ("customer-history-1", "customer-history-2"):
        store.upsert_tender(
            Tender(
                source="mosreg_market",
                external_id=external_id,
                url=f"https://example.test/{external_id}",
                title="Previous tender",
                customer="School",
                status="Completed",
                raw_payload={
                    "customers": [{"inn": "5047152960"}],
                    "__detail": {"uniqueSupplierCount": 0},
                },
            )
        )
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="customer-risk",
            url="https://example.test/customer-risk",
            title="Current tender",
            customer="School",
            price=100000.0,
            status="Active",
            raw_payload={
                "purchaseNumber": "0373200000126000012",
                "customers": [{"inn": "5047152960"}],
                "__detail": {"uniqueSupplierCount": 0},
                "eis_customer_context": {"terminated_contracts_count": 3},
            },
        )
    )

    payload = build_dashboard_queues_payload(store.database_path, {"status": "active"})
    queues = {queue["id"]: queue for queue in payload["queues"]}

    assert queues["customer_review"]["count"] == 1
    item = queues["customer_review"]["items"][0]
    assert item["external_id"] == "customer-risk"
    assert item["customer_risk_profile"]["level"] == "high"
    assert item["eis_reference"]["identifiers"]["purchase_number"] == "0373200000126000012"
