from __future__ import annotations

import importlib
import importlib.util


def _customer_eis_service():
    spec = importlib.util.find_spec("tender_killer.reports_customer_eis")
    assert spec is not None
    return importlib.import_module("tender_killer.reports_customer_eis")


def _flat_text(elements: list[tuple[str, object, str]]) -> str:
    parts: list[str] = []
    for kind, payload, _style in elements:
        if kind == "table":
            for row in payload:
                parts.extend(str(value) for value in row)
        else:
            parts.append(str(payload))
    return "\n".join(parts)


def test_customer_eis_elements_render_risk_summary_signals_and_links():
    service = _customer_eis_service()

    elements = service.customer_eis_elements(
        {
            "customer": "School",
            "customer_risk_profile": {
                "level": "high",
                "score": 72,
                "customer": {"name": "School", "inn": "5047152960"},
                "history": {"total": 4},
                "factors": [
                    {"severity": "high", "evidence": "Terminated contracts: 3."},
                    {"severity": "medium", "evidence": "Local history has tenders without participants."},
                ],
            },
            "eis_reference": {
                "network_fetch_enabled": False,
                "identifiers": {
                    "purchase_number": "0373200000126000012",
                    "customer_inn": "5047152960",
                },
                "links": [
                    {
                        "id": "eis_purchase_search",
                        "label": "EIS purchase search",
                        "url": "https://zakupki.gov.ru/epz/order/extendedsearch/results.html",
                    }
                ],
            },
        }
    )

    text = _flat_text(elements)

    assert "Заказчик / ЕИС" in text
    assert "School" in text
    assert "5047152960" in text
    assert "high / 72" in text
    assert "4 закупок" in text
    assert "0373200000126000012" in text
    assert "network fetch: off" in text
    assert "Terminated contracts: 3." in text
    assert "EIS purchase search" in text


def test_customer_eis_elements_returns_empty_without_customer_context():
    service = _customer_eis_service()

    assert service.customer_eis_elements({"customer": "School"}) == []
