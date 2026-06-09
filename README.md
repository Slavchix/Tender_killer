# Tender Killer

## Current Handoff Snapshot

Date: 2026-06-09.

Current branch: `codex/moscow-mo-parser`.

Next-session starter prompt:

```text
Продолжаем Tender Killer в `C:\Users\zinin.v.a\Documents\tender_killer`, ветка `codex/moscow-mo-parser`.

Нужно переработать экономику и подключение поставщиков по безопасной модели: Tender Killer не должен быть ботом для массового парсинга сайтов, а должен быть центром подтверждения закупочной цены.

Перед кодом прочитай:
- `README.md`
- `memory/project-context.md`
- `src/tender_killer/supplier_search_service.py`
- `src/tender_killer/supplier_catalog_presets.py`
- `src/tender_killer/supplier_price_discovery_service.py`
- `src/tender_killer/supplier_discovery_service.py`
- `src/tender_killer/price_candidate_service.py`
- `src/tender_killer/supplier_catalog_fetcher.py`
- `src/tender_killer/supplier_browser_fetcher.py`
- `scripts/browser-fetch.mjs`
- `web/src/TenderEconomicsTab.jsx`
- `web/src/api.js`

Ключевое продуктовое правило:
- Для мелких закупок на 1-5 позиций можно оставить текущий review-only сценарий активного поиска цен, потому что малое число запросов обычно не провоцирует блокировки. Но он все равно не должен автоматически писать цену в расчет без подтверждения.
- Для крупных закупок больше 5 позиций кнопку активного автопоиска цен нужно скрыть или отключить, чтобы оператор случайно не запустил массовый сбор. Для них основной сценарий: подготовить quick links, открыть по одной ссылке на подходящий каталог, вручную выбрать товар, вставить публичный product URL, извлечь цену из карточки, создать price candidate и подтвердить его в расчет.

Ограничения обязательны:
- не использовать приватные API, cookies, tokens, passwords, личные кабинеты и служебные endpoints;
- не обходить captcha/challenge/WAF;
- не делать массовый парсинг;
- не открывать много вкладок;
- не авто-заказывать товары и не выполнять юридически значимые действия;
- любые найденные цены остаются evidence/price candidate до явного подтверждения оператором.

Реализация должна идти через provider policy:
- добавить/использовать `supplier_provider_policy.py`;
- разделить quick links для оператора и auto collectors;
- запретить unsafe URL перед fetch;
- сделать manual product URL основным безопасным сценарием;
- browser fetch только `manual_only`, без background-массового режима;
- добавить место под `manual_feed`, `quote_upload`, `supplier_price_feed`;
- улучшить отображение price candidates: поставщик, товар, цена, НДС, наличие, доставка, единица, упаковка/кратность, минимум заказа, источник, confidence, quality flags;
- расширить provider health/status policy mode и allowed actions.

Поставщики:
- Lemana Pro: quick link/manual product URL, без auto search fetch.
- OfficeMag: quick link/manual product URL, без auto background search.
- Komus: quick link/feed/КП recommended, без auto search fetch.
- ВсеИнструменты: limited public search для малых закупок, product URL allowed, при access_blocked сразу manual_required.
- Petrovich: пока нет подтвержденного публичного API цен; partner API возможен только при официальном JWT-доступе. Без доступа: product URL/B2B quote/manual feed, limited public search только для малых закупок.

Последний проверенный коммит перед этой задачей: `37f537d Harden supplier catalog discovery`. Он добавил защиту от access_blocked/403/401/429/503 и останавливает заблокированный provider до конца текущего поиска.

Сначала составь короткий план файлов и тестов, затем реализуй по шагам с проверками. После реализации обнови memory/README и предложи commit/push.
```

Current handoff branches and worktrees:

