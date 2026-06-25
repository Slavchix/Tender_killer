from __future__ import annotations

from tender_killer.analysis_evidence_drilldown_service import build_evidence_drilldowns


def test_build_evidence_drilldowns_indexes_fact_sources():
    items = [
        {
            "id": "fact:payment",
            "kind": "execution_term",
            "label": "Payment",
            "value": "Payment after acceptance.",
            "category": "payment",
            "severity": "medium",
            "document_name": "Contract.docx",
            "source_label": "Contract.docx p. 8",
            "fragment": "Payment after acceptance.",
            "source_binding": {"level": "explicit"},
        }
    ]

    drilldowns = build_evidence_drilldowns(items)

    assert drilldowns["version"] == 1
    assert drilldowns["by_fact_id"] == {"fact:payment": "fact:payment"}
    assert drilldowns["items"][0]["title"] == "Payment"
    assert drilldowns["items"][0]["source_label"] == "Contract.docx p. 8"
    assert items[0]["evidence_drilldown_id"] == "fact:payment"
