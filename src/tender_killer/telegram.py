from __future__ import annotations

import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from tender_killer.models import Tender


def format_price(tender: Tender) -> str:
    if tender.price is None:
        return "не указана"
    return f"{tender.price:,.2f} {tender.currency}".replace(",", " ")


def build_tender_message(tender: Tender, reasons: list[str]) -> str:
    lines = [
        "Новая закупка Tender Killer",
        "",
        f"Название: {tender.title}",
        f"Источник: {tender.source}",
        f"Заказчик: {tender.customer or 'не указан'}",
        f"Сумма: {format_price(tender)}",
        f"Дедлайн: {tender.deadline_at.isoformat() if tender.deadline_at else 'не указан'}",
        f"Регион/адрес: {tender.delivery_place or tender.region or 'не указан'}",
        f"Фильтр: {', '.join(reasons) if reasons else 'материалы'}",
        "",
        tender.url,
    ]
    return "\n".join(lines)


class TelegramNotifier:
    def __init__(self, bot_token: str | None, chat_id: str | None, dry_run: bool = False) -> None:
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.dry_run = dry_run

    def send(self, text: str) -> bool:
        if self.dry_run:
            print(text)
            return True
        if not self.bot_token or not self.chat_id:
            return False
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        body = urlencode({"chat_id": self.chat_id, "text": text, "disable_web_page_preview": "true"}).encode()
        request = Request(
            url,
            data=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        with urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return bool(payload.get("ok"))

