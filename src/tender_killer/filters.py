from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from tender_killer.models import Tender


MOSCOW_TZ = timezone(timedelta(hours=3), name="MSK")


@dataclass(frozen=True)
class FilterResult:
    matched: bool
    reasons: list[str]


@dataclass(frozen=True)
class FilterProfile:
    keywords: tuple[str, ...]
    exclude_keywords: tuple[str, ...] = ()
    regions: tuple[str, ...] = ()
    statuses: tuple[str, ...] = ()
    min_price: float | None = None
    max_price: float | None = None
    include_without_price: bool = True
    include_without_deadline: bool = True

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

    @classmethod
    def default(cls) -> "FilterProfile":
        return cls(keywords=cls.DEFAULT_KEYWORDS)

    @classmethod
    def from_json_file(cls, path: str | Path) -> "FilterProfile":
        data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
        if not isinstance(data, dict):
            raise ValueError("Filter profile must be a JSON object.")
        return cls.from_mapping(data)

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "FilterProfile":
        keywords = tuple(_clean_list(data.get("keywords"))) or cls.DEFAULT_KEYWORDS
        return cls(
            keywords=keywords,
            exclude_keywords=tuple(_clean_list(data.get("exclude_keywords", data.get("exclude", ())))),
            regions=tuple(_clean_list(data.get("regions", ()))),
            statuses=tuple(_clean_list(data.get("statuses", ()))),
            min_price=_optional_float(data.get("min_price")),
            max_price=_optional_float(data.get("max_price")),
            include_without_price=bool(data.get("include_without_price", True)),
            include_without_deadline=bool(data.get("include_without_deadline", True)),
        )


class TenderFilter:
    def __init__(self, profile: FilterProfile | None = None) -> None:
        self.profile = profile or FilterProfile.default()
        self.keywords = tuple(keyword.lower().replace("ё", "е") for keyword in self.profile.keywords)
        self.exclude_keywords = tuple(
            keyword.lower().replace("ё", "е") for keyword in self.profile.exclude_keywords
        )
        self.regions = tuple(region.lower() for region in self.profile.regions)
        self.statuses = tuple(status.lower() for status in self.profile.statuses)
        self.reason_labels = {"кабел": "кабель"}

    def match(self, tender: Tender) -> FilterResult:
        if self._is_expired(tender):
            return FilterResult(False, ["deadline_expired"])

        price_reason = self._price_rejected(tender)
        if price_reason:
            return FilterResult(False, [price_reason])

        if self._region_rejected(tender):
            return FilterResult(False, ["region_not_allowed"])

        if self._status_rejected(tender):
            return FilterResult(False, ["status_not_allowed"])

        haystack = self._haystack(tender)
        for keyword in self.exclude_keywords:
            if self._keyword_matches(keyword, haystack):
                return FilterResult(False, [f"excluded:{self._label(keyword)}"])

        reasons = [
            f"keyword:{self._label(keyword)}"
            for keyword in self.keywords
            if self._keyword_matches(keyword, haystack)
        ]
        return FilterResult(bool(reasons), reasons)

    def _haystack(self, tender: Tender) -> str:
        return " ".join(
            part
            for part in (
                tender.title,
                tender.category,
                tender.delivery_place,
                tender.okpd2,
                tender.region,
                tender.status,
            )
            if part
        ).lower().replace("ё", "е")

    def _label(self, keyword: str) -> str:
        return self.reason_labels.get(keyword, keyword)

    def _keyword_matches(self, keyword: str, haystack: str) -> bool:
        if keyword in haystack:
            return True
        stem = _soft_stem(keyword)
        return stem != keyword and stem in haystack

    def _price_rejected(self, tender: Tender) -> str | None:
        if tender.price is None:
            return None if self.profile.include_without_price else "price_missing"
        if self.profile.min_price is not None and tender.price < self.profile.min_price:
            return "price_below_min"
        if self.profile.max_price is not None and tender.price > self.profile.max_price:
            return "price_above_max"
        return None

    def _region_rejected(self, tender: Tender) -> bool:
        if not self.regions:
            return False
        haystack = " ".join(part for part in (tender.region, tender.delivery_place) if part).lower()
        return not any(region in haystack for region in self.regions)

    def _status_rejected(self, tender: Tender) -> bool:
        if not self.statuses or not tender.status:
            return False
        status = tender.status.lower()
        return not any(allowed in status for allowed in self.statuses)

    def _is_expired(self, tender: Tender) -> bool:
        if tender.deadline_at is None:
            return not self.profile.include_without_deadline
        deadline = tender.deadline_at
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=MOSCOW_TZ)
        return deadline <= datetime.now(deadline.tzinfo)


class MaterialFilter(TenderFilter):
    def __init__(self, keywords: tuple[str, ...] | None = None) -> None:
        super().__init__(FilterProfile(keywords=keywords or FilterProfile.DEFAULT_KEYWORDS))


def _clean_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if not isinstance(value, list | tuple):
        raise ValueError("Filter list values must be strings or arrays.")
    return [str(item).strip() for item in value if str(item).strip()]


def _optional_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    return float(value)


def _soft_stem(value: str) -> str:
    if len(value) < 5:
        return value
    endings = (
        "иями",
        "ями",
        "ами",
        "ого",
        "ему",
        "ыми",
        "ими",
        "ая",
        "ое",
        "ые",
        "ие",
        "ой",
        "ей",
        "ий",
        "ый",
        "ов",
        "ев",
        "ам",
        "ям",
        "ах",
        "ях",
        "ом",
        "ем",
        "ою",
        "ею",
        "у",
        "ю",
        "а",
        "я",
        "ы",
        "и",
        "е",
        "о",
        "ь",
    )
    for ending in endings:
        if value.endswith(ending) and len(value) - len(ending) >= 4:
            return value[: -len(ending)]
    return value
