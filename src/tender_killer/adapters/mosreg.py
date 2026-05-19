from __future__ import annotations

import logging
from typing import Any

import httpx

from tender_killer.adapters.base import AdapterError
from tender_killer.adapters.base import BaseAdapter
from tender_killer.models import Tender
from tender_killer.normalization import absolute_url, first_present, parse_datetime, parse_float

LOGGER = logging.getLogger(__name__)


class MosregMarketAdapter(BaseAdapter):
    source = "mosreg_market"
    allow_card_like_html_fallback = False
    items_per_page = 50
    max_pages = 1

    @property
    def default_url(self) -> str:
        return "https://api.market.mosreg.ru/api/Trade/GetTradesForParticipantOrAnonymous"

    def fetch(self) -> list[Tender]:
        tenders: list[Tender] = []
        for page in range(1, self.max_pages + 1):
            data = self._fetch_page(page)
            payloads = self._payloads_from_trade_response(data)
            for payload in payloads:
                try:
                    tenders.append(self.normalize_payload(payload))
                except Exception as exc:  # noqa: BLE001 - adapter must continue on bad records.
                    LOGGER.warning("Failed to normalize %s payload: %s", self.source, exc)
            total_pages = int(data.get("totalpages") or 1) if isinstance(data, dict) else 1
            if page >= total_pages or not payloads:
                break
        return tenders

    def _fetch_page(self, page: int) -> dict[str, Any]:
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json; charset=UTF-8",
            "Origin": "https://market.mosreg.ru",
            "Referer": "https://market.mosreg.ru/",
            "User-Agent": "TenderKiller/0.1 (+https://github.com/Slavchix/Tender_killer)",
            "XXX-TenantId-Header": "2",
        }
        try:
            response = httpx.post(
                self.url,
                json=_trade_search_payload(page, self.items_per_page),
                headers=headers,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise AdapterError(f"{self.url}: {exc}") from exc
        if not isinstance(data, dict):
            raise AdapterError("Mosreg trade search returned non-object JSON.")
        return data

    def _payloads_from_trade_response(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        payloads = data.get("invdata")
        if isinstance(payloads, list):
            return [item for item in payloads if isinstance(item, dict)]
        return self._payloads_from_json(data)

    def normalize_payload(self, payload: dict[str, Any]) -> Tender:
        external_id = str(
            first_present(payload, "purchaseNumber", "Id", "id", "number", "registryNumber") or ""
        )
        if not external_id:
            raise AdapterError("Mosreg payload has no procurement id.")
        title = str(
            first_present(payload, "TradeName", "subject", "name", "title", "purchaseName") or ""
        ).strip()
        if not title:
            raise AdapterError("Mosreg payload has no procurement title.")

        trade_id = first_present(payload, "Id", "id")
        url = absolute_url(
            "https://market.mosreg.ru",
            first_present(payload, "href", "url", "link", "purchaseUrl")
            or (f"/Trade/ViewTrade/{trade_id}" if trade_id else "/"),
        )
        if url.rstrip("/") == "https://market.mosreg.ru":
            raise AdapterError("Mosreg payload has no detail URL.")

        return Tender(
            source=self.source,
            external_id=external_id,
            url=url,
            title=title,
            customer=first_present(
                payload,
                "CustomerFullName",
                "customer.name",
                "customerName",
                "organizationName",
                "customer",
            ),
            region=first_present(payload, "region", "regionName") or "Московская область",
            price=parse_float(first_present(payload, "InitialPrice", "maxPrice", "price", "startPrice", "amount")),
            currency=first_present(payload, "currency", "currencyCode") or "RUB",
            status=first_present(payload, "TradeStateName", "state", "status", "statusName"),
            published_at=parse_datetime(
                first_present(payload, "PublicationDate", "publishDate", "createdAt", "startDate")
            ),
            deadline_at=parse_datetime(
                first_present(payload, "FillingApplicationEndDate", "deadline", "endDate", "finishDate")
            ),
            delivery_place=first_present(payload, "deliveryPlace", "deliveryAddress", "address"),
            category=first_present(payload, "CategoryName", "category", "categoryName", "rubricName"),
            okpd2=first_present(payload, "Koz2Value", "okpd2", "okpd2Code", "okpdCode"),
            documents=self._documents(payload),
            raw_payload=payload,
        )

    def _documents(self, payload: dict[str, Any]) -> list[str]:
        documents = first_present(payload, "documents", "files", "attachments")
        urls = []
        if isinstance(documents, list):
            for document in documents:
                if isinstance(document, str):
                    urls.append(absolute_url("https://market.mosreg.ru", document))
                elif isinstance(document, dict):
                    value = first_present(document, "url", "href", "fileUrl", "downloadUrl")
                    if value:
                        urls.append(absolute_url("https://market.mosreg.ru", value))
        trade_id = first_present(payload, "Id", "id")
        if trade_id:
            urls.append(f"https://api.market.mosreg.ru/api/Trade/{trade_id}/GetTradeDocuments")
        return urls


def _trade_search_payload(page: int, items_per_page: int) -> dict[str, Any]:
    return {
        "page": page,
        "itemsPerPage": items_per_page,
        "tradeState": "15",
        "OnlyTradesWithMyApplications": False,
        "sortingParams": [],
        "filterPriceMin": "",
        "filterPriceMax": "",
        "filterDateFrom": None,
        "filterDateTo": None,
        "filterFillingApplicationEndDateFrom": None,
        "FilterFillingApplicationEndDateTo": None,
        "filterTradeEasuzNumber": "",
        "showOnlyOwnTrades": False,
        "showApprovementTrades": False,
        "IsImmediate": False,
        "UsedClassificatorType": 20,
        "classificatorCodes": [],
        "CustomerFullNameOrInn": "",
        "CustomerAddress": "",
        "Koz2Value": "",
        "ParticipantHasApplicationsOnTrade": "",
        "ProductPriceMin": "",
        "ProductPriceMax": "",
    }
