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
- `TENDER_KILLER_FILTERS` - путь к JSON-файлу с пользовательскими фильтрами.

## Пользовательские фильтры

Фильтры можно настроить через JSON-файл. Пример лежит в `filters.example.json`.

```json
{
  "keywords": ["бумага", "кабель", "крепеж"],
  "exclude_keywords": ["услуги", "обслуживание"],
  "regions": ["Москва", "Московская область"],
  "okpd2": ["17.12", "27.32.13"],
  "min_price": 10000,
  "max_price": 500000,
  "statuses": ["active", "прием"],
  "only_active": true,
  "include_without_price": true,
  "include_without_deadline": true
}
```

Программа ищет по названию, категории, адресу поставки, региону, статусу и ОКПД2. Ключевые слова понимаются мягко: `бумага` найдет закупку с текстом `бумаги`, а `кабель` - `кабеля`.

ОКПД2 работает по префиксам: `17.12` найдет `17.12.14`, а полный код `17.12.14` найдет `17.12.14` и более детальные дочерние коды. Если нужно искать только по ОКПД2 без ключевых слов, укажи `"keywords": []`.

`only_active` по умолчанию включен: завершенные, закрытые, отмененные и просроченные закупки не отправляются в Telegram.

Запуск с файлом фильтров:

```powershell
tender-killer --filters filters.example.json --dry-run
```

Или через переменную окружения:

```powershell
$env:TENDER_KILLER_FILTERS="filters.example.json"
tender-killer --dry-run
```

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
