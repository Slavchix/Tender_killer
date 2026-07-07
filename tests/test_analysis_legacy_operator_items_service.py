from __future__ import annotations

from tender_killer.analysis_legacy_operator_items_service import build_legacy_operator_items


def test_build_legacy_operator_items_preserves_summary_checklist_and_execution_terms():
    items = build_legacy_operator_items(
        {
            "summary": "Поставка электронного табло для баскетбола.",
            "checklist": [
                {
                    "label": "Оплата",
                    "evidence": "Оплата в течение 7 рабочих дней после подписания УПД.",
                    "category": "payment",
                    "severity": "medium",
                }
            ],
            "execution_terms": [
                {
                    "label": "Поставка",
                    "value": "Поставка в течение 10 календарных дней.",
                    "category": "delivery",
                }
            ],
        }
    )

    by_label = {item["label"]: item for item in items}

    assert by_label["Предмет"]["kind"] == "subject"
    assert by_label["Предмет"]["value"] == "Поставка электронного табло для баскетбола."
    assert by_label["Оплата"]["fragment"] == "Оплата в течение 7 рабочих дней после подписания УПД."
    assert by_label["Оплата"]["kind"] == "execution_term"
    assert by_label["Поставка"]["kind"] == "execution_term"
