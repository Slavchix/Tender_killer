from __future__ import annotations

import json
from dataclasses import dataclass
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from tender_killer.models import Tender
from tender_killer.sources import SOURCE_ALIASES, SOURCE_LABELS
from tender_killer.tender_metadata import normalize_law


@dataclass(frozen=True)
class TenderAction:
    action: str
    source: str
    external_id: str


def format_price(tender: Tender) -> str:
    if tender.price is None:
        return "не указана"
    return f"{tender.price:,.2f} {tender.currency}".replace(",", " ")


def build_tender_message(tender: Tender, reasons: list[str]) -> str:
    law = normalize_law(tender.raw_payload)
    source_meta = [_source_label(tender.source)]
    if law:
        source_meta.append(law)
    lines = [
        "Новая закупка",
        _shorten(tender.title, 180),
        f"Источник: {' · '.join(source_meta)}",
        f"Сумма/срок: {format_price(tender)} · {tender.deadline_at.isoformat() if tender.deadline_at else 'не указан'}",
        f"Заказчик/регион: {_shorten(tender.customer or 'не указан', 80)} · {_shorten(tender.delivery_place or tender.region or 'не указан', 80)}",
        f"Фильтр: {_shorten(', '.join(reasons) if reasons else 'материалы', 120)}",
        tender.url,
    ]
    return "\n".join(lines)


def build_tender_actions(tender: Tender) -> dict[str, list[list[dict[str, str]]]]:
    keyboard: list[list[dict[str, str]]] = []
    if tender.url:
        keyboard.append([{"text": "Открыть источник", "url": tender.url}])
    keyboard.append(
        [
            {"text": "Документы", "callback_data": _callback_data("docs", tender)},
            {"text": "Анализ", "callback_data": _callback_data("analysis", tender)},
        ]
    )
    return {"inline_keyboard": keyboard}


def parse_tender_action(value: str | None) -> TenderAction | None:
    if not value:
        return None
    parts = value.split(":", 3)
    if len(parts) != 4 or parts[0] != "tk" or parts[1] not in {"docs", "analysis"}:
        return None
    return TenderAction(action=parts[1], source=parts[2], external_id=parts[3])


class TelegramNotifier:
    def __init__(self, bot_token: str | None, chat_id: str | None, dry_run: bool = False) -> None:
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.dry_run = dry_run

    def send(self, text: str, reply_markup: dict | None = None) -> bool:
        if self.dry_run:
            print(text)
            return True
        if not self.bot_token or not self.chat_id:
            return False
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {"chat_id": self.chat_id, "text": text, "disable_web_page_preview": "true"}
        if reply_markup:
            payload["reply_markup"] = json.dumps(reply_markup, ensure_ascii=False)
        body = urlencode(payload).encode()
        request = Request(
            url,
            data=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        with urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return bool(payload.get("ok"))


def _callback_data(action: str, tender: Tender) -> str:
    return f"tk:{action}:{tender.source}:{tender.external_id}"[:64]


def _source_label(source: str) -> str:
    normalized = SOURCE_ALIASES.get(source.strip().lower())
    return SOURCE_LABELS.get(normalized or source, source)


def _shorten(value: str, limit: int) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip() + "…"
