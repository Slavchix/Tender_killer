from tender_killer.analysis_operator_fact_source_service import build_operator_fact_source


def test_build_operator_fact_source_prefers_structured_analysis_facts():
    source = build_operator_fact_source(
        {
            "summary": "Legacy summary must not be used when structured facts exist.",
            "analysis_facts": {
                "version": 1,
                "items": [
                    {
                        "id": "fact:payment",
                        "kind": "requirement",
                        "label": "Условия оплаты",
                        "value": "Оплата в течение 30 календарных дней.",
                        "category": "payment",
                        "severity": "medium",
                        "source_context": "Оплата в течение 30 календарных дней.",
                    }
                ],
                "metrics": {"unbound": 2, "facts": 1},
            },
        }
    )

    assert source["source"] == "analysis_facts"
    assert source["metrics"] == {"unbound": 2, "facts": 1}
    assert [item["label"] for item in source["items"]] == ["Условия оплаты"]
    assert source["items"][0]["operator_summary"]


def test_build_operator_fact_source_falls_back_to_legacy_payload():
    source = build_operator_fact_source(
        {
            "summary": "Поставка электронного табло.",
            "checklist": [
                {
                    "label": "Лицензия",
                    "value": "Требуется лицензия на монтажные работы.",
                    "category": "legal",
                    "severity": "high",
                    "source_context": "Требуется лицензия на монтажные работы.",
                }
            ],
        }
    )

    assert source["source"] == "legacy"
    assert source["metrics"] is None
    assert {"Предмет", "лицензия/СРО"} <= {item["label"] for item in source["items"]}
