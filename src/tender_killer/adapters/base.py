from __future__ import annotations

import json
import logging
import re
from abc import ABC, abstractmethod
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from tender_killer.models import Tender

LOGGER = logging.getLogger(__name__)


class AdapterError(RuntimeError):
    pass


class BaseAdapter(ABC):
    source: str
    allow_card_like_html_fallback = True

    def __init__(self, url: str | None = None, timeout_seconds: float = 20) -> None:
        self.url = url or self.default_url
        self.timeout_seconds = timeout_seconds

    @property
    @abstractmethod
    def default_url(self) -> str:
        raise NotImplementedError

    def fetch(self) -> list[Tender]:
        raw_text = self.fetch_text(self.url)
        payloads = self.extract_payloads(raw_text)
        tenders = []
        for payload in payloads:
            try:
                tenders.append(self.normalize_payload(payload))
            except Exception as exc:  # noqa: BLE001 - adapter must continue on bad records.
                LOGGER.warning("Failed to normalize %s payload: %s", self.source, exc)
        return tenders

    def fetch_text(self, url: str) -> str:
        request = Request(
            url,
            headers={
                "User-Agent": "TenderKiller/0.1 (+https://github.com/Slavchix/Tender_killer)",
                "Accept": "application/json,text/html;q=0.9,*/*;q=0.8",
            },
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                charset = response.headers.get_content_charset() or "utf-8"
                return response.read().decode(charset, errors="replace")
        except HTTPError as exc:
            body = exc.read(300).decode("utf-8", errors="replace").strip().replace("\n", " ")
            raise AdapterError(f"{url}: HTTP {exc.code} {exc.reason}. {body}") from exc
        except URLError as exc:
            raise AdapterError(f"{url}: {exc.reason}") from exc

    def extract_payloads(self, raw_text: str) -> list[dict[str, Any]]:
        raw_text = raw_text.lstrip("\ufeff").strip()
        if not raw_text:
            return []
        if raw_text.startswith(("{", "[")):
            return self._payloads_from_json(json.loads(raw_text))
        return self._payloads_from_html(raw_text)

    def _payloads_from_json(self, data: Any) -> list[dict[str, Any]]:
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        if not isinstance(data, dict):
            return []
        for key in ("items", "result", "results", "data", "rows", "auctions", "purchases"):
            value = data.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
            if isinstance(value, dict):
                nested = self._payloads_from_json(value)
                if nested:
                    return nested
        return [data]

    def _payloads_from_html(self, raw_text: str) -> list[dict[str, Any]]:
        payloads: list[dict[str, Any]] = []
        for match in re.finditer(
            r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
            raw_text,
            flags=re.IGNORECASE | re.DOTALL,
        ):
            try:
                payloads.extend(self._payloads_from_json(json.loads(match.group(1))))
            except json.JSONDecodeError:
                continue
        if payloads:
            return payloads
        if not self.allow_card_like_html_fallback:
            return []
        return self._extract_card_like_payloads(raw_text)

    def _extract_card_like_payloads(self, raw_text: str) -> list[dict[str, Any]]:
        title_matches = re.finditer(r"<a[^>]+href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>", raw_text, re.DOTALL)
        payloads = []
        for index, match in enumerate(title_matches, start=1):
            title = re.sub(r"<[^>]+>", " ", match.group(2))
            title = re.sub(r"\s+", " ", title).strip()
            if len(title) < 10:
                continue
            payloads.append({"id": f"html-{index}", "name": title, "url": match.group(1)})
        return payloads

    @abstractmethod
    def normalize_payload(self, payload: dict[str, Any]) -> Tender:
        raise NotImplementedError
