from __future__ import annotations

from tender_killer.analysis_operator_condition_service import prepare_operator_condition_items


def test_prepare_operator_condition_items_marks_conflicts_and_adds_expected_missing_checks():
    items = [
        {
            "id": "advance:no",
            "kind": "execution_term",
            "type": "execution_term",
            "label": "Аванс",
            "value": "Авансирование не предусмотрено.",
            "category": "financial",
            "severity": "medium",
            "fragment": "Авансирование не предусмотрено.",
        },
        {
            "id": "advance:yes",
            "kind": "execution_term",
            "type": "execution_term",
            "label": "Аванс",
            "value": "Предусмотрен аванс 30% от цены контракта.",
            "category": "financial",
            "severity": "medium",
            "fragment": "Предусмотрен аванс 30% от цены контракта.",
        },
    ]
    documents = [{"name": "Контракт.docx", "local_path": "contract.docx", "text_status": "ok"}]

    prepared = prepare_operator_condition_items(items, {}, documents)

    conflicted = [item for item in prepared if item.get("conflict_flags")]
    expected_missing = [item for item in prepared if item.get("expected_missing")]

    assert {item["id"] for item in conflicted} == {"advance:no", "advance:yes"}
    assert all(item["needs_review"] for item in conflicted)
    assert all(item["evidence_quality"]["level"] == "conflict" for item in conflicted)
    assert any(item["label"] == "условия оплаты" for item in expected_missing)
    assert any(item["label"] == "приемка и закрывающие документы" for item in expected_missing)
    assert not any(item["label"] == "аванс" for item in expected_missing)
