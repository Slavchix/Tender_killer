# Project Context

Дата старта: 2026-05-18.

## Идея продукта

Tender Killer - будущий софт для поставщиков в госзакупках. Главная ценность: до подачи заявки быстро понять, есть ли экономический смысл участвовать в закупке, какая будет чистая маржа и какие риски могут съесть прибыль.

## Пользовательский сценарий

Сначала продукт создается для собственного участия в закупках. После проверки на реальном опыте планируется превратить его в подписочный сервис через сайт и/или Telegram-бот.

## Первая ниша

Фокус - поставка материалов, потому что это кажется проще услуг. Материалы разные: часть требует сертификатов, деклараций, лицензий или других документов, часть проще. Для поиска и фильтрации важны ОКПД2 и, где применимо, КТРУ.

## Предварительный MVP

Не делать сразу "всю систему госзакупок". Первый полезный продукт - маржинальный радар:

1. Находит закупку.
2. Разбирает предмет закупки и позиции.
3. Сопоставляет позиции с ценами поставщиков.
4. Считает себестоимость, налоги, доставку, обеспечения, комиссии и заморозку денег.
5. Показывает маржу и стоп-цену.
6. Подсвечивает красные флаги.
7. Помогает решить: участвовать, смотреть осторожно или пропустить.

## MVP parser implementation checkpoint

На ветке `codex/moscow-mo-parser` реализован первый технический MVP:

- Python 3.12 модульный монолит с SQLite-хранилищем, дедупликацией по `source + external_id` и Telegram-уведомлениями.
- Первые источники: `moscow` = Портал поставщиков Москвы `zakupki.mos.ru`, `mosreg` = электронный магазин МО `market.mosreg.ru`.
- Фильтры вынесены в JSON-профиль и могут настраиваться по регионам, диапазону цены, ОКПД2, ключевым словам, стоп-словам, active-only режиму и выбранным площадкам.
- ОКПД2 работает по префиксам: `17.12` ловит `17.12.14`, полный код тоже можно указывать.
- Завершенные, закрытые, отмененные и просроченные закупки по умолчанию не отправляются.
- Telegram-бот добавлен как быстрый личный интерфейс настройки фильтров. Команды: `/filters`, `/region`, `/price`, `/okpd2`, `/sources`, `/active`, `/search`.
- Бот меняет тот же локальный файл фильтров, который читает CLI. На текущем этапе это быстрее и проще, чем отдельный веб-кабинет; позже эти же профили можно перенести в SaaS-хранилище.
- Бот работает только пока локально запущен процесс `python -m tender_killer.bot` и выставлен корректный `TELEGRAM_BOT_TOKEN`. Публикация в GitHub сама по себе бота не запускает.
- Важно: Telegram-токен был однажды вставлен в чат, поэтому для долгого использования безопаснее перевыпустить токен через BotFather.

## Telegram profiles and source diagnostics checkpoint

Дата: 2026-05-19.

- Фильтры переведены из одиночного JSON-профиля в коллекцию профилей: `profiles` + `active_profile_ids`.
- Каждый профиль хранит `name`, `regions`, `sources`, `okpd2`, `min_price`, `max_price`, `keywords`, `exclude_keywords`, `only_active`.
- Старый формат `filters.json` поддерживается через автоматическую миграцию в профиль `Default`.
- Telegram-команды профилей: `/profiles`, `/profile_new`, `/profile_edit`, `/profile_toggle`, `/sources_status`, `/search`.
- Меню бота теперь показывает основные действия: профили, создание профиля, редактирование, включение/выключение, запуск поиска и статус источников.
- Поиск работает по всем активным профилям; отключенные профили не участвуют.
- Добавлен фоновый авто-поиск внутри процесса бота, интервал задается `TENDER_KILLER_AUTO_SEARCH_MINUTES`, по умолчанию 30 минут. Для авто-отправки нужен `TELEGRAM_CHAT_ID`.
- Summary `/search` теперь показывает не только `FailedSources=1`, но и конкретные ошибки источников с URL/HTTP-кодом/коротким текстом.
- `/sources_status` показывает последний запуск и ошибки источников.
- Текущее важное правило сохранено: лучше `Fetched=0`, чем мусорная карточка из HTML.
- Проверка публичных endpoints: `zakupki.mos.ru/newapi/api/Auction/Get` без нужных параметров возвращает JSON-ошибку 400, `market.mosreg.ru/api/Purchase/Get` возвращает HTML главной страницы. У `api.market.mosreg.ru` найден JSON `Common/TradesFilterContent`, но это справочник фильтров, не список закупок. Подтвержденные стабильные list endpoints Москвы/МО еще надо найти отдельно через браузерную сетевую диагностику.

## Mosreg working endpoint checkpoint

Дата: 2026-05-19.

- Через Network на `market.mosreg.ru` найден рабочий публичный endpoint списка закупок МО: `POST https://api.market.mosreg.ru/api/Trade/GetTradesForParticipantOrAnonymous`.
- Payload v1: `tradeState="15"` для активных закупок, `page=1`, `itemsPerPage=50`, `UsedClassificatorType=20`, пустые фильтры цены/дат/классификаторов.
- Endpoint работает без сохранения пользовательского `Authorization: Bearer ...`; токен из браузера не нужен в коде и не должен храниться в репозитории.
- Ответ содержит `totalpages`, `totalrecords`, `invdata`. Основные поля: `Id`, `TradeName`, `CustomerFullName`, `InitialPrice`, `TradeStateName`, `FillingApplicationEndDate`, `PublicationDate`, `CategoryName`, `SourcePlatformName`.
- Детальная ссылка строится как `https://market.mosreg.ru/Trade/ViewTrade/{Id}`.
- Документы конкретной закупки доступны через `GET https://api.market.mosreg.ru/api/Trade/{Id}/GetTradeDocuments`.
- Dry-run после подключения МО: `Fetched=50 Saved=50 Matched=14 Notified=14 FailedSources=0`.
- Москва пока не подключена к реальному list endpoint; placeholder `zakupki.mos.ru/newapi/api/Auction/Get` отключен на уровне адаптера и возвращает пустой список.

## Telegram filter UX checkpoint

Дата: 2026-05-19.

- Фильтры в Telegram переводятся от ручного редактирования командой к мастеру `Настроить поиск`.
- Мастер создает профиль по шаблону категории: `Бумага/канцелярия`, `Хозтовары`, `Картриджи/оргтехника`, `Электрика`, `Сантехника`, `Стройматериалы`.
- После шаблона пользователь выбирает закон (`44-ФЗ`, `223-ФЗ`, `44-ФЗ + 223-ФЗ`), этап (`Подача заявок`, `Работа комиссии`, `Закупка отменена`, `Закупка завершена`, `Все этапы`), регион, цену и ОКПД2.
- В профиль добавлено поле `laws`; фильтр закона смотрит на данные источника, например `SourcePlatformName` из МО (`ЕАСУЗ 44`).
- Этап закупки хранится через `statuses`; пресет `Подача заявок` включает active-only, остальные этапы отключают strict active-only.
- Ориентир UX: фильтры должны быть ближе к панели поискового робота: закон, этап, регион, ОКПД2, площадки, цена, активность. Ключевые слова остаются внутри шаблонов и расширенного редактирования.
- Добавлен режим `Тест поиска` / `/test_search`: он отправляет подходящие карточки повторно, даже если они уже были в таблице уведомлений. Это нужно для проверки новых фильтров; обычный `/search` сохраняет дедупликацию и не спамит дублями.

## Источники закупок

Основные источники для изучения и будущих адаптеров:

