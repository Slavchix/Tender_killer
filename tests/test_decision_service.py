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


def test_decision_returns_reason_tree_with_pros_cons_and_actions():
    decision = build_tender_decision(
        {
            "economics": {
                "status": "manual_review",
                "margin_percent": 18,
                "risk_reserve": 6000,
                "participation_decision": {
                    "status": "guarded_bid",
                    "label": "участвовать осторожно",
                    "limit_price": 214000,
                    "recommendation": "Маржа после расходов 18%, но нужны документы поставщика.",
                },
            },
            "analysis": {
                "status": "needs_review",
                "risks": ["нужна разгрузка силами поставщика"],
                "red_flags": [],
                "requirements": ["не подтверждена декларация"],
                "operator_view": {
                    "version": 3,
                    "decision_brief": {
                        "summary": "Есть условия для проверки перед участием.",
                        "next_step": "Запросить документы у поставщика",
                        "reasons": ["срок поставки 3 дня"],
                    },
                },
            },
            "document_records": [{"text_status": "ok"}],
            "product_profiles": [{"profile_status": "priced"}],
        }
    )

    tree = decision["reason_tree"]

    assert tree["title"] == "участвовать осторожно"
    assert "Маржа после расходов: 18%" in tree["positive"]
    assert "Товарные позиции с ценами: 1/1" in tree["positive"]
    assert "не подтверждена декларация" in tree["negative"]
    assert "нужна разгрузка силами поставщика" in tree["negative"]
    assert tree["actions"] == [
        "Запросить документы у поставщика",
        "Проверить лимит ставки",
        "Не падать ниже 214 000.00 ₽",
    ]


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


def test_decision_uses_tz_passport_blockers_and_price_factors():
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
                "tz_passport": {
                    "version": 1,
                    "sections": [
                        {
                            "id": "blockers",
                            "items": [
                                {
                                    "label": "обеспечение исполнения контракта",
                                    "severity": "high",
                                }
                            ],
                        },
                        {
                            "id": "price_factors",
                            "items": [
                                {
                                    "label": "срочная поставка",
                                    "severity": "high",
                                }
                            ],
                        },
                    ],
                },
            },
            "document_records": [{"text_status": "ok"}],
        }
    )

    assert decision["status"] == "needs_review"
    assert "обеспечение исполнения контракта" in decision["blockers"]
    assert "срочная поставка" in decision["reasons"]


def test_decision_exposes_economics_decision_v2_for_safe_bid_and_policy():
    decision = build_tender_decision(
        {
            "economics": {
                "status": "manual_review",
                "margin_percent": 18.0,
                "target_margin_percent": 15.0,
                "minimum_margin_price": 93000.0,
                "target_bid_price": 105000.0,
                "participation_decision": {
                    "status": "guarded_bid",
                    "label": "with limit",
                    "limit_price": 93000.0,
                    "recommendation": "Keep minimum margin.",
                },
            },
            "analysis": {"status": "ok", "risks": ["rush delivery"], "red_flags": [], "requirements": []},
            "market_state": {"current_offer_price": 100000.0, "nmc_price": 120000.0, "bid_count": 2},
            "document_records": [{"text_status": "ok"}],
            "product_profiles": [
                {"profile_status": "priced"},
                {"profile_status": "priced"},
                {"profile_status": "priced"},
            ],
        }
    )

    economics_decision = decision["economics_decision"]

    assert economics_decision["version"] == 2
    assert economics_decision["can_participate"] is True
    assert economics_decision["safe_bid"] == {"amount": 93000.0, "source": "minimum_margin_price"}
    assert economics_decision["minimum_margin_percent"] == 15.0
    assert economics_decision["current_margin_percent"] == 18.0
    assert economics_decision["discount_buffer"] == {
        "amount": 7000.0,
        "percent": 7.0,
        "basis": "current_offer_price",
    }
    assert economics_decision["one_line_explanation"].startswith("Можно участвовать")
    assert "93 000" in economics_decision["one_line_explanation"]
    assert "18%" in economics_decision["one_line_explanation"]
    assert "15%" in economics_decision["one_line_explanation"]
    assert "7%" in economics_decision["one_line_explanation"]
    assert economics_decision["auto_price_policy"]["level"] == "small_review_only_auto_search"
    assert economics_decision["auto_price_policy"]["active_search_allowed"] is True
    assert economics_decision["auto_price_policy"]["mass_launch_allowed"] is True
    assert "rush delivery" in economics_decision["risks"]


def test_decision_v2_exposes_final_decision_card_for_operator():
    decision = build_tender_decision(
        {
            "economics": {
                "status": "manual_review",
                "margin_percent": 18.0,
                "target_margin_percent": 15.0,
                "minimum_margin_price": 93000.0,
                "participation_decision": {
                    "status": "guarded_bid",
                    "label": "with limit",
                    "limit_price": 93000.0,
                    "recommendation": "Keep minimum margin.",
                },
            },
            "analysis": {"status": "ok", "risks": ["rush delivery"], "red_flags": [], "requirements": []},
            "market_state": {"current_offer_price": 100000.0, "nmc_price": 120000.0, "bid_count": 2},
            "document_records": [{"text_status": "ok"}],
            "product_profiles": [{"profile_status": "priced"} for _ in range(3)],
        }
    )

    card = decision["economics_decision"]["final_decision_card"]

    assert card["status"] == "can_bid_with_limit"
    assert card["headline"].startswith("Можно участвовать до")
    assert card["safe_bid"] == {"amount": 93000.0, "source": "minimum_margin_price"}
    assert card["margin_text"] == "маржа 18%, минимум 15%"
    assert card["buffer_text"] == "запас снижения 7%"
    assert card["primary_reasons"][:2] == ["Keep minimum margin.", "rush delivery"]
    assert len(card["primary_reasons"]) <= 3
    assert card["next_action"] == "Проверить лимит и условия перед заявкой"


