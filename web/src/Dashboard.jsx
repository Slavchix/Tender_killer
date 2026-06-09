import { useState } from 'react'
import { Bell, CheckCircle2, ChevronDown, Clock, FileText, Layers, RefreshCcw, WalletCards } from 'lucide-react'
import { sourceLabels } from './constants'
import { formatDate, formatDateTime, formatMoney, hasParticipantBid, nmcPriceValue, participantBidValue, tenderDecisionLabel } from './formatters'

const SUPPLIER_CATALOG_DASHBOARD_FALLBACKS = [
  { preset_id: 'officemag_office_supplies', label: 'OfficeMag', provider: 'officemag' },
  { preset_id: 'komus_office_supplies', label: 'Komus', provider: 'komus' },
  { preset_id: 'petrovich_building_materials', label: 'Petrovich', provider: 'petrovich' },
  { preset_id: 'vseinstrumenti_building_materials', label: 'ВсеИнструменты', provider: 'vseinstrumenti' },
  { preset_id: 'lemanapro_building_materials', label: 'Lemana Pro', provider: 'lemanapro' },
]

const SUPPLIER_CATALOG_PROVIDER_POLICY = {
  officemag: {
    search_mode: 'manual_only',
    small_tender_active_search: false,
    recommended_flow: 'quick links/manual URL',
    operator_note: 'Quick links или вручную выбранная публичная карточка товара.',
  },
  komus: {
    search_mode: 'manual_only',
    small_tender_active_search: false,
    recommended_flow: 'quick links/feed/КП',
    operator_note: 'Quick links, прайс/feed или коммерческое предложение.',
  },
  petrovich: {
    search_mode: 'active_small_search',
    small_tender_active_search: true,
    recommended_flow: 'limited search/manual URL',
    operator_note: 'Активный поиск только для закупок до 5 позиций.',
  },
  vseinstrumenti: {
    search_mode: 'active_small_search',
    small_tender_active_search: true,
    recommended_flow: 'limited search/manual URL',
    operator_note: 'Активный поиск только для закупок до 5 позиций.',
  },
  lemanapro: {
    search_mode: 'manual_only',
    small_tender_active_search: false,
    recommended_flow: 'quick links/manual URL',
    operator_note: 'Quick links или вручную выбранная публичная карточка товара.',
  },
}

