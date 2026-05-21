from __future__ import annotations

import pytest

from tender_killer.database_view_service import get_database_table_payload
from tender_killer.database_view_service import list_database_tables_payload
from tender_killer.models import Tender
from tender_killer.storage import TenderStore


def test_database_view_service_lists_allowed_tables_and_reads_rows(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="3668200",
            url="https://market.mosreg.ru/Trade/ViewTrade/3668200",
            title="Поставка бумаги",
            customer="Школа",
        )
    )

    tables = list_database_tables_payload(store.database_path)
    tenders = get_database_table_payload(store.database_path, "tenders", {"limit": "10", "q": "бумаги"})

    assert {"name": "tenders", "rows": 1} in tables["tables"]
    assert tenders["table"] == "tenders"
    assert "external_id" in tenders["columns"]
    assert tenders["total"] == 1
    assert tenders["rows"][0]["external_id"] == "3668200"


def test_database_view_service_rejects_non_allowlisted_tables(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()

    with pytest.raises(KeyError, match="not allowed"):
        get_database_table_payload(store.database_path, "sqlite_master", {})
