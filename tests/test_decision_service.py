from __future__ import annotations

from tender_killer.decision_service import build_tender_decision


def test_decision_requires_costs_before_participation():
    decision = build_tender_decision(
        {
            "title": "Paper",
            "economics": {
                "status": "needs_costs",
                "missing_cost_inputs": ["Paper A4"],
                "participation_decision": {"status": "needs_costs", "label": "Не хватает цен"},
            },
            "document_records": [{"text_status": "empty"}],
        }
    )

    assert decision["status"] == "missing_prices"
    assert decision["label"] == "Не хватает цен"
    assert decision["next_step"] == "Добавить себестоимость"
    assert "Paper A4" in decision["blockers"]
    assert decision["metrics"]["documents_ready"] == 0


def test_decision_marks_guarded_bid_when_economics_has_limit():
    decision = build_tender_decision(
        {
            "economics": {
                "status": "manual_review",
                "margin_percent": 8.5,
                "participation_decision": {
                    "status": "guarded_bid",
                    "label": "Только с лимитом",
                    "limit_price": 14903.23,
                    "recommendation": "Участвовать только с лимитом.",
                },
            },
            "analysis": {"status": "ok", "risks": [], "red_flags": [], "requirements": []},
            "market_state": {"current_offer_price": 16000, "bid_count": 2},
            "document_records": [{"text_status": "ok"}],
            "product_profiles": [{"profile_status": "priced"}],
        }
    )

    assert decision["status"] == "with_limit"
    assert decision["label"] == "Только с лимитом"
    assert decision["limit_price"] == 14903.23
    assert decision["metrics"]["current_offer_price"] == 16000
    assert decision["metrics"]["bid_count"] == 2


def test_decision_requires_analysis_review_for_red_flags():
    decision = build_tender_decision(
        {
            "economics": {
                "status": "interesting",
                "margin_percent": 25,
                "participation_decision": {"status": "can_bid", "label": "Можно заходить"},
            },
            "analysis": {
                "status": "needs_review",
                "risks": ["короткий срок поставки"],
                "red_flags": ["лицензия/СРО"],
                "requirements": [],
            },
            "document_records": [{"text_status": "ok"}],
        }
    )

    assert decision["status"] == "needs_review"
    assert decision["label"] == "Проверить ТЗ"
    assert "лицензия/СРО" in decision["blockers"]
    assert decision["next_step"] == "Проверить анализ"


def test_decision_uses_operator_view_blockers_when_legacy_flags_are_empty():
    decision = build_tender_decision(
        {
            "economics": {
                "status": "interesting",
                "margin_percent": 18,
                "participation_decision": {"status": "can_bid", "label": "Можно заходить"},
            },
            "analysis": {
                "status": "ok",
                "risks": [],
                "red_flags": [],
                "requirements": [],
                "operator_view": {
                    "version": 2,
                    "decision_brief": {
                        "status": "manual_review",
                        "summary": "Нужна ручная проверка ТЗ.",
                        "next_step": "Разобрать блокеры",
                        "reasons": ["сертификат/декларация"],
                    },
                    "sections": [
                        {
                            "id": "blockers",
                            "items": [
                                {
                                    "label": "сертификат/декларация",
                                    "description": "Нужны документы подтверждения.",
                                }
                            ],
                        }
                    ],
                },
            },
            "document_records": [{"text_status": "ok"}],
        }
    )

    assert decision["status"] == "needs_review"
    assert decision["label"] == "Проверить ТЗ"
    assert decision["summary"] == "Нужна ручная проверка ТЗ."
    assert decision["next_step"] == "Разобрать блокеры"
    assert "сертификат/декларация" in decision["blockers"]
    assert "сертификат/декларация" in decision["reasons"]