- Shared/preview branch: `codex/moscow-mo-parser` in `C:\Users\zinin.v.a\Documents\tender_killer`.
- Dedicated economics branch: `codex/economics-flow` in `C:\Users\zinin.v.a\Documents\tender_killer_economics`.
- The economics branch should merge fresh `origin/codex/moscow-mo-parser` before pushing back into the shared branch. Never force-push and never reset the shared preview worktree without explicit confirmation.
- Current preview watched by the user is `http://127.0.0.1:5175`; API is `http://127.0.0.1:8000`. The checked-in `scripts/dev-web.ps1` still defaults to web port `5173`, so if the user says the active preview is `5175`, kill stale `5173/5174` listeners and restart the intended preview explicitly.

Latest verified checkpoint:

- Current checkpoint prepares supplier price discovery and the focused economics workspace on `codex/moscow-mo-parser`.
- Supplier catalog discovery is review-first and now covers OfficeMag, Vseinstrumenti, and Lemana Pro as active practical providers. Komus/Petrovich remain visible in health/status diagnostics when blocked.
- Dashboard owns source/API status and supplier catalog health. The economics modal should not carry low-level source request forms or catalog health cards anymore.
- The economics workspace is now a focused calculation tool: top command summary, position rail, selected position, price candidates, accepted supplier/options, manual costs, assumptions, and collapsed analysis/TZ context.
- Tender item reference price/total is carried into economics and price candidates for quick visual comparison against supplier offers.
- Local dev control should prefer the Python dev-control path. Avoid the old long inline PowerShell `Start-Process` supervisor command because it repeatedly caused hanging restarts.

Current product/UI state:

- The main procurement page has moved toward a full-width tender list with collapsible top filters. Clicking a tender opens a full-screen tender card instead of keeping analysis/economics cramped in a right rail.
- The short card summary should stay decision-first: top metrics, source/refresh, compact economics and analysis cards, and working status. Product details now belong inside economics; documents now belong inside analysis.
- The analysis workspace owns document download, text extraction, rule-based TZ analysis, and Word export. The desired Word report is a compact 5-8 page operator brief, not a long raw dump.
- Analysis is moving toward a fact/evidence model: every important condition should show source document/page or at least source document plus fragment/context, so the operator can verify it manually.
- The economics workspace owns product positions, quantities, supplier price discovery, price candidates, manual cost inputs, assumptions, auto-estimate, and final participation economics.
- Dashboard supplier/source cards are intentionally collapsible because more marketplaces and catalogs will be added later.
- The economics modal keeps analysis/TZ results available in a collapsed drawer, but the main default screen stays on positions, candidates, and calculation.

Current economics focus for the next session:

- Keep the economics modal focused. Do not bring back catalog health/status forms or generic supplier-source request fields; those diagnostics now belong on the dashboard.
- Continue tightening provider routing: run only catalogs that fit the position category and keep at most one manual review link per selected catalog/provider.
- Product matching should keep using manufacturer/model/pack/quantity gates where available, then fall back to broader category matches only when exact signals are absent.
- Next provider work should improve candidate ranking and explanations before adding more catalogs, not auto-confirm unknown offers.

