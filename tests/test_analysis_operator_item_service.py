from __future__ import annotations

from tender_killer.analysis_operator_item_service import build_operator_item
from tender_killer.analysis_operator_item_service import dedupe_operator_items
from tender_killer.analysis_operator_item_service import operator_item_is_visible


def test_build_operator_item_normalizes_unbound_fact_for_manual_review():
    item = build_operator_item(
        {
            "kind": "execution_term",
            "label": "Advance",
            "value": "Advance is possible.",
            "category": "financial",
            "severity": "medium",
            "fragment": "Advance is possible.",
            "source": "Документ не привязан",
        },
        0,
    )

    assert item["id"] == "execution_term:advance"
    assert item["label"] == "Advance"
    assert item["kind"] == "execution_term"
    assert item["needs_review"] is True
    assert item["source_binding"]["level"] == "unbound"
    assert item["confidence_level"]["level"] == "low"
    assert item["display_tier"] == "weak"
    assert item["operator_group"] == "manual_review"


def test_dedupe_operator_items_keeps_stronger_semantic_item():
    weak = {
        "id": "weak",
        "kind": "execution_term",
        "label": "Оплата",
        "category": "payment",
        "value": "Оплата",
        "source": "",
    }
    strong = {
        "id": "strong",
        "kind": "execution_term",
        "label": "Оплата",
        "category": "payment",
        "value": "Оплата в течение 10 дней.",
        "source_label": "Contract.docx p. 8",
        "fragment": "Оплата в течение 10 дней.",
    }

    assert dedupe_operator_items([weak, strong]) == [strong]


def test_operator_item_is_visible_hides_label_only_requirement():
    item = {
        "id": "empty",
        "kind": "requirement",
        "label": "license",
        "category": "legal",
        "value": "license",
        "source": "",
    }

    assert operator_item_is_visible(item) is False
