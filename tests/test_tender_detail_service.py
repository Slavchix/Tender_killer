from __future__ import annotations

from tender_killer.models import Tender
from tender_killer.models import TenderDocument
from tender_killer.models import TenderItem
from tender_killer.storage import TenderStore
from tender_killer.tender_detail_service import get_tender_payload
from tender_killer.tender_detail_service import refresh_tender_detail_payload


def test_refresh_tender_detail_payload_saves_detail_and_rebuilds_profiles(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="3668200",
            url="https://market.mosreg.ru/Trade/ViewTrade/3668200",
            title="Paper tender",
            raw_payload={"Id": 3668200},
        )
    )

    class DetailAdapter:
        source = "mosreg_market"

        def enrich_payload(self, payload):
            enriched = dict(payload)
            enriched["__detail"] = {"loaded": True}
            return enriched

        def normalize_payload(self, payload):
            return Tender(
                source="mosreg_market",
                external_id="3668200",
                url="https://market.mosreg.ru/Trade/ViewTrade/3668200",
                title="Paper tender detail",
                raw_payload=payload,
                items=[
                    TenderItem(
                        name="Office paper",
                        quantity=10.0,
                        unit="pack",
                        okpd2="17.12.14.110",
                    )
                ],
                document_records=[
                    TenderDocument(
                        url="https://example.test/tz.docx",
                        name="tz.docx",
                        document_type="technical specification",
                    )
                ],
            )

    response = refresh_tender_detail_payload(
        store.database_path,
        "mosreg_market",
        "3668200",
        adapter=DetailAdapter(),
    )

    assert response["ok"] is True
    assert response["refreshed"] is True
    assert response["summary"]["items_count"] == 1
    assert response["summary"]["documents_count"] == 1
    assert response["summary"]["product_profiles_count"] == 1
    assert response["tender"]["items"][0]["name"] == "Office paper"
    assert response["tender"]["document_records"][0]["name"] == "tz.docx"

    detail = get_tender_payload(store.database_path, "mosreg_market", "3668200")
    assert detail["product_profile_summary"]["total"] == 1
    assert detail["product_profiles"][0]["product_name"] == "Office paper"
