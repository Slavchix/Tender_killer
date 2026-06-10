from __future__ import annotations

import json
import re
from typing import Any
from urllib.parse import urlencode

from tender_killer.normalization import first_present
from tender_killer.tender_metadata import normalize_customer_inn
from tender_killer.tender_metadata import normalize_law

EIS_HOME_URL = "https://zakupki.gov.ru/"
EIS_PURCHASE_SEARCH_URL = "https://zakupki.gov.ru/epz/order/extendedsearch/results.html"
EIS_CONTRACT_SEARCH_URL = "https://zakupki.gov.ru/epz/contract/search/results.html"
EIS_COMPLAINT_SEARCH_URL = "https://zakupki.gov.ru/epz/complaint/search/results.html"
EIS_RNP_SEARCH_URL = "https://zakupki.gov.ru/epz/dishonestsupplier/search/results.html"


def build_eis_reference(tender: dict[str, Any]) -> dict[str, Any]:
    raw_payload = _raw_payload(tender)
    purchase_number = _purchase_number(tender, raw_payload)
    customer_inn = _customer_inn(tender, raw_payload)
    law = _text(tender.get("law")) or normalize_law(raw_payload)
    title = _text(tender.get("title"))
    search_value = purchase_number or customer_inn or _short_query(title)
    queries = _queries(purchase_number=purchase_number, customer_inn=customer_inn, title=title)
    links = _links(search_value=search_value, customer_inn=customer_inn)

    return {
        "version": 1,
        "source": "eis",
        "status": "ready" if purchase_number or customer_inn else "manual_lookup",
        "network_fetch_enabled": False,
        "identifiers": {
            "purchase_number": purchase_number,
            "customer_inn": customer_inn,
            "law": law,
        },
        "queries": queries,
        "links": links,
        "coverage": {
            "purchase_search": bool(search_value),
            "documents_and_protocols": bool(search_value),
            "customer_contracts": bool(customer_inn),
            "customer_complaints": bool(customer_inn),
            "customer_rnp": bool(customer_inn),
        },
    }


def _links(*, search_value: str | None, customer_inn: str | None) -> list[dict[str, Any]]:
    links: list[dict[str, Any]] = []
    if search_value:
        links.append(
            {
                "id": "eis_purchase_search",
                "kind": "purchase_search",
                "label": "EIS purchase search",
                "url": _url(EIS_PURCHASE_SEARCH_URL, searchString=search_value),
                "manual": True,
            }
        )
    if customer_inn:
        links.extend(
            [
                {
                    "id": "eis_contracts_by_customer",
                    "kind": "customer_contracts",
                    "label": "EIS customer contracts",
                    "url": _url(EIS_CONTRACT_SEARCH_URL, searchString=customer_inn),
                    "manual": True,
                },
                {
                    "id": "eis_complaints_by_customer",
                    "kind": "customer_complaints",
                    "label": "EIS customer complaints",
                    "url": _url(EIS_COMPLAINT_SEARCH_URL, searchString=customer_inn),
                    "manual": True,
                },
                {
                    "id": "eis_rnp_by_customer",
                    "kind": "customer_rnp",
                    "label": "EIS dishonest supplier register",
                    "url": _url(EIS_RNP_SEARCH_URL, searchString=customer_inn),
                    "manual": True,
                },
            ]
        )
    links.append(
        {
            "id": "eis_home",
            "kind": "home",
            "label": "EIS home",
            "url": EIS_HOME_URL,
            "manual": True,
        }
    )
    return links


def _queries(*, purchase_number: str | None, customer_inn: str | None, title: str | None) -> list[dict[str, str]]:
    if purchase_number or customer_inn:
        result: list[dict[str, str]] = []
        if purchase_number:
            result.append({"kind": "purchase_number", "value": purchase_number})
        if customer_inn:
            result.append({"kind": "customer_inn", "value": customer_inn})
        return result
    title_query = _short_query(title)
    return [{"kind": "title", "value": title_query}] if title_query else []


def _purchase_number(tender: dict[str, Any], raw_payload: dict[str, Any]) -> str | None:
    value = first_present(
        raw_payload,
        "purchaseNumber",
        "PurchaseNumber",
        "noticeNumber",
        "notificationNumber",
        "registrationNumber",
        "registryNumber",
        "zakupkiNumber",
        "commonInfo.purchaseNumber",
        "__detail.purchaseNumber",
        "__detail.noticeNumber",
    )
    number = _official_number(value)
    if number:
        return number
    return _official_number(tender.get("external_id"))


def _customer_inn(tender: dict[str, Any], raw_payload: dict[str, Any]) -> str | None:
    return _official_inn(tender.get("customer_inn")) or normalize_customer_inn(raw_payload)


def _official_number(value: Any) -> str | None:
    digits = re.sub(r"\D+", "", str(value or ""))
    return digits if len(digits) >= 11 else None


def _official_inn(value: Any) -> str | None:
    digits = re.sub(r"\D+", "", str(value or ""))
    return digits if len(digits) in {10, 12} else None


def _short_query(value: Any) -> str | None:
    text = _text(value)
    return text[:160] if text else None


def _text(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None


def _raw_payload(tender: dict[str, Any]) -> dict[str, Any]:
    raw_payload = tender.get("raw_payload")
    if isinstance(raw_payload, dict):
        return raw_payload
    raw_payload_json = tender.get("raw_payload_json")
    if isinstance(raw_payload_json, str) and raw_payload_json.strip():
        try:
            data = json.loads(raw_payload_json)
        except json.JSONDecodeError:
            return {}
        return data if isinstance(data, dict) else {}
    return {}


def _url(base_url: str, **params: str) -> str:
    return f"{base_url}?{urlencode(params)}"
