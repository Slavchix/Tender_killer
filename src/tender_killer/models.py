from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


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
    raw_payload: dict[str, Any] = field(default_factory=dict)

    @property
    def identity(self) -> tuple[str, str]:
        return self.source, self.external_id

