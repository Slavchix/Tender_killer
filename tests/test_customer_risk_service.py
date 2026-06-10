from __future__ import annotations

from tender_killer.customer_risk_service import build_customer_risk_profile


def test_build_customer_risk_profile_uses_local_history_and_eis_context() -> None:
    profile = build_customer_risk_profile(
        {
            "source": "mosreg_market",
            "external_id": "current",
            "customer": "School",
            "customer_inn": "5047152960",
            "market_state": {"status": "no_participants", "participant_count": 0},
            "analysis": {"red_flags": ["license required"], "risks": []},
            "raw_payload": {
                "eis_customer_context": {
                    "contracts_count": 18,
                    "terminated_contracts_count": 2,
                    "complaints_count": 3,
                    "payment_delay_count": 1,
                }
            },
        },
        [
            {
                "source": "mosreg_market",
                "external_id": "old-1",
                "title": "Previous paper",
                "market_state": {"status": "no_participants", "participant_count": 0},
                "status_normalized": "completed",
            },
            {
                "source": "moscow_supplier_portal",
                "external_id": "old-2",
                "title": "Previous frames",
                "market_state": {"status": "no_participants", "participant_count": 0},
                "status_normalized": "completed",
            },
        ],
    )

    assert profile["version"] == 1
    assert profile["status"] == "ready"
    assert profile["customer"] == {"name": "School", "inn": "5047152960"}
    assert profile["level"] == "high"
    assert profile["history"]["total"] == 2
    assert profile["history"]["market_state_counts"]["no_participants"] == 2
    assert {factor["id"] for factor in profile["factors"]} >= {
        "current_no_participants",
        "repeated_no_participants",
        "customer_complaints",
        "terminated_contracts",
        "payment_delay",
        "analysis_red_flags",
    }


def test_build_customer_risk_profile_requires_customer_identity_for_history() -> None:
    profile = build_customer_risk_profile(
        {
            "source": "mosreg_market",
            "external_id": "current",
            "title": "No customer yet",
            "raw_payload": {},
            "market_state": {"status": "unknown"},
        }
    )

    assert profile["status"] == "needs_customer_identity"
    assert profile["level"] == "medium"
    assert profile["history"]["total"] == 0
    assert profile["factors"][0]["id"] == "missing_customer_identity"