- ЕИС `zakupki.gov.ru` - центральный источник по 44-ФЗ и части 223-ФЗ.
- Федеральные ЭТП: Сбербанк-АСТ, РТС-тендер, Росэлторг/ЕЭТП, ТЭК-Торг, ЭТП ГПБ, ЗаказРФ, РАД, ЭТС.
- Портал поставщиков Москвы `zakupki.mos.ru` - важный источник малых закупок Москвы.
- Электронный магазин Московской области `market.mosreg.ru`.
- ЕАТ "Березка" `agregatoreat.ru`.
- Платные агрегаторы: Контур.Закупки, Тендерплан, Bicotender.

## API и парсеры

Парсер будет не один. Нужна архитектура адаптеров, которые приводят разные источники к единому формату.

Предварительная карта:

- ЕИС: SOAP/XML сервисы отдачи данных, токен, отдельный `eis_adapter`.
- 44-ФЗ на федеральных ЭТП: на старте лучше брать публичную информацию через ЕИС, а не парсить каждую ЭТП отдельно.
- ТЭК-Торг: есть отдельный API `https://api.tektorg.ru`, SOAP и JSON-описание ресурсов; потенциальный отдельный адаптер.
- Портал поставщиков Москвы: публичной стабильной API-документации пока не найдено; вероятно нужен отдельный HTTP/HTML/внутренний JSON-парсер после изучения сетевых запросов.
- Электронный магазин МО: публичной API-документации пока не найдено; нужен отдельный адаптер.
- Березка: публичная API-документация не подтверждена; вероятно отдельный адаптер или интеграция после регистрации.
- Контур.Закупки, Тендерплан, Bicotender: есть коммерческие API, можно рассматривать как быстрый платный источник данных.

## Расчет маржи

Для решения "участвовать или нет" нужно учитывать:

- НМЦК или бюджет закупки;
- закупочную цену материала;
- доставку, погрузку, упаковку, хранение;
- налог;
- комиссию площадки, если есть;
- обеспечение заявки;
- обеспечение контракта;
- банковскую гарантию, если нужна;
- срок оплаты и стоимость заморозки денег;
- требования к сертификатам, декларациям, лицензиям;
- национальный режим и страну происхождения;
- надежность заказчика;
- срок поставки и реалистичность исполнения.

## Важные правовые ориентиры

- 44-ФЗ - более формализованные государственные и муниципальные закупки.
- 223-ФЗ - закупки госкорпораций и компаний с госучастием, где правила зависят от положения о закупке заказчика.
- Малые закупки не стоит жестко считать только "до 100 000 рублей": в документах найдено противоречие, а актуальные лимиты зависят от основания и формата закупки.

## Web workspace checkpoint

Дата: 2026-05-19.

- Принято продуктовое разделение: сайт становится основной рабочей панелью для просмотра, фильтрации и будущего анализа закупок; Telegram-бот остается каналом уведомлений о новых подходящих закупках.
- Добавлен локальный Vite + React интерфейс в `web/`, запуск из корня проекта через `npm run dev`. Скрипт одновременно поднимает Python API и Vite dev server.
- Добавлен локальный HTTP API `tender_killer.web_api` поверх SQLite: `GET /api/health`, `GET /api/tenders`, `GET /api/tenders/{source}/{external_id}`.
- Сайт читает закупки из SQLite и поддерживает фильтры: поиск по названию/заказчику/raw payload, площадка, закон (`44-ФЗ`/`223-ФЗ`), регион, статус/активность, ОКПД2-префикс, минимальная и максимальная цена.
- В интерфейсе видны основные поля карточки: источник, номер, цена, дедлайн, статус, регион, заказчик, ссылка на источник, документы и сырые признаки (`Закон`, `ОКПД2`, `Категория`).
- Telegram-профили пока остаются отдельным механизмом настройки поиска/уведомлений; сайт на этом этапе является панелью просмотра сохраненной SQLite-истории. Следующий логичный шаг - добавить рабочие статусы на сайте: `Новая`, `Открыта`, `Интересно`, `В работу`, `Пропустить`, `Архив`.
- Проверка перед публикацией: `pytest` показал `68 passed`, Vite production build прошел, локальная страница открылась в браузере и отрисовала фильтры без console errors.

## Web search and Telegram notification checkpoint

Дата: 2026-05-20.

- Принято финальное разделение MVP: сайт - основное рабочее место, Telegram - только канал уведомлений.
- Кнопка `Запустить поиск` на сайте отправляет текущие фильтры экрана в API и запускает поиск именно по ним, а не по старым Telegram-профилям из `filters.json`.
- После поиска сайт перезагружает список с теми же фильтрами, чтобы счетчик `Matched` и видимые карточки не жили разными логиками.
- Telegram-уведомления в web/API режиме работают в режиме `new_only`: отправляются только закупки, впервые созданные в SQLite на текущем запуске и прошедшие фильтр.
- Старые закупки остаются на сайте и повторно в Telegram не отправляются, даже если токен Telegram был включен позже.
- В summary сайта добавлен признак `Telegram=on/off`, чтобы понимать, настроены ли `TELEGRAM_BOT_TOKEN` и `TELEGRAM_CHAT_ID`.
- Фоновый поиск оставляется как будущая возможность, но он должен использовать тот же принцип `new_only`, чтобы не спамить архивом.
- Telegram-бот постепенно превращается в notification-only канал; настройки, фильтры, статусы и ручной запуск должны жить на сайте.

## Future analyst and critic agents

Дата: 2026-05-20.

- Для автоматической расстановки статусов нужна не одна LLM, а минимум двухэтапная схема: агент-аналитик и агент-критик.
- Агент-аналитик разбирает карточку, документы, ТЗ, позиции, требования, сроки, поставку, сертификаты, национальный режим, цену, себестоимость, доставку, обеспечение, налоги и предварительную маржу.
- Выход аналитика должен быть структурированным: `summary`, `items`, `requirements`, `risks`, `economics`, `recommended_status`, `confidence`, `reasons`.
- Агент-критик повторно анализирует тендер и вывод аналитика. Его задача - искать пропуски, завышенную уверенность, скрытые требования, нереалистичную маржу, неподходящий товар, проблемы с сертификатами/лицензиями/СРО, поставкой, приемкой и оплатой.
- Финальный статус не должен ставиться без правил согласования:
  - аналитик рекомендует `Интересно`, критик согласен - ставим `Интересно`;
  - аналитик рекомендует `Интересно`, критик нашел блокирующий риск - ставим `Нужна проверка`;
  - аналитик рекомендует `Пропустить`, критик согласен - ставим `Пропустить`;
  - аналитик и критик расходятся - ставим `Нужна проверка`, а не автоматическое решение.
- Будущие рабочие статусы: `Новая`, `Анализируется`, `Интересно`, `В работу`, `Нужна проверка`, `Пропустить`, `Архив`.
- Автоматический статус всегда должен сохранять объяснение: какие факты повлияли на решение, какие риски найдены, чего не хватает для уверенного решения.
- Ручное изменение статуса на сайте должно оставаться главным: пользователь может переопределить решение агентов, а система должна хранить это как пользовательское решение.

## Mosreg detail data and web workspace checkpoint

Дата: 2026-05-20.

- Добавлен фундамент detail-данных для МО: модель `TenderItem`, SQLite-таблица `tender_items`, сохранение позиций вместе с закупкой и выдача позиций через detail API.
- `MosregMarketAdapter` умеет нормализовать позиции из payload, если источник отдает массивы вроде `TradeObjects`, `Products`, `Items`, `Positions`.
- Проверенные endpoint-ы МО для позиций `GetTradeProducts`, `GetTradeObjects`, `GetTradePositions`, `GetTradeItems` вернули 404; подтвержденный endpoint документов - `GET https://api.market.mosreg.ru/api/Trade/{Id}/GetTradeDocuments`.
- Адаптер МО теперь может добирать реальные документы через `GetTradeDocuments`; если запрос документов не сработал, остается fallback на endpoint документов.
- Сайт показывает `items_count` в списке и блок `Позиции закупки` в карточке: наименование, детализация, количество, цена за единицу, сумма, ОКПД2/КОЗ.
- Документы в карточке сайта теперь отображаются как кликабельные ссылки.
- Улучшена рабочая панель сайта: добавлена кнопка `Очистить`, вкладки по рабочим статусам, фильтр `workflow_status` в API и ручная кнопка `Отправить в Telegram` из карточки.
- Следующий важный шаг по данным: найти реальный network endpoint МО для позиций на detail-странице или извлечь позиции из документа/ТЗ после скачивания документов.

