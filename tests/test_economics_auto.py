from __future__ import annotations

from tender_killer.economics_auto import build_auto_economics_estimate
from tender_killer.economics_service import accept_profile_auto_economics
from tender_killer.economics_service import update_profile_auto_economics
from tender_killer.models import ProductProfile
from tender_killer.models import Tender
from tender_killer.storage import TenderStore
from tender_killer.tender_detail_service import get_tender_payload


def test_build_auto_economics_estimate_uses_selected_supplier_and_cost_drivers():
    profile = {
        "product_name": "Office paper",
        "quantity": 10,
        "unit": "pack",
        "fulfillment_requirements": [
            {"type": "delivery", "source": "TZ.docx", "value": "Delivery and unloading required."},
            {"type": "warranty", "source": "TZ.docx", "value": "Warranty replacement required."},
        ],
        "raw_payload": {
            "selected_supplier_option_index": 1,
            "supplier_options": [
                {"name": "Expensive paper", "unit_price": 1200.0, "status": "candidate"},
                {"name": "Best paper", "unit_price": 900.0, "status": "selected"},
            ],
        },
    }

    estimate = build_auto_economics_estimate(
        profile,
        [{"name": "TZ.docx", "text_content": "Срок поставки 3 дня. Требуется сертификат. НДС не указан."}],
    )

    assert estimate["status"] == "needs_review"
    assert estimate["base_source"] == "selected_supplier"
    assert estimate["estimated_unit_cost"] == 900.0
    assert estimate["base_total_cost"] == 9000.0
    assert estimate["hidden_costs_total"] > 0
    assert estimate["estimated_total_cost"] > 9000.0
    assert estimate["tax_mode"] == "unknown"
    assert "НДС не определен" in estimate["needs_review"]
    assert {driver["type"] for driver in estimate["cost_drivers"]} >= {"delivery", "warranty", "certificates", "short_deadline"}


def test_build_auto_economics_estimate_uses_best_supplier_when_none_selected():
    profile = {
        "product_name": "Office paper",
        "quantity": 10,
        "unit": "pack",
        "raw_payload": {
            "supplier_options": [
                {"name": "Expensive paper", "unit_price": 1200.0, "status": "candidate", "availability": "in_stock"},
                {"name": "Rejected cheap", "unit_price": 500.0, "status": "rejected", "availability": "in_stock"},
                {"name": "Best paper", "unit_price": 900.0, "status": "suitable", "availability": "on_request"},
            ],
        },
    }

    estimate = build_auto_economics_estimate(profile, [])

    assert estimate["base_source"] == "best_supplier_option"
    assert estimate["estimated_unit_cost"] == 900.0
    assert estimate["evidence"][0] == {"source": "best_supplier_option", "value": "Best paper"}


def test_update_profile_auto_economics_persists_draft_without_overwriting_manual_inputs(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="auto-economics",
            url="https://market.mosreg.ru/Trade/ViewTrade/auto-economics",
            title="Paper tender",
            price=100000.0,
        )
    )
    store.upsert_product_profiles(
        "mosreg_market",
        "auto-economics",
        [
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="auto-economics",
                position_index=1,
                product_name="Office paper",
                quantity=10,
                unit="pack",
                raw_payload={
                    "economics": {"unit_cost": 1000.0},
                    "selected_supplier_option_index": 0,
                    "supplier_options": [{"name": "Best paper", "unit_price": 900.0, "status": "selected"}],
                },
            )
        ],
    )

    payload = update_profile_auto_economics(
        store.database_path,
        "mosreg_market",
        "auto-economics",
        1,
        [{"name": "TZ.docx", "text_content": "Поставка и разгрузка. НДС включен."}],
    )

    assert payload["ok"] is True
    detail = get_tender_payload(store.database_path, "mosreg_market", "auto-economics")
    raw_payload = detail["product_profiles"][0]["raw_payload"]
    assert raw_payload["economics"] == {"unit_cost": 1000.0}
    assert raw_payload["economics_auto"]["estimated_unit_cost"] == 900.0
    assert raw_payload["economics_auto"]["manual_inputs_present"] is True
    assert detail["economics"]["supplier_cost"] == 10000.0