Historical provider notes kept for regression tests:
- OfficeMag is the active proving ground. Public catalog access is unstable: it can show `доступен`, `блокировка 503`, or "opened catalog but saw no product cards" depending on browser/server checks.
- Do not patch one product at a time. The next fix should trace the full pipeline: tender position -> generated search queries -> OfficeMag fetch/browser fetch -> parsed product cards -> normalized price candidates -> matcher/scoring -> UI -> confirmed unit cost -> tender economics.
- Known bad behavior to fix: searches for cartridges or stationery can return unrelated paper/sign/mop items; found prices can appear without a clear source link; accepted prices may update the summary but not the selected position row; quantity and unit price breaks must drive totals.
- OfficeMag paper example used for tests: product code `110532`, prices `364` from 1, `361` from 5, `359` from 10, package 5, Moscow stock 14194, preorder +2047. For a 60-pack tender, the selected unit price should be `359`, total `21540`.

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
- Tender/database API path parsing is isolated in `src/tender_killer/api_routes.py`.
- GET/POST API dispatch is isolated in `src/tender_killer/api_handlers.py`, leaving `web_api.py` as a thin HTTP adapter.
- TZ analysis run persistence is isolated in `src/tender_killer/analysis_service.py`.
- Search run orchestration is isolated in `src/tender_killer/search_service.py`.
- Telegram now supports a quick-entry profile: send a natural-language request like `строительные материалы Москва МО до 2 млн 44-ФЗ`, and the bot saves it as a separate `quick-entry` profile without deleting existing filters.
- Telegram tender notifications now use compact cards with inline buttons for opening the source, showing saved documents, and showing saved analysis.
- Manual site-to-Telegram sending now reports missing Telegram configuration explicitly. The bot remembers the last chat id in local SQLite after any user message, so the site can reuse it when `TELEGRAM_BOT_TOKEN` is available to the API process.
- Rule-based TZ analysis now emits an actionable checklist with category, severity, and source evidence for supplier-side checks.
- The site renders the TZ checklist in the tender analysis tab, so supplier-side checks are visible without opening the Word report.
- Product profiles now extract and persist fulfillment requirements for delivery, packaging, warranty, and acceptance; the product tab shows them as inputs for future economics.
- Draft economics now calculates revenue, manual supplier cost, risk reserve, estimated total cost, gross margin, margin percent, and missing cost inputs.
- The site can save per-position supplier economics inputs (unit cost, logistics, documents, other costs) and immediately refresh the tender economics summary from SQLite.
- The site can save manual supplier candidates per product position: supplier name, URL, unit price, availability, status, and note.
- The site can prepare supplier search queries per product position and save them in SQLite under `raw_payload.supplier_search`; prepared queries include manual Google/Yandex quick links, optional public catalog provider links from `raw_payload.supplier_catalogs`, and matching built-in catalog presets, still without network scraping or automatic economics changes.
- Built-in supplier catalog presets currently cover first-pass office supplies (`officemag`, `komus`) and building/tool materials (`petrovich`, `vseinstrumenti`). The economics supplier block can switch each product profile between auto matching, exact preset IDs, or disabled presets through `raw_payload.supplier_catalog_preset_ids`; changing presets clears stale prepared supplier search queries.
- Manual supplier candidates can keep the prepared search query that led to them (`source_query` / `source_kind`), preserving review evidence before any price is selected for economics.
- The site can run a schema.org public supplier discovery pass from prepared quick links: search-engine links are ignored, public catalog pages can lead to same-site product pages, public product pages are parsed for Product/Offer JSON-LD, and candidates stay review-only until imported.
- The economics workspace can apply the best available supplier prices across all product positions in one action. `POST /api/tenders/{source}/{external_id}/product-profiles/supplier-options/best/select` fills per-position `raw_payload.economics.unit_cost` where eligible supplier candidates exist, preserves manual selections, skips positions without prices, and returns a refreshed tender decision.
- Public supplier discovery now tries built-in catalog collectors for `officemag`, `komus`, `petrovich`, and `vseinstrumenti` before the generic schema.org fallback. Built-in catalog links get provider-specific diagnostics and candidates, while manual/unknown catalog links still use the generic public schema.org path.
- Built-in catalog collectors can fall back to visible product-page text for OfficeMag, Komus, Petrovich, and Vseinstrumenti when schema.org offers are missing, extracting the product heading, visible ruble price, and availability without treating category pages as supplier candidates.
- The API exposes public supplier catalog health at `/api/supplier-catalogs/health`: by default it reports configured providers without network access, and `?live=1` records per-provider HTTP diagnostics for real public catalog search pages.
- Live supplier catalog health now classifies access-blocked/network failures and keeps short readable response previews, so the economics panel shows when public catalogs require browser/captcha checks instead of silently failing.
- Public supplier discovery now normalizes unit price, currency, VAT mode, delivery note, availability, provider confidence, and collector diagnostics under `raw_payload.supplier_discovery`.
- The economics supplier block surfaces configured supplier catalog health next to preset controls, so the operator can see which built-in catalogs are wired before running discovery.
- The economics supplier block has an explicit manual live health check button; normal page load stays network-free, and live external catalog checks run only after the operator asks for them.
- The economics tab shows supplier discovery collector diagnostics next to staged candidates, including seen links, skipped links, fetched pages, candidates found, and fetch errors.
- Public supplier discovery fetch errors reuse catalog access-blocked/network diagnostics, preserving readable response previews when a provider returns a browser/captcha challenge instead of a product page.
- The economics supplier form can now run review-only discovery from a manually pasted supplier product URL, staging any parsed schema.org or provider-visible offer as a candidate without selecting it or changing economics.
- API errors from supplier discovery are surfaced in the React client, so no-new-candidates and missing-prepared-query messages are visible to the user.
- Supplier discovery run errors for missing prepared queries or no new candidates now return JSON `400` responses from the API handler instead of bubbling up as server errors.
- No-candidate supplier discovery runs now preserve collector diagnostics in the product profile and include the refreshed tender payload in the API error response, so the economics tab can show what was checked even when nothing was staged.
- The economics supplier discovery preview shows a distinct `Кандидаты не найдены` state when only diagnostics are available, avoiding a misleading found-candidates header.
- Supplier discovery candidates can now be staged into `raw_payload.supplier_discovery.candidates` with normalized provider/confidence metadata and reviewed/imported into `supplier_options`; import does not select a supplier or update economics.
- Tender Workbench v1 makes the selected tender area wider, adds a compact decision summary, and splits product details into `Паспорт`, `Цены`, `Поставщики`, and `ТЗ` sub-tabs.
- Tender filters are collapsible in the workbench, letting the tender list expand while preserving quick access to filter controls.
- The site now has a global shell with left navigation for `Дашборд`, `Закупки`, and `SQLite`; the dashboard shows metrics, source state, and workflow queue counts.
- The left navigation can collapse into an icon rail, and the dashboard now also surfaces attention items plus recent tender previews.
- Dashboard cards share one aligned full-width grid, so metrics, source status, queue, attention items, and recent tenders read as one organized workspace.
- The tender list has a page-size selector for 10/25/50/100 rows while keeping 25 as the default.
- Search runs now return readable statistics: new/existing relevant matches plus breakdowns by law, region, and source for Telegram summaries and `/api/search/run`.
- Local dev startup is guarded by `tender_killer.dev_health`, which checks `/api/health` capabilities plus `/api/sources/status` and supplier catalog health before the frontend starts.
- The API health payload now advertises required local-dev capabilities, so a stale backend on port 8000 is rejected before Vite proxies product-profile supplier actions to it.
- The web API now runs an hourly background source refresh through the same search runner as the site `Запустить поиск` button; overlapping manual/auto runs are rejected instead of racing SQLite writes.
- Public market state now tracks NMC, current/minimum public participant bid, participant count, and bid count where the source exposes them; tender cards, economics, lists, and dashboard surfaces use the same saved state from SQLite.
- Local market-state import is available for authenticated Moscow bid snapshots: the operator can paste only the safe `GetBetUpdate` JSON response body into the tender card, and `POST /api/tenders/{source}/{external_id}/market-state/import` stores a sanitized subset under `raw_payload.__market_state_import`.
- The market-state import endpoint rejects recursive sensitive keys such as `Authorization`, `Cookie`, `token`, `password`, and `secret`; Tender Killer still must not store portal passwords, bearer tokens, cookies, SMS codes, or ЭП credentials.
- PDF text extraction now supports `/ToUnicode` CMaps and PDF `Tj`/`TJ` text tokens, so Moscow contract PDFs with embedded text layers extract readable Cyrillic instead of being marked as empty. True scanned image-only PDFs can use an optional local OCR command fallback without adding a mandatory OCR dependency.
- `scripts/ocr-pdf.ps1` is the local OCR wrapper for scanned PDFs. Configure `TENDER_KILLER_PDF_OCR_COMMAND="powershell -NoProfile -ExecutionPolicy Bypass -File scripts\ocr-pdf.ps1 {path}"`; the wrapper uses OCRmyPDF when available, or Tesseract plus Poppler `pdftoppm`. `scripts/dev-web.ps1` auto-enables this wrapper for local API runs when the env var is not already set.
- Runtime/UI text encoding is guarded by `tender_killer.encoding_guard`; `dev_smoke` reuses it to catch Cyrillic mojibake regressions.
- Active tender lists now hide expired purchases by normalized active status plus `deadline_at >= datetime('now')`, so completed/old cards do not dominate the workbench.
- The React frontend has been decomposed out of the former oversized `App.jsx` / `TenderDetails.jsx` surface. Current extracted modules include `api.js`, `constants.js`, `formatters.js`, `Dashboard.jsx`, `DatabaseView.jsx`, `FiltersPanel.jsx`, `TenderList.jsx`, `PaginationBar.jsx`, `TenderDetailActions.jsx`, `TenderDetailsHeader.jsx`, `TenderDetailsStatusStack.jsx`, `TenderDetailsTabs.jsx`, `TenderDetailsShared.jsx`, `TenderDecisionSummary.jsx`, `TenderOverviewTab.jsx`, `TenderAnalysisTab.jsx`, `TenderAnalysisDocumentsPanel.jsx`, `TenderWorkflowTab.jsx`, `TenderProductsTab.jsx`, and `TenderEconomicsTab.jsx`.
- Tender detail behavior is split across focused hooks: `useTenderDetailsUi.js`, `useTenderDocumentAnalysis.js`, `useTenderNotification.js`, `useTenderProductProfiles.js`, `useTenderRefreshDetails.js`, and `useTenderWorkflow.js`.
- `TenderDetails.jsx` is now a thin coordinator for selected tender actions, hooks, and tab composition; workflow, product, overview, analysis/document preparation, and economics UI live in dedicated modules.
- The economics tab owns product cost entry, supplier candidates, assumptions, auto-estimate preview/accept, bid thresholds, and participation decision UI.
- Decision Engine v1 now lives in `src/tender_killer/decision_service.py`. `get_tender_payload(...)` attaches a stable `decision` object that combines economics, analysis, documents, market state, and product profiles into one status/label/next-step payload for future card, list, dashboard, and report surfaces.
- The tender card decision strip, tender list badges, and dashboard previews now read the shared backend `tender.decision` payload through frontend formatter helpers, falling back to saved economics only for older payloads.
- The tender card decision strip and Word report now surface backend decision reasons and blockers, so the operator can see why the current status/next step was recommended.
- Dashboard decision queues now live on the backend in `src/tender_killer/dashboard_queue_service.py` and are exposed as `GET /api/dashboard/queues`. The dashboard no longer infers core queues from the currently visible 25 rows; it scans the active filtered set and returns counts/items for missing prices, TZ review, bid limits, interesting tenders, document text gaps, and urgent deadlines.
- Tender list decision cues are decision-first: each row shows the backend next step and the first blocker/reason instead of separate low-level analysis/economics snippets.
- Auto-pricing now has its first normalized persistence layer: `price_candidates` stores per-position supplier price candidates with provider, source URL/query, unit price, currency, VAT/availability metadata, confidence, review status, fingerprint deduplication, and raw payload evidence. Existing supplier discovery still keeps its UI JSON, but staged/imported candidates are mirrored into this backend table for future automated economics.
- Price candidate review is now live: detail payloads rank per-position price candidates, the API exposes confirm/reject actions, confirming a candidate writes `raw_payload.economics.unit_cost` plus `economics_price_source`, and the economics workspace shows accept/reject controls before supplier options.
- Price candidate quality gates are now live: ranking evaluates VAT, delivery, availability, pack/unit conversion, minimum order, currency, and missing-price risks before any future auto-accept. Candidates expose `quality_status`, `auto_eligible`, and `quality_flags`; confirming a candidate stores this quality snapshot in `economics_price_source`.
- The economics workspace can now accept ready normalized price candidates across the whole tender in one review action. `POST /api/tenders/{source}/{external_id}/price-candidates/ready/confirm` applies only `auto_eligible` candidates to positions without saved costs, skips incomplete/manual positions, marks accepted candidates as confirmed, and refreshes the tender economics/decision payload.
- The economics workspace can now auto-stage saved supplier evidence into normalized price candidates. `POST /api/tenders/{source}/{external_id}/price-candidates/stage` reads existing `raw_payload.supplier_options` and `raw_payload.supplier_discovery.candidates`, normalizes VAT, availability, pack-to-piece unit prices, delivery hints, and raw evidence into `price_candidates`, but does not select suppliers or change economics until the operator confirms ready candidates.
- The economics workspace can now run active review-only supplier price discovery across all product positions that still need costs. `POST /api/tenders/{source}/{external_id}/price-discovery/run` prepares search queries, runs configured public provider collectors, records per-position/provider diagnostics, normalizes discovered evidence into `price_candidates`, and keeps calculation changes gated behind operator confirmation or the existing ready-candidate bulk action.
- Analysis document evidence now has one backend-owned model in `src/tender_killer/analysis_evidence_service.py`. Analysis runs, detail payloads, Word reports, and the React evidence view all read `analysis.evidence_items`, so labels, importance, document names, fragments, and impact text stay consistent for future agents.
- TZ analysis now also emits `analysis.execution_terms`: normalized delivery, payment, advance, warranty, contract security, and penalty conditions. `operator_view` surfaces them as the dedicated `Условия исполнения` section between requirements and price factors, giving the operator a faster route from documents to economics.
- Analysis runs bind checklist evidence and execution terms back to the source document when the fragment can be matched to extracted document text, so multi-document tenders can show whether a condition came from the ТЗ, contract draft, or another file.
- Analysis runs now build `analysis.tz_passport`, a compact backend-owned ТЗ passport with subject, execution terms, supplier documents/compliance, blockers, and price factors. The full-screen analysis workspace renders this passport above the detailed evidence workspace.
- Analysis runs now also build `analysis.analysis_facts` v1, a single fact layer for subject, supplier-document requirements, execution terms, blockers, and price factors. Every actionable fact carries rule id, document binding, evidence fragment, confidence, and operator impact.
- Analysis facts now also carry operator routing fields: `operator_group`, `operator_action`, `price_impact`, and `priority`. This gives the UI, economics layer, reports, and future agents one shared contract for "what to do with this fact".
- Operator analysis sections now prefer `analysis.analysis_facts` when present, grouping the same facts into `Блокеры участия`, `Что подготовить`, `Исполнение договора`, `Влияние на цену`, and `Проверить руками`.
- Operator analysis sections sort fact-backed items by priority, so manually questionable or blocking facts rise above ordinary preparation tasks.
- Operator analysis now also exposes `operator_view.action_plan` and `operator_view.document_state`, turning analysis into a short decision workflow: what to check first, what to price, and whether documents are ready for analysis.
- Rule-based analysis now applies context filters for noisy matches such as storage/confidentiality terms that mention `в течение 3 лет` and licensing-agreement text that is not a supplier license/SRO requirement.
- Economics now reads `analysis.analysis_facts` blockers and price factors first, then falls back to `analysis.tz_passport` and `operator_view`, so delivery, security, payment, compliance, and manually reviewable facts can influence the reserve hint and participation decision from one source contract.
- Rule-based analysis now includes a small benchmark suite for realistic pre-agent ТЗ cases, including medical registration certificates, shelf-life/storage/sterility requirements, installation/commissioning, equivalents/compatibility, SRO/service risks, staff/acceptance acts, and known noisy text that must not trigger false risks.
- Word reports now use one compact operator report mode: ТЗ passport, decision, action plan, document readiness, positions, and economics summary stay in Word, while raw analysis sections, long extracted text, search phrases, and full product-profile detail stay on the site.
- Decision Engine now reads ТЗ passport blockers and price factors as decision inputs, so the tender card/list/dashboard status follows the same analysis contract as the full-screen workspace.