function Metric({ label, value, tone }) {
  return (
    <div className={`metric ${tone || ''}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}

export function DashboardView({
  dashboardQueueError,
  dashboardQueues,
  tenderPage,
  stats,
  workflowCounts,
  sources,
  sourceStatusError,
  supplierCatalogHealth,
  supplierCatalogHealthError,
  supplierCatalogHealthLoading,
  searchSummary,
  error,
  onRefreshSources,
  onRefreshSupplierCatalogs,
  onOpenTender,
  onOpenTenders,
  tenders,
}) {
  const queuePayload = dashboardQueues || {}
  const summary = queuePayload.summary || {}
  const currentOfferCount = numberOrFallback(
    summary.current_offers,
    (tenders || []).filter((tender) => hasParticipantBid(tender.market_state)).length,
  )
  const noParticipantsCount = numberOrFallback(
    summary.no_participants,
    (tenders || []).filter((tender) => tender.market_state?.status === 'no_participants').length,
  )
  const decisionReadyCount = numberOrFallback(
    summary.decisions,
    (tenders || []).filter((tender) => tender.decision).length,
  )
  const marketMetric = currentOfferCount ? `${currentOfferCount} с ценой` : (noParticipantsCount ? `${noParticipantsCount} без участников` : 'нет данных')
  const queueColumns = dashboardQueueColumns(dashboardQueues, tenders)
  const urgentQueue = queueById(dashboardQueues, 'urgent_deadline')
  const documentsQueue = queueById(dashboardQueues, 'documents_review')
  const totalActive = numberOrFallback(summary.total, tenderPage.total || stats.active)
  const tzReviewCount = queueCount(dashboardQueues, 'needs_review')
  const noCostCount = queueCount(dashboardQueues, 'missing_prices')
  const readyCount = queueCount(dashboardQueues, 'interesting') || decisionReadyCount
  const deadlineTodayCount = queueCount(dashboardQueues, 'urgent_deadline')

  return (
    <section className="dashboard-view">
      <section className="metrics dashboard-hero-metrics">
        <Metric label="Всего активных" value={totalActive} />
        <Metric label="На разборе ТЗ" value={tzReviewCount} tone={tzReviewCount ? 'purple' : ''} />
        <Metric label="Без себестоимости" value={noCostCount} tone={noCostCount ? 'warning' : ''} />
        <Metric label="Готовы к участию" value={readyCount} tone={readyCount ? 'good' : ''} />
        <Metric label="Дедлайны сегодня" value={deadlineTodayCount} tone={deadlineTodayCount ? 'danger' : ''} />
        <Metric label="API" value={error || dashboardQueueError ? 'ошибка' : 'ok'} tone={error || dashboardQueueError ? 'danger' : 'good'} />
      </section>
      {searchSummary && <div className="run-summary">{searchSummary}</div>}
      <section className="dashboard-grid dashboard-main-layout">
        <div className="dashboard-left-stack">
          <section className="dashboard-panel dashboard-queue-panel" aria-label="Очередь решений">
            <div className="dashboard-queue-heading">
              <div>
                <div className="panel-title"><Layers size={18} /> Очередь закупок</div>
                <p className="dashboard-panel-lead">Быстрый разбор того, что мешает участию: ТЗ, цена, лимит и готовность заявки.</p>
              </div>
              <div className="dashboard-queue-summary">
                <span>Ставки: {marketMetric}</span>
                {dashboardQueueError && <span className="source-status-error">{dashboardQueueError}</span>}
                <button className="primary-button dashboard-open-button" onClick={() => onOpenTenders()} type="button">
                  Открыть закупки
                </button>
              </div>
            </div>
            <div className="dashboard-queue-board">
              {queueColumns.map((column) => (
                <DashboardQueueColumn column={column} key={column.id} onOpenTender={onOpenTender} />
              ))}
            </div>
          </section>

          <section className="dashboard-secondary-grid">
            <DashboardTenderPreview onOpenTender={onOpenTender} tenders={tenders} />
            <DashboardWorkInProgressPanel onOpenTender={onOpenTender} tenders={tenders} />
          </section>
        </div>

        <aside className="dashboard-right-rail">
          <DashboardDeadlinePanel onOpenTender={onOpenTender} queue={urgentQueue} />
          <DashboardDocumentProblemsPanel onOpenTender={onOpenTender} queue={documentsQueue} />
          <DashboardAttentionPanel
            dashboardQueueError={dashboardQueueError}
            dashboardQueues={dashboardQueues}
            error={error}
            onOpenTender={onOpenTender}
            sources={sources}
            tenders={tenders}
            workflowCounts={workflowCounts}
          />
          <SourceStatusPanel
            error={sourceStatusError}
            onRefresh={onRefreshSources}
            sources={sources}
          />
          <SupplierCatalogStatusPanel
            catalogHealth={supplierCatalogHealth}
            error={supplierCatalogHealthError}
            loading={supplierCatalogHealthLoading}
            onRefresh={onRefreshSupplierCatalogs}
          />
        </aside>
      </section>
    </section>
  )
}

function numberOrFallback(value, fallback) {
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : fallback
}

function queueById(dashboardQueues, id) {
  return (dashboardQueues?.queues || []).find((queue) => queue.id === id) || null
}

function queueCount(dashboardQueues, id) {
  return Number(queueById(dashboardQueues, id)?.count || 0)
}

function dashboardQueueKpis(dashboardQueues, workflowCounts) {
  const queues = dashboardQueues?.queues || []
  if (queues.length) {
    return queues.slice(0, 4).map((queue) => ({ label: queue.label, value: queue.count || 0 }))
  }
  return [
    { label: 'Новые', value: workflowCounts.new || 0 },
    { label: 'Интересные', value: workflowCounts.interesting || 0 },
    { label: 'В работе', value: workflowCounts.in_progress || 0 },
    { label: 'Архив', value: workflowCounts.archive || 0 },
  ]
}

function dashboardQueueColumns(dashboardQueues, tenders) {
  const queues = dashboardQueues?.queues || []
  const queueMap = Object.fromEntries(queues.map((queue) => [queue.id, queue]))
  const fallbackTenders = tenders || []
  return [
    {
      id: 'needs_review',
      label: 'Разобрать',
      description: 'Проверить ТЗ, ограничения и документы до расчета.',
      tone: 'purple',
      icon: FileText,
      items: queueMap.needs_review?.items || fallbackTenders.filter((tender) => !tender.decision).slice(0, 5),
    },
    {
      id: 'missing_prices',
      label: 'Посчитать',
      description: 'Нужна себестоимость, ставка поставщика или рыночная цена.',
      tone: 'warning',
      icon: WalletCards,
      items: queueMap.missing_prices?.items || fallbackTenders.filter((tender) => !hasParticipantBid(tender.market_state)).slice(0, 5),
    },
    {
      id: 'with_limit',
      label: 'Проверить лимит',
      description: 'Есть данные для решения, нужен контроль маржи и риска.',
      tone: 'primary',
      icon: Clock,
      items: queueMap.with_limit?.items || fallbackTenders.filter((tender) => tender.decision).slice(0, 5),
    },
    {
      id: 'interesting',
      label: 'Готово',
      description: 'Можно открывать карточку и готовить заявку.',
      tone: 'good',
      icon: CheckCircle2,
      items: queueMap.interesting?.items || fallbackTenders.filter((tender) => ['interesting', 'in_progress'].includes(tender.workflow_status)).slice(0, 5),
    },
  ]
}

function DashboardQueueColumn({ column, onOpenTender }) {
  const Icon = column.icon
  const items = (column.items || []).slice(0, 4)
  return (
    <section className={`dashboard-queue-column ${column.tone}`}>
      <div className="dashboard-queue-column-title">
        <Icon size={17} />
        <div>
          <strong>{column.label}</strong>
          <span>{items.length}</span>
        </div>
      </div>
      <p>{column.description}</p>
      <div className="dashboard-queue-items">
        {items.map((item) => (
          <button key={`${item.source}-${item.external_id}`} onClick={() => onOpenTender(item)} type="button">
            <strong>{item.title || 'Закупка без названия'}</strong>
            <span>{dashboardTenderLine(item)}</span>
          </button>
        ))}
        {!items.length && <div className="dashboard-empty-note">Очередь пустая</div>}
      </div>
    </section>
  )
}

function DashboardDeadlinePanel({ queue, onOpenTender }) {
  const items = (queue?.items || []).slice(0, 4)
  return (
    <section className="dashboard-panel dashboard-rail-panel">
      <div className="panel-title"><Clock size={18} /> Срочные дедлайны</div>
      <div className="dashboard-rail-list">
        {items.map((item) => (
          <button key={`${item.source}-${item.external_id}-deadline`} onClick={() => onOpenTender(item)} type="button">
            <strong>{formatDate(item.deadline_at)}</strong>
            <span>{item.title}</span>
          </button>
        ))}
        {!items.length && <div className="dashboard-empty-note">Сегодня срочных дедлайнов нет</div>}
      </div>
    </section>
  )
}

function DashboardDocumentProblemsPanel({ queue, onOpenTender }) {
  const items = (queue?.items || []).slice(0, 4)
  return (
    <section className="dashboard-panel dashboard-rail-panel">
      <div className="panel-title"><FileText size={18} /> Проблемы документов</div>
      <div className="dashboard-rail-list">
        {items.map((item) => (
          <button key={`${item.source}-${item.external_id}-documents`} onClick={() => onOpenTender(item)} type="button">
            <strong>{item.customer || 'Документы'}</strong>
            <span>{item.title}</span>
          </button>
        ))}
        {!items.length && <div className="dashboard-empty-note">Критичных проблем с документами нет</div>}
      </div>
    </section>
  )
}

function DashboardAttentionPanel({ dashboardQueueError, dashboardQueues, error, sources, tenders, workflowCounts, onOpenTender }) {
  const sourceErrors = (sources || []).filter((source) => source.last_error)
  const attentionItems = []

  if (error) attentionItems.push({ label: 'API сайта', value: error })
  if (dashboardQueueError) attentionItems.push({ label: 'Очереди', value: dashboardQueueError })
  if (sourceErrors.length) attentionItems.push({ label: 'Источники', value: `${sourceErrors.length} требуют проверки` })
  attentionItems.push(...dashboardQueueItems(dashboardQueues))
  if (!dashboardQueues?.queues?.length) {
    if (workflowCounts.new) attentionItems.push({ label: 'Новые закупки', value: `${workflowCounts.new} еще не разобраны` })
    if (workflowCounts.interesting) attentionItems.push({ label: 'Интересные', value: `${workflowCounts.interesting} ждут решения` })
    attentionItems.push(...decisionAttentionItems(tenders))
  }

  return (
    <section className="dashboard-panel dashboard-rail-panel">
      <div className="panel-title"><Bell size={18} /> Требует внимания</div>
      <div className="dashboard-attention-list">
        {attentionItems.slice(0, 4).map((item) => (
          item.tender ? (
            <button key={item.key || item.label} onClick={() => onOpenTender(item.tender)} type="button">
              <span>{item.label}</span>
              <strong>{item.value}</strong>
            </button>
          ) : (
            <div className="dashboard-attention-note" key={item.key || item.label}>
              <span>{item.label}</span>
              <strong>{item.value}</strong>
            </div>
          )
        ))}
        {!attentionItems.length && <div className="dashboard-empty-note">Критичных событий нет</div>}
      </div>
    </section>
  )
}

function dashboardQueueItems(dashboardQueues) {
  return (dashboardQueues?.queues || [])
    .filter((queue) => Number(queue.count || 0) > 0)
    .slice(0, 4)
    .map((queue) => {
      const firstItem = queue.items?.[0]
      const preview = firstItem?.title ? ` · ${firstItem.title}` : ''
      return {
        key: `dashboard-queue-${queue.id}`,
        label: 'Очередь решений',
        tender: firstItem,
        value: `${queue.label}: ${queue.count}${preview}`,
      }
    })
}

function decisionAttentionItems(tenders) {
  return (tenders || [])
    .filter((tender) => tender.decision?.blockers?.length)
    .slice(0, 3)
    .map((tender) => ({
      key: `${tender.source}-${tender.external_id}-decision`,
      label: 'ТЗ/решение',
      tender,
      value: `${tenderDecisionLabel(tender)}: ${tender.decision.blockers[0]}`,
    }))
}

function DashboardTenderPreview({ tenders, onOpenTender }) {
  const previewTenders = (tenders || []).slice(0, 6)

  return (
    <section className="dashboard-panel">
      <div className="panel-title"><FileText size={18} /> Последние закупки</div>
      <div className="dashboard-tender-list">
        {previewTenders.map((tender) => (
          <button key={`${tender.source}-${tender.external_id}`} onClick={() => onOpenTender(tender)} type="button">
            <strong>{tender.title}</strong>
            <span>{dashboardTenderLine(tender)}</span>
          </button>
        ))}
        {!previewTenders.length && <div className="dashboard-empty-note">Запусти поиск, чтобы увидеть свежие закупки</div>}
      </div>
    </section>
  )
}

function DashboardWorkInProgressPanel({ tenders, onOpenTender }) {
  const [activeTab, setActiveTab] = useState('in_progress')
  const buckets = {
    in_progress: (tenders || []).filter((tender) => ['interesting', 'in_progress'].includes(tender.workflow_status)),
    preparing: (tenders || []).filter((tender) => tender.decision || tender.workflow_status === 'opened'),
    completed: (tenders || []).filter((tender) => tender.workflow_status === 'archive'),
  }
  const tabs = [
    { id: 'in_progress', label: 'В работе' },
    { id: 'preparing', label: 'Готовим заявку' },
    { id: 'completed', label: 'Завершенные' },
  ]
  const activeItems = (buckets[activeTab] || []).slice(0, 6)

  return (
    <section className="dashboard-panel dashboard-work-panel">
      <div className="panel-title"><CheckCircle2 size={18} /> Наши закупки в работе</div>
      <div className="dashboard-work-tabs">
        {tabs.map((tab) => (
          <button
            className={activeTab === tab.id ? 'active' : ''}
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            type="button"
          >
            {tab.label}
            <span>{buckets[tab.id].length}</span>
          </button>
        ))}
      </div>
      <div className="dashboard-tender-list">
        {activeItems.map((tender) => (
          <button key={`${tender.source}-${tender.external_id}-${activeTab}`} onClick={() => onOpenTender(tender)} type="button">
            <strong>{tender.title}</strong>
            <span>{dashboardTenderLine(tender)}</span>
          </button>
        ))}
        {!activeItems.length && <div className="dashboard-empty-note">В этой вкладке пока пусто</div>}
      </div>
    </section>
  )
}

function dashboardTenderLine(tender) {
  return `${sourceLabels[tender.source] || tender.source} · НМЦК ${nmcPriceValue(tender)} · ставка ${participantBidValue(tender.market_state)} · ${tenderDecisionLabel(tender)} · ${formatDate(tender.deadline_at)}`
}

function SourceStatusPanel({ sources, error, onRefresh }) {
  const [expanded, setExpanded] = useState(false)
  return (
    <section className={`source-status-panel collapsible-status-panel ${expanded ? 'expanded' : 'collapsed'}`}>
      <div className="source-status-header">
        <button
          aria-expanded={expanded}
          className="source-status-toggle"
          onClick={() => setExpanded((value) => !value)}
          type="button"
        >
          <span className="panel-title"><RefreshCcw size={18} /> Источники</span>
          <span className="source-status-summary">{sourceSummaryText(sources, error)}</span>
          <ChevronDown className="source-status-chevron" size={16} />
        </button>
        <button className="icon-button small" onClick={onRefresh} title="Обновить статус источников" type="button">
          <RefreshCcw size={16} />
        </button>
      </div>
      {expanded && (
        <>
          {error && <div className="source-status-error">{error}</div>}
          <div className="source-status-list">
            {(sources || []).map((source) => (
              <SourceStatusRow key={source.source} source={source} />
            ))}
            {!sources?.length && !error && <span className="source-status-empty">Статус источников пока не загружен</span>}
          </div>
        </>
      )}
    </section>
  )
}

function SourceStatusRow({ source }) {
  const tone = source.last_error ? 'danger' : source.last_success_at ? 'good' : 'idle'
  const statusText = source.last_error ? 'ошибка' : source.last_success_at ? 'ok' : 'нет запусков'
  return (
    <div className={`source-status-row ${tone}`}>
      <span className="source-status-dot" />
      <div className="source-status-main">
        <div>
          <strong>{source.label || sourceLabels[source.source] || source.source}</strong>
          <span>{statusText}</span>
        </div>
        <div className="source-status-meta">
          <span>успех: {formatDateTime(source.last_success_at)}</span>
          <span>checkpoint: {formatDateTime(source.last_seen_published_at)}</span>
          {source.last_error && <span className="source-status-message">{source.last_error}</span>}
        </div>
      </div>
    </div>
  )
}

function sourceSummaryText(sources, error) {
  if (error) {
    return 'API ошибка'
  }
  const items = sources || []
  const failed = items.filter((source) => source.last_error).length
  if (failed) {
    return `${failed} ошибок из ${items.length || failed}`
  }
  if (items.length) {
    return `${items.length} подключено`
  }
  return 'нет данных'
}

function SupplierCatalogStatusPanel({ catalogHealth, error, loading, onRefresh }) {
  const [expanded, setExpanded] = useState(false)
  const catalogs = mergeSupplierCatalogDashboardFallbacks(catalogHealth?.catalogs || [])
  return (
    <section className={`source-status-panel supplier-catalog-dashboard collapsible-status-panel ${expanded ? 'expanded' : 'collapsed'}`}>
      <div className="source-status-header">
        <button
          aria-expanded={expanded}
          className="source-status-toggle"
          onClick={() => setExpanded((value) => !value)}
          type="button"
        >
          <span className="panel-title"><RefreshCcw size={18} /> Каталоги поставщиков</span>
          <span className="source-status-summary">{catalogSummaryText(catalogs, error, loading)}</span>
          <ChevronDown className="source-status-chevron" size={16} />
        </button>
        <button
          className="icon-button small"
          disabled={loading}
          onClick={onRefresh}
          title="Проверить каталоги поставщиков"
          type="button"
        >
          <RefreshCcw size={16} />
        </button>
      </div>
      {expanded && (
        <>
          {error && <div className="source-status-error">{error}</div>}
          <div className="source-status-meta">
            <span>{catalogHealth?.checked_at ? `проверка: ${formatDateTime(catalogHealth.checked_at)}` : 'live-проверки еще не было'}</span>
            {catalogHealth?.cached && <span>последний сохраненный статус</span>}
            {loading && <span>проверяю...</span>}
          </div>
          <div className="source-status-list">
            {catalogs.map((catalog) => (
              <SupplierCatalogStatusRow catalog={catalog} key={catalog.preset_id || catalog.provider} />
            ))}
            {!catalogs.length && !error && <span className="source-status-empty">Каталоги поставщиков пока не проверялись</span>}
          </div>
        </>
      )}
    </section>
  )
}

function mergeSupplierCatalogDashboardFallbacks(catalogs) {
  const merged = catalogs.map(enrichSupplierCatalogPolicy)
  const seen = new Set()
  merged.forEach((catalog) => {
    const catalogKeys = [catalog.preset_id, catalog.provider]
    catalogKeys.forEach((value) => {
      if (value) seen.add(value.toString().toLowerCase())
    })
  })
  for (const fallback of SUPPLIER_CATALOG_DASHBOARD_FALLBACKS) {
    const keys = [fallback.preset_id, fallback.provider].map((value) => value.toLowerCase())
    if (keys.some((key) => seen.has(key))) continue
    merged.push(enrichSupplierCatalogPolicy({
      ...fallback,
      status: 'configured',
      connection_state: 'configured',
      access_mode: 'configured',
    }))
    keys.forEach((key) => seen.add(key))
  }
  return merged
}

function enrichSupplierCatalogPolicy(catalog) {
  const provider = (catalog.provider || '').toString().toLowerCase()
  const policy = SUPPLIER_CATALOG_PROVIDER_POLICY[provider] || {}
  return {
    ...policy,
    ...catalog,
    search_mode: catalog.search_mode || policy.search_mode,
    small_tender_active_search: catalog.small_tender_active_search ?? policy.small_tender_active_search,
    recommended_flow: catalog.recommended_flow || policy.recommended_flow,
    operator_note: catalog.operator_note || policy.operator_note,
  }
}

function catalogSummaryText(catalogs, error, loading) {
  if (loading) {
    return 'проверяю...'
  }
  if (error) {
    return 'API ошибка'
  }
  const activeCatalogs = catalogs.filter(isCatalogActiveSmallSearch)
  const manualOnly = catalogs.filter(isCatalogManualOnly).length
  const failed = activeCatalogs.filter(isCatalogProblem).length
  if (failed) {
    return manualOnly ? `${failed} активн. проблем · ${manualOnly} вручную` : `${failed} активн. проблем`
  }
  const ready = activeCatalogs.filter(isCatalogReady).length
  if (activeCatalogs.length) {
    return manualOnly ? `${ready}/${activeCatalogs.length} авто · ${manualOnly} вручную` : `${ready}/${activeCatalogs.length} авто`
  }
  return manualOnly ? `${manualOnly} вручную` : `${catalogs.length} настроено`
}

function SupplierCatalogStatusRow({ catalog }) {
  const manualOnly = isCatalogManualOnly(catalog)
  const tone = manualOnly
    ? 'idle'
    : isCatalogReady(catalog)
    ? 'good'
    : isCatalogProblem(catalog)
      ? 'danger'
      : 'idle'
  const detailMessage = supplierCatalogDetailMessage(catalog)
  return (
    <div className={`source-status-row ${tone}`}>
      <span className="source-status-dot" />
      <div className="source-status-main">
        <div>
          <strong>{catalog.label || catalog.provider}</strong>
          <span>{supplierCatalogStatusText(catalog)}</span>
        </div>
        <div className="source-status-meta">
          <span>{supplierCatalogStateLabel(catalog)}</span>
          {manualOnly && catalog.recommended_flow && <span>{catalog.recommended_flow}</span>}
          {!manualOnly && catalog.http_status && <span>HTTP {catalog.http_status}</span>}
          {!manualOnly && catalog.error_kind && <span>{supplierCatalogErrorKindLabel(catalog.error_kind)}</span>}
          {detailMessage && <span className="source-status-message">{detailMessage}</span>}
        </div>
      </div>
    </div>
  )
}

function isCatalogActiveSmallSearch(catalog) {
  return catalog.small_tender_active_search === true || catalog.search_mode === 'active_small_search'
}

function isCatalogManualOnly(catalog) {
  return catalog.small_tender_active_search === false
    || catalog.search_mode === 'manual_only'
    || catalog.connection_state === 'manual_only'
    || catalog.status === 'manual_only'
}

function isCatalogReady(catalog) {
  const state = catalog.connection_state || catalog.status || 'configured'
  return state === 'reachable' || catalog.status === 'ok'
}

function isCatalogProblem(catalog) {
  const state = catalog.connection_state || catalog.status || 'configured'
  return ['blocked', 'captcha', 'timeout', 'no_cards', 'parser_broken', 'network_error'].includes(state) || catalog.status === 'error'
}

function supplierCatalogStatusText(catalog) {
  const state = catalog.connection_state || catalog.status || 'configured'
  if (isCatalogManualOnly(catalog)) {
    return 'вручную'
  }
  if (state === 'reachable' || catalog.status === 'ok') {
    return 'ok'
  }
  if (state === 'captcha') {
    return 'капча'
  }
  if (state === 'blocked') {
    return 'блокировка'
  }
  if (state === 'timeout') {
    return 'таймаут'
  }
  if (state === 'no_cards') {
    return 'нет карточек'
  }
  if (state === 'parser_broken') {
    return 'проверить парсер'
  }
  if (catalog.status === 'error') {
    return 'ошибка'
  }
  return isCatalogActiveSmallSearch(catalog) ? 'автопоиск' : 'настроен'
}

function supplierCatalogStateLabel(catalog) {
  const state = catalog.connection_state || catalog.status || 'configured'
  if (isCatalogManualOnly(catalog)) {
    return 'ручной режим'
  }
  if (state === 'reachable') {
    return `автопоиск до ${catalog.max_active_positions || 5}`
  }
  if (state === 'configured') {
    return isCatalogActiveSmallSearch(catalog) ? `автопоиск до ${catalog.max_active_positions || 5}` : 'настроен'
  }
  if (state === 'blocked') return 'блокировка'
  if (state === 'captcha') return 'капча'
  if (state === 'timeout') return 'таймаут'
  if (state === 'no_cards') return 'нет карточек'
  if (state === 'parser_broken') return 'парсер'
  if (state === 'network_error') return 'сеть'
  return state
}

function supplierCatalogErrorKindLabel(errorKind) {
  if (errorKind === 'access_blocked') return 'доступ закрыт'
  if (errorKind === 'network_error') return 'сеть'
  if (errorKind === 'http_error') return 'HTTP'
  return errorKind
}

function supplierCatalogDetailMessage(catalog) {
  if (isCatalogManualOnly(catalog)) {
    return catalog.operator_note || ''
  }
  return catalog.error || catalog.body_preview || ''
}
