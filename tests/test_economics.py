from __future__ import annotations

from tender_killer.economics import build_economics_summary


def test_build_economics_summary_calculates_margin_from_manual_profile_costs():
    tender = {
        "price": 100000.0,
        "product_profiles": [
            {
                "product_name": "Бумага офисная А4",
                "quantity": 10,
                "unit": "пачка",
                "raw_payload": {
                    "economics": {
                        "unit_cost": 6000,
                        "logistics_cost": 5000,
                        "documents_cost": 2000,
                    }
                },
                "fulfillment_requirements": [
                    {"type": "delivery", "source": "ТЗ.docx", "value": "Срок поставки 5 дней."},
                    {"type": "warranty", "source": "ТЗ.docx", "value": "Гарантия 12 месяцев."},
                    {"type": "acceptance", "source": "ТЗ.docx", "value": "Приемка через ЕИС."},
                ],
            }
        ],
    }

    summary = build_economics_summary(tender)

    assert summary["status"] == "interesting"
    assert summary["revenue"] == 100000.0
    assert summary["supplier_cost"] == 67000.0
    assert summary["risk_reserve_rate_percent"] == 3.5
    assert summary["risk_reserve"] == 3500.0
    assert summary["estimated_total_cost"] == 70500.0
    assert summary["gross_margin"] == 29500.0
    assert summary["margin_percent"] == 29.5
    assert summary["missing_cost_inputs"] == []
    assert summary["items"][0]["total_cost"] == 60000.0
    assert summary["items"][0]["extra_costs"] == 7000.0
    assert "delivery" in summary["risk_types"]


def test_build_economics_summary_requires_manual_costs_before_margin_decision():
    tender = {
        "price": 50000.0,
        "product_profiles": [
            {
                "product_name": "Огнетушитель ОП-5",
                "quantity": 5,
                "unit": "шт",
                "fulfillment_requirements": [{"type": "packaging", "source": "ТЗ.docx", "value": "Заводская упаковка."}],
            }
        ],
    }

    summary = build_economics_summary(tender)

    assert summary["status"] == "needs_costs"
    assert summary["revenue"] == 50000.0
    assert summary["estimated_total_cost"] is None
    assert summary["gross_margin"] is None
    assert summary["margin_percent"] is None
    assert summary["missing_cost_inputs"] == ["Огнетушитель ОП-5"]
    assert summary["recommendation"] == "Нужно добавить закупочную себестоимость по позициям."


def test_build_economics_summary_does_not_assume_single_unit_when_quantity_missing():
    summary = build_economics_summary(
        {
            "price": 19890.0,
            "product_profiles": [
                {
                    "product_name": "Office paper",
                    "quantity": None,
                    "unit": "pack",
                    "raw_payload": {"economics": {"unit_cost": 359.0}},
                }
            ],
        }
    )

    assert summary["status"] == "needs_costs"
    assert summary["supplier_cost"] is None
    assert summary["estimated_total_cost"] is None
    assert summary["missing_cost_inputs"] == ["Office paper"]
    assert summary["items"][0]["quantity"] is None
    assert summary["items"][0]["unit_cost"] == 359.0
    assert summary["items"][0]["total_cost"] is None


def test_build_economics_summary_uses_tender_item_quantity_for_legacy_profile():
    summary = build_economics_summary(
        {
            "price": 19890.0,
            "items": [
                {
                    "position_index": 1,
                    "name": "Office paper A4",
                    "quantity": 60,
                    "unit": "pack",
                    "unit_price": 331.5,
                    "total_price": 19890.0,
                }
            ],
            "product_profiles": [
                {
                    "position_index": 1,
                    "product_name": "Paper tender title",
                    "quantity": None,
                    "unit": None,
                    "raw_payload": {"economics": {"unit_cost": 359.0}},
                }
            ],
        }
    )

    assert summary["status"] == "low_margin"
    assert summary["supplier_cost"] == 21540.0
    assert summary["items"][0]["quantity"] == 60.0
    assert summary["items"][0]["unit"] == "pack"
    assert summary["items"][0]["unit_cost"] == 359.0
    assert summary["items"][0]["total_cost"] == 21540.0


