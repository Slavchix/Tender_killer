from __future__ import annotations

from typing import Any

from tender_killer.adapters.base import AdapterError
from tender_killer.adapters.base import BaseAdapter
from tender_killer.models import Tender
from tender_killer.normalization import absolute_url, first_present, parse_datetime, parse_float


class MoscowSupplierPortalAdapter(BaseAdapter):
    source = "moscow_supplier_portal"
    allow_card_like_html_fallback = False

    @property
    def default_url(self) -> str:
        return "https://zakupki.mos.ru/newapi/api/Auction/Get"

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
        if url.rstrip("/") == "https://zakupki.mos.ru":
            raise AdapterError("Moscow payload has no detail URL.")

        return Tender(
            source=self.source,
            external_id=external_id,
            url=url,
            title=title,
            customer=first_present(payload, "customerName", "CustomerName", "customer.name", "customer"),
            region=first_present(payload, "region", "regionName") or "Москва",
            price=parse_float(first_present(payload, "price", "startPrice", "maxPrice", "amount")),
            currency=first_present(payload, "currency", "currencyCode") or "RUB",
            status=first_present(payload, "status", "state", "statusName"),
            published_at=parse_datetime(first_present(payload, "publishDate", "createdAt", "startDate")),
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
