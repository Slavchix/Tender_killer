from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tender_killer.models import Tender
from tender_killer.models import TenderDocument
from tender_killer.normalization import parse_datetime
from tender_killer.telegram import TelegramNotifier
from tender_killer.telegram import build_tender_actions
from tender_killer.telegram import build_tender_message
from tender_killer.telegram_chat_service import get_remembered_telegram_chat_id
from tender_killer.tender_detail_service import get_tender_payload


def send_tender_notification_payload(
    database_path: str | Path,
    source: str,
    external_id: str,
    settings: Any,
    notifier: Any | None = None,
    notifier_factory=TelegramNotifier,
) -> dict[str, Any]:
    tender_payload = get_tender_payload(database_path, source, external_id)
    tender = _payload_to_tender(tender_payload)
    if notifier is None:
        bot_token = getattr(settings, "telegram_bot_token", None)
        chat_id = getattr(settings, "telegram_chat_id", None) or get_remembered_telegram_chat_id(database_path)
        missing = []
        if not bot_token:
            missing.append("TELEGRAM_BOT_TOKEN")
        if not chat_id:
            missing.append("TELEGRAM_CHAT_ID")
        if missing:
            return {
                "ok": False,
                "sent": False,
                "reason": "missing_telegram_settings",
                "missing": missing,
                "message": _missing_settings_message(missing),
            }
        sender = notifier_factory(bot_token, chat_id, dry_run=settings.dry_run)
    else:
        sender = notifier
    sent = sender.send(build_tender_message(tender, ["manual:site"]), reply_markup=build_tender_actions(tender))
    if not sent:
        return {
            "ok": False,
            "sent": False,
            "reason": "telegram_send_failed",
            "message": "Telegram настроен, но API Telegram не подтвердил отправку.",
        }
    return {"ok": True, "sent": True}


def _payload_to_tender(payload: dict[str, Any]) -> Tender:
    return Tender(
        source=payload["source"],
        external_id=payload["external_id"],
        url=payload["url"],
        title=payload["title"],
        customer=payload.get("customer"),
        region=payload.get("region"),
        price=payload.get("price"),
        currency=payload.get("currency") or "RUB",
        status=payload.get("status"),
        published_at=parse_datetime(payload.get("published_at")),
        deadline_at=parse_datetime(payload.get("deadline_at")),
        delivery_place=payload.get("delivery_place"),
        category=payload.get("category"),
        okpd2=payload.get("okpd2"),
        documents=payload.get("documents") or [],
        document_records=[
            TenderDocument(
                url=document["url"],
                name=document.get("name"),
                document_type=document.get("document_type"),
                source_document_id=document.get("source_document_id"),
                local_path=document.get("local_path"),
                downloaded_at=parse_datetime(document.get("downloaded_at")),
                text_status=document.get("text_status") or "pending",
                raw_payload=document.get("raw_payload") or {},
            )
            for document in payload.get("document_records") or []
            if document.get("url")
        ],
        raw_payload=_json_object(payload.get("raw_payload_json")),
    )


def _json_object(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    try:
        data = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _missing_settings_message(missing: list[str]) -> str:
    if missing == ["TELEGRAM_CHAT_ID"]:
        return (
            "Не задан TELEGRAM_CHAT_ID. Напишите боту любое сообщение или задайте "
            "TELEGRAM_CHAT_ID перед запуском сайта."
        )
    if missing == ["TELEGRAM_BOT_TOKEN"]:
        return "Не задан TELEGRAM_BOT_TOKEN для API сайта. Запустите сайт с тем же токеном, что и бота."
    return "Telegram не настроен для API сайта: задайте TELEGRAM_BOT_TOKEN и TELEGRAM_CHAT_ID."