def test_build_economics_summary_returns_bid_thresholds():
    summary = build_economics_summary(
        {
            "price": 100000.0,
            "market_state": {
                "status": "has_current_offer",
                "participant_count": 2,
                "current_offer_price": 90000.0,
                "nmc_price": 100000.0,
            },
            "product_profiles": [
                {
                    "product_name": "Fuel",
                    "quantity": 1000,
                    "raw_payload": {"economics": {"unit_cost": 70, "logistics_cost": 1000}},
                }
            ],
        }
    )

    assert summary["revenue"] == 90000.0
    assert summary["revenue_kind"] == "current_offer"
    assert summary["nmc_price"] == 100000.0
    assert summary["market_state"]["participant_count"] == 2
    assert summary["break_even_price"] == 71000.0
    assert summary["minimum_margin_price"] == 76344.09
    assert summary["interesting_price"] == 83529.41


def test_build_economics_summary_ignores_zero_participant_bid_and_falls_back_to_nmc():
    summary = build_economics_summary(
        {
            "price": 100000.0,
            "market_state": {
                "status": "no_participants",
                "participant_count": 0,
                "bid_count": 0,
                "current_offer_price": 0.0,
                "nmc_price": 100000.0,
            },
            "product_profiles": [
                {
                    "product_name": "Fuel",
                    "quantity": 10,
                    "raw_payload": {"economics": {"unit_cost": 5000}},
                }
            ],
        }
    )

    assert summary["revenue"] == 100000.0
    assert summary["revenue_kind"] == "nmc"
    assert summary["market_state"]["status"] == "no_participants"
    assert summary["market_state"]["current_offer_price"] is None
    assert summary["market_state"]["participant_count"] == 0
    assert summary["market_state"]["bid_count"] == 0
    assert summary["bid_scenarios"][-1]["id"] == "current_nmc"


def test_build_economics_summary_surfaces_analysis_cost_drivers():
    summary = build_economics_summary(
        {
            "price": 100000.0,
            "analysis": {
                "operator_view": {
                    "sections": [
                        {
                            "id": "price_factors",
                            "items": [
                                {
                                    "label": "delivery in 3 working days",
                                    "category": "delivery",
                                    "severity": "high",
                                    "source": "TZ.docx",
                                    "impact": "rush logistics",
                                },
                                {
                                    "label": "certificate package",
                                    "category": "documents",
                                    "severity": "medium",
                                    "source": "TZ.docx",
                                },
                            ],
                        },
                        {
                            "id": "blockers",
                            "items": [
                                {
                                    "label": "contract security",
                                    "category": "financial",
                                    "severity": "medium",
                                    "source": "Contract.pdf",
                                }
                            ],
                        },
                    ]
                }
            },
            "product_profiles": [
                {
                    "product_name": "Fuel",
                    "quantity": 10,
                    "raw_payload": {"economics": {"unit_cost": 1000, "logistics_cost": 1000}},
                }
            ],
        }
    )

    assert [driver["label"] for driver in summary["analysis_cost_drivers"]] == [
        "delivery in 3 working days",
        "certificate package",
        "contract security",
    ]
    assert summary["analysis_cost_drivers"][0]["reserve_hint_percent"] == 2.0
    assert summary["analysis_cost_drivers"][1]["reserve_hint_percent"] == 1.0
    assert summary["analysis_reserve_hint"] == {
        "driver_count": 3,
        "level": "high",
        "rate_percent": 4.0,
    }
    assert summary["risk_reserve_rate_percent"] == 4.0
    assert summary["execution_risk_reserve"] == 4000.0


def test_build_economics_summary_uses_tz_passport_cost_drivers():
    summary = build_economics_summary(
        {
            "price": 100000.0,
            "analysis": {
                "tz_passport": {
                    "version": 1,
                    "sections": [
                        {
                            "id": "price_factors",
                            "title": "Price impact",
                            "items": [
                                {
                                    "label": "urgent delivery window",
                                    "category": "delivery",
                                    "severity": "high",
                                    "source": "TZ.docx",
                                    "value": "5 working days",
                                    "impact": "add logistics reserve",
                                }
                            ],
                        },
                        {
                            "id": "blockers",
                            "title": "Blockers",
                            "items": [
                                {
                                    "label": "contract security",
                                    "category": "financial",
                                    "severity": "high",
                                    "source": "Contract.pdf",
                                    "value": "5%",
                                }
                            ],
                        },
                    ],
                }
            },
            "product_profiles": [
                {
                    "product_name": "Fuel",
                    "quantity": 10,
                    "raw_payload": {"economics": {"unit_cost": 1000, "logistics_cost": 1000}},
                }
            ],
        }
    )

    assert [driver["label"] for driver in summary["analysis_cost_drivers"]] == [
        "urgent delivery window",
        "contract security",
    ]
    assert summary["analysis_cost_drivers"][1]["impact"] == "5%"
    assert summary["analysis_reserve_hint"] == {
        "driver_count": 2,
        "level": "high",
        "rate_percent": 4.0,
    }