def test_update_profile_auto_economics_prefills_empty_assumptions_from_estimate(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="auto-economics-assumptions",
            url="https://market.mosreg.ru/Trade/ViewTrade/auto-economics-assumptions",
            title="Paper tender",
            price=100000.0,
        )
    )
    store.upsert_product_profiles(
        "mosreg_market",
        "auto-economics-assumptions",
        [
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="auto-economics-assumptions",
                position_index=1,
                product_name="Office paper",
                quantity=10,
                unit="pack",
                raw_payload={
                    "selected_supplier_option_index": 0,
                    "supplier_options": [{"name": "Best paper", "unit_price": 900.0, "status": "selected"}],
                },
            )
        ],
    )

    update_profile_auto_economics(
        store.database_path,
        "mosreg_market",
        "auto-economics-assumptions",
        1,
        [{"name": "TZ.docx", "text_content": "Цена указана без учета НДС. Требуется проверка документов."}],
    )

    detail = get_tender_payload(store.database_path, "mosreg_market", "auto-economics-assumptions")
    raw_payload = detail["product_profiles"][0]["raw_payload"]
    assert raw_payload["economics_assumptions"] == {
        "vat_mode": "vat_excluded",
        "vat_rate_percent": 20.0,
        "risk_reserve_percent": 1.0,
        "target_margin_percent": 15.0,
    }


def test_update_profile_auto_economics_keeps_manual_assumptions(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="auto-economics-manual-assumptions",
            url="https://market.mosreg.ru/Trade/ViewTrade/auto-economics-manual-assumptions",
            title="Paper tender",
            price=100000.0,
        )
    )
    store.upsert_product_profiles(
        "mosreg_market",
        "auto-economics-manual-assumptions",
        [
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="auto-economics-manual-assumptions",
                position_index=1,
                product_name="Office paper",
                quantity=10,
                unit="pack",
                raw_payload={
                    "economics_assumptions": {
                        "vat_mode": "no_vat",
                        "risk_reserve_percent": 3.0,
                        "target_margin_percent": 25.0,
                    },
                    "selected_supplier_option_index": 0,
                    "supplier_options": [{"name": "Best paper", "unit_price": 900.0, "status": "selected"}],
                },
            )
        ],
    )

    update_profile_auto_economics(
        store.database_path,
        "mosreg_market",
        "auto-economics-manual-assumptions",
        1,
        [{"name": "TZ.docx", "text_content": "Цена указана без учета НДС."}],
    )

    detail = get_tender_payload(store.database_path, "mosreg_market", "auto-economics-manual-assumptions")
    assert detail["product_profiles"][0]["raw_payload"]["economics_assumptions"] == {
        "vat_mode": "no_vat",
        "risk_reserve_percent": 3.0,
        "target_margin_percent": 25.0,
    }


def test_accept_profile_auto_economics_moves_draft_to_working_economics(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="accept-auto-economics",
            url="https://market.mosreg.ru/Trade/ViewTrade/accept-auto-economics",
            title="Paper tender",
            price=50000.0,
        )
    )
    store.upsert_product_profiles(
        "mosreg_market",
        "accept-auto-economics",
        [
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="accept-auto-economics",
                position_index=1,
                product_name="Office paper",
                quantity=10,
                unit="pack",
                raw_payload={
                    "economics_auto": {
                        "estimated_unit_cost": 900.0,
                        "hidden_costs_total": 450.0,
                        "risk_reserve": 100.0,
                        "cost_drivers": [
                            {"type": "delivery", "amount": 135.0},
                            {"type": "unloading", "amount": 45.0},
                            {"type": "certificates", "amount": 90.0},
                            {"type": "warranty", "amount": 180.0},
                        ],
                    }
                },
            )
        ],
    )

    payload = accept_profile_auto_economics(store.database_path, "mosreg_market", "accept-auto-economics", 1)

    assert payload["ok"] is True
    detail = get_tender_payload(store.database_path, "mosreg_market", "accept-auto-economics")
    profile = detail["product_profiles"][0]
    assert profile["profile_status"] == "priced"
    assert profile["raw_payload"]["economics"] == {
        "unit_cost": 900.0,
        "logistics_cost": 180.0,
        "documents_cost": 90.0,
        "other_costs": 280.0,
    }
    assert profile["raw_payload"]["economics_auto"]["estimated_unit_cost"] == 900.0
    assert profile["raw_payload"]["economics_acceptance"] == {
        "source": "auto_estimate",
        "accepted": True,
    }
    assert detail["economics"]["supplier_cost"] == 9550.0
