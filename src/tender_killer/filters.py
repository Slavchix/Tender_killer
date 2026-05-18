from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from tender_killer.models import Tender


MOSCOW_TZ = timezone(timedelta(hours=3), name="MSK")


@dataclass(frozen=True)
class FilterResult:
    matched: bool
    reasons: list[str]


class MaterialFilter:
    DEFAULT_KEYWORDS = (
        "стройматериал",
        "цемент",
        "смесь",
        "шпатлев",
        "штукатур",
        "бетон",
        "жби",
        "арматур",
        "металлопрокат",
        "лист сталь",
        "профиль",
        "крепеж",
        "метиз",
        "саморез",
        "болт",
        "гайк",
        "кабел",
        "провод",
        "электр",
        "светильник",
        "ламп",
        "сантех",
        "труб",
        "кран",
        "смесител",
        "краск",
        "лак",
        "эмаль",
        "бумаг",
        "канцеляр",
        "картридж",
        "хозтовар",
        "моющ",
        "расходн",
        "сиз",
        "перчат",
        "инструмент",
    )

    def __init__(self, keywords: tuple[str, ...] | None = None) -> None:
        self.keywords = tuple(keyword.lower() for keyword in (keywords or self.DEFAULT_KEYWORDS))
        self.reason_labels = {"кабел": "кабель"}

    def match(self, tender: Tender) -> FilterResult:
        reasons: list[str] = []
        if self._is_expired(tender):
            return FilterResult(False, ["deadline_expired"])

        haystack = " ".join(
            part
            for part in (
                tender.title,
                tender.category,
                tender.delivery_place,
                tender.okpd2,
            )
            if part
        ).lower()

        for keyword in self.keywords:
            if keyword in haystack:
                reasons.append(self.reason_labels.get(keyword, keyword))

        return FilterResult(bool(reasons), reasons)

    def _is_expired(self, tender: Tender) -> bool:
        if tender.deadline_at is None:
            return False
        deadline = tender.deadline_at
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=MOSCOW_TZ)
        return deadline <= datetime.now(deadline.tzinfo)