def test_decision_v2_keeps_large_tender_auto_prices_manual_and_benchmarks_history():
    decision = build_tender_decision(
        {
            "economics": {
                "status": "interesting",
                "margin_percent": 24.0,
                "target_margin_percent": 15.0,
                "participation_decision": {
                    "status": "can_bid",
                    "label": "can bid",
                    "limit_price": 250000.0,
                    "recommendation": "Healthy economics.",
                },
            },
            "analysis": {"status": "ok", "risks": [], "red_flags": [], "requirements": []},
            "market_state": {"nmc_price": 420000.0, "bid_count": 0},
            "customer_risk_profile": {
                "history": {
                    "recent": [
                        {"title": "similar 1", "price": 200000.0, "market_state": {"status": "completed"}},
                        {"title": "similar 2", "price": 220000.0, "market_state": {"status": "completed"}},
                        {"title": "similar 3", "price": 240000.0, "market_state": {"status": "no_participants"}},
                    ]
                }
            },
            "document_records": [{"text_status": "ok"}],
            "product_profiles": [{"profile_status": "priced"} for _ in range(6)],
        }
    )

    economics_decision = decision["economics_decision"]

    assert economics_decision["auto_price_policy"]["level"] == "large_manual_sources"
    assert economics_decision["auto_price_policy"]["active_search_allowed"] is False
    assert economics_decision["auto_price_policy"]["mass_launch_allowed"] is False
    assert economics_decision["auto_price_policy"]["primary_sources"] == [
        "price_book_feed",
        "supplier_quote",
        "manual_url",
        "quick_links",
    ]
    assert economics_decision["historical_benchmark"] == {
        "status": "warning",
        "sample_size": 3,
        "typical_price": 220000.0,
        "current_price": 420000.0,
        "delta_percent": 90.91,
        "no_participant_count": 1,
        "note": "Historical benchmark is a control signal only; landed cost remains the decision basis.",
    }


def test_decision_requires_price_quality_review_before_interesting_bid():
    decision = build_tender_decision(
        {
            "economics": {
                "status": "interesting",
                "margin_percent": 24.0,
                "target_margin_percent": 15.0,
                "participation_decision": {
                    "status": "can_bid",
                    "label": "can bid",
                    "limit_price": 250000.0,
                    "recommendation": "Healthy economics.",
                },
                "price_quality": {
                    "positions_total": 2,
                    "positions_priced": 2,
                    "positions_missing": 0,
                    "candidates_total": 3,
                    "candidates_ready": 1,
                    "candidates_review": 1,
                    "candidates_blocked": 1,
                    "review_flags": [{"id": "vat_unknown", "label": "НДС уточнить", "count": 1}],
                    "block_flags": [{"id": "product_name_mismatch", "label": "Не тот товар", "count": 1}],
                },
            },
            "analysis": {"status": "ok", "risks": [], "red_flags": [], "requirements": []},
            "market_state": {"nmc_price": 420000.0},
            "document_records": [{"text_status": "ok"}],
            "product_profiles": [{"profile_status": "priced"}, {"profile_status": "priced"}],
        }
    )

    assert decision["status"] == "needs_review"
    assert decision["label"] == "Проверить цены"
    assert decision["next_step"] == "Проверить кандидатов цен"
    assert "Не тот товар" in decision["blockers"]
    assert "НДС уточнить" in decision["reasons"]
    assert decision["metrics"]["price_candidates_review"] == 1
    assert decision["metrics"]["price_candidates_blocked"] == 1
    assert decision["economics_decision"]["can_participate"] is None
    assert decision["economics_decision"]["one_line_explanation"].startswith("Нужна проверка")
    assert "Не тот товар" in decision["economics_decision"]["what_blocks_application"]


def test_decision_requires_price_quality_review_even_without_flag_labels():
    decision = build_tender_decision(
        {
            "economics": {
                "status": "interesting",
                "participation_decision": {"status": "can_bid", "label": "can bid"},
                "price_quality": {
                    "positions_total": 1,
                    "positions_priced": 1,
                    "candidates_total": 1,
                    "candidates_ready": 0,
                    "candidates_review": 1,
                    "candidates_blocked": 0,
                    "review_flags": [],
                    "block_flags": [],
                },
            },
            "analysis": {"status": "ok", "risks": [], "red_flags": [], "requirements": []},
            "document_records": [{"text_status": "ok"}],
            "product_profiles": [{"profile_status": "priced"}],
        }
    )

    assert decision["status"] == "needs_review"
    assert decision["blockers"] == ["Есть кандидаты цен на проверку"]
