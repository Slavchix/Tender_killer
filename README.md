# Tender Killer

## Current Handoff Snapshot

Date: 2026-05-21.

Current branch: `codex/moscow-mo-parser`.

Current product shape:

- Local React/Vite site is the main cockpit.
- Telegram is a notification channel, not the main control surface.
- SQLite is the local source of truth for tenders, documents, workflow statuses, analysis, and product profiles.
- Supported MVP sources are Moscow supplier portal and Moscow Oblast market.
- The app does not submit applications, sign documents, log into private cabinets, or perform legally significant actions.

Recent architecture cleanup:

- `web_api.py` is being split into services.
- Tender list SQL and site filter construction now live in `src/tender_killer/tender_query_service.py`.
- SQLite schema is centralized in `src/tender_killer/schema.py`.
- Adapter detail enrichment now uses public `enrich_payload(...)` contracts.
- Product profiles, document operations, and SQLite admin views were moved into separate service modules.
- Tender filtering now has normalized DB fields: `law`, `status_normalized`, `region_code`, `source_family`, `procedure_type`, `customer_inn`.
- The site exposes normalized metadata filters for source family, procedure type, and customer INN.
- Source adapters accept configurable pagination via `TENDER_KILLER_SOURCE_MAX_PAGES`.
- Source runs now keep SQLite checkpoints with last success, last seen publication date, and last error diagnostics.
- The site exposes source run diagnostics through `/api/sources/status` and shows checkpoint/error state in the tender cockpit.
- Incremental source fetches use a configurable overlap window via `TENDER_KILLER_SOURCE_OVERLAP_MINUTES`.
- Tender list pagination is explicit in the UI: the site requests bounded pages and uses API `total/limit/offset` navigation metadata.
- Workflow status persistence is isolated in `src/tender_killer/workflow_service.py`.
- Report download payload construction is isolated in `src/tender_killer/report_service.py`.
- Tender detail payload/refresh logic is isolated in `src/tender_killer/tender_detail_service.py`.
- Manual Telegram notification payload construction is isolated in `src/tender_killer/notification_service.py`.
- TZ analysis run persistence is isolated in `src/tender_killer/analysis_service.py`.
- Search run orchestration is isolated in `src/tender_killer/search_service.py`.
- The tender list has a page-size selector for 10/25/50/100 rows while keeping 25 as the default.

Current verification command:

```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp pytest-cache-files-full
```

Latest verified result before this handoff: `162 passed`.

Good next steps:

1. After architecture cleanup, return to deeper TZ extraction and product search/economics.
2. Start margin/economics workflow once product search inputs are reliable.

Личный инструмент, готовый к будущему SaaS-расширению: публично мониторит закупки Москвы и Московской области, сохраняет их в SQLite, фильтрует по профилям поиска и отправляет новые релевантные карточки в Telegram.

Система не логинится в личные кабинеты, не подает заявки, не подписывает документы и не совершает юридически значимых действий. Сейчас это слой сбора, нормализации, фильтрации и уведомлений.

## Что Уже Есть

- Модульный Python 3.12+ монолит.
- Единая модель закупки `Tender`.
- SQLite-хранилище с дедупликацией по `source + external_id`.
- Адаптеры источников `moscow` и `mosreg` с жесткой валидацией, чтобы не отправлять мусорные HTML-карточки.
- Профили поиска: закон, этап закупки, регион, площадки, цена, ОКПД2, ключевые слова, стоп-слова, active-only.
- Локальный сайт на React/Vite как основной рабочий кабинет: фильтры, список закупок, карточка, SQLite-просмотр, статусы, документы, анализ и товарные профили.
- Telegram используется как канал уведомлений: на него можно отправлять найденные/выбранные закупки, но основная работа теперь удобнее на сайте.
- Детальное обновление карточки: `POST /api/tenders/{source}/{external_id}/details/refresh` добирает документы/позиции, сохраняет их в SQLite и пересобирает товарные профили.
- Документы закупки: скачивание, извлечение текста из DOCX/PDF/TXT/HTML и отображение статуса по каждому документу.
- Первый rule-based анализ ТЗ: требования, риски, красные флаги, национальный режим/1875, сертификаты, приемка, обеспечение, штрафы.
- Товарные профили в SQLite: один тендер может иметь 20-40 отдельных профилей, по одному на позицию закупки.
- Word-отчет по закупке: паспорт, позиции, документы, выжимка ТЗ, товарные профили и заготовка под будущий расчет экономики.
- CLI-команда `tender-killer` для dry-run и отладки.