## Web filter UX checkpoint

Дата: 2026-05-20.

- Фильтры сайта переведены из технической формы в рабочую панель: площадки выбираются мультикнопками, закон и статус - сегментированными переключателями, регион - быстрыми кнопками и ручным вводом.
- Статус по умолчанию для сайта теперь `active`, чтобы завершенные закупки не попадали в рабочую выдачу без явного переключения.
- ОКПД2 на сайте принимает несколько префиксов через запятую, например `17.12, 22.23, 27`.
- Backend API поддерживает мультивыбор `source`, `law`, `region`, `okpd2`; быстрый регион `Москва + МО` разворачивается в `Москва` и `Московская область`.
- SQLite-выдача умеет фильтровать ОКПД2 не только по полю закупки, но и по сохраненным позициям `tender_items.okpd2`.
- На сайте добавлен блок `Применено сейчас`, чтобы видеть фактические условия текущей выдачи.

## Local SQLite admin viewer checkpoint

Дата: 2026-05-20.

- Для личной локальной версии добавлен встроенный read-only просмотр SQLite прямо на сайте через верхнюю кнопку `SQLite`.
- Backend API добавил админские read-only endpoints: `GET /api/db/tables` и `GET /api/db/tables/{table}`.
- В целях безопасности MVP использует allowlist таблиц: `tenders`, `tender_items`, `tender_workflow`; произвольные таблицы и `sqlite_master` не отдаются.
- На сайте экран SQLite показывает список таблиц с количеством строк, строки выбранной таблицы, колонки и поиск по содержимому таблицы.
- Это личная/админская функция. При появлении ролей и пользователей экран SQLite должен быть доступен только администраторам, а обычным пользователям показывать только рабочие закупки и аналитику.

## Moscow detail enrichment checkpoint

Дата: 2026-05-20.

- Подтвержден публичный detail endpoint Москвы: `GET https://zakupki.mos.ru/newapi/api/Auction/Get?auctionId={id}`. Без авторизации он вернул карточку КС с `items`, `auctionItem`, `deliveries`, `files`, `federalLawName`, `state`, `startCost`.
- `MoscowSupplierPortalAdapter` теперь после списка закупок добирает detail JSON по `auctionId` и кладет его в `raw_payload.__detail`.
- Для Москвы теперь нормализуются позиции `TenderItem`: наименование, количество, единица измерения, цена за единицу, сумма, классификационный/описательный признак из `okpdName`.
- Для Москвы теперь нормализуются документы из `files`/`licenseFiles` в download-ссылки `newapi/api/FileStorage/Download?id=...&fileName=...`.
- Карточка сайта показывает имя московского файла из `fileName` query-параметра, а не технический путь `Download`.
- Проверка на живом endpoint: один реальный московский тендер вернул 2 документа и 1 позицию.

## Tender documents layer checkpoint

Дата: 2026-05-20.

- Документы вынесены в отдельную модель `TenderDocument` и SQLite-таблицу `tender_documents`.
- Для каждого документа сохраняются: `name`, `document_type`, `url`, `source_document_id`, `local_path`, `downloaded_at`, `text_status`, `raw_payload_json`.
- `TenderStore.upsert_tender` теперь сохраняет документы отдельно, при повторном поиске не затирая уже скачанный `local_path/downloaded_at`.
- Detail API карточки возвращает `document_records`; старый `documents_json` остается для совместимости.
- Добавлен endpoint `POST /api/tenders/{source}/{external_id}/documents/download`: скачивает документы выбранной закупки в `data/documents/{source}/{external_id}/` и обновляет `local_path`, `downloaded_at`, `text_status`.
- Для старых закупок, у которых есть только `documents_json`, скачивание делает fallback-заполнение `tender_documents`.
- Сайт показывает документы таблицей: имя, тип, статус скачивания и будущий статус извлечения текста; добавлена кнопка `Скачать документы`.
- Следующий логичный слой: извлечение текста из `.docx`, `.pdf`, `.xlsx` и сохранение результата для будущего анализа ТЗ.

## Document text extraction checkpoint

Дата: 2026-05-20.

- Подключен следующий слой конвейера документов: скачанный файл теперь можно превратить в машинно-читаемый текст прямо из карточки закупки на сайте.
- SQLite-таблица `tender_documents` расширена полями `text_content`, `text_extracted_at`, `text_error`; старые базы автоматически получают эти колонки при обращении через API.
- Добавлен backend endpoint `POST /api/tenders/{source}/{external_id}/documents/extract-text`.
- Извлечение текста использует существующий `DocumentTextExtractor` из `src/tender_killer/documents.py`: поддерживаются `.docx`, `.xlsx`, `.zip`, текстовые форматы и простой best-effort для `.pdf`.
- Если локальный файл документа отсутствует, документ получает `text_status = missing_file`, а ошибка сохраняется в `text_error`; это видно на сайте и в SQLite.
- Карточка сайта теперь показывает кнопку `Извлечь текст`, результат обработки, `text_status`, ошибку и короткое превью извлеченного текста.
- Это еще не LLM-анализ ТЗ. Это подготовительный слой: `карточка закупки -> документы -> локальные файлы -> текст -> будущий аналитик/критик`.

## Rule-based TZ analysis checkpoint

Дата: 2026-05-20.

- Добавлен первый слой анализа ТЗ без LLM: `src/tender_killer/analysis.py`.
- Анализатор читает извлеченный текст документов и детерминированно ищет признаки, важные поставщику материалов:
  - сертификаты и декларации;
  - сроки поставки;
  - приемку через ЕИС;
  - ГОСТ/ТУ;
  - обеспечение исполнения контракта и независимую гарантию;
  - штрафы/пени;
  - национальный режим, страну происхождения и постановление 1875;
  - лицензии/СРО.
- Результат сохраняется в новую SQLite-таблицу `tender_analysis`: `summary`, `requirements_json`, `risks_json`, `red_flags_json`, `recommended_status`, `confidence`, `raw_payload_json`, `analyzed_at`.
- Добавлен API endpoint `POST /api/tenders/{source}/{external_id}/analysis/run`.
- `get_tender_payload` теперь возвращает блок `analysis`, если анализ уже запускался.
- Сайт получил блок `Выжимка ТЗ` с кнопкой `Проанализировать ТЗ`, краткой выжимкой, требованиями, рисками, красными флагами, статусом и уверенностью.
- На этом этапе анализатор намеренно осторожный: базовый статус `needs_review` / `Нужна проверка`. Автоматическое `Интересно` или `Пропустить` лучше включать позже, когда появятся расчет экономики, товары, маржа и агент-критик.

## Tender Word report checkpoint

Дата: 2026-05-20.

- Добавлен DOCX-отчет v1 без внешних зависимостей: `src/tender_killer/reports.py` собирает Word-файл через стандартный ZIP/XML.
- Отчет предназначен не для краткого UI, а как рабочий документ для сохранения и дальнейшего пополнения.
- В отчет входят:
  - паспорт закупки: номер, источник, ссылка, заказчик, регион, статус, цена, дедлайн;
  - блок `Что закупают`: позиции, количество, единица, цена, сумма, ОКПД2/КОЗ;
  - документы: имя, тип, статус извлечения текста;
  - выжимка ТЗ, требования, риски, красные флаги и предварительный статус;
  - заготовка `Будущий расчет экономики` для будущих товаров, поставщиков, доставки, налогов, маржи и минимальной ставки;
  - фрагменты извлеченного текста для проверки источника выводов.
