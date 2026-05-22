from __future__ import annotations

from tender_killer.models import Tender
from tender_killer.notification_service import send_tender_notification_payload
from tender_killer.storage import TenderStore


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
