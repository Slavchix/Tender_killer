# Tender Killer

Личный инструмент, готовый к будущему SaaS-расширению: публично мониторит закупки Москвы и Московской области, сохраняет их в SQLite, фильтрует по профилям поиска и отправляет новые релевантные карточки в Telegram.

Система не логинится в личные кабинеты, не подает заявки, не подписывает документы и не совершает юридически значимых действий. Сейчас это слой сбора, нормализации, фильтрации и уведомлений.

## Что Уже Есть

- Модульный Python 3.12+ монолит.
- Единая модель закупки `Tender`.
- SQLite-хранилище с дедупликацией по `source + external_id`.
- Адаптеры источников `moscow` и `mosreg` с жесткой валидацией, чтобы не отправлять мусорные HTML-карточки.
- Профили поиска: регион, площадки, цена, ОКПД2, ключевые слова, стоп-слова, active-only.
- Telegram-бот с меню, ручным `/search`, статусом источников и авто-поиском по расписанию.
- CLI-команда `tender-killer` для dry-run и отладки.

Важно: для МО подключен рабочий публичный endpoint `https://api.market.mosreg.ru/api/Trade/GetTradesForParticipantOrAnonymous`. Для Москвы list endpoint еще ищется; текущий placeholder отключен и специально возвращает `Fetched=0`, чтобы не отправлять мусор.

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
- `TELEGRAM_CHAT_ID` - чат для автоматических уведомлений. Для ручного `/search` бот берет текущий чат.
- `TENDER_KILLER_DB` - путь к SQLite, по умолчанию `data/tenders.sqlite`.
- `TENDER_KILLER_DRY_RUN=1` - печатать сообщения вместо отправки.
- `TENDER_KILLER_MOSCOW_URL` - переопределить URL источника Москвы.
- `TENDER_KILLER_MOSREG_URL` - переопределить URL источника МО.
- `TENDER_KILLER_FILTERS` - путь к JSON-файлу с профилями поиска.
- `TENDER_KILLER_AUTO_SEARCH_MINUTES` - интервал авто-поиска в минутах, по умолчанию `30`.

## Профили Поиска

Фильтры теперь хранятся как набор профилей. Это нужно, чтобы отдельно искать, например, бумагу, электрику и сантехнику с разными ОКПД2, ценами и стоп-словами.

Пример лежит в `filters.example.json`:

```json
{
  "profiles": [
    {
      "id": "paper",
      "name": "Бумага",
      "profile": {
        "keywords": ["бумага", "канцелярия"],
        "exclude_keywords": ["услуги", "обслуживание"],
        "regions": ["Москва", "Московская область"],
        "sources": ["moscow", "mosreg"],
        "okpd2": ["17.12"],
        "min_price": 10000,
        "max_price": 500000,
        "only_active": true
      }
    }
  ],
  "active_profile_ids": ["paper"]
}
```

Старый одиночный `filters.json` поддерживается: при первом чтении он автоматически мигрирует в профиль `Default`.

ОКПД2 работает по префиксам: `17.12` найдет `17.12.14`, а полный код тоже можно указывать. Если нужно искать только по ОКПД2 без ключевых слов, укажите `"keywords": []`.

`only_active` по умолчанию включен. При `only_active=true` сомнительные записи без статуса и без дедлайна не проходят фильтр.

Площадки v1:

- `moscow` - Портал поставщиков Москвы `zakupki.mos.ru`.
- `mosreg` - Электронный магазин МО `market.mosreg.ru`, данные берутся через `api.market.mosreg.ru/api/Trade/GetTradesForParticipantOrAnonymous`.

## Telegram-Бот

Запуск:

```powershell
$env:TELEGRAM_BOT_TOKEN="..."
$env:TENDER_KILLER_FILTERS="filters.json"
$env:TENDER_KILLER_AUTO_SEARCH_MINUTES="30"
.\.venv\Scripts\python.exe -m tender_killer.bot
```

Для авто-поиска в фоне добавьте `TELEGRAM_CHAT_ID`. Без него ручной `/search` работает, но фоновой рассылке некуда писать.

Команды:

- `/profiles` - показать профили и их id.
- `/profile_new Бумага` - создать новый профиль.
- `/profile_edit paper okpd2 17.12` - изменить поле профиля.
- `/profile_edit paper price 10000 500000` - задать диапазон цены.
- `/profile_edit paper region Москва, Московская область` - задать регионы.
- `/profile_edit paper sources moscow, mosreg` - выбрать площадки.
- `/profile_edit paper keywords бумага, канцтовары` - задать ключевые слова.
- `/profile_edit paper exclude услуги, ремонт` - задать стоп-слова.
- `/profile_edit paper active on` - включить active-only.
- `/profile_toggle paper off` - выключить профиль из поиска.
- `/sources_status` - показать последний запуск и ошибки источников.
- `/search` - вручную запустить поиск.

Кнопки в меню дублируют основные действия. Редактирование профиля идет пошагово: выбрать профиль, выбрать поле, затем ввести значение. Быстрые команды остаются как запасной способ.

## CLI

Dry-run без Telegram:

```powershell
.\.venv\Scripts\python.exe -m tender_killer.cli --filters filters.example.json --dry-run --verbose
```

С отправкой в Telegram:

```powershell
$env:TELEGRAM_BOT_TOKEN="..."
$env:TELEGRAM_CHAT_ID="..."
.\.venv\Scripts\python.exe -m tender_killer.cli --filters filters.example.json
```

## Диагностика Источников

`/search` и `/sources_status` показывают:

- сколько закупок загружено, сохранено, сматчено и отправлено;
- какие источники упали;
- URL, HTTP-код и короткий текст ошибки, если источник вернул ошибку.

Если один источник падает, второй продолжает работать.

## Проверка

```powershell
.\.venv\Scripts\python.exe -m pytest --basetemp .pytest-tmp
```