- Добавлен endpoint `GET /api/tenders/{source}/{external_id}/report.docx`, который сразу отдает скачиваемый Word-файл.
- На сайте в карточке закупки добавлена кнопка `Скачать отчет Word`.
- Дальше сайт должен оставаться коротким “экраном решения”, а полный разбор и будущая экономика будут расти внутри Word-отчета.

## Product search profile checkpoint

Дата: 2026-05-21.

- Добавлен мост между закупкой и будущим парсером товаров: `src/tender_killer/product_profile.py`.
- `get_tender_payload` теперь возвращает `product_profiles`.
- Каждый товарный профиль содержит:
  - `product_name`;
  - `category`;
  - `okpd2`;
  - `quantity`;
  - `unit`;
  - `required_characteristics`;
  - `search_phrases`;
  - `stop_words`;
  - `source` (`item` или `card`).
- Если структурированные позиции найдены, профиль строится по позициям. Если позиций нет, используется fallback из карточки: название закупки, категория, ОКПД2/КОЗ и цена.
- На сайте добавлен блок `Товарный профиль`: он показывает товар, ОКПД2/КОЗ, количество, поисковые фразы, характеристики и стоп-слова.
- Word-отчет получил раздел `Товарный профиль для поиска`, чтобы отчет стал входом для будущего парсера товаров и расчета экономики.
- Это пока не поиск товаров и не расчет маржи. Это нормализованный запрос, который дальше можно отдавать CSV-прайсам, ручным ссылкам поставщиков или полноценным парсерам сайтов.

## Classifier code/type checkpoint

Дата: 2026-05-21.

- Для позиций закупки добавлены отдельные поля `classifier_code` и `classifier_type`.
- Важно: `КОЗ-2` не то же самое, что `ОКПД2`. `КОЗ-2` - классификатор, который встречается на площадке МО/ЕАСУЗ. Его код может выглядеть как `11.218.01.01.01.002`; это не классический ОКПД2, но для поиска товара он так же важен.
- `TenderItem` теперь хранит не только старое поле `okpd2`, но и явные `classifier_code`/`classifier_type`, чтобы не смешивать разные классификаторы в одно поле.
- SQLite-таблица `tender_items`, API, сайт, товарный профиль и Word-отчет теперь показывают код классификатора и тип классификатора отдельно.
- Для будущего парсера товаров это критично: товарный поиск должен использовать название позиции, детальное название, количество, единицу измерения, цену, `classifier_code` и `classifier_type`.
- Если у конкретной МО-закупки в карточке на сайте позиции видны, но в Tender Killer товарный профиль строится только из общей карточки, значит текущий list endpoint не отдал `TradeObjects`. Следующий слой должен добирать позиции из detail endpoint, документа или страницы карточки.

## Product search classifier research checkpoint

Дата: 2026-05-21.

- Проведено отдельное исследование: можно ли искать реальные товары только по ОКПД2/КТРУ/КОЗ-2.
- Ключевой вывод: классификатор не является товарным SKU. Он полезен как фильтр категории и регуляторный признак, но для подбора товара нужен гибридный профиль: наименование позиции, детальное наименование, характеристики, ГОСТ/ТУ/ТР ТС, сертификаты/декларации, бренд/модель/артикул, страна происхождения, единица измерения, количество, цена и классификаторы.
- Для архитектуры Tender Killer это означает: следующий слой должен быть не “поиск по ОКПД2”, а “движок товарного профиля”, который формирует поисковые фразы, стоп-слова и обязательные признаки для будущих парсеров поставщиков.
- Сохранены рабочие материалы:
  - `memory/product-search-classifier-research.md`;
  - `memory/product-search-classifier-research.docx`.

## Persistent product profiles checkpoint

Дата: 2026-05-21.

- `ProductProfile` стал отдельной постоянной сущностью в SQLite.
- Один тендер теперь может иметь много товарных профилей: по одному на каждую позицию закупки.
- Это важно для закупок с 20-40 товарами: поиск, подбор поставщиков, будущий расчет маржи и агент-критик должны работать на уровне позиции, а не только тендера.
- `product_profiles` хранит товарное имя, детальное описание, количество, единицу, цену, ОКПД2, классификаторы, характеристики, ГОСТ/ТУ, сертификаты/декларации, поисковые фразы, стоп-слова, evidence, статус и уверенность.
- `POST /api/tenders/{source}/{external_id}/product-profiles/rebuild` пересобирает и сохраняет профили.
- Сайт показывает товарные профили списком с компактной сводкой и детальной панелью выбранной позиции.
- Word-отчет показывает сводку по всем товарным профилям, чтобы отчеты по закупкам с множеством позиций оставались читаемыми.
- При обновлении тендера сохраненные товарные профили инвалидируются, чтобы не показывать устаревшую сводку после изменения позиций.

## Detail refresh checkpoint

Дата: 2026-05-21.

- Добавлен ручной backend refresh для детальной карточки: `POST /api/tenders/{source}/{external_id}/details/refresh`.
- Refresh берет сохраненный `raw_payload`, добирает detail payload через адаптер источника, заново нормализует тендер, сохраняет документы и позиции в SQLite и пересобирает товарные профили.
- Если источник не отдал новые detail-данные, refresh не перезаписывает существующие позиции/документы. Это защищает от потери уже сохраненной информации.
- На сайте в карточке закупки появилась кнопка `Обновить детали карточки`. После обновления показывается краткая сводка: сколько позиций, документов и товарных профилей получилось.
- Для Москвы refresh использует `MoscowSupplierPortalAdapter` и detail marker `__detail`.
- Для МО refresh использует `MosregMarketAdapter` и подтвержденный endpoint документов `GetTradeDocuments`; позиции появляются, если источник/детальный payload отдал массивы вроде `TradeObjects`, `Products`, `Items`, `Positions`.
- Практический смысл: старые сохраненные тендеры можно обогащать без нового общего поиска, а будущий парсер товаров получает более полные товарные профили.

## Tender detail UX checkpoint

Дата: 2026-05-21.

- Правая панель сайта была перегружена: паспорт закупки, действия, анализ, документы, товарные профили, позиции и сырые признаки показывались одной длинной простыней.
- Принято UX-решение: правая карточка должна быть коротким рабочим экраном, а не техническим дампом.
- Карточка разделена на вкладки:
  - `Обзор` - паспорт закупки, заказчик, регион, закон, категория;
  - `Товары` - товарные профили и раскрываемые позиции из карточки;
  - `Документы` - список документов, статус скачивания и извлечения текста;
  - `Анализ` - выжимка ТЗ, требования, риски, красные флаги;
  - `Статус` - рабочий статус, заметка и debug-блок с сырыми признаками.
- Основные действия вынесены в компактную верхнюю строку: источник, обновить, документы, текст, анализ, Word, Telegram.
- Превью текста документов скрыто под раскрытие, чтобы не забивать интерфейс.
- `Сырые признаки` спрятаны в debug-блок, потому что это полезно разработчику, но мешает рабочему просмотру закупки.
- Telegram остается каналом уведомлений; сайт становится основным рабочим кабинетом.
- README обновлен под фактическую архитектуру: сайт, detail refresh, документы, анализ ТЗ, товарные профили, Word-отчет и SQLite-viewer.

## Mosreg HTML item fallback checkpoint

Дата: 2026-05-21.

