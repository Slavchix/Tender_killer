from __future__ import annotations

import importlib
import importlib.util

from tender_killer.analysis_operator_item_service import build_operator_item
from tender_killer.analysis_operator_item_service import canonical_label
from tender_killer.analysis_operator_item_service import dedupe_operator_items
from tender_killer.analysis_operator_item_service import description_is_only_label
from tender_killer.analysis_operator_item_service import fallback_kind
from tender_killer.analysis_operator_item_service import operator_item_is_visible
from tender_killer.analysis_operator_item_service import operator_item_quality


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


def test_operator_item_quality_helpers_live_in_focused_module():
    spec = importlib.util.find_spec("tender_killer.analysis_operator_item_quality_service")
    assert spec is not None

    quality_service = importlib.import_module("tender_killer.analysis_operator_item_quality_service")

    focused_dedupe_operator_items = quality_service.dedupe_operator_items
    focused_operator_item_is_visible = quality_service.operator_item_is_visible
    focused_operator_item_quality = quality_service.operator_item_quality

    assert dedupe_operator_items is focused_dedupe_operator_items
    assert operator_item_is_visible is focused_operator_item_is_visible
    assert operator_item_quality is focused_operator_item_quality


def test_operator_item_taxonomy_helpers_live_in_focused_module():
    spec = importlib.util.find_spec("tender_killer.analysis_operator_item_taxonomy_service")
    assert spec is not None

    taxonomy_service = importlib.import_module("tender_killer.analysis_operator_item_taxonomy_service")

    assert fallback_kind is taxonomy_service.fallback_kind
    assert canonical_label is taxonomy_service.canonical_label


def test_operator_item_wording_helpers_live_in_focused_module():
    spec = importlib.util.find_spec("tender_killer.analysis_operator_item_wording_service")
    assert spec is not None

    wording_service = importlib.import_module("tender_killer.analysis_operator_item_wording_service")

    assert description_is_only_label is wording_service.description_is_only_label
    assert hasattr(wording_service, "operator_impact")
    assert hasattr(wording_service, "operator_action")
    assert hasattr(wording_service, "operator_description")
    assert hasattr(wording_service, "operator_display_tier")
    assert hasattr(wording_service, "operator_summary")
    assert hasattr(wording_service, "operator_check")
    assert hasattr(wording_service, "operator_weak_reason")