Важно: для МО подключен рабочий публичный endpoint `https://api.market.mosreg.ru/api/Trade/GetTradesForParticipantOrAnonymous`, документы добираются через `GET https://api.market.mosreg.ru/api/Trade/{Id}/GetTradeDocuments`. Для Москвы используется list endpoint `https://old.zakupki.mos.ru/api/Cssp/Purchase/Query`, а детальная карточка добирается через `https://zakupki.mos.ru/newapi/api/Auction/Get?auctionId=...`.

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
- `TENDER_KILLER_SOURCE_MAX_PAGES` - сколько страниц запрашивать у каждого источника, по умолчанию `1`.
- `TENDER_KILLER_SOURCE_OVERLAP_MINUTES` - на сколько минут откатывать checkpoint при инкрементальном поиске, по умолчанию `60`.

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
        "sources": ["mosreg"],
        "laws": ["44-ФЗ"],
        "okpd2": ["17.12"],
        "statuses": ["прием предложений", "прием заявок", "active"],
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

Сейчас Telegram лучше рассматривать как уведомления, а не как основной интерфейс. Фильтры, карточки, документы, анализ и товарные профили удобнее смотреть на сайте.

Запуск:

```powershell
$env:TELEGRAM_BOT_TOKEN="..."
$env:TENDER_KILLER_FILTERS="filters.json"
$env:TENDER_KILLER_AUTO_SEARCH_MINUTES="30"
.\.venv\Scripts\python.exe -m tender_killer.bot
```

Для авто-поиска в фоне добавьте `TELEGRAM_CHAT_ID`. Без него ручной `/search` работает, но фоновой рассылке некуда писать.

Команды:

- `Настроить поиск` - мастер создания профиля: шаблон, закон, этап, регион, цена, ОКПД2, площадки.
- `/profiles` - показать профили и их id.
- `/profile_new Бумага` - создать новый профиль.
- `/profile_edit paper law 44-ФЗ` - задать закон.
- `/profile_edit paper stage Подача заявок` - задать этап закупки.
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
- `/test_search` - тестово показать подходящие карточки повторно, даже если они уже были отправлены.

Кнопки в меню дублируют основные действия. `Настроить поиск` создает профиль через готовые шаблоны: `Бумага/канцелярия`, `Хозтовары`, `Картриджи/оргтехника`, `Электрика`, `Сантехника`, `Стройматериалы`. `Тест поиска` нужен для проверки новых фильтров: он повторно показывает уже известные подходящие карточки, но обычный `Запустить поиск` не спамит дублями. Редактирование профиля идет пошагово: выбрать профиль, выбрать поле, затем ввести значение.

## Локальный Сайт

Сайт - основной рабочий интерфейс текущего MVP.

Backend API:

```powershell
.\.venv\Scripts\python.exe -m tender_killer.web_api --host 127.0.0.1 --port 8000
```

Frontend:

```powershell
cd web
npm run dev
```

Открыть: `http://127.0.0.1:5173`.

На сайте сейчас есть:

- фильтры по площадке, закону, региону, статусу, ОКПД2/классификатору и цене;
- ручной запуск поиска;
- список закупок с количеством документов и позиций;
- правая карточка с вкладками `Обзор`, `Товары`, `Документы`, `Анализ`, `Статус`;
- кнопка `Обновить` для добора детальной карточки;
- скачивание документов и извлечение текста;
- rule-based анализ ТЗ;
- товарные профили по позициям закупки;
- скачивание Word-отчета;
- отправка выбранной закупки в Telegram;
- SQLite-viewer для локальной диагностики базы.

Правая карточка специально сделана вкладками, чтобы не перегружать интерфейс: сайт должен быть коротким экраном решения, а полный разбор уходит в документы, товарные профили и Word-отчет.

## Товарные Профили И Анализ

Товарный профиль - это мост между закупкой и будущим парсером поставщиков. Он строится по позициям закупки, а если позиции пока не найдены, использует fallback из карточки.

Профиль хранит:

- наименование и детальное описание товара;
- количество, единицу, цену за единицу и сумму;
- ОКПД2/КОЗ/тип классификатора;
- требования, ГОСТ/ТУ, сертификаты/декларации;
- поисковые фразы и стоп-слова;
- evidence, статус и уверенность.

Следующий большой слой после MVP: дополнять эти профили требованиями из ТЗ и использовать их для поиска товаров, расчета закупочной цены, доставки, налогов, минимальной ставки и маржи.

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

В Codex sandbox полный прогон может падать на `tmp_path`/`basetemp` с `PermissionError`, потому что часть тестов создает временные SQLite/документные файлы. В таком случае запускать проверку вне sandbox:

```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp pytest-cache-files-full
```
