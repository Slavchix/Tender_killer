from __future__ import annotations

import logging
import re
from typing import Any

from bs4 import BeautifulSoup
import httpx

from tender_killer.adapters.base import AdapterError
from tender_killer.adapters.base import BaseAdapter
from tender_killer.models import Tender, TenderDocument, TenderItem
from tender_killer.normalization import absolute_url, first_present, parse_datetime, parse_float

LOGGER = logging.getLogger(__name__)


class MosregMarketAdapter(BaseAdapter):
    source = "mosreg_market"
    allow_card_like_html_fallback = False
    items_per_page = 50
    max_pages = 1

    def __init__(
        self,
        url: str | None = None,
        timeout_seconds: float = 20,
        enrich_documents: bool = True,
        enrich_html: bool = False,
        max_pages: int | None = None,
        published_from: Any | None = None,
    ) -> None:
        super().__init__(url, timeout_seconds)
        self.enrich_documents = enrich_documents
        self.enrich_html = enrich_html
        self.max_pages = max(1, int(max_pages or self.max_pages))
        self.published_from = published_from

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
                    payload = self.enrich_payload(payload)
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
                json=self.trade_search_payload(
                    page=page,
                    items_per_page=self.items_per_page,
                    published_from=_checkpoint_value(self.published_from),
                ),
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

    def enrich_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.enrich_documents and not self.enrich_html:
            return payload
        trade_id = first_present(payload, "Id", "id")
        if not trade_id:
            return payload
        enriched = dict(payload)
        if self.enrich_documents:
            documents = self._fetch_trade_documents(str(trade_id))
            if documents:
                enriched["__documents"] = documents
        if self.enrich_html:
            html = self._fetch_trade_html(str(trade_id))
            if html:
                enriched["__html"] = html
        return enriched

    def _fetch_trade_documents(self, trade_id: str) -> list[dict[str, Any]]:
        url = f"https://api.market.mosreg.ru/api/Trade/{trade_id}/GetTradeDocuments"
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://market.mosreg.ru",
            "Referer": "https://market.mosreg.ru/",
            "User-Agent": "TenderKiller/0.1 (+https://github.com/Slavchix/Tender_killer)",
            "XXX-TenantId-Header": "2",
        }
        try:
            response = httpx.get(url, headers=headers, timeout=self.timeout_seconds)
            response.raise_for_status()
            data = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            LOGGER.warning("Failed to fetch Mosreg documents for %s: %s", trade_id, exc)
            return []
        if not isinstance(data, list):
            return []
        return [item for item in data if isinstance(item, dict)]

    def _fetch_trade_html(self, trade_id: str) -> str:
        url = f"https://market.mosreg.ru/Trade/ViewTrade/{trade_id}"
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "User-Agent": "TenderKiller/0.1 (+https://github.com/Slavchix/Tender_killer)",
        }
        try:
            response = httpx.get(url, headers=headers, timeout=self.timeout_seconds)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            LOGGER.warning("Failed to fetch Mosreg HTML card for %s: %s", trade_id, exc)
            return ""
        return response.text

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
            document_records=self._document_records(payload),
            items=self._items(payload),
            raw_payload=payload,
        )

    def _items(self, payload: dict[str, Any]) -> list[TenderItem]:
        raw_items = first_present(
            payload,
            "TradeObjects",
            "Objects",
            "Products",
            "Items",
            "Positions",
            "LotItems",
            "objects",
            "products",
            "items",
            "positions",
        )
        if not isinstance(raw_items, list):
            html_items = self._items_from_html(str(payload.get("__html") or ""))
            if html_items:
                return html_items
        if not isinstance(raw_items, list):
            return []
        items: list[TenderItem] = []
        for raw_item in raw_items:
            if not isinstance(raw_item, dict):
                continue
            name = str(
                first_present(
                    raw_item,
                    "ProductName",
                    "Name",
                    "name",
                    "ItemName",
                    "PurchaseObjectName",
                    "Koz2Name",
                )
                or ""
            ).strip()
            if not name:
                continue
            classifier_code = first_present(raw_item, "Koz2Value", "Okpd2", "okpd2", "okpd2Code", "ClassifierCode")
            items.append(
                TenderItem(
                    name=name,
                    details=first_present(
                        raw_item,
                        "DetailedName",
                        "DetailName",
                        "ProductDescription",
                        "Description",
                        "description",
                    ),
                    quantity=parse_float(first_present(raw_item, "Quantity", "quantity", "Count", "count", "Amount")),
                    unit=first_present(raw_item, "UnitName", "unitName", "Unit", "unit", "OkeiName"),
                    unit_price=parse_float(
                        first_present(raw_item, "UnitPrice", "unitPrice", "ProductPrice", "Price", "price")
                    ),
                    total_price=parse_float(
                        first_present(raw_item, "TotalPrice", "totalPrice", "Sum", "sum", "AmountPrice")
                    ),
                    okpd2=classifier_code,
                    classifier_code=classifier_code,
                    classifier_type=first_present(
                        raw_item,
                        "ClassificatorType",
                        "ClassifierType",
                        "classificatorType",
                        "classifierType",
                        "Koz2Type",
                    ),
                    raw_payload=raw_item,
                )
            )
        return items

    def _items_from_html(self, html: str) -> list[TenderItem]:
        if not html.strip():
            return []
        soup = BeautifulSoup(html, "html.parser")
        root = soup.select_one(".objectPurchase") or soup
        cards = root.select(".outputResults__oneResult")
        items: list[TenderItem] = []
        for card in cards:
            name = _html_labeled_value(card, "Наименование товара, работ, услуг")
            if not name:
                continue
            classifier_code = _html_labeled_value(card, "Код классификатор")
            items.append(
                TenderItem(
                    name=name,
                    details=_html_labeled_value(card, "Детализированное наименование"),
                    quantity=parse_float(_html_labeled_value(card, "Количество")),
                    unit=_html_labeled_value(card, "Единицы измерения"),
                    unit_price=parse_float(_html_labeled_value(card, "Стоимость единицы продукции")),
                    total_price=parse_float(_html_labeled_value(card, "Стоимость поставленого товара")),
                    okpd2=classifier_code,
                    classifier_code=classifier_code,
                    classifier_type=_html_labeled_value(card, "Тип классификатор"),
                    raw_payload={"source": "html"},
                )
            )
        return items

    def _documents(self, payload: dict[str, Any]) -> list[str]:
        return [document.url for document in self._document_records(payload)]

    def _document_records(self, payload: dict[str, Any]) -> list[TenderDocument]:
        documents = first_present(payload, "__documents", "documents", "files", "attachments")
        records: list[TenderDocument] = []
        if isinstance(documents, list):
            for document in documents:
                if isinstance(document, str):
                    records.append(TenderDocument(url=absolute_url("https://market.mosreg.ru", document)))
                elif isinstance(document, dict):
                    value = first_present(document, "Url", "url", "href", "fileUrl", "downloadUrl")
                    if value:
                        records.append(
                            TenderDocument(
                                url=absolute_url("https://market.mosreg.ru", value),
                                name=first_present(document, "FileName", "UserFileNameFromOuterSystem", "name", "fileName"),
                                document_type=first_present(document, "Type", "type", "DocumentType"),
                                source_document_id=str(first_present(document, "Id", "id") or "") or None,
                                raw_payload=document,
                            )
                        )
        if records:
            return records
        trade_id = first_present(payload, "Id", "id")
        if trade_id:
            records.append(
                TenderDocument(
                    url=f"https://api.market.mosreg.ru/api/Trade/{trade_id}/GetTradeDocuments",
                    name="Документы закупки",
                    document_type="Список документов",
                    source_document_id=str(trade_id),
                )
            )
        return records

    @staticmethod
    def trade_search_payload(
        page: int,
        items_per_page: int,
        published_from: Any | None = None,
    ) -> dict[str, Any]:
        return _trade_search_payload(page, items_per_page, published_from)


def _trade_search_payload(page: int, items_per_page: int, published_from: Any | None = None) -> dict[str, Any]:
    return {
        "page": page,
        "itemsPerPage": items_per_page,
        "tradeState": "15",
        "OnlyTradesWithMyApplications": False,
        "sortingParams": [],
        "filterPriceMin": "",
        "filterPriceMax": "",
        "filterDateFrom": _checkpoint_value(published_from),
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


def _checkpoint_value(value: Any | None) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    text = str(value).strip()
    return text or None


def _html_labeled_value(card: Any, label: str) -> str | None:
    for label_node in card.select(".grayText"):
        label_text = _clean_html_text(label_node.get_text(" ", strip=True)).rstrip(":")
        if label not in label_text:
            continue
        parent = label_node.parent
        if parent is None:
            continue
        text = _clean_html_text(parent.get_text(" ", strip=True))
        text = re.sub(rf"^{re.escape(label_text)}:?\s*", "", text).strip()
        return text or None
    return None


def _clean_html_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("\xa0", " ")).strip()