Current verification command:

```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp pytest-cache-files-full
```

Latest full verified result after backend dashboard queues and decision-first list cues: `465 passed`.

Good next steps:

1. Expand provider collectors and candidate scoring so active price discovery can cover more товарные позиции before manual fallback.
2. Surface richer provider-run diagnostics in the economics modal: provider availability, query used, links checked, blocked/network states, candidates found, and why each candidate is ready/review/blocked.
3. Improve the analysis engine from rule-based extraction toward document-aware agent prompts while preserving `analysis.evidence_items`, `analysis.analysis_facts`, and document/page bindings.
4. Add tighter browser visual verification for dashboard queues, list rows, and full-screen analysis/economics workspaces after each major frontend slice.

Previous next steps:

1. Run `Извлечь текст` on real scanned Moscow/MO PDFs and tune OCR settings (`Dpi`, `Language`, `--psm`) if the output is noisy.
2. Continue the workbench split: keep the tender card as the decision summary and use full-screen analysis/economics modes for deeper work.
3. Start the next product/economics UX slice after the current checkpoint is pushed.

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
- Подготовка анализа в сайте собрана внутри `Анализ ТЗ`: кнопка `Подготовить анализ` запускает скачивание документов, извлечение текста и rule-based анализ одной цепочкой; ручные кнопки документов остаются там же для диагностики.
- Первый rule-based анализ ТЗ: требования, риски, красные флаги, национальный режим/1875, сертификаты, приемка, обеспечение, штрафы, хранение/стерильность, монтаж, эквивалентность, совместимость, персонал и акты.
- Анализ ТЗ отдельно выделяет условия исполнения (`analysis.execution_terms`): срок поставки, оплату, аванс, гарантию, обеспечение исполнения и штрафы/пени; в полноэкранном анализе они отображаются отдельной секцией `Условия исполнения`.
- Анализ ТЗ сохраняет единый слой фактов `analysis.analysis_facts` v1: предмет, документы поставщика, условия исполнения, блокеры и факторы цены с привязкой к документу, фрагменту, rule id, уверенности и влиянию на решение.
- Каждый факт анализа дополнительно содержит операторские поля: группу, действие, тип влияния на цену и приоритет. Это будущий контракт для агента: агент должен улучшать эти же поля, а не придумывать новый формат.
- Полноэкранный анализ показывает план проверки из backend `operator_view.action_plan` и состояние документов из `operator_view.document_state`, чтобы оператор видел следующий шаг без прокрутки сырых списков.
- Экономика использует `analysis.analysis_facts` как первый источник блокеров и факторов цены для `analysis_cost_drivers` / `analysis_reserve_hint`; старые `tz_passport` и `operator_view` остаются fallback.
- До подключения агентов есть мини-бенчмарк rule-based анализа: медицинские документы/срок годности/хранение, монтаж, эквиваленты, СРО/услуги, персонал, акты и шумовые фразы без ложных рисков.
- Товарные профили в SQLite: один тендер может иметь 20-40 отдельных профилей, по одному на позицию закупки.
- Word-отчет по закупке теперь один и короткий: паспорт, позиции, документы, паспорт ТЗ, решение по анализу, план проверки, состояние документов и компактная экономика без сырого текста, поисковых фраз и полного разворота товарных профилей.
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
- `TENDER_KILLER_WEB_AUTO_SEARCH_MINUTES` - интервал фонового обновления источников в web API, по умолчанию `60`; `0` отключает.
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

