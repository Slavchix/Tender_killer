from __future__ import annotations

from tender_killer.analysis_document_state_service import build_document_items
from tender_killer.analysis_document_state_service import build_document_state


def test_build_document_state_and_summary_item_for_partial_text_extraction():
    documents = [
        {"name": "Spec.docx", "local_path": "docs/spec.docx", "text_status": "ok"},
        {"name": "Contract.docx", "local_path": "docs/contract.docx", "text_status": "pending"},
    ]

    state = build_document_state(documents)
    items = build_document_items(documents)

    assert state["status"] == "needs_text"
    assert state["total"] == 2
    assert state["downloaded"] == 2
    assert state["text_ready"] == 1
    assert state["attention"] == 1
    assert items[0]["type"] == "document_summary"
    assert items[0]["status"] == "needs_text"
    assert items[0]["needs_review"] is True
    assert items[0]["documents"] == ["Spec.docx", "Contract.docx"]