- Найден корень проблемы с МО-закупками: endpoint списка `GetTradesForParticipantOrAnonymous` и `GetTradeDocuments` не всегда отдают позиции закупки.
- На странице `https://market.mosreg.ru/Trade/ViewTrade/{Id}` блок `Объекты закупки` присутствует в HTML и содержит товар, детализированное наименование, количество, единицу, цену, код классификатора и тип классификатора.
- `MosregMarketAdapter` теперь при detail refresh может скачать HTML карточки и распарсить позиции из `.objectPurchase .outputResults__oneResult`.
- Для закупки `3666760` проверено локально: подтягивается товар `Бланк из бумаги или картона`, детали `Поставка зачетных книжек`, количество `700`, классификатор `11.105.01.02.08.01.008`, тип `КОЗ-2`.
- В интерфейсе поле `Детали` означает `Детализированное наименование` позиции из карточки источника. Это не юридический анализ и не характеристики ТЗ; характеристики позже должны добавляться из документов/ТЗ в товарный профиль.

## Product profile document evidence and readable Word report checkpoint

Дата: 2026-05-21.

- Товарный профиль начал связывать позицию закупки с требованиями из документов/ТЗ: релевантные предложения из извлеченного текста добавляются в `required_characteristics`.
- Для таких фрагментов добавляется `evidence` с источником документа, чтобы дальше было понятно, откуда взялось требование.
- Это сделано без новой миграции БД: используются уже существующие поля профиля `required_characteristics` и `evidence`.
- Word-отчет перестроен из длинного потока абзацев в читаемые блоки с таблицами:
  - `Краткое решение`;
  - `Паспорт закупки`;
  - `Что закупают`;
  - `Сводка товарных профилей`;
  - `Товарный профиль для поиска`;
  - `Документы и ТЗ`;
  - `Выжимка ТЗ`;
  - приложение с фрагментами извлеченного текста.
- Сайт остается коротким рабочим экраном, а Word-отчет становится местом для полного разбора закупки и будущего добавления расчета маржи.
- Проверка этапа: `127 passed` при запуске `.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp pytest-cache-files-full` вне sandbox. Внутри sandbox полный pytest может падать на правах временных папок `tmp_path`, поэтому для полного прогона нужен unrestricted shell.

## Product profile v2 checkpoint

Дата: 2026-05-21.

- Детальная карточка товарного профиля на сайте разделена на рабочие блоки:
  - `Идентификация позиции`: товар, детализированное наименование, количество, цена, сумма, ОКПД2 и классификатор площадки;
  - `Пакет для поиска товара`: поисковые фразы и стоп-слова для будущего парсера поставщиков;
  - `Требования и документы`: характеристики, стандарты, сертификаты/декларации, страна происхождения;
  - `Подтверждения из ТЗ`: фрагменты документов с указанием файла-источника.
- Это закрепляет архитектуру: сайт показывает компактный профиль позиции, а Word-отчет хранит более полный доказательный разбор.
- В Word-отчет добавлена таблица `Подтверждения из ТЗ` внутри товарного профиля, чтобы было видно, из какого документа взято требование.
- Следующий логичный шаг: улучшить качество извлечения требований из ТЗ, чтобы профиль заполнялся не общими фразами, а конкретными характеристиками товара, сертификатами, ГОСТами и ограничениями по происхождению.

## Rule-based TZ extraction v2 checkpoint

Дата: 2026-05-21.

- Следующий слой анализа ТЗ делаем без LLM: сначала надежные правила, потом подключение агентов/LLM как опциональный усилитель.
- Товарный профиль начал вытаскивать более конкретные параметры из документов:
  - формат, плотность, белизна, количество листов в пачке;
  - размеры, масса, объем;
  - признак нового товара;
  - декларация/сертификат соответствия, паспорт качества;
  - национальный режим / ПП 1875, страна происхождения, РРПП/РПП/ЕРПТ и реестр российской промышленной продукции.
- Общий `analysis` также подсвечивает паспорт качества, реестры российской продукции и страну происхождения, чтобы вкладка анализа и товарный профиль не расходились по смыслу.
- Ограничение текущей версии: это не полноценное понимание ТЗ, а регулярные правила. Для сложных формулировок и конфликтов требований позже нужен LLM-аналитик и агент-критик.

## Architecture cleanup checkpoint: public adapter detail enrichment

Дата: 2026-05-21.

- Начата поэтапная чистка раздела `Что мы сделали спорно или временно` из audit-документа.
- Исправлен пункт 3.3: `refresh_tender_detail_payload` больше не вызывает приватный метод адаптера `_enrich_payload`.
- В адаптерах Москвы и МО введен публичный контракт `enrich_payload(payload)`, который используют и обычный `fetch`, и ручной detail refresh.
- Практический смысл: API-слой больше не знает внутренности адаптера, а следующий шаг по разделению `web_api.py` можно делать через устойчивые публичные интерфейсы.

## Architecture cleanup checkpoint: centralized SQLite schema

Дата: 2026-05-21.

- Исправлен пункт 3.2 audit-документа: схема SQLite больше не размазана между `storage.py` и `web_api.py`.
- Добавлен модуль `src/tender_killer/schema.py` с единым контрактом создания и мягкого апгрейда таблиц.
- `TenderStore.initialize()` теперь вызывает `initialize_schema(connection)`.
- `web_api.py` использует публичные `ensure_*` функции из `schema.py` для SQLite-viewer, документов, анализа и workflow.
- Добавлены тесты `tests/test_schema.py`, которые проверяют создание базовых таблиц и миграцию старых минимальных таблиц.
- Практический смысл: перед экономикой, ЕИС и SaaS-слоем у нас появляется одно место, где эволюционирует структура базы.

## Architecture cleanup checkpoint: normalized tender filter metadata

Date: 2026-05-21.

- Continued audit item 3.4: tender filtering should rely on normalized fields instead of scanning `raw_payload_json`.
- `tenders` now stores normalized metadata: `law`, `status_normalized`, `region_code`, `source_family`, `procedure_type`, `customer_inn`.
- `TenderStore.upsert_tender()` fills these fields via `src/tender_killer/tender_metadata.py`.
- Web list filters now support stable filters for active status, law, quick region code, `procedure_type`, `source_family`, and `customer_inn`, while retaining legacy text fallback where useful.
- Practical meaning: later UI filters, analytics, margin workflow, and customer/risk views can use stable columns rather than source-specific payload strings.
- Session handoff note: after this checkpoint, branch `codex/moscow-mo-parser` was ahead of origin by the normalized metadata commits. README now contains a `Current Handoff Snapshot` with the current architecture, verification command, and recommended next steps for a fresh session.

## Architecture cleanup checkpoint: product profile service split

Дата: 2026-05-21.

- Начат пункт 3.1 audit-документа: уменьшение монолитного `web_api.py`.
- Вынесен первый доменный сервис `src/tender_killer/product_profile_service.py`.
- Сервис отвечает за:
  - сборку товарных профилей из готового payload;
  - сохранение пересобранных профилей;
  - расчет summary по статусам профилей.
- `web_api.py` сохранил совместимый endpoint/wrapper `rebuild_product_profiles`, но больше не содержит саму бизнес-логику summary/rebuild.
- Добавлены тесты `tests/test_product_profile_service.py`.
- Следующий срез по 3.1: вынести document service (`download_tender_documents_payload`, `extract_tender_document_text_payload`) из `web_api.py`.

## Architecture cleanup checkpoint: tender query service and source checkpoints

Date: 2026-05-21.

