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


def test_build_economics_summary_returns_bid_thresholds():
    summary = build_economics_summary(
        {
            "price": 100000.0,
            "current_offer_price": 90000.0,
            "product_profiles": [
                {
                    "product_name": "Fuel",
                    "quantity": 1000,
                    "raw_payload": {"economics": {"unit_cost": 70, "logistics_cost": 1000}},
                }
            ],
        }
    )

    assert summary["revenue"] == 100000.0
    assert summary["break_even_price"] == 71000.0
    assert summary["minimum_margin_price"] == 76344.09
    assert summary["interesting_price"] == 83529.41


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
    assert summary["break_even_price"] == 13860.0