Те же переменные можно хранить в локальном `.env` в корне проекта. Файл игнорируется Git, чтобы токен бота не попал в репозиторий:

```text
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
TENDER_KILLER_FILTERS=filters.json
```

Для авто-поиска в фоне добавьте `TELEGRAM_CHAT_ID`. Без него ручной `/search` работает, но фоновой рассылке некуда писать.

Команды:

- Можно отправить обычный текст, например `строительные материалы Москва МО до 2 млн 44-ФЗ`. Бот сохранит отдельный быстрый профиль `quick-entry` и предложит запустить поиск только по нему. Старые фильтры и профили останутся на месте.
- Карточки найденных закупок короткие: название, площадка/закон, сумма/срок, заказчик/регион, фильтр и ссылка. Под карточкой есть кнопки `Открыть источник`, `Документы`, `Анализ`; документы и анализ берутся из локальной SQLite, если они уже сохранены.
- Чтобы кнопка `TG` на сайте отправляла выбранную закупку, API сайта должен быть запущен с `TELEGRAM_BOT_TOKEN`. `TELEGRAM_CHAT_ID` можно не задавать вручную после того, как вы написали боту любое сообщение: бот сохранит последний chat id в локальную SQLite, и сайт использует его для ручной отправки.
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

Recommended combined local startup:

