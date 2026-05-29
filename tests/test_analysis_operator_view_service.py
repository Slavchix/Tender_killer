from __future__ import annotations

from tender_killer.analysis_operator_view_service import build_analysis_operator_view


def test_build_analysis_operator_view_prioritizes_blockers_and_groups_operator_sections():
    analysis = {
        "summary": "Supply office paper.",
        "status": "needs_review",
        "confidence": 0.82,
        "requirements": ["certificate"],
        "risks": ["contract security"],
        "red_flags": ["national regime"],
        "checklist": [
            {
                "label": "contract security",
                "category": "financial",
                "severity": "high",
                "evidence": "Security is 5%.",
            },
            {
                "label": "certificate",
                "category": "documents",
                "severity": "medium",
                "evidence": "Certificate is required.",
            },
            {
                "label": "short delivery",
                "category": "delivery",
                "severity": "high",
                "evidence": "Delivery in 3 days.",
            },
        ],
        "evidence_items": [
            {
                "id": "certificate-1",
                "label": "certificate",
                "category": "documents",
                "severity": "medium",
                "fragment": "Certificate is required.",
                "impact": "Check supplier documents.",
            }
        ],
    }
    documents = [
        {"name": "TZ.docx", "text_status": "ok"},
        {"name": "Contract.pdf", "text_status": "empty"},
    ]

    view = build_analysis_operator_view(analysis, documents)

    assert view["version"] == 2
    assert view["decision_brief"]["status"] == "manual_review"
    assert view["decision_brief"]["tone"] == "danger"
    assert view["decision_brief"]["primary_section"] == "blockers"
    assert view["decision_brief"]["confidence"] == 0.82
    assert view["metrics"] == {
        "requirements": 1,
        "risks": 2,
        "blockers": 3,
        "checklist": 3,
        "evidence": 1,
        "documents_ready": 1,
        "documents_total": 2,
    }

    sections = {section["id"]: section for section in view["sections"]}
    assert list(sections) == ["blockers", "requirements", "price_factors", "documents", "evidence"]
    assert [item["label"] for item in sections["blockers"]["items"]] == [
        "national regime",
        "contract security",
        "short delivery",
    ]
    assert [item["label"] for item in sections["requirements"]["items"]] == ["certificate"]
    assert [item["label"] for item in sections["price_factors"]["items"]] == [
        "contract security",
        "short delivery",
    ]
    assert sections["documents"]["items"][0]["label"] == "TZ.docx"
    assert sections["documents"]["items"][1]["status"] == "attention"
    assert sections["evidence"]["items"][0]["label"] == "certificate"


def test_build_analysis_operator_view_returns_pending_contract_without_analysis():
    view = build_analysis_operator_view(None, [{"name": "Spec.docx", "text_status": "pending"}])

    assert view["version"] == 2
    assert view["decision_brief"]["status"] == "pending"
    assert view["decision_brief"]["primary_section"] == "documents"
    assert view["metrics"]["documents_total"] == 1
    assert view["sections"][0]["id"] == "blockers"
