from __future__ import annotations

from tender_killer.product_profile_service import product_profile_summary, rebuild_product_profiles
from tender_killer.storage import TenderStore


def test_product_profile_summary_counts_known_statuses_only():
    summary = product_profile_summary(
        [
            {"profile_status": "ready"},
            {"profile_status": "ready"},
            {"profile_status": "needs_review"},
            {"profile_status": "unknown"},
            {},
        ]
    )

    assert summary == {
        "total": 5,
        "draft": 0,
        "needs_review": 1,
        "ready": 2,
        "searching": 0,
        "matched": 0,
        "priced": 0,
        "rejected": 0,
    }


def test_rebuild_product_profiles_persists_profiles(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    tender_payload = {
        "source": "mosreg_market",
        "external_id": "bulk",
        "title": "Bulk tender",
        "customer": "School",
        "items": [
            {"name": "Бумага офисная А4", "quantity": 10, "unit": "пачка", "okpd2": "17.12.14.110"},
            {"name": "Папка-вкладыш", "quantity": 100, "unit": "шт", "okpd2": "22.29.25.000"},
        ],
        "document_records": [],
    }

    result = rebuild_product_profiles(store.database_path, "mosreg_market", "bulk", tender_payload)

    assert result["ok"] is True
    assert result["summary"]["total"] == 2
    assert result["summary"]["ready"] == 2
    assert [profile["product_name"] for profile in result["product_profiles"]] == [
        "Бумага офисная А4",
        "Папка-вкладыш",
    ]
    assert len(store.get_product_profiles("mosreg_market", "bulk")) == 2
