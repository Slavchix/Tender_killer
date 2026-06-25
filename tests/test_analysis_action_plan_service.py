from __future__ import annotations

from tender_killer.analysis_action_plan_service import build_analysis_action_plan


def test_build_analysis_action_plan_uses_condition_groups_as_source():
    sections = [
        {
            "id": "acceptance_payment",
            "items": [
                {
                    "id": "fact:payment",
                    "kind": "execution_term",
                    "label": "Payment",
                    "category": "payment",
                }
            ],
        }
    ]
    condition_groups = {
        "items": [
            {
                "family": "payment",
                "label": "payment",
                "status": "confirmed",
                "source_status": "primary_source",
                "related_fact_ids": ["fact:payment"],
                "operator_action": "Use the contract payment clause.",
            }
        ]
    }

    plan = build_analysis_action_plan(sections, {"status": "ready"}, condition_groups)

    assert plan == [
        {
            "id": "acceptance_payment",
            "title": "Проверить приемку и оплату",
            "status": "ok",
            "next_step": "Use the contract payment clause.",
            "items": ["payment · подтверждено"],
            "condition_fact_ids": ["fact:payment"],
            "source": "condition_groups",
        }
    ]