def test_build_economics_summary_prefers_analysis_facts_cost_drivers():
    summary = build_economics_summary(
        {
            "price": 100000.0,
            "analysis": {
                "analysis_facts": {
                    "version": 1,
                    "items": [
                        {
                            "label": "национальный режим",
                            "category": "national_regime",
                            "kind": "restriction",
                            "severity": "high",
                            "is_blocker": True,
                            "is_price_factor": False,
                            "impact": "Проверить документы происхождения товара.",
                            "document_name": "ТЗ.docx",
                        },
                        {
                            "label": "срочная поставка",
                            "category": "delivery",
                            "kind": "execution_term",
                            "severity": "medium",
                            "is_blocker": False,
                            "is_price_factor": True,
                            "impact": "Заложить резерв на логистику.",
                            "document_name": "Контракт.pdf",
                        },
                        {
                            "label": "сертификат/декларация",
                            "category": "documents",
                            "kind": "supplier_document",
                            "severity": "medium",
                            "is_blocker": False,
                            "is_price_factor": False,
                            "impact": "Подготовить комплект документов.",
                            "document_name": "ТЗ.docx",
                        },
                    ],
                },
                "tz_passport": {
                    "version": 1,
                    "sections": [
                        {
                            "id": "price_factors",
                            "items": [
                                {
                                    "label": "legacy price factor",
                                    "category": "delivery",
                                    "severity": "high",
                                }
                            ],
                        }
                    ],
                },
            },
            "product_profiles": [
                {
                    "product_name": "Fuel",
                    "quantity": 10,
                    "raw_payload": {"economics": {"unit_cost": 1000, "logistics_cost": 1000}},
                }
            ],
        }
    )

    assert [driver["label"] for driver in summary["analysis_cost_drivers"]] == [
        "национальный режим",
        "срочная поставка",
    ]
    assert summary["analysis_cost_drivers"][0] == {
        "label": "национальный режим",
        "category": "national_regime",
        "severity": "high",
        "source": "ТЗ.docx",
        "impact": "Проверить документы происхождения товара.",
        "reserve_hint_percent": 2.0,
    }
    assert summary["analysis_cost_drivers"][1]["source"] == "Контракт.pdf"
    assert summary["analysis_reserve_hint"] == {
        "driver_count": 2,
        "level": "high",
        "rate_percent": 3.0,
    }


def test_build_economics_summary_applies_analysis_reserve_hint_to_execution_reserve():
    summary = build_economics_summary(
        {
            "price": 100000.0,
            "analysis": {
                "analysis_facts": {
                    "version": 1,
                    "items": [
                        {
                            "label": "короткий срок поставки",
                            "category": "delivery",
                            "severity": "high",
                            "kind": "execution_term",
                            "is_price_factor": True,
                            "document_name": "ТЗ.docx",
                            "source_page": 2,
                            "impact": "Заложить ускоренную логистику.",
                        },
                        {
                            "label": "обеспечение исполнения",
                            "category": "financial",
                            "severity": "medium",
                            "kind": "execution_term",
                            "is_price_factor": True,
                            "document_name": "Контракт.pdf",
                            "source_page": 4,
                            "impact": "Учесть нагрузку на оборотку.",
                        },
                    ],
                }
            },
            "product_profiles": [
                {
                    "product_name": "Fuel",
                    "quantity": 10,
                    "raw_payload": {"economics": {"unit_cost": 5000}},
                }
            ],
        }
    )

    assert summary["analysis_reserve_hint"] == {
        "driver_count": 2,
        "level": "high",
        "rate_percent": 3.0,
    }
    assert summary["execution_risk_reserve"] == 3000.0
    assert summary["risk_reserve_rate_percent"] == 3.0
    assert summary["risk_reserve"] == 3000.0
    assert summary["estimated_total_cost"] == 53000.0
    assert summary["analysis_cost_drivers"][0]["source_label"] == "ТЗ.docx · стр. 2"


def test_build_economics_summary_applies_position_assumptions():
    summary = build_economics_summary(
        {
            "price": 20000.0,
            "product_profiles": [
                {
                    "product_name": "Fuel",
                    "quantity": 10,
                    "raw_payload": {
                        "economics": {"unit_cost": 1000, "logistics_cost": 1000},
                        "economics_assumptions": {
                            "vat_mode": "vat_excluded",
                            "vat_rate_percent": 20,
                            "risk_reserve_percent": 5,
                            "target_margin_percent": 15,
                        },
                    },
                }
            ],
        }
    )

    item = summary["items"][0]
    assert item["total_cost"] == 10000.0
    assert item["extra_costs"] == 1000.0
    assert item["vat_cost"] == 2200.0
    assert item["position_risk_reserve"] == 660.0
    assert item["estimated_total_cost"] == 13860.0
    assert item["target_margin_percent"] == 15.0
    assert item["target_price"] == 16305.88
    assert summary["supplier_cost"] == 13860.0
    assert summary["risk_reserve"] == 660.0
    assert summary["risk_reserve_rate_percent"] == 5.0
    assert summary["break_even_price"] == 13860.0


