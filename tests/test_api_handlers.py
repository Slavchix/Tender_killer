from tender_killer.api_handlers import handle_get_request, handle_post_request
from tender_killer.models import ProductProfile, Tender
from tender_killer.storage import TenderStore


def _store_with_tender(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="3668200",
            url="https://market.mosreg.ru/Trade/ViewTrade/3668200",
            title="Paper supply",
            customer="School",
            region="Moscow Oblast",
            price=120000.0,
            status="Reception of proposals",
            raw_payload={"SourcePlatformName": "ЕАСУЗ 44"},
        )
    )
    return store


def test_handle_get_request_returns_health_payload(tmp_path) -> None:
    response = handle_get_request(tmp_path / "tenders.sqlite", "/api/health", {})

    assert response.kind == "json"
    assert response.status == 200
    assert response.payload == {"ok": True}


def test_handle_get_request_routes_tender_detail(tmp_path) -> None:
    store = _store_with_tender(tmp_path)

    response = handle_get_request(store.database_path, "/api/tenders/mosreg_market/3668200", {})

    assert response.kind == "json"
    assert response.status == 200
    assert response.payload["source"] == "mosreg_market"
    assert response.payload["external_id"] == "3668200"


def test_handle_post_request_routes_workflow_update(tmp_path) -> None:
    store = _store_with_tender(tmp_path)

    response = handle_post_request(
        store.database_path,
        "/api/tenders/mosreg_market/3668200/workflow",
        {"workflow_status": "interesting", "workflow_note": "check margin"},
    )

    assert response.status == 200
    assert response.payload["workflow_status"] == "interesting"
    assert response.payload["workflow_note"] == "check margin"


def test_handle_post_request_routes_product_profile_economics_update(tmp_path) -> None:
    store = _store_with_tender(tmp_path)
    store.upsert_product_profiles(
        "mosreg_market",
        "3668200",
        [
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="3668200",
                position_index=1,
                product_name="Office paper",
                quantity=10,
                unit="pack",
            )
        ],
    )

    response = handle_post_request(
        store.database_path,
        "/api/tenders/mosreg_market/3668200/product-profiles/1/economics",
        {"unit_cost": 6000, "logistics_cost": 5000},
    )

    assert response.status == 200
    assert response.payload["product_profiles"][0]["raw_payload"]["economics"] == {
        "unit_cost": 6000.0,
        "logistics_cost": 5000.0,
    }
    assert response.payload["economics"]["supplier_cost"] == 65000.0


def test_handle_request_reports_invalid_tender_route(tmp_path) -> None:
    response = handle_get_request(tmp_path / "tenders.sqlite", "/api/tenders/mosreg_market/3668200/extra", {})

    assert response.status == 400
    assert response.payload == {"error": "invalid tender path"}