- Continued audit items 3.4 and 3.5.
- Tender list SQL, list filtering, pagination, and site search filter construction moved from `src/tender_killer/web_api.py` to `src/tender_killer/tender_query_service.py`.
- `GET /api/tenders` payload now includes real filtered `total`, `limit`, and `offset` in addition to `items`.
- Source adapters accept configurable page depth through `TENDER_KILLER_SOURCE_MAX_PAGES`; default remains `1` to preserve conservative MVP behavior.
- Moscow and Mosreg adapters now accept a `published_from` checkpoint and pass it into source query payloads (`publicationDateFrom` / `filterDateFrom`).
- SQLite schema now includes `source_runs` for source success/error diagnostics and last seen publication date.
- `TenderPipeline` passes stored source checkpoints into adapters before fetch, records successful runs with the newest fetched publication date, and records source errors for diagnostics.
- Source publication checkpoints are monotonic: older fetched pages cannot move `last_seen_published_at` backwards.
- Verification during this slice:
  - `25 passed` for `tests/test_tender_query_service.py tests/test_sources.py tests/test_pipeline.py tests/test_config.py`
  - `40 passed` for `tests/test_web_api.py tests/test_schema.py`
  - `147 passed` for full `.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp pytest-cache-files-full`
  - `148 passed` after adding the monotonic checkpoint regression test

## Architecture cleanup checkpoint: source status UI and incremental overlap

Date: 2026-05-21.

- Continued audit item 3.5.
- Added `src/tender_killer/source_run_service.py` as the public service for source run diagnostics.
- The local API now exposes `GET /api/sources/status` with known source rows, labels, last success, checkpoint, and last error state.
- SQLite admin view includes the `source_runs` table, so checkpoint and error diagnostics are inspectable from the site database tab.
- The React tender cockpit shows source status/checkpoint rows and refreshes them after manual search.
- `TENDER_KILLER_SOURCE_OVERLAP_MINUTES` controls the incremental overlap window, defaulting to `60`.
- `TenderPipeline` applies the overlap only to `adapter.published_from`; stored `last_seen_published_at` remains monotonic and is not moved backwards by older pages.
- Tender list pagination now has explicit API navigation fields (`has_next`, `has_previous`, `next_offset`, `previous_offset`) and the React cockpit uses them for next/previous controls.
- The site requests tender pages with a bounded limit of 25 rows, shows the total count, and resets offset when filters/workflow tabs change.
- The React filter panel now exposes normalized metadata filters for `source_family`, `procedure_type`, and `customer_inn`.
- Workflow persistence moved from `web_api.py` into `src/tender_killer/workflow_service.py`; request-level workflow payload handling now lives in `src/tender_killer/api_handlers.py`.
- Report download payload construction moved into `src/tender_killer/report_service.py`; request-level report loading now lives in `src/tender_killer/api_handlers.py`.
- Tender detail payload loading and detail refresh moved into `src/tender_killer/tender_detail_service.py`; `web_api.py` keeps the existing HTTP routes/API names through `api_handlers`.
- Manual Telegram notification payload construction moved into `src/tender_killer/notification_service.py`; `web_api.py` no longer owns payload-to-`Tender` conversion for manual notifications.
- TZ analysis run persistence moved into `src/tender_killer/analysis_service.py`; HTTP dispatch goes through `src/tender_killer/api_handlers.py`.
- Search run orchestration moved into `src/tender_killer/search_service.py`; `/api/search` remains available through the thin HTTP adapter plus `api_handlers`.
- The React tender list now has a page-size selector for 10/25/50/100 rows. Default remains 25, and changing page size resets the list to offset 0 while keeping active filters.
- Added `src/tender_killer/dev_health.py` and wired `scripts/dev-web.ps1` through it. `npm run dev` now checks both `/api/health` and `/api/sources/status`, reuses a healthy existing API, and fails clearly if port 8000 is occupied by a stale or incompatible backend.
- Added `src/tender_killer/dev_smoke.py` for local site smoke checks: direct API, Vite HTML, Vite `/api` proxy, source status proxying, and key UI labels that guard against the page-size mojibake regression.
- Added `src/tender_killer/encoding_guard.py` plus `tests/test_encoding_guard.py` to scan runtime/UI/docs files for Cyrillic mojibake; `dev_smoke` now uses the same detector instead of a hand-written forbidden-string list.
- Added `src/tender_killer/api_routes.py` so tender/database API path parsing is no longer hand-split throughout `web_api.py`.
- Added `src/tender_killer/api_handlers.py` so GET/POST route dispatch lives outside `web_api.py`; `web_api.py` now reads request bodies and serializes responses, while the handler module chooses the service.
- Cleanup before product work: removed ignored pytest/cache/build artifacts from the workspace, removed old `web_api.py` service re-export imports, and added a regression test that keeps `web_api.py` as a thin HTTP adapter.
- Latest full verification in this slice: `177 passed` for `.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp pytest-cache-files-full`.

## Product analysis checkpoint: actionable TZ checklist

Date: 2026-05-21.

- Started the product layer before economics by improving rule-based TZ analysis.
- `analyze_tender_texts(...)` still returns backward-compatible `requirements`, `risks`, and `red_flags`, but now also returns `checklist`.
- Each checklist row has `label`, `category`, `severity`, and `evidence`, so later economics/margin work can ask concrete questions like: which documents are required, what delivery risk exists, whether national regime applies, and what proof fragment triggered the flag.
- `get_tender_payload(...)` lifts the checklist from `tender_analysis.raw_payload_json` into `analysis.checklist`.
- Word reports now include a `Проверочный список` section under `Выжимка ТЗ`.
- Full verification after this slice: `178 passed` for `.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp pytest-cache-files-full`.

## Product UI checkpoint: TZ checklist in analysis tab

Date: 2026-05-22.

- After pushing the backend/report checklist slice, the React tender details panel now renders `analysis.checklist` in the `Анализ` tab.
- The UI keeps the existing summary/requirements/risks/red-flags blocks, and adds a compact `Проверочный список` with category, importance, and evidence text.
- This makes the supplier-side checks visible in the main site flow instead of hiding them only inside the Word report.
- Full verification after this slice: `179 passed` for `.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp pytest-cache-files-full`.

## Product profile checkpoint: fulfillment requirements for economics

Date: 2026-05-22.

- Product profiles now include `fulfillment_requirements`: structured rows with `type`, `source`, and `value`.
- Rule-based extraction currently recognizes delivery timing, packaging, warranty, and acceptance/EIS sentences from extracted TZ documents.
- SQLite persists the new field through `fulfillment_requirements_json`, including migration for existing `product_profiles` tables.
- The product tab renders these rows under `Поставка и исполнение`, so the future economics workflow can see non-price obligations next to item characteristics.
- Full verification after this slice: `181 passed` for `.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp pytest-cache-files-full`.

## Economics checkpoint: draft margin summary

Date: 2026-05-22.

- Added `src/tender_killer/economics.py` as the first draft calculation service.
- The calculation uses tender price as revenue, manual per-profile cost inputs from `profile.raw_payload.economics`, and fulfillment requirements to create a simple risk reserve.
- `get_tender_payload(...)` now returns `economics` with status, recommendation, revenue, supplier cost, risk reserve, estimated total cost, gross margin, margin percent, missing cost inputs, risk types, and item rows.
- Word reports render `Черновик экономики` when an economics payload is present.
- The site has an `Экономика` tab in the tender card with the same summary and missing-cost prompts.
- The service does not guess market prices; if supplier costs are absent, it returns `needs_costs`.
- Full verification after this slice: `185 passed` for `.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp pytest-cache-files-full`.

## Economics input checkpoint: site cost entry

Date: 2026-05-22.

- Added `src/tender_killer/economics_service.py` for saving supplier cost inputs into a product profile without putting this logic back into `web_api.py`.
- Added `POST /api/tenders/{source}/{external_id}/product-profiles/{position_index}/economics`; route parsing lives in `src/tender_killer/api_routes.py`, request dispatch lives in `src/tender_killer/api_handlers.py`.
- The service stores cleaned numeric inputs in `profile.raw_payload.economics`: `unit_cost`, `logistics_cost`, `documents_cost`, and `other_costs`. Existing raw payload keys are preserved.
- After save, the API returns the full tender detail payload, so the React card refreshes product profiles and the `Экономика` tab immediately shows the recalculated margin.
- The product profile detail on the site now has a compact `Себестоимость` form next to the position context. This makes the first economics workflow usable without a supplier parser yet.
- Full verification after this slice: `189 passed` for `.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp pytest-cache-files-full`.

