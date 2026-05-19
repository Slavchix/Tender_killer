from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from tender_killer.adapters.base import AdapterError
from tender_killer.adapters.base import BaseAdapter
from tender_killer.models import Tender
from tender_killer.normalization import absolute_url, first_present, parse_datetime, parse_float

LOGGER = logging.getLogger(__name__)


class MoscowSupplierPortalAdapter(BaseAdapter):
    source = "moscow_supplier_portal"
    allow_card_like_html_fallback = False
    items_per_page = 50
    max_pages = 1

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
            region=first_present(payload, "region", "regionName") or "Москва",
            price=parse_float(first_present(payload, "price", "startPrice", "maxPrice", "amount")),
            currency=first_present(payload, "currency", "currencyCode") or "RUB",
            status=first_present(payload, "status", "state", "statusName", "stateName"),
            published_at=parse_datetime(first_present(payload, "publishDate", "createdAt", "startDate", "beginDate")),
            deadline_at=parse_datetime(first_present(payload, "endDate", "deadline", "finishDate")),
            delivery_place=first_present(payload, "deliveryAddress", "deliveryPlace", "address"),
            category=first_present(payload, "category", "categoryName", "rubricName"),
            okpd2=first_present(payload, "okpd2", "okpd2Code", "okpdCode"),
            documents=self._documents(payload),
            raw_payload=payload,
        )

    def _documents(self, payload: dict[str, Any]) -> list[str]:
        documents = first_present(payload, "documents", "files", "attachments")
        if not isinstance(documents, list):
            return []
        urls = []
        for document in documents:
            if isinstance(document, str):
                urls.append(absolute_url("https://zakupki.mos.ru", document))
            elif isinstance(document, dict):
                value = first_present(document, "url", "href", "fileUrl", "downloadUrl")
                if value:
                    urls.append(absolute_url("https://zakupki.mos.ru", value))
        return urls
