from __future__ import annotations

from tender_killer.models import Tender
from tender_killer.notification_service import send_tender_notification_payload
from tender_killer.storage import TenderStore
from tender_killer.telegram_chat_service import remember_telegram_chat


def test_send_tender_notification_payload_sends_selected_card(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="3668200",
            url="https://market.mosreg.ru/Trade/ViewTrade/3668200",
            title="Paper tender",
        )
    )

    class FakeSettings:
        telegram_bot_token = "token"
        telegram_chat_id = "123"
        dry_run = False

    class FakeNotifier:
        def __init__(self):
            self.messages = []
            self.reply_markups = []

        def send(self, text, reply_markup=None):
            self.messages.append(text)
            self.reply_markups.append(reply_markup)
            return True

    notifier = FakeNotifier()

    payload = send_tender_notification_payload(
        store.database_path,
        "mosreg_market",
        "3668200",
        FakeSettings(),
        notifier=notifier,
    )

    assert payload == {"ok": True, "sent": True}
    assert len(notifier.messages) == 1
    assert "Paper tender" in notifier.messages[0]
    assert notifier.reply_markups[0]["inline_keyboard"][0][0]["text"] == "Открыть источник"


def test_send_tender_notification_payload_reports_missing_settings(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="3668200",
            url="https://market.mosreg.ru/Trade/ViewTrade/3668200",
            title="Paper tender",
        )
    )

    class FakeSettings:
        telegram_bot_token = None
        telegram_chat_id = None
        dry_run = False

    payload = send_tender_notification_payload(
        store.database_path,
        "mosreg_market",
        "3668200",
        FakeSettings(),
    )

    assert payload["ok"] is False
    assert payload["sent"] is False
    assert payload["reason"] == "missing_telegram_settings"
    assert payload["missing"] == ["TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"]
    assert "TELEGRAM_BOT_TOKEN" in payload["message"]


def test_send_tender_notification_payload_uses_remembered_chat_id(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="3668200",
            url="https://market.mosreg.ru/Trade/ViewTrade/3668200",
            title="Paper tender",
        )
    )
    remember_telegram_chat(store.database_path, "777")
    captured = {}

    class FakeSettings:
        telegram_bot_token = "token"
        telegram_chat_id = None
        dry_run = False

    class FakeNotifier:
        def __init__(self, token, chat_id, dry_run=False):
            captured["token"] = token
            captured["chat_id"] = chat_id
            captured["dry_run"] = dry_run

        def send(self, text, reply_markup=None):
            captured["text"] = text
            captured["reply_markup"] = reply_markup
            return True

    payload = send_tender_notification_payload(
        store.database_path,
        "mosreg_market",
        "3668200",
        FakeSettings(),
        notifier_factory=FakeNotifier,
    )

    assert payload == {"ok": True, "sent": True}
    assert captured["token"] == "token"
    assert captured["chat_id"] == "777"
    assert captured["reply_markup"]["inline_keyboard"][0][0]["text"] == "Открыть источник"
