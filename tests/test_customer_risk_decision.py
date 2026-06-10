from __future__ import annotations

from tender_killer.decision_service import build_tender_decision


def test_decision_requires_customer_review_for_high_risk_profile() -> None:
    decision = build_tender_decision(
        {
            "economics": {
                "status": "interesting",
                "margin_percent": 22,
                "participation_decision": {"status": "can_bid", "label": "can bid"},
            },
            "analysis": {"status": "ok", "risks": [], "red_flags": [], "requirements": []},
            "document_records": [{"text_status": "ok"}],
            "product_profiles": [{"profile_status": "priced"}],
            "customer_risk_profile": {
                "level": "high",
                "score": 72,
                "factors": [
                    {
                        "id": "terminated_contracts",
                        "severity": "high",
                        "evidence": "Terminated contracts: 2.",
                    }
                ],
            },
        }
    )

    assert decision["status"] == "needs_review"
    assert "Terminated contracts: 2." in decision["blockers"]
    assert "Terminated contracts: 2." in decision["reason_tree"]["negative"]