## Supplier options checkpoint: manual product candidates

Date: 2026-05-22.

- Added `src/tender_killer/supplier_option_service.py` for appending manual supplier candidates to a product profile.
- Added `POST /api/tenders/{source}/{external_id}/product-profiles/{position_index}/supplier-options`; route parsing lives in `src/tender_killer/api_routes.py`, request dispatch lives in `src/tender_killer/api_handlers.py`.
- The service stores cleaned candidate rows in `profile.raw_payload.supplier_options`: `name`, `url`, `unit_price`, `availability`, `status`, and `note`. Existing raw payload keys and existing candidates are preserved.
- The React product profile detail now has a `Поставщики` block: a compact form for adding a candidate and a list of saved candidates with link, price, availability/status, and note.
- Supplier candidates intentionally do not overwrite `raw_payload.economics` yet. Next step after UI review: choose/mark a candidate and copy its unit price into the economics input deliberately.
- Full verification after this slice: `194 passed` for `.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp pytest-cache-files-full`.

## Frontend UX checkpoint: Tender Workbench v1

Date: 2026-05-22.

- UX issue found after adding economics and supplier candidates: the selected tender card became a full workbench squeezed into a narrow right sidebar.
- First repair slice keeps the current app structure but changes the tender screen into `workspace workbench-layout`, giving the selected tender detail a wider desktop area.
- Added `TenderDecisionSummary` at the top of the tender card: НМЦК, срок, заказчик, экономика/margin, workflow status, and next step are visible before the deeper tabs.
- Product detail is split into sub-tabs: `Паспорт`, `Цены`, `Поставщики`, and `ТЗ`. This removes the long single-column product profile stream while keeping the data close to the selected position.
- The global SaaS shell/dashboard is intentionally left for the next UX slice; the first priority was making the tender workbench readable.
- Verification: frontend contract `8 passed`; full `.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp pytest-cache-files-full` returned `195 passed`.
- Build note: direct `node ... vite build` is blocked in this Windows shell with `Access is denied`; JSX syntax was checked separately through Babel parser in the Node REPL.

## Frontend UX checkpoint: collapsible tender filters

Date: 2026-05-22.

- Continued the workbench readability slice after user review: the left filter panel can now collapse into a narrow rail.
- Collapsing filters changes the desktop grid to give the tender list more width while keeping the selected tender detail visible on the right.
- Mobile keeps a single-column layout and shows the filter title again when collapsed, so the control remains understandable on narrow screens.
- Verification in this slice: frontend contract `9 passed`; JSX syntax parsed successfully through Babel parser in the Node REPL.

## Frontend UX checkpoint: global shell and dashboard

Date: 2026-05-22.

- Fixed the tender workflow status row: buttons now wrap instead of forcing a horizontal scrollbar under the list header.
- Added a global SaaS-style shell with left navigation for `Дашборд`, `Закупки`, and `SQLite`; filters remain inside the `Закупки` workbench and are not mixed with product navigation.
- The app now opens on `Дашборд`, showing the existing metrics, source status, and workflow queue counts. `Закупки` keeps the workbench/list/card flow, and `SQLite` remains a separate data view.
- Verification in this slice before full run: frontend contract `11 passed`; JSX syntax parsed successfully through Babel parser in the Node REPL.

## Frontend UX checkpoint: collapsible sidebar and dashboard contents

Date: 2026-05-22.

- The global left navigation now collapses into a narrow icon rail and expands back by button click; the main content grid shifts with it instead of overlaying the work area.
- Dashboard V1 is framed as an operational start screen: metrics, source state, workflow queue, `Требует внимания`, and `Последние закупки`.
- The attention panel uses existing local state: API error, source errors, new tenders, and interesting tenders. No new backend endpoint is needed for this slice.
- Frontend contract after this slice: `13 passed`; JSX syntax parsed successfully through Babel parser in the Node REPL.

## Frontend UX checkpoint: aligned dashboard grid

Date: 2026-05-22.

- Fixed the first visual pass of the dashboard: metrics now occupy the same full-width content container as the rest of the page instead of floating in the middle.
- Dashboard rows now share the same two-column grid, and cards stretch to the row height. This removes the accidental uneven gaps between source status, queue, attention, and recent tender blocks.
- Added a frontend contract that keeps the dashboard on a full-width aligned grid.

## Competitor-inspired Telegram checkpoint: quick entry

Date: 2026-05-22.

- After reviewing Zakupki Assistant, the product direction is: keep the website as the main workbench, but add Telegram as a fast entry point for natural-language search setup.
- Added `src/tender_killer/quick_search.py`: parses text like `строительные материалы Москва МО до 2 млн 44-ФЗ` into a dedicated `quick-entry` filter profile.
- Existing filters/profiles are preserved. The quick profile is upserted separately and can be used for an immediate preview search.
- Telegram `text_menu_handler` now treats unknown free text as quick-entry setup and replies with a parsed summary plus `Запустить быстрый поиск`.
- Added competitor notes in `docs/competitors/zakupkiassistant-analysis.md`.

## Competitor-inspired Telegram checkpoint: search statistics

Date: 2026-05-22.

- `PipelineStats` now separates relevant matches into `matched_new` and `matched_existing`.
- Search stats now include compact breakdowns by source, law, and region, collected only for tenders that matched active filters.
- Telegram `/search`, `/test_search`, and `/sources_status` now show readable Russian summaries instead of raw `Fetched/Saved/Matched` counters.
- `/api/search/run` exposes the same structured counters through `source_counts`, `law_counts`, and `region_counts`, so the site can later render a competitor-style search results panel.
- Full verification after this slice: `207 passed` for `.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp pytest-cache-files-full`.

## Competitor-inspired Telegram checkpoint: compact tender cards

Date: 2026-05-22.

- Telegram tender notifications are now compact: title, source/law, price/deadline, customer/region, matched filter, and source URL.
- `build_tender_actions(...)` adds inline buttons: `Открыть источник`, `Документы`, and `Анализ`.
- `TelegramNotifier.send(...)` can send Telegram `reply_markup`, and both pipeline notifications and manual site notifications pass the new inline keyboard.
- Bot callback handling for `Документы` and `Анализ` reads the local SQLite tender payload and replies with saved document links or saved analysis/checklist. It does not submit applications, log in, sign, or mutate procurement data.
- Full verification after this slice: `212 passed` for `.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp pytest-cache-files-full`.

## Telegram site notification diagnostics checkpoint

Date: 2026-05-22.

- Root cause of the site `TG` button appearing to do nothing: `/api/tenders/{source}/{external_id}/notify` returned `sent=false` when the API process did not have Telegram settings, and the UI only showed a generic `Telegram не настроен`.
- Added local `app_state` table plus `telegram_chat_service.py`; the bot stores the last chat id after user interaction, so the site can reuse it when `TELEGRAM_CHAT_ID` is not set.
- The API still requires `TELEGRAM_BOT_TOKEN` in the API process environment; the token is not stored in SQLite.
- Manual notification payloads now return explicit `reason`, `missing`, and `message` fields for missing Telegram settings or send failure.
- The React tender card now displays the backend message, so the user sees which setting is missing instead of a silent/no-op feeling.
- Full verification after this slice: `216 passed` for `.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp pytest-cache-files-full`.

## Quick search and document extraction checkpoint

Date: 2026-05-22.