def test_build_economics_summary_returns_bid_scenarios():
    summary = build_economics_summary(
        {
            "price": 20000.0,
            "product_profiles": [
                {
                    "product_name": "Fuel",
                    "quantity": 10,
                    "raw_payload": {
                        "economics": {"unit_cost": 1000, "logistics_cost": 1000},
                        "economics_assumptions": {
                            "vat_mode": "vat_excluded",
                            "vat_rate_percent": 20,
                            "risk_reserve_percent": 5,
                            "target_margin_percent": 20,
                        },
                    },
                }
            ],
        }
    )

    assert summary["target_margin_percent"] == 20.0
    assert summary["target_bid_price"] == 17325.0
    assert summary["participation_decision"] == {
        "status": "can_bid",
        "label": "Можно заходить",
        "limit_price": 17325.0,
        "recommendation": "НМЦК выше целевой цены. Можно участвовать, если поставщик и условия подтверждены.",
    }
    assert summary["bid_scenarios"] == [
        {
            "id": "break_even",
            "label": "Безубыток",
            "price": 13860.0,
            "margin_amount": 0.0,
            "margin_percent": 0.0,
        },
        {
            "id": "minimum_margin",
            "label": "Минимум",
            "price": 14903.23,
            "margin_amount": 1043.23,
            "margin_percent": 7.0,
        },
        {
            "id": "target",
            "label": "Цель",
            "price": 17325.0,
            "margin_amount": 3465.0,
            "margin_percent": 20.0,
        },
        {
            "id": "interesting",
            "label": "Интересно",
            "price": 16305.88,
            "margin_amount": 2445.88,
            "margin_percent": 15.0,
        },
        {
            "id": "current_nmc",
            "label": "НМЦК",
            "price": 20000.0,
            "margin_amount": 6140.0,
            "margin_percent": 30.7,
        },
    ]


def test_build_economics_summary_returns_guarded_participation_decision():
    summary = build_economics_summary(
        {
            "price": 16000.0,
            "product_profiles": [
                {
                    "product_name": "Fuel",
                    "quantity": 10,
                    "raw_payload": {
                        "economics": {"unit_cost": 1000, "logistics_cost": 1000},
                        "economics_assumptions": {
                            "vat_mode": "vat_excluded",
                            "vat_rate_percent": 20,
                            "risk_reserve_percent": 5,
                            "target_margin_percent": 20,
                        },
                    },
                }
            ],
        }
    )

    assert summary["participation_decision"] == {
        "status": "guarded_bid",
        "label": "Только с лимитом",
        "limit_price": 14903.23,
        "recommendation": "НМЦК ниже целевой цены. Участвовать только если не снижаться ниже минимальной цены.",
    }


def test_build_economics_summary_returns_low_margin_decision():
    summary = build_economics_summary(
        {
            "price": 14500.0,
            "product_profiles": [
                {
                    "product_name": "Fuel",
                    "quantity": 10,
                    "raw_payload": {
                        "economics": {"unit_cost": 1000, "logistics_cost": 1000},
                        "economics_assumptions": {
                            "vat_mode": "vat_excluded",
                            "vat_rate_percent": 20,
                            "risk_reserve_percent": 5,
                            "target_margin_percent": 20,
                        },
                    },
                }
            ],
        }
    )

    assert summary["participation_decision"] == {
        "status": "low_margin",
        "label": "Низкая маржа",
        "limit_price": 13860.0,
        "recommendation": "НМЦК покрывает себестоимость, но не дает минимальную маржу. Участвовать рискованно.",
    }


def test_build_economics_summary_returns_missing_costs_decision():
    summary = build_economics_summary(
        {
            "price": 50000.0,
            "product_profiles": [{"product_name": "Fuel", "quantity": 10}],
        }
    )

    assert summary["participation_decision"] == {
        "status": "needs_costs",
        "label": "Не хватает цен",
        "limit_price": None,
        "recommendation": "Добавьте себестоимость по позициям, чтобы принять решение по участию.",
    }
