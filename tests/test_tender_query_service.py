from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

from tender_killer.models import ProductProfile
from tender_killer.models import Tender
from tender_killer.models import TenderDocument
from tender_killer.storage import TenderStore
from tender_killer.tender_query_service import list_tenders_payload


def test_tender_query_service_returns_total_limit_and_offset(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    for index in range(3):
        store.upsert_tender(
            Tender(
                source="mosreg_market",
                external_id=f"mo-{index}",
                url=f"https://example.test/mo-{index}",
                title=f"Paper tender {index}",
                published_at=datetime(2026, 5, 20 + index, tzinfo=UTC),
            )
        )

    payload = list_tenders_payload(store.database_path, {"limit": "1", "offset": "1"})

    assert payload["total"] == 3
    assert payload["limit"] == 1
    assert payload["offset"] == 1
    assert payload["has_previous"] is True
    assert payload["previous_offset"] == 0
    assert payload["has_next"] is True
    assert payload["next_offset"] == 2
    assert len(payload["items"]) == 1
    assert payload["items"][0]["external_id"] == "mo-1"
    assert payload["items"][0]["decision"] is None


def test_tender_query_service_includes_market_state_and_saved_economics(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="moscow_supplier_portal",
            external_id="Auction10206191",
            url="https://zakupki.mos.ru/auction/10206191",
            title="Auction with current offer",
            price=100000.0,
            raw_payload={
                "__detail": {
                    "startCost": 100000.0,
                    "lastBetCost": 90000.0,
                    "uniqueSupplierCount": 2,
                }
            },
        )
    )
    store.upsert_product_profiles(
        "moscow_supplier_portal",
        "Auction10206191",
        [
            ProductProfile(
                tender_source="moscow_supplier_portal",
                tender_external_id="Auction10206191",
                position_index=1,
                product_name="Office paper",
                quantity=10,
                unit="pack",
                raw_payload={"economics": {"unit_cost": 6000.0, "logistics_cost": 5000.0}},
            )
        ],
    )

    payload = list_tenders_payload(store.database_path, {})
    item = payload["items"][0]

    assert item["market_state"]["status"] == "has_current_offer"
    assert item["market_state"]["participant_count"] == 2
    assert item["market_state"]["current_offer_price"] == 90000.0
    assert item["economics"]["revenue"] == 90000.0
    assert item["economics"]["revenue_kind"] == "current_offer"
    assert item["economics"]["participation_decision"]["status"] == "can_bid"
    assert item["decision"]["status"] == "interesting"


def test_tender_query_service_decision_metrics_use_persisted_document_text_counts(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="doc-metrics",
            url="https://example.test/doc-metrics",
            title="Tender with document metrics",
            price=100000.0,
            document_records=[
                TenderDocument(url="https://example.test/spec.docx", name="spec.docx"),
                TenderDocument(url="https://example.test/contract.pdf", name="contract.pdf"),
            ],
        )
    )
    with store._connect() as connection:
        connection.execute(
            """
            UPDATE tender_documents
            SET text_status = 'ok', text_content = 'extracted text'
            WHERE source = ? AND external_id = ? AND url = ?
            """,
            ("mosreg_market", "doc-metrics", "https://example.test/spec.docx"),
        )
    store.upsert_product_profiles(
        "mosreg_market",
        "doc-metrics",
        [
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="doc-metrics",
                position_index=1,
                product_name="Office paper",
                quantity=10,
                raw_payload={"economics": {"unit_cost": 6000.0}},
            )
        ],
    )

    payload = list_tenders_payload(store.database_path, {})
    metrics = payload["items"][0]["decision"]["metrics"]

    assert metrics["documents_total"] == 2
    assert metrics["documents_ready"] == 1


