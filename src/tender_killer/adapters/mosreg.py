from __future__ import annotations

from typing import Any

from tender_killer.adapters.base import AdapterError
from tender_killer.adapters.base import BaseAdapter
from tender_killer.models import Tender
from tender_killer.normalization import absolute_url, first_present, parse_datetime, parse_float


class MosregMarketAdapter(BaseAdapter):
    source = "mosreg_market"
    allow_card_like_html_fallback = False

    @property
    def default_url(self) -> str:
        return "https://market.mosreg.ru/api/Purchase/Get"

    def normalize_payload(self, payload: dict[str, Any]) -> Tender:
        external_id = str(
            first_present(payload, "purchaseNumber", "id", "Id", "number", "registryNumber") or ""
        )
        if not external_id:
            raise AdapterError("Mosreg payload has no procurement id.")
        title = str(
            first_present(payload, "subject", "name", "title", "purchaseName") or ""
        ).strip()
        if not title:
            raise AdapterError("Mosreg payload has no procurement title.")

        url = absolute_url(
            "https://market.mosreg.ru",
            first_present(payload, "href", "url", "link", "purchaseUrl") or "/",
        )
        if url.rstrip("/") == "https://market.mosreg.ru":
            raise AdapterError("Mosreg payload has no detail URL.")

        return Tender(
            source=self.source,
            external_id=external_id,
            url=url,
            title=title,
            customer=first_present(payload, "customer.name", "customerName", "organizationName", "customer"),
            region=first_present(payload, "region", "regionName") or "Московская область",
            price=parse_float(first_present(payload, "maxPrice", "price", "startPrice", "amount")),
            currency=first_present(payload, "currency", "currencyCode") or "RUB",
            status=first_present(payload, "state", "status", "statusName"),
            published_at=parse_datetime(first_present(payload, "publishDate", "createdAt", "startDate")),
            deadline_at=parse_datetime(first_present(payload, "deadline", "endDate", "finishDate")),
            delivery_place=first_present(payload, "deliveryPlace", "deliveryAddress", "address"),
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
                urls.append(absolute_url("https://market.mosreg.ru", document))
            elif isinstance(document, dict):
                value = first_present(document, "url", "href", "fileUrl", "downloadUrl")
                if value:
                    urls.append(absolute_url("https://market.mosreg.ru", value))
        return urls
