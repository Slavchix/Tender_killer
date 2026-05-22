from tender_killer.models import Tender
from tender_killer.telegram import TelegramNotifier
from tender_killer.telegram import build_tender_actions
from tender_killer.telegram import build_tender_message
from tender_killer.telegram import parse_tender_action


def test_build_tender_message_contains_decision_fields():
    tender = Tender(
        source="moscow_supplier_portal",
        external_id="1",
        url="https://example.test/1",
        title="Поставка бумаги офисной",
        customer="ГБУ Школа",
        region="Москва",
        price=42000,
        currency="RUB",
        status="active",
        delivery_place="Москва",
    )

    message = build_tender_message(tender, ["бумага", "канцелярия"])

    assert "Поставка бумаги офисной" in message
    assert "ГБУ Школа" in message
    assert "42 000.00 RUB" in message
    assert "бумага, канцелярия" in message
    assert "https://example.test/1" in message


def test_build_tender_message_is_compact_and_uses_action_labels():
    tender = Tender(
        source="moscow_supplier_portal",
        external_id="10205128",
        url="https://example.test/10205128",
        title="Поставка очень длинного набора офисной бумаги и канцелярских товаров для образовательной организации",
        customer="ГБУ Школа",
        region="Москва",
        price=98084,
        currency="RUB",
        status="active",
        delivery_place="Москва",
        raw_payload={"law": "44-ФЗ"},
    )

    message = build_tender_message(tender, ["бумага", "канцелярия"])

    assert len(message.splitlines()) <= 9
    assert "Новая закупка" in message
    assert "Источник: Москва: zakupki.mos.ru" in message
    assert "44-ФЗ" in message
    assert "Документы" not in message
    assert "ИИ" not in message


def test_build_tender_actions_adds_safe_inline_buttons():
    tender = Tender(
        source="mosreg_market",
        external_id="3668200",
        url="https://market.mosreg.ru/Trade/ViewTrade/3668200",
        title="Paper tender",
    )

    actions = build_tender_actions(tender)

    assert actions == {
        "inline_keyboard": [
            [{"text": "Открыть источник", "url": "https://market.mosreg.ru/Trade/ViewTrade/3668200"}],
            [
                {"text": "Документы", "callback_data": "tk:docs:mosreg_market:3668200"},
                {"text": "Анализ", "callback_data": "tk:analysis:mosreg_market:3668200"},
            ],
        ]
    }
    assert parse_tender_action("tk:docs:mosreg_market:3668200").action == "docs"


def test_telegram_notifier_posts_reply_markup(monkeypatch):
    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return b'{"ok": true}'

    def fake_urlopen(request, timeout):
        captured["request"] = request
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr("tender_killer.telegram.urlopen", fake_urlopen)
    notifier = TelegramNotifier("token", "123")

    sent = notifier.send(
        "text",
        reply_markup={"inline_keyboard": [[{"text": "Open", "url": "https://example.test"}]]},
    )

    assert sent is True
    assert captured["timeout"] == 20
    body = captured["request"].data.decode("utf-8")
    assert "reply_markup=" in body
    assert "%22inline_keyboard%22" in body