```powershell
npm run dev
```

This starts a persistent local dev supervisor. It keeps the backend on `http://127.0.0.1:8000` and the site on `http://127.0.0.1:5173`, checks health continuously, and restarts stale or unhealthy processes on those ports. If `npm.cmd` is available, the supervisor uses Vite for the frontend. If Node/npm is unavailable or Vite does not become healthy, it falls back to `tender_killer.dev_static_proxy`, which serves the existing `web/dist` build and proxies `/api` to the backend so the site remains reachable. Set `TENDER_KILLER_DEV_FORCE_STATIC=1` to force the static proxy fallback.

The supervisor writes local runtime logs to `logs/` and runs until `Ctrl+C`.

Manual API health check:

```powershell
.\.venv\Scripts\python.exe -m tender_killer.dev_health --base-url http://127.0.0.1:8000
```

Local site smoke check after Vite is running:

```powershell
.\.venv\Scripts\python.exe -m tender_killer.dev_smoke --api-base-url http://127.0.0.1:8000 --web-base-url http://127.0.0.1:5173
```

The smoke check verifies direct API health, Vite HTML, Vite `/api` proxy health, source status proxying, key UI labels, and Cyrillic mojibake detection.

Открыть: `http://127.0.0.1:5173`.

На сайте сейчас есть:

- фильтры по площадке, закону, региону, статусу, ОКПД2/классификатору и цене;
- ручной запуск поиска;
- список закупок с количеством документов и позиций;
- правая карточка с короткой сводкой решения и полноэкранными рабочими режимами `Товары`, `Анализ ТЗ` и `Экономика`;
- кнопка `Обновить` для добора детальной карточки;
- скачивание документов, извлечение текста и rule-based анализ ТЗ внутри рабочего режима `Анализ ТЗ`;
- товарные профили по позициям закупки;
- скачивание Word-отчета;
- отправка выбранной закупки в Telegram;
- SQLite-viewer для локальной диагностики базы.

Правая карточка специально оставлена коротким экраном решения: полный разбор уходит в полноэкранные рабочие режимы анализа, товарных профилей и экономики, а документы живут внутри анализа вместе с извлечением текста и Word-отчетом.

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