def test_tender_query_service_includes_operator_decision_for_dashboard_attention(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="moscow_supplier_portal",
            external_id="Auction10220001",
            url="https://zakupki.mos.ru/auction/10220001",
            title="Tender with operator blockers",
            price=50000.0,
        )
    )
    raw_payload = {
        "analysis_facts": {
            "version": 1,
            "items": [
                {
                    "id": "blocker:certificate",
                    "kind": "blocker",
                    "label": "сертификат/декларация",
                    "is_blocker": True,
                    "is_price_factor": False,
                }
            ],
            "metrics": {"total": 1, "blockers": 1, "price_factors": 0, "unbound": 0},
        },
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
                    "items": [{"label": "сертификат/декларация"}],
                }
            ],
        }
    }
    with store._connect() as connection:
        connection.execute(
            """
            INSERT INTO tender_analysis (
                source, external_id, summary, requirements_json, risks_json,
                red_flags_json, recommended_status, confidence, raw_payload_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "moscow_supplier_portal",
                "Auction10220001",
                "Analysis summary",
                "[]",
                "[]",
                "[]",
                "needs_review",
                0.9,
                json.dumps(raw_payload, ensure_ascii=False),
            ),
        )

    payload = list_tenders_payload(store.database_path, {})
    item = payload["items"][0]

    assert item["analysis"]["operator_view"]["version"] == 2
    assert item["analysis"]["analysis_facts"]["version"] == 1
    assert item["analysis"]["analysis_facts"]["metrics"]["blockers"] == 1
    assert item["decision"]["status"] == "needs_review"
    assert item["decision"]["blockers"] == ["сертификат/декларация"]


def test_tender_query_service_filters_with_normalized_columns(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="match",
            url="https://example.test/match",
            title="Paper supply",
            region="Moscow Oblast",
            status="Reception of proposals",
            raw_payload={
                "federalLawName": "44-FZ",
                "customers": [{"inn": "5047152960"}],
                "tradeType": 1,
            },
        )
    )
    store.upsert_tender(
        Tender(
            source="moscow_supplier_portal",
            external_id="skip",
            url="https://example.test/skip",
            title="Paper supply",
            region="Moscow",
            status="Completed",
            raw_payload={"federalLawName": "223-FZ"},
        )
    )

    payload = list_tenders_payload(
        store.database_path,
        {
            "source_family": "mosreg",
            "status": "active",
            "region": "MO",
            "procedure_type": "electronic_shop",
            "customer_inn": "5047152960",
        },
    )

    assert payload["total"] == 1
    assert payload["items"][0]["external_id"] == "match"


def test_tender_query_service_active_status_hides_expired_deadlines(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    now = datetime.now(UTC)
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="expired",
            url="https://example.test/expired",
            title="Expired active-looking tender",
            status="Прием предложений",
            deadline_at=now - timedelta(days=1),
        )
    )
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="actual",
            url="https://example.test/actual",
            title="Actual tender",
            status="Прием предложений",
            deadline_at=now + timedelta(days=1),
        )
    )

    payload = list_tenders_payload(store.database_path, {"status": "active"})

    assert payload["total"] == 1
    assert payload["items"][0]["external_id"] == "actual"


def test_tender_query_service_active_status_hides_expired_moscow_local_deadlines(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    local_now = datetime.now()
    store.upsert_tender(
        Tender(
            source="moscow_supplier_portal",
            external_id="expired-moscow",
            url="https://example.test/expired-moscow",
            title="Expired Moscow tender",
            status="Активная",
            deadline_at=local_now - timedelta(hours=1),
        )
    )
    store.upsert_tender(
        Tender(
            source="moscow_supplier_portal",
            external_id="actual-moscow",
            url="https://example.test/actual-moscow",
            title="Actual Moscow tender",
            status="Активная",
            deadline_at=local_now + timedelta(hours=1),
        )
    )

    payload = list_tenders_payload(store.database_path, {"source": "moscow_supplier_portal", "status": "active"})

    assert payload["total"] == 1
    assert payload["items"][0]["external_id"] == "actual-moscow"


def test_tender_query_service_expands_construction_material_search_query(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="materials",
            url="https://example.test/materials",
            title="Поставка материалов для ремонта помещений",
            status="Прием предложений",
        )
    )

    payload = list_tenders_payload(store.database_path, {"q": "строительные материалы"})

    assert payload["total"] == 1
    assert payload["items"][0]["external_id"] == "materials"


def test_tender_query_service_does_not_match_expanded_query_only_in_raw_payload(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="fuel",
            url="https://example.test/fuel",
            title="Поставка автомобильного бензина",
            status="Прием предложений",
            raw_payload={"note": "материал заказчика"},
        )
    )

    payload = list_tenders_payload(store.database_path, {"q": "строительные материалы"})

    assert payload["total"] == 0


def test_tender_query_service_does_not_treat_generic_information_materials_as_construction(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="media",
            url="https://example.test/media",
            title="Оказание услуг по выпуску информационных материалов",
            status="Прием предложений",
        )
    )

    payload = list_tenders_payload(store.database_path, {"q": "строительные материалы"})

    assert payload["total"] == 0


def test_tender_query_service_does_not_treat_repair_works_as_materials(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="road-works",
            url="https://example.test/road-works",
            title="Выполнение работ по текущему ремонту автомобильной дороги",
            status="Прием предложений",
        )
    )

    payload = list_tenders_payload(store.database_path, {"q": "строительные материалы"})

    assert payload["total"] == 0
