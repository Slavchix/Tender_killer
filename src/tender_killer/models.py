from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class TenderDocument:
    url: str
    name: str | None = None
    document_type: str | None = None
    source_document_id: str | None = None
    local_path: str | None = None
    downloaded_at: datetime | None = None
    text_status: str = "pending"
    raw_payload: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class TenderItem:
    name: str
    details: str | None = None
    quantity: float | None = None
    unit: str | None = None
    unit_price: float | None = None
    total_price: float | None = None
    okpd2: str | None = None
    classifier_code: str | None = None
    classifier_type: str | None = None
    raw_payload: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ProductProfile:
    tender_source: str
    tender_external_id: str
    position_index: int
    product_name: str
    normalized_name: str | None = None
    details: str | None = None
    category: str | None = None
    quantity: float | None = None
    unit: str | None = None
    unit_price: float | None = None
    total_price: float | None = None
    okpd2: str | None = None
    classifier_code: str | None = None
    classifier_type: str | None = None
    classifiers: list[dict[str, Any]] = field(default_factory=list)
    required_characteristics: list[Any] = field(default_factory=list)
    standards: list[Any] = field(default_factory=list)
    cert_documents: list[Any] = field(default_factory=list)
    brand_model: list[Any] = field(default_factory=list)
    origin_country_requirements: list[Any] = field(default_factory=list)
    search_phrases: list[str] = field(default_factory=list)
    stop_words: list[str] = field(default_factory=list)
    evidence: list[dict[str, Any]] = field(default_factory=list)
    profile_status: str = "needs_review"
    confidence: float | None = None
    source: str | None = None
    raw_payload: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Tender:
    source: str
    external_id: str
    url: str
    title: str
    customer: str | None = None
    region: str | None = None
    price: float | None = None
    currency: str = "RUB"
    status: str | None = None
    published_at: datetime | None = None
    deadline_at: datetime | None = None
    delivery_place: str | None = None
    category: str | None = None
    okpd2: str | None = None
    documents: list[str] = field(default_factory=list)
    document_records: list[TenderDocument] = field(default_factory=list)
    items: list[TenderItem] = field(default_factory=list)
    raw_payload: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.document_records and not self.documents:
            self.documents = [document.url for document in self.document_records]
        elif self.documents and not self.document_records:
            self.document_records = [TenderDocument(url=url) for url in self.documents]

    @property
    def identity(self) -> tuple[str, str]:
        return self.source, self.external_id
