from __future__ import annotations

from tender_killer.market_state import extract_market_state


def test_extract_market_state_uses_moscow_last_bet_as_current_offer() -> None:
    state = extract_market_state(
        {
            "source": "moscow_supplier_portal",
            "price": 14700.0,
            "raw_payload": {
                "__detail": {
                    "startCost": 14700.0,
                    "lastBetCost": 9996.0,
                    "nextCost": 9922.5,
                    "uniqueSupplierCount": 5,
                    "lastBetSupplier": {"name": "Supplier A"},
                    "bets": [{"cost": 9996.0}],
                }
            },
        }
    )

    assert state == {
        "status": "has_current_offer",
        "participant_count": 5,
        "bid_count": 1,
        "has_participants": True,
        "current_offer_price": 9996.0,
        "next_bid_price": 9922.5,
        "nmc_price": 14700.0,
        "price_source": "moscow_last_bet",
        "last_offer_supplier": "Supplier A",
    }


def test_extract_market_state_reports_mosreg_without_participants() -> None:
    state = extract_market_state(
        {
            "source": "mosreg_market",
            "price": 200106.0,
            "raw_payload": {
                "InitialPrice": 200106.0,
                "ApplicationsCount": 0,
            },
        }
    )

    assert state["status"] == "no_participants"
    assert state["participant_count"] == 0
    assert state["bid_count"] == 0
    assert state["has_participants"] is False
    assert state["current_offer_price"] is None
    assert state["nmc_price"] == 200106.0


def test_extract_market_state_reports_participants_without_public_price() -> None:
    state = extract_market_state(
        {
            "source": "moscow_supplier_portal",
            "price": 156000.0,
            "raw_payload": {
                "__detail": {
                    "startCost": 156000.0,
                    "lastBetCost": None,
                    "uniqueSupplierCount": 1,
                    "bets": [],
                }
            },
        }
    )

    assert state["status"] == "participants_without_public_price"
    assert state["participant_count"] == 1
    assert state["bid_count"] == 0
    assert state["current_offer_price"] is None


def test_extract_market_state_ignores_zero_bid_price_without_participants() -> None:
    state = extract_market_state(
        {
            "source": "moscow_supplier_portal",
            "price": 38970.0,
            "raw_payload": {
                "__detail": {
                    "startCost": 38970.0,
                    "lastBetCost": 0,
                    "nextCost": 0,
                    "uniqueSupplierCount": 0,
                    "bets": [{"cost": 0}],
                }
            },
        }
    )

    assert state["status"] == "no_participants"
    assert state["participant_count"] == 0
    assert state["bid_count"] == 0
    assert state["current_offer_price"] is None
    assert state["next_bid_price"] is None
    assert state["price_source"] is None


def test_extract_market_state_uses_lowest_moscow_bid_and_counts_bids() -> None:
    state = extract_market_state(
        {
            "source": "moscow_supplier_portal",
            "price": 48_460.0,
            "raw_payload": {
                "__detail": {
                    "startCost": 48_460.0,
                    "lastBetCost": 47_900.0,
                    "uniqueSupplierCount": 2,
                    "bets": [
                        {"cost": 47_900.0, "supplier": {"id": 1, "name": "A"}},
                        {"cost": 47_100.0, "supplier": {"id": 2, "name": "B"}},
                        {"cost": 47_500.0, "supplier": {"id": 1, "name": "A"}},
                    ],
                }
            },
        }
    )

    assert state["status"] == "has_current_offer"
    assert state["current_offer_price"] == 47_100.0
    assert state["price_source"] == "moscow_bets_min"
    assert state["participant_count"] == 2
    assert state["bid_count"] == 3


def test_extract_market_state_uses_completed_moscow_session_last_price() -> None:
    state = extract_market_state(
        {
            "source": "moscow_supplier_portal",
            "price": 13560.0,
            "raw_payload": {
                "__detail": {
                    "state": {"name": "Проведена", "id": 19000004},
                    "startCost": 13560.0,
                    "lastBetCost": 13492.2,
                    "lastBetSupplier": {"name": "ИП ТИТОВА АНАСТАСИЯ МИХАЙЛОВНА"},
                    "uniqueSupplierCount": 1,
                    "bets": [{"cost": 13492.2}],
                },
            },
        }
    )

    assert state["status"] == "has_current_offer"
    assert state["current_offer_price"] == 13492.2
    assert state["nmc_price"] == 13560.0
    assert state["participant_count"] == 1
    assert state["bid_count"] == 1
    assert state["last_offer_supplier"] == "ИП ТИТОВА АНАСТАСИЯ МИХАЙЛОВНА"


def test_extract_market_state_estimates_active_moscow_bid_when_public_detail_hides_bets() -> None:
    state = extract_market_state(
        {
            "source": "moscow_supplier_portal",
            "price": 48_460.0,
            "raw_payload": {
                "__detail": {
                    "state": {"name": "Активная", "id": 19000002},
                    "startCost": 48_460.0,
                    "lastBetCost": None,
                    "nextCost": None,
                    "uniqueSupplierCount": 1,
                    "bets": [],
                }
            },
        }
    )

    assert state["status"] == "has_current_offer"
    assert state["current_offer_price"] == 48_217.7
    assert state["price_source"] == "moscow_public_step_estimate"
    assert state["participant_count"] == 1
    assert state["bid_count"] == 1


def test_extract_market_state_uses_imported_moscow_get_bet_update_payload() -> None:
    state = extract_market_state(
        {
            "source": "moscow_supplier_portal",
            "price": 48_460.0,
            "raw_payload": {
                "__detail": {
                    "state": {"name": "Активная", "id": 19000002},
                    "startCost": 48_460.0,
                    "lastBetCost": None,
                    "uniqueSupplierCount": 1,
                    "bets": [],
                },
                "__market_state_import": {
                    "source": "zakupki_mos_get_bet_update",
                    "lastBetCost": 48_217.7,
                    "nextCost": 47_975.4,
                    "uniqueSupplierCount": 1,
                    "lastBetSupplier": {"name": "Другой участник"},
                    "rowVersion": "AAAAAvAo3L0=",
                },
            },
        }
    )

    assert state["status"] == "has_current_offer"
    assert state["current_offer_price"] == 48_217.7
    assert state["next_bid_price"] == 47_975.4
    assert state["price_source"] == "moscow_get_bet_update_import"
    assert state["participant_count"] == 1
    assert state["bid_count"] == 1
    assert state["last_offer_supplier"] == "Другой участник"
