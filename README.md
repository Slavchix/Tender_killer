# Tender Killer

Личный инструмент, готовый к будущему SaaS-расширению: публично мониторит закупки Москвы и Московской области, сохраняет их в SQLite, фильтрует широкие категории материалов и отправляет новые релевантные карточки в Telegram.

## Что уже есть

- Два адаптера источников: `zakupki.mos.ru` и `market.mosreg.ru`.
- Единая модель закупки `Tender`.
- SQLite-хранилище с дедупликацией по `source + external_id`.
- Фильтр широких категорий материалов.
- Telegram-уведомления с dry-run режимом.
- CLI-команда `tender-killer`.

Система не логинится в личные кабинеты, не подаёт заявки, не подписывает документы и не совершает юридически значимых действий.

## Установка

Нужен Python 3.12+.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

## Настройки

Переменные окружения:

- `TELEGRAM_BOT_TOKEN` - токен Telegram-бота.
- `TELEGRAM_CHAT_ID` - чат для уведомлений.
- `TENDER_KILLER_DB` - путь к SQLite, по умолчанию `data/tenders.sqlite`.
- `TENDER_KILLER_DRY_RUN=1` - печатать сообщения вместо отправки.
- `TENDER_KILLER_MOSCOW_URL` - переопределить URL источника Москвы.
- `TENDER_KILLER_MOSREG_URL` - переопределить URL источника МО.

## Запуск

Dry-run без Telegram:

```powershell
tender-killer --dry-run --verbose
```

С отправкой в Telegram:

```powershell
$env:TELEGRAM_BOT_TOKEN="..."
$env:TELEGRAM_CHAT_ID="..."
tender-killer
```

## Проверка

```powershell
pytest
```

