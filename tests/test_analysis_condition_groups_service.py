from __future__ import annotations

from tender_killer.analysis_condition_groups_service import build_condition_groups


def test_build_condition_groups_groups_delivery_fact_without_operator_view():
    items = [
        {
            "id": "fact:delivery",
            "kind": "execution_term",
            "label": "Delivery deadline",
            "value": "Delivery within 10 days.",
            "category": "delivery",
            "source_label": "Spec.docx p. 1",
            "source_binding": {"level": "explicit"},
            "context_document_role": "technical_spec",
            "context_source_authority": "primary_for_topic",
        }
    ]

    groups = build_condition_groups(items)

    assert groups["version"] == 1
    assert groups["metrics"]["confirmed"] == 1
    assert groups["items"][0]["family"] == "delivery_deadline"
    assert groups["items"][0]["primary_fact_id"] == "fact:delivery"
    assert groups["items"][0]["sources"] == ["Spec.docx p. 1"]
    assert items[0]["condition_family"] == "delivery_deadline"
    assert items[0]["condition_families"] == ["delivery_deadline"]