- Root cause of Telegram quick search returning `Релевантных: 0` for `строительные материалы`: the phrase was treated as one exact keyword both in the bot quick profile and in the site search collection.
- `quick_search.py` now expands `строительные материалы` / `стройматериалы` into construction-material terms (`стройматериал`, `материал`, `смесь`, `цемент`, `краск`, `крепеж`, etc.) and adds stop words for obvious non-material matches (`услуг`, `работ`, `информацион`, `медицин`, `картридж`, etc.).
- Site `/api/search` and list `q` filtering reuse the same expansion. List filtering searches visible tender fields instead of raw JSON, so broad terms do not match hidden payload noise.
- Added local `.env` support in `Settings.from_env`; `.env` is ignored by Git. This lets the API site and bot share `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` without retyping PowerShell env vars each run.
- Document extraction now distinguishes unsupported files from empty text. RAR archives and true legacy binary `.doc` files are marked `unsupported`; simple `.doc` text/HTML/RTF-like files can be extracted heuristically.
- Updated the local ignored `filters.json` quick-entry profile and re-extracted text statuses for `mosreg_market/3673016`; SQLite now shows unsupported `.doc`/`.rar` clearly instead of `empty`.
- Full verification after this slice: `228 passed` for `.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp pytest-cache-files-full`.

## Frontend architecture checkpoint: tender detail decomposition

Date: 2026-05-26.

- The current branch is `codex/moscow-mo-parser`.
- The project direction remains: website is the main workbench; Telegram is notifications and quick entry only; SQLite is the local source of truth; no legal actions such as application submission, signing, or user-login automation.
- Active tender filtering now excludes expired deadlines in `src/tender_killer/tender_query_service.py`: active lists require normalized active status and `(deadline_at IS NULL OR datetime(deadline_at) >= datetime('now'))`.
- The frontend has been split into focused modules instead of concentrating everything in `App.jsx` and `TenderDetails.jsx`.
- Extracted frontend modules now include:
  - `web/src/api.js`;
  - `web/src/constants.js`;
  - `web/src/formatters.js`;
  - `web/src/Dashboard.jsx`;
  - `web/src/DatabaseView.jsx`;
  - `web/src/FiltersPanel.jsx`;
  - `web/src/TenderList.jsx`;
  - `web/src/PaginationBar.jsx`;
  - `web/src/TenderDetailActions.jsx`;
  - `web/src/TenderDetailsHeader.jsx`;
  - `web/src/TenderDetailsStatusStack.jsx`;
  - `web/src/TenderDetailsTabs.jsx`;
  - `web/src/TenderDetailsShared.jsx`;
  - `web/src/TenderDecisionSummary.jsx`;
  - `web/src/TenderOverviewTab.jsx`;
  - `web/src/TenderDocumentsTab.jsx`;
  - `web/src/TenderAnalysisTab.jsx`;
  - `web/src/TenderWorkflowTab.jsx`;
  - `web/src/TenderProductsTab.jsx`;
  - `web/src/TenderEconomicsTab.jsx`.
- Tender detail hooks now include `web/src/useTenderDetailsUi.js`, `web/src/useTenderDocumentAnalysis.js`, `web/src/useTenderNotification.js`, `web/src/useTenderProductProfiles.js`, `web/src/useTenderRefreshDetails.js`, and `web/src/useTenderWorkflow.js`.
- `TenderDocumentsTab.jsx` owns document summary, download/extract buttons, document rows, text preview, and document status labels.
- `TenderAnalysisTab.jsx` owns the TZ analysis panel and checklist. It also exports `AnalysisList`, which is reused by product/economics views.
- `TenderEconomicsTab.jsx` owns the economics workbench: NMC summary, cost inputs, supplier candidates, selected supplier price source, assumptions, auto-estimate run/accept controls, bid thresholds, and participation decision UI.
- Supplier search preparation now lives in `src/tender_killer/supplier_search_service.py`. It builds deterministic per-position supplier search queries from normalized product names, search phrases, and classifiers; `POST /api/tenders/{source}/{external_id}/product-profiles/{position}/supplier-search/prepare` persists those queries under `raw_payload.supplier_search`. Prepared queries include manual Google/Yandex links, optional public catalog provider links from `raw_payload.supplier_catalogs`, and matching built-in catalog presets, without running network search or changing economics.
- Built-in supplier catalog presets live in `src/tender_killer/supplier_catalog_presets.py`. Current first-pass providers are `officemag` and `komus` for office supplies, plus `petrovich` and `vseinstrumenti` for building/tool materials. `raw_payload.supplier_catalog_preset_ids` can select exact preset IDs or disable presets with an empty list, and the economics supplier block now exposes compact controls for auto/select/disable per product profile.
- Manual supplier candidates now preserve the prepared search query that led to them through `source_query` and `source_kind` fields in `raw_payload.supplier_options`, so review evidence stays attached to candidate prices before selection.
- Supplier discovery review now lives in `src/tender_killer/supplier_discovery_service.py`. Discovered candidates can be staged under `raw_payload.supplier_discovery.candidates` and imported into `supplier_options`; import marks the discovery candidate as `imported` but does not select the supplier or update economics.
- Supplier discovery candidates now normalize `provider`, derive `confidence` and `confidence_reasons` from price/link/source-query evidence, and preserve provider/confidence when imported into `supplier_options`.
- First public supplier discovery run now lives in `src/tender_killer/supplier_price_discovery_service.py`. `SchemaOrgProductCollector` ignores Google/Yandex search pages, can follow same-site schema.org catalog/ListItem product URLs, fetches public product pages, parses JSON-LD Product/Offer, and stages review-only `schema_org_product` candidates with unit price, currency, VAT mode, delivery note, availability, provider confidence, and source-query evidence.
- Built-in public catalog discovery now has provider-specific collectors for `officemag`, `komus`, `petrovich`, and `vseinstrumenti`. They only consume matching `catalog_search` links, follow same-site catalog anchors/product URLs, parse schema.org Product/Offer on product pages, and stage review-only candidates under the real catalog provider while the generic schema.org collector remains the fallback for manual/unknown public links.
- Supplier catalog health diagnostics now live in `src/tender_killer/supplier_catalog_health_service.py` and `GET /api/supplier-catalogs/health`. The endpoint is network-free by default and returns configured provider/sample URL diagnostics; `?live=1` performs public HTTP checks per built-in catalog provider and reports HTTP status or fetch errors.
- Supplier discovery staging now stores provider collector diagnostics under `raw_payload.supplier_discovery.collector_diagnostics`, including seen queries/links, skipped links, fetched pages, candidates found, and fetch errors.
- `TenderEconomicsTab.jsx` renders collector diagnostics in the supplier discovery preview next to staged candidates, so operator review can see provider, seen/skipped links, fetched pages, candidates found, and errors.
- `web/src/api.js` now surfaces backend JSON `error` messages, so supplier discovery can show no-new-candidates and missing-prepared-query responses instead of only generic client text.
- `tender_killer.dev_health` now requires `/api/health` capabilities for `supplier_search_prepare`, `supplier_catalog_presets`, and `supplier_catalog_health`, and also checks `/api/supplier-catalogs/health`, so stale backend processes on port 8000 are rejected before Vite proxies newer supplier UI actions to them.
- The API dispatcher has a regression test for `/api/tenders?status=active&limit=25&offset=0`, covering the tender list route that powers the main workbench.
- `web/src/TenderDetails.jsx` is now a thin coordinator for selected tender actions, hooks, and tab composition; workflow, product, overview, document, analysis, and economics UI live in dedicated modules.
- Latest local targeted verification after supplier catalog health diagnostics: `11 passed` for supplier catalog health service/API/dev health/dev smoke checks.
- Full verification after this slice: `334 passed` for `.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp pytest-cache-files-full`.
- JSX syntax was checked through Babel parser in the Node REPL after wiring the supplier catalog preset controls into the economics tab.
- Next planned steps:
  1. Validate real catalog pages and add narrow provider parsing rules where schema.org/anchor discovery is not enough.
  2. Surface supplier catalog health in the economics supplier diagnostics UI.
  3. Keep Telegram as notifications/quick entry, not the main workbench.
