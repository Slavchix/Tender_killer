from __future__ import annotations

import json
import logging
from typing import Any
from urllib.parse import urlencode

import httpx

from tender_killer.adapters.base import AdapterError
from tender_killer.adapters.base import BaseAdapter
from tender_killer.models import Tender, TenderDocument, TenderItem
from tender_killer.normalization import absolute_url, first_present, parse_datetime, parse_float

LOGGER = logging.getLogger(__name__)


class MoscowSupplierPortalAdapter(BaseAdapter):
    source = "moscow_supplier_portal"
    allow_card_like_html_fallback = False
    items_per_page = 50
    max_pages = 1

    def __init__(self, url: str | None = None, timeout_seconds: float = 20, enrich_details: bool = True) -> None:
        super().__init__(url, timeout_seconds)
        self.enrich_details = enrich_details

    @property
    def default_url(self) -> str:
        return "https://old.zakupki.mos.ru/api/Cssp/Purchase/Query"

    def fetch(self) -> list[Tender]:
        tenders: list[Tender] = []
        for page in range(self.max_pages):
            skip = page * self.items_per_page
            data = self._fetch_page(skip)
            payloads = [payload for payload in self._payloads_from_json(data) if payload.get("auctionId")]
            for payload in payloads:
                try:
                    payload = self.enrich_payload(payload)
                    tenders.append(self.normalize_payload(payload))
                except Exception as exc:  # noqa: BLE001 - adapter must continue on bad records.
                    LOGGER.warning("Failed to normalize %s payload: %s", self.source, exc)
            if len(payloads) < self.items_per_page:
                break
        return tenders

    def _fetch_page(self, skip: int) -> dict[str, Any]:
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://zakupki.mos.ru",
            "Referer": "https://zakupki.mos.ru/",
            "User-Agent": "TenderKiller/0.1 (+https://github.com/Slavchix/Tender_killer)",
        }
        query = self.purchase_query(skip=skip, take=self.items_per_page)
        try:
            response = httpx.get(
                self.url,
                params={"queryDto": json.dumps(query, ensure_ascii=False, separators=(",", ":"))},
                headers=headers,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise AdapterError(f"{self.url}: {exc}") from exc
        if not isinstance(data, dict):
            raise AdapterError("Moscow purchase query returned non-object JSON.")
        return data

    def enrich_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.enrich_details:
            return payload
        auction_id = first_present(payload, "auctionId", "id", "number")
        if not auction_id:
            return payload
        detail = self._fetch_auction_detail(str(auction_id))
        if not detail:
            return payload
        enriched = dict(payload)
        enriched["__detail"] = detail
        return enriched

    def _fetch_auction_detail(self, auction_id: str) -> dict[str, Any]:
        url = "https://zakupki.mos.ru/newapi/api/Auction/Get"
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Referer": f"https://zakupki.mos.ru/auction/{auction_id}",
            "User-Agent": "TenderKiller/0.1 (+https://github.com/Slavchix/Tender_killer)",
        }
        try:
            response = httpx.get(
                url,
                params={"auctionId": auction_id},
                headers=headers,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            LOGGER.warning("Failed to fetch Moscow auction detail for %s: %s", auction_id, exc)
            return {}
        return data if isinstance(data, dict) else {}

    @staticmethod
    def purchase_query(skip: int, take: int) -> dict[str, Any]:
        return {
            "filter": {
                "typeIn": {},
                "nameLike": {"contains": True},
                "regionPaths": {"values": [".1.504."]},
                "customerInnOrName": {"contains": True},
                "numberLike": {"contains": True},
                "externalNumberLike": {"contains": True},
                "auctionSpecificFilter": {
                    "stateIdIn": [19000002],
                    "initialDuration": [3, 6, 24],
                    "supplierTotalPoints": {},
                },
                "needSpecificFilter": {"supplierTotalPoints": {}},
                "tenderSpecificFilter": {},
                "ptkrSpecificFilter": {},
            },
            "order": [{"field": "relevance", "desc": True}],
            "withCount": True,
            "take": take,
            "skip": skip,
        }

    def normalize_payload(self, payload: dict[str, Any]) -> Tender:
        external_id = str(
            first_present(payload, "id", "Id", "auctionId", "number", "registryNumber") or ""
        )
        if not external_id:
            raise AdapterError("Moscow payload has no procurement id.")
        title = str(
            first_present(payload, "name", "Name", "title", "subject", "purchaseName") or ""
        ).strip()
        if not title:
            raise AdapterError("Moscow payload has no procurement title.")

        url = absolute_url(
            "https://zakupki.mos.ru",
            first_present(payload, "url", "href", "link", "auctionUrl") or "/",
        )
        auction_id = first_present(payload, "auctionId")
        if url.rstrip("/") == "https://zakupki.mos.ru" and auction_id:
            url = f"https://zakupki.mos.ru/auction/{auction_id}"
        if url.rstrip("/") == "https://zakupki.mos.ru":
            raise AdapterError("Moscow payload has no detail URL.")
        customer = first_present(
            payload,
            "__detail.customer.name",
            "__detail.createdByCustomer.name",
            "purchaseCreator.name",
            "customerName",
            "CustomerName",
            "customer.name",
            "customer",
        )
        customers = payload.get("customers")
        if not customer and isinstance(customers, list) and customers and isinstance(customers[0], dict):
            customer = customers[0].get("name")

        return Tender(
            source=self.source,
            external_id=external_id,
            url=url,
            title=title,
            customer=customer,
            region=self._region(payload),
            price=parse_float(first_present(payload, "__detail.startCost", "price", "startPrice", "maxPrice", "amount")),
            currency=first_present(payload, "currency", "currencyCode") or "RUB",
            status=first_present(payload, "__detail.state.name", "status", "state", "statusName", "stateName"),
            published_at=parse_datetime(
                first_present(payload, "__detail.startDate", "publishDate", "createdAt", "startDate", "beginDate")
            ),
            deadline_at=parse_datetime(first_present(payload, "__detail.endDate", "endDate", "deadline", "finishDate")),
            delivery_place=self._delivery_place(payload),
            category=first_present(payload, "category", "categoryName", "rubricName"),
            okpd2=first_present(payload, "okpd2", "okpd2Code", "okpdCode"),
            document_records=self._document_records(payload),
            items=self._items(payload),
            raw_payload=payload,
        )

    def _region(self, payload: dict[str, Any]) -> Any:
        direct = first_present(payload, "region", "regionName")
        if direct:
            return direct
        regions = first_present(payload, "__detail.auctionRegion")
        if isinstance(regions, list) and regions and isinstance(regions[0], dict):
            return first_present(regions[0], "name")
        return "Москва"

    def _delivery_place(self, payload: dict[str, Any]) -> Any:
        direct = first_present(payload, "deliveryAddress", "deliveryPlace", "address")
        if direct:
            return direct
        deliveries = first_present(payload, "__detail.deliveries")
        if isinstance(deliveries, list) and deliveries and isinstance(deliveries[0], dict):
            return first_present(deliveries[0], "deliveryPlace", "deliveryAddress", "address")
        return None

    def _items(self, payload: dict[str, Any]) -> list[TenderItem]:
        raw_items = first_present(payload, "__detail.items", "__detail.auctionItem", "items", "auctionItem")
        if not isinstance(raw_items, list):
            return []
        delivery_items_by_name = self._delivery_items_by_name(payload)
        items: list[TenderItem] = []
        for raw_item in raw_items:
            if not isinstance(raw_item, dict):
                continue
            name = str(first_present(raw_item, "name", "okpdName", "productionDirectoryName") or "").strip()
            if not name:
                continue
            delivery_item = delivery_items_by_name.get(name)
            quantity = parse_float(first_present(raw_item, "currentValue", "quantity", "Quantity"))
            unit_price = parse_float(first_present(raw_item, "costPerUnit", "unitPrice", "price"))
            total_price = parse_float(first_present(delivery_item or {}, "sum", "totalPrice"))
            if total_price is None and quantity is not None and unit_price is not None:
                total_price = quantity * unit_price
            items.append(
                TenderItem(
                    name=name,
                    details=first_present(raw_item, "productionDirectoryName", "okpdName"),
                    quantity=quantity,
                    unit=first_present(raw_item, "okeiName", "unit", "unitName"),
                    unit_price=unit_price,
                    total_price=total_price,
                    okpd2=first_present(raw_item, "okpd2", "okpdCode", "okpdName"),
                    raw_payload=raw_item,
                )
            )
        return items

    def _delivery_items_by_name(self, payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
        deliveries = first_present(payload, "__detail.deliveries")
        if not isinstance(deliveries, list):
            return {}
        items: dict[str, dict[str, Any]] = {}
        for delivery in deliveries:
            if not isinstance(delivery, dict) or not isinstance(delivery.get("items"), list):
                continue
            for item in delivery["items"]:
                if isinstance(item, dict) and item.get("name"):
                    items[str(item["name"])] = item
        return items

    def _documents(self, payload: dict[str, Any]) -> list[str]:
        return [document.url for document in self._document_records(payload)]

    def _document_records(self, payload: dict[str, Any]) -> list[TenderDocument]:
        documents = first_present(payload, "__detail.files", "documents", "files", "attachments")
        license_documents = first_present(payload, "__detail.licenseFiles")
        if isinstance(documents, list) and isinstance(license_documents, list):
            documents = [*documents, *license_documents]
        if not isinstance(documents, list):
            return []
        records: list[TenderDocument] = []
        for document in documents:
            if isinstance(document, str):
                records.append(TenderDocument(url=absolute_url("https://zakupki.mos.ru", document)))
            elif isinstance(document, dict):
                value = first_present(document, "url", "href", "fileUrl", "downloadUrl")
                if value:
                    records.append(
                        TenderDocument(
                            url=absolute_url("https://zakupki.mos.ru", value),
                            name=first_present(document, "name", "fileName"),
                            document_type=first_present(document, "type", "documentType", "description"),
                            source_document_id=str(first_present(document, "id", "fileId") or "") or None,
                            raw_payload=document,
                        )
                    )
                    continue
                file_id = first_present(document, "id", "fileId")
                if file_id:
                    params = {"id": str(file_id)}
                    if name := first_present(document, "name", "fileName"):
                        params["fileName"] = str(name)
                    records.append(
                        TenderDocument(
                            url=f"https://zakupki.mos.ru/newapi/api/FileStorage/Download?{urlencode(params)}",
                            name=first_present(document, "name", "fileName"),
                            document_type=first_present(document, "type", "documentType", "description"),
                            source_document_id=str(file_id),
                            raw_payload=document,
                        )
                    )
        return records
