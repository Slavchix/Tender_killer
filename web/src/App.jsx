import { useEffect, useMemo, useRef, useState } from 'react'
import {
  Bell,
  Building2,
  CalendarClock,
  ChevronLeft,
  ChevronRight,
  CircleDollarSign,
  Database,
  ExternalLink,
  FileText,
  Filter,
  PlayCircle,
  RefreshCcw,
  Scale,
  Search,
} from 'lucide-react'
import './styles.css'

const sourceLabels = {
  moscow_supplier_portal: 'Москва',
  mosreg_market: 'МО',
}

const workflowLabels = {
  new: 'Новая',
  opened: 'Открыта',
  interesting: 'Интересно',
  in_progress: 'В работу',
  skipped: 'Пропустить',
  archive: 'Архив',
}

const viewLabels = {
  dashboard: 'Дашборд',
  tenders: 'Закупки',
  database: 'SQLite',
}

const navItems = [
  { id: 'dashboard', label: viewLabels.dashboard, caption: 'Сводка', icon: Building2 },
  { id: 'tenders', label: viewLabels.tenders, caption: 'Работа', icon: FileText },
  { id: 'database', label: viewLabels.database, caption: 'Данные', icon: Database },
]

const sourceOptions = [
  { value: 'moscow_supplier_portal', label: 'Москва' },
  { value: 'mosreg_market', label: 'МО' },
]

const lawOptions = [
  { value: '', label: 'Все' },
  { value: '44-ФЗ', label: '44-ФЗ' },
  { value: '223-ФЗ', label: '223-ФЗ' },
]

const statusOptions = [
  { value: 'active', label: 'Активные' },
  { value: '', label: 'Все' },
  { value: 'Прием', label: 'Прием заявок' },
  { value: 'Заверш', label: 'Завершенные' },
]

const quickRegionOptions = [
  { value: 'Москва', label: 'Москва' },
  { value: 'Московская область', label: 'МО' },
  { value: 'Москва + МО', label: 'Москва + МО' },
]

const sourceFamilyOptions = [
  { value: '', label: 'Все' },
  { value: 'moscow', label: 'Москва' },
  { value: 'mosreg', label: 'МО' },
]

const procedureTypeOptions = [
  { value: '', label: 'Все' },
  { value: 'electronic_shop', label: 'Эл-магазин' },
  { value: 'quotation_session', label: 'Котировка' },
  { value: 'supplier_portal', label: 'Портал' },
  { value: 'need', label: 'Потребность' },
  { value: 'tender', label: 'Тендер' },
]

const initialFilters = {
  q: '',
  source: '',
  law: '',
  region: '',
  status: 'active',
  source_family: '',
  procedure_type: '',
  customer_inn: '',
  workflow_status: '',
  okpd2: '',
  min_price: '',
  max_price: '',
}

const defaultTenderPageLimit = 25
const tenderPageLimitOptions = [10, 25, 50, 100]

const productDetailModes = [
  { id: 'overview', label: 'Паспорт' },
  { id: 'pricing', label: 'Цены' },
  { id: 'suppliers', label: 'Поставщики' },
  { id: 'requirements', label: 'ТЗ' },
]

const initialTenderPage = {
  total: 0,
  limit: defaultTenderPageLimit,
  offset: 0,
  has_previous: false,
  previous_offset: null,
  has_next: false,
  next_offset: null,
}

function App() {
  const [filters, setFilters] = useState(initialFilters)
  const [appliedFilters, setAppliedFilters] = useState(initialFilters)
  const [tenders, setTenders] = useState([])
  const [selected, setSelected] = useState(null)
  const [details, setDetails] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [searching, setSearching] = useState(false)
  const [searchSummary, setSearchSummary] = useState('')
  const [view, setView] = useState('dashboard')
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [filtersCollapsed, setFiltersCollapsed] = useState(false)
  const [sourceStatus, setSourceStatus] = useState([])
  const [sourceStatusError, setSourceStatusError] = useState('')
  const [pageOffset, setPageOffset] = useState(0)
  const [pageLimit, setPageLimit] = useState(defaultTenderPageLimit)
  const [tenderPage, setTenderPage] = useState(initialTenderPage)

  useEffect(() => {
    loadTenders(appliedFilters, pageOffset)
  }, [appliedFilters, pageOffset, pageLimit])

  useEffect(() => {
    loadSourceStatus()
  }, [])

  useEffect(() => {
    if (!selected) {
      setDetails(null)
      return
    }
    fetch(`/api/tenders/${encodeURIComponent(selected.source)}/${encodeURIComponent(selected.external_id)}`)
      .then((response) => response.ok ? response.json() : Promise.reject(new Error('Карточка не найдена')))
      .then(setDetails)
      .catch((err) => setError(err.message))
  }, [selected])

  function loadTenders(nextAppliedFilters = appliedFilters, nextOffset = pageOffset) {
    if (nextAppliedFilters && typeof nextAppliedFilters.preventDefault === 'function') {
      nextAppliedFilters = appliedFilters
      nextOffset = pageOffset
    }
    setLoading(true)
    setError('')
    const params = new URLSearchParams()
    Object.entries(nextAppliedFilters).forEach(([key, value]) => {
      if (value) params.set(key, value)
    })
    params.set('limit', String(pageLimit))
    params.set('offset', String(Math.max(0, Number(nextOffset) || 0)))
    return fetch(`/api/tenders?${params.toString()}`)
      .then((response) => response.ok ? response.json() : Promise.reject(new Error('API не отвечает')))
      .then((payload) => {
        setTenders(payload.items || [])
        setTenderPage({
          total: payload.total || 0,
          limit: payload.limit || pageLimit,
          offset: payload.offset || 0,
          has_previous: Boolean(payload.has_previous),
          previous_offset: payload.previous_offset,
          has_next: Boolean(payload.has_next),
          next_offset: payload.next_offset,
        })
        setSelected((current) => {
          const items = payload.items || []
          const stillVisible = current && items.some((item) => (
            item.source === current.source && item.external_id === current.external_id
          ))
          return stillVisible ? current : items[0] || null
        })
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }

  function loadSourceStatus() {
    setSourceStatusError('')
    return fetch('/api/sources/status')
      .then((response) => response.ok ? response.json() : Promise.reject(new Error('API не отвечает')))
      .then((payload) => setSourceStatus(payload.sources || []))
      .catch((err) => setSourceStatusError(err.message))
  }

  const stats = useMemo(() => {
    const active = tenders.filter((item) => /актив|прием|приём|подач/i.test(item.status || '')).length
    const totalPrice = tenders.reduce((sum, item) => sum + (Number(item.price) || 0), 0)
    return { active, totalPrice }
  }, [tenders])

  const workflowCounts = useMemo(() => {
    return tenders.reduce((counts, item) => {
      const status = item.workflow_status || 'new'
      counts[status] = (counts[status] || 0) + 1
      return counts
    }, {})
  }, [tenders])

  const activeFilterChips = useMemo(() => filterSummary(appliedFilters), [appliedFilters])
  const pageTitle = viewLabels[view] || viewLabels.dashboard

  function updateFilter(name, value) {
    setFilters((current) => ({ ...current, [name]: value }))
  }

  function toggleMultiFilter(name, value) {
    setFilters((current) => {
      const values = splitFilterValues(current[name])
      const nextValues = values.includes(value)
        ? values.filter((item) => item !== value)
        : [...values, value]
      return { ...current, [name]: nextValues.join(',') }
    })
  }

  function isSelected(name, value) {
    return splitFilterValues(filters[name]).includes(value)
  }

  function applyFilters(event) {
    event.preventDefault()
    setPageOffset(0)
    setAppliedFilters(filters)
    setSelected(null)
  }

  function clearFilters() {
    setFilters(initialFilters)
    setPageOffset(0)
    setAppliedFilters(initialFilters)
    setSelected(null)
    setSearchSummary('')
  }

  function setWorkflowFilter(workflowStatus) {
    const nextFilters = { ...filters, workflow_status: workflowStatus }
    setFilters(nextFilters)
    setPageOffset(0)
    setAppliedFilters(nextFilters)
    setSelected(null)
  }

  function goToOffset(nextOffset) {
    if (nextOffset === null || nextOffset === undefined) return
    setSelected(null)
    setPageOffset(Math.max(0, Number(nextOffset) || 0))
  }

  function changePageLimit(nextLimit) {
    const parsedLimit = Number(nextLimit)
    const normalizedLimit = tenderPageLimitOptions.includes(parsedLimit) ? parsedLimit : defaultTenderPageLimit
    setSelected(null)
    setPageOffset(0)
    setPageLimit(normalizedLimit)
  }

  function updateTenderWorkflow(updatedTender) {
    setDetails(updatedTender)
    setTenders((current) => current.map((item) => (
      item.source === updatedTender.source && item.external_id === updatedTender.external_id
        ? {
            ...item,
            workflow_status: updatedTender.workflow_status,
            workflow_note: updatedTender.workflow_note,
          }
        : item
    )))
  }

  function updateTenderDetails(updatedTender) {
    setDetails(updatedTender)
    setTenders((current) => current.map((item) => (
      item.source === updatedTender.source && item.external_id === updatedTender.external_id
        ? {
            ...item,
            title: updatedTender.title,
            customer: updatedTender.customer,
            price: updatedTender.price,
            status: updatedTender.status,
            deadline_at: updatedTender.deadline_at,
            documents_count: updatedTender.document_records?.length || updatedTender.documents?.length || 0,
            items_count: updatedTender.items?.length || 0,
            workflow_status: updatedTender.workflow_status,
            workflow_note: updatedTender.workflow_note,
          }
        : item
    )))
  }

  function runSearch() {
    const nextFilters = { ...filters }
    setSearching(true)
    setError('')
    setSearchSummary('')
    setSelected(null)
    setPageOffset(0)
    setAppliedFilters(nextFilters)
    fetch('/api/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filters: nextFilters }),
    })
      .then((response) => response.ok ? response.json() : Promise.reject(new Error('Не удалось запустить поиск')))
      .then((payload) => {
        const stats = payload.stats || {}
        setSearchSummary(
          `Fetched=${stats.fetched || 0} Saved=${stats.saved || 0} Matched=${stats.matched || 0} Notified=${stats.notified || 0} Telegram=${payload.notifications_enabled ? 'on' : 'off'}`
        )
        loadSourceStatus()
        return loadTenders(nextFilters, 0)
      })
      .catch((err) => setError(err.message))
      .finally(() => setSearching(false))
  }

  return (
    <main className="app-shell">
      <div className={sidebarCollapsed ? 'app-frame sidebar-collapsed' : 'app-frame'}>
        <aside className={sidebarCollapsed ? 'app-sidebar collapsed' : 'app-sidebar'}>
          <div className="sidebar-brand">
            <div>
              <strong>Tender Killer</strong>
              <span>Москва / МО</span>
            </div>
            <button
              aria-label={sidebarCollapsed ? 'Развернуть меню' : 'Свернуть меню'}
              className="icon-button small sidebar-toggle-button"
              onClick={() => setSidebarCollapsed((current) => !current)}
              title={sidebarCollapsed ? 'Развернуть меню' : 'Свернуть меню'}
              type="button"
            >
              {sidebarCollapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
            </button>
          </div>
          <nav aria-label="Основная навигация" className="side-nav">
            {navItems.map((item) => {
              const Icon = item.icon
              return (
                <button
                  className={view === item.id ? 'active' : ''}
                  key={item.id}
                  onClick={() => setView(item.id)}
                  title={item.label}
                  type="button"
                >
                  <Icon size={18} />
                  <span className="sidebar-text">{item.label}</span>
                  <small className="sidebar-caption">{item.caption}</small>
                </button>
              )
            })}
          </nav>
        </aside>

        <section className="app-main">
          <header className="topbar">
            <div>
              <div className="eyebrow">Tender Killer</div>
              <h1>{pageTitle}</h1>
            </div>
            <div className="top-actions">
              <button className="primary-action" disabled={searching} onClick={runSearch} type="button">
                <PlayCircle size={18} />
                {searching ? 'Поиск...' : 'Запустить поиск'}
              </button>
              <button className="icon-button" onClick={loadTenders} title="Обновить список">
                <RefreshCcw size={18} />
              </button>
              <span className="status-pill"><Bell size={16} /> Telegram: уведомления</span>
            </div>
          </header>

          {view === 'dashboard' && (
            <DashboardView
              error={error}
              onOpenTenders={() => setView('tenders')}
              onRefreshSources={loadSourceStatus}
              searchSummary={searchSummary}
              sourceStatusError={sourceStatusError}
              sources={sourceStatus}
              stats={stats}
              tenderPage={tenderPage}
              tenders={tenders}
              workflowCounts={workflowCounts}
            />
          )}

          {view === 'database' && (
        <DatabaseView />
      )}

          {view === 'tenders' && (
      <section className={filtersCollapsed ? 'workspace workbench-layout filters-collapsed' : 'workspace workbench-layout'}>
        <aside className={filtersCollapsed ? 'filters-panel collapsed' : 'filters-panel'}>
          <div className="filters-header">
            <div className="panel-title"><Filter size={18} /> <span className="filters-title-text">Фильтры</span></div>
            <button
              aria-expanded={!filtersCollapsed}
              className="icon-button small filter-collapse-button"
              onClick={() => setFiltersCollapsed((current) => !current)}
              title={filtersCollapsed ? 'Развернуть фильтры' : 'Свернуть фильтры'}
              type="button"
            >
              {filtersCollapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
            </button>
          </div>
          {!filtersCollapsed && (
            <>
              <form onSubmit={applyFilters}>
            <label>
              Поиск
              <div className="input-with-icon">
                <Search size={16} />
                <input value={filters.q} onChange={(event) => updateFilter('q', event.target.value)} placeholder="бумага, кабель, бетон" />
              </div>
            </label>
            <div className="filter-group">
              Площадка
              <div className="check-grid">
                {sourceOptions.map((option) => (
                  <button
                    className={isSelected('source', option.value) || !filters.source ? 'selected' : ''}
                    key={option.value}
                    onClick={() => toggleMultiFilter('source', option.value)}
                    type="button"
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            </div>
            <div className="filter-group">
              Закон
              <div className="segmented-control">
                {lawOptions.map((option) => (
                  <button
                    className={filters.law === option.value ? 'selected' : ''}
                    key={option.label}
                    onClick={() => updateFilter('law', option.value)}
                    type="button"
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            </div>
            <div className="filter-group">
              Регион
              <div className="segmented-control wrap">
                {quickRegionOptions.map((option) => (
                  <button
                    className={filters.region === option.value ? 'selected' : ''}
                    key={option.value}
                    onClick={() => updateFilter('region', option.value)}
                    type="button"
                  >
                    {option.label}
                  </button>
                ))}
              </div>
              <input value={filters.region} onChange={(event) => updateFilter('region', event.target.value)} placeholder="Москва, Московская область" />
            </div>
            <div className="filter-group">
              Статус
              <div className="segmented-control wrap">
                {statusOptions.map((option) => (
                  <button
                    className={filters.status === option.value ? 'selected' : ''}
                    key={option.label}
                    onClick={() => updateFilter('status', option.value)}
                    type="button"
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            </div>
            <label>
              ОКПД2
              <input value={filters.okpd2} onChange={(event) => updateFilter('okpd2', event.target.value)} placeholder="17.12, 22.23, 27" />
            </label>
            <div className="filter-group">
              Тип источника
              <div className="segmented-control">
                {sourceFamilyOptions.map((option) => (
                  <button
                    className={filters.source_family === option.value ? 'selected' : ''}
                    key={option.label}
                    onClick={() => updateFilter('source_family', option.value)}
                    type="button"
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            </div>
            <div className="filter-group">
              Тип процедуры
              <div className="segmented-control wrap procedure-control">
                {procedureTypeOptions.map((option) => (
                  <button
                    className={filters.procedure_type === option.value ? 'selected' : ''}
                    key={option.label}
                    onClick={() => updateFilter('procedure_type', option.value)}
                    type="button"
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            </div>
            <label>
              ИНН заказчика
              <input value={filters.customer_inn} onChange={(event) => updateFilter('customer_inn', event.target.value)} inputMode="numeric" placeholder="7708044657" />
            </label>
            <div className="split">
              <label>
                Мин. цена
                <input value={filters.min_price} onChange={(event) => updateFilter('min_price', event.target.value)} inputMode="numeric" placeholder="0" />
              </label>
              <label>
                Макс. цена
                <input value={filters.max_price} onChange={(event) => updateFilter('max_price', event.target.value)} inputMode="numeric" placeholder="500000" />
              </label>
            </div>
            <button className="primary-button" type="submit">Применить</button>
            <button className="secondary-button compact" onClick={clearFilters} type="button">Очистить</button>
              </form>
              <div className="applied-filters">
                <span>Применено сейчас</span>
                <div>
                  {activeFilterChips.map((chip) => <strong key={chip}>{chip}</strong>)}
                </div>
              </div>
            </>
          )}
        </aside>

        <section className="tender-list">
          <div className="list-header">
            <h2>Закупки</h2>
            {loading && <span>обновление...</span>}
          </div>
          <div className="workflow-tabs">
            <button className={!filters.workflow_status ? 'active' : ''} onClick={() => setWorkflowFilter('')} type="button">Все</button>
            {Object.entries(workflowLabels).map(([status, label]) => (
              <button
                className={filters.workflow_status === status ? 'active' : ''}
                key={status}
                onClick={() => setWorkflowFilter(status)}
                type="button"
              >
                {label}
              </button>
            ))}
          </div>
          <PaginationBar
            loading={loading}
            onNext={() => goToOffset(tenderPage.next_offset)}
            onPageLimitChange={changePageLimit}
            onPrevious={() => goToOffset(tenderPage.previous_offset)}
            page={tenderPage}
            pageLimit={pageLimit}
            pageLimitOptions={tenderPageLimitOptions}
            shown={tenders.length}
          />
          {error && <div className="error-box">{error}</div>}
          <div className="rows">
            {tenders.map((tender) => (
              <button
                className={`tender-row ${selected?.source === tender.source && selected?.external_id === tender.external_id ? 'selected' : ''}`}
                key={`${tender.source}-${tender.external_id}`}
                onClick={() => setSelected(tender)}
              >
                <div className="row-main">
                  <span className="row-tags">
                    <span className="source-chip">{sourceLabels[tender.source] || tender.source}</span>
                    <span className={`workflow-chip ${tender.workflow_status || 'new'}`}>
                      {workflowLabels[tender.workflow_status] || 'Новая'}
                    </span>
                  </span>
                  <strong>{tender.title}</strong>
                  <span>{tender.customer || 'Заказчик не указан'}</span>
                </div>
                <div className="row-meta">
                  <span><CircleDollarSign size={15} /> {formatMoney(tender.price)}</span>
                  <span><Scale size={15} /> {tender.law || 'закон не указан'}</span>
                  <span><CalendarClock size={15} /> {formatDate(tender.deadline_at)}</span>
                  <span><FileText size={15} /> {tender.documents_count}</span>
                  <span>Позиций: {tender.items_count || 0}</span>
                </div>
              </button>
            ))}
          </div>
        </section>

        <aside className="details-panel">
          {details ? (
            <TenderDetails tender={details} onTenderRefresh={updateTenderDetails} onWorkflowUpdate={updateTenderWorkflow} />
          ) : (
            <div className="empty-state">Выбери закупку из списка</div>
          )}
        </aside>
      </section>
      )}
        </section>
      </div>
    </main>
  )
}

function Metric({ label, value, tone }) {
  return (
    <div className={`metric ${tone || ''}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}

function DashboardView({ tenderPage, stats, workflowCounts, sources, sourceStatusError, searchSummary, error, onRefreshSources, onOpenTenders, tenders }) {
  const queue = [
    { label: 'Новые', value: workflowCounts.new || 0 },
    { label: 'Интересные', value: workflowCounts.interesting || 0 },
    { label: 'В работе', value: workflowCounts.in_progress || 0 },
    { label: 'Архив', value: workflowCounts.archive || 0 },
  ]

  return (
    <section className="dashboard-view">
      <section className="metrics">
        <Metric label="Найдено" value={tenderPage.total} />
        <Metric label="Активные" value={stats.active} />
        <Metric label="Сумма в выдаче" value={formatMoney(stats.totalPrice)} />
        <Metric label="API" value={error ? 'ошибка' : 'ok'} tone={error ? 'danger' : 'good'} />
      </section>
      {searchSummary && <div className="run-summary">{searchSummary}</div>}
      <section className="dashboard-grid">
        <SourceStatusPanel
          error={sourceStatusError}
          onRefresh={onRefreshSources}
          sources={sources}
        />
        <section className="dashboard-panel">
          <div className="panel-title"><FileText size={18} /> Очередь</div>
          <div className="dashboard-kpis">
            {queue.map((item) => (
              <div key={item.label}>
                <span>{item.label}</span>
                <strong>{item.value}</strong>
              </div>
            ))}
          </div>
          <button className="primary-button dashboard-open-button" onClick={onOpenTenders} type="button">
            Открыть закупки
          </button>
        </section>
      </section>
      <section className="dashboard-secondary-grid">
        <DashboardAttentionPanel
          error={error}
          onOpenTenders={onOpenTenders}
          sources={sources}
          workflowCounts={workflowCounts}
        />
        <DashboardTenderPreview onOpenTenders={onOpenTenders} tenders={tenders} />
      </section>
    </section>
  )
}

function DashboardAttentionPanel({ error, sources, workflowCounts, onOpenTenders }) {
  const sourceErrors = (sources || []).filter((source) => source.last_error)
  const attentionItems = []

  if (error) attentionItems.push({ label: 'API сайта', value: error })
  if (sourceErrors.length) attentionItems.push({ label: 'Источники', value: `${sourceErrors.length} требуют проверки` })
  if (workflowCounts.new) attentionItems.push({ label: 'Новые закупки', value: `${workflowCounts.new} еще не разобраны` })
  if (workflowCounts.interesting) attentionItems.push({ label: 'Интересные', value: `${workflowCounts.interesting} ждут решения` })

  return (
    <section className="dashboard-panel">
      <div className="panel-title"><Bell size={18} /> Требует внимания</div>
      <div className="dashboard-attention-list">
        {attentionItems.map((item) => (
          <button key={item.label} onClick={onOpenTenders} type="button">
            <span>{item.label}</span>
            <strong>{item.value}</strong>
          </button>
        ))}
        {!attentionItems.length && <div className="dashboard-empty-note">Критичных событий нет</div>}
      </div>
    </section>
  )
}

function DashboardTenderPreview({ tenders, onOpenTenders }) {
  const previewTenders = (tenders || []).slice(0, 5)

  return (
    <section className="dashboard-panel">
      <div className="panel-title"><FileText size={18} /> Последние закупки</div>
      <div className="dashboard-tender-list">
        {previewTenders.map((tender) => (
          <button key={`${tender.source}-${tender.external_id}`} onClick={onOpenTenders} type="button">
            <strong>{tender.title}</strong>
            <span>{sourceLabels[tender.source] || tender.source} · {formatMoney(tender.price)} · {formatDate(tender.deadline_at)}</span>
          </button>
        ))}
        {!previewTenders.length && <div className="dashboard-empty-note">Запусти поиск, чтобы увидеть свежие закупки</div>}
      </div>
    </section>
  )
}

function SourceStatusPanel({ sources, error, onRefresh }) {
  return (
    <section className="source-status-panel">
      <div className="source-status-header">
        <div className="panel-title"><RefreshCcw size={18} /> Источники</div>
        <button className="icon-button small" onClick={onRefresh} title="Обновить статус источников" type="button">
          <RefreshCcw size={16} />
        </button>
      </div>
      {error && <div className="source-status-error">{error}</div>}
      <div className="source-status-list">
        {(sources || []).map((source) => (
          <SourceStatusRow key={source.source} source={source} />
        ))}
        {!sources?.length && !error && <span className="source-status-empty">Статус источников пока не загружен</span>}
      </div>
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

function PaginationBar({ page, shown, loading, onPrevious, onNext, pageLimit, pageLimitOptions, onPageLimitChange }) {
  const total = Number(page.total) || 0
  const offset = Number(page.offset) || 0
  const limit = Math.max(1, Number(page.limit) || pageLimit || defaultTenderPageLimit)
  const from = total === 0 ? 0 : offset + 1
  const to = Math.min(total, offset + shown)
  const pageNumber = total === 0 ? 0 : Math.floor(offset / limit) + 1
  const pageCount = total === 0 ? 0 : Math.ceil(total / limit)

  return (
    <div className="pagination-bar">
      <div>
        <strong>{from}-{to}</strong>
        <span>из {total}</span>
        <em>{pageNumber}/{pageCount}</em>
      </div>
      <div className="pagination-actions">
        <label className="page-size-control">
          <span>На странице</span>
          <select
            aria-label="Закупок на странице"
            disabled={loading}
            onChange={(event) => onPageLimitChange(event.target.value)}
            value={pageLimit}
          >
            {pageLimitOptions.map((option) => (
              <option key={option} value={option}>{option}</option>
            ))}
          </select>
        </label>
        <button disabled={loading || !page.has_previous} onClick={onPrevious} title="Предыдущая страница" type="button">
          <ChevronLeft size={18} />
        </button>
        <button disabled={loading || !page.has_next} onClick={onNext} title="Следующая страница" type="button">
          <ChevronRight size={18} />
        </button>
      </div>
    </div>
  )
}

function DatabaseView() {
  const [tables, setTables] = useState([])
  const [selectedTable, setSelectedTable] = useState('tenders')
  const [tableData, setTableData] = useState({ columns: [], rows: [], total: 0 })
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    fetch('/api/db/tables')
      .then((response) => response.ok ? response.json() : Promise.reject(new Error('Не удалось открыть SQLite')))
      .then((payload) => {
        const nextTables = payload.tables || []
        setTables(nextTables)
        setSelectedTable((current) => current || nextTables[0]?.name || 'tenders')
      })
      .catch((err) => setError(err.message))
  }, [])

  useEffect(() => {
    if (!selectedTable) return
    const params = new URLSearchParams({ limit: '100' })
    if (query.trim()) params.set('q', query.trim())
    setLoading(true)
    setError('')
    fetch(`/api/db/tables/${encodeURIComponent(selectedTable)}?${params.toString()}`)
      .then((response) => response.ok ? response.json() : Promise.reject(new Error('Не удалось прочитать таблицу')))
      .then(setTableData)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [selectedTable, query])

  return (
    <section className="database-view">
      <aside className="database-sidebar">
        <div className="panel-title"><Database size={18} /> SQLite</div>
        <div className="table-tabs">
          {tables.map((table) => (
            <button
              className={selectedTable === table.name ? 'active' : ''}
              key={table.name}
              onClick={() => setSelectedTable(table.name)}
              type="button"
            >
              <span>{table.name}</span>
              <strong>{table.rows}</strong>
            </button>
          ))}
        </div>
      </aside>

      <section className="database-table-panel">
        <div className="database-toolbar">
          <div>
            <h2>{selectedTable}</h2>
            <span>{tableData.total || 0} строк, показаны первые {tableData.rows?.length || 0}</span>
          </div>
          <div className="input-with-icon db-search">
            <Search size={16} />
            <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Поиск по таблице" />
          </div>
        </div>
        {error && <div className="error-box">{error}</div>}
        <div className="db-table-wrap">
          <table className="db-table">
            <thead>
              <tr>
                {tableData.columns.map((column) => <th key={column}>{column}</th>)}
              </tr>
            </thead>
            <tbody>
              {(tableData.rows || []).map((row, index) => (
                <tr key={`${selectedTable}-${index}`}>
                  {tableData.columns.map((column) => (
                    <td key={column}>{formatDbCell(row[column])}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
          {!loading && !tableData.rows?.length && <div className="empty-state compact">Строки не найдены</div>}
          {loading && <div className="empty-state compact">Загрузка таблицы...</div>}
        </div>
      </section>
    </section>
  )
}

function TenderDetails({ tender, onTenderRefresh, onWorkflowUpdate }) {
  const raw = safeJson(tender.raw_payload_json)
  const autoRefreshKey = useRef('')
  const [activeTab, setActiveTab] = useState('overview')
  const [note, setNote] = useState(tender.workflow_note || '')
  const [saving, setSaving] = useState(false)
  const [sending, setSending] = useState(false)
  const [downloading, setDownloading] = useState(false)
  const [extracting, setExtracting] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [refreshingDetails, setRefreshingDetails] = useState(false)
  const [notifyStatus, setNotifyStatus] = useState('')
  const [downloadStatus, setDownloadStatus] = useState('')
  const [extractStatus, setExtractStatus] = useState('')
  const [detailStatus, setDetailStatus] = useState('')
  const [documentRecords, setDocumentRecords] = useState(documentRecordsForTender(tender))
  const [analysis, setAnalysis] = useState(tender.analysis || null)
  const [productProfiles, setProductProfiles] = useState(tender.product_profiles || [])
  const [productProfileSummary, setProductProfileSummary] = useState(tender.product_profile_summary || null)
  const [economics, setEconomics] = useState(tender.economics || null)
  const [selectedProfileIndex, setSelectedProfileIndex] = useState(0)
  const [profilesLoading, setProfilesLoading] = useState(false)
  const [savingEconomicsPosition, setSavingEconomicsPosition] = useState(null)
  const [savingSupplierOptionPosition, setSavingSupplierOptionPosition] = useState(null)

  useEffect(() => {
    setActiveTab('overview')
    setNote(tender.workflow_note || '')
    setNotifyStatus('')
    setDownloadStatus('')
    setExtractStatus('')
    setDetailStatus('')
    setDocumentRecords(documentRecordsForTender(tender))
    setAnalysis(tender.analysis || null)
    setProductProfiles(tender.product_profiles || [])
    setProductProfileSummary(tender.product_profile_summary || null)
    setEconomics(tender.economics || null)
    setSelectedProfileIndex(0)
    setSavingEconomicsPosition(null)
    setSavingSupplierOptionPosition(null)
  }, [tender.source, tender.external_id, tender.workflow_note, tender.analysis, tender.product_profiles, tender.product_profile_summary, tender.economics])

  useEffect(() => {
    const key = `${tender.source}/${tender.external_id}`
    if (!shouldAutoRefreshDetails(tender) || autoRefreshKey.current === key) return
    autoRefreshKey.current = key
    refreshDetails({ automatic: true })
  }, [tender.source, tender.external_id, tender.items?.length])

  function saveWorkflow(workflowStatus = tender.workflow_status || 'new', workflowNote = note) {
    setSaving(true)
    fetch(`/api/tenders/${encodeURIComponent(tender.source)}/${encodeURIComponent(tender.external_id)}/workflow`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        workflow_status: workflowStatus,
        workflow_note: workflowNote,
      }),
    })
      .then((response) => response.ok ? response.json() : Promise.reject(new Error('Не удалось сохранить статус')))
      .then(onWorkflowUpdate)
      .finally(() => setSaving(false))
  }

  function sendToTelegram() {
    setSending(true)
    setNotifyStatus('')
    fetch(`/api/tenders/${encodeURIComponent(tender.source)}/${encodeURIComponent(tender.external_id)}/notify`, {
      method: 'POST',
    })
      .then((response) => response.ok ? response.json() : Promise.reject(new Error('Не удалось отправить в Telegram')))
      .then((payload) => setNotifyStatus(payload.message || (payload.sent ? 'Отправлено в Telegram' : 'Telegram не настроен')))
      .catch((err) => setNotifyStatus(err.message))
      .finally(() => setSending(false))
  }

  function downloadDocuments() {
    setDownloading(true)
    setDownloadStatus('')
    fetch(`/api/tenders/${encodeURIComponent(tender.source)}/${encodeURIComponent(tender.external_id)}/documents/download`, {
      method: 'POST',
    })
      .then((response) => response.ok ? response.json() : Promise.reject(new Error('Не удалось скачать документы')))
      .then((payload) => {
        setDocumentRecords(payload.document_records || [])
        const firstError = payload.failed?.[0]?.error
        setDownloadStatus(
          `Скачано: ${payload.downloaded || 0}${payload.failed?.length ? `, ошибок: ${payload.failed.length}${firstError ? `: ${firstError}` : ''}` : ''}`
        )
      })
      .catch((err) => setDownloadStatus(err.message))
      .finally(() => setDownloading(false))
  }

  function extractDocumentText() {
    setExtracting(true)
    setExtractStatus('')
    fetch(`/api/tenders/${encodeURIComponent(tender.source)}/${encodeURIComponent(tender.external_id)}/documents/extract-text`, {
      method: 'POST',
    })
      .then((response) => response.ok ? response.json() : Promise.reject(new Error('Не удалось извлечь текст документов')))
      .then((payload) => {
        setDocumentRecords(payload.document_records || [])
        const firstError = payload.failed?.[0]?.error
        setExtractStatus(
          `Извлечено: ${payload.extracted || 0}${payload.failed?.length ? `, ошибок: ${payload.failed.length}${firstError ? `: ${firstError}` : ''}` : ''}`
        )
      })
      .catch((err) => setExtractStatus(err.message))
      .finally(() => setExtracting(false))
  }

  function analyzeTender() {
    setAnalyzing(true)
    fetch(`/api/tenders/${encodeURIComponent(tender.source)}/${encodeURIComponent(tender.external_id)}/analysis/run`, {
      method: 'POST',
    })
      .then((response) => response.ok ? response.json() : Promise.reject(new Error('Не удалось проанализировать ТЗ')))
      .then((payload) => setAnalysis(payload.analysis || null))
      .catch((err) => {
        setAnalysis({
          summary: err.message,
          requirements: [],
          risks: [],
          red_flags: ['ошибка анализа'],
          checklist: [],
          status: 'needs_review',
          confidence: 0,
        })
      })
      .finally(() => setAnalyzing(false))
  }

  function refreshDetails(options = {}) {
    setRefreshingDetails(true)
    setDetailStatus(options.automatic ? 'Автоматически добираю позиции и классификаторы...' : '')
    fetch(`/api/tenders/${encodeURIComponent(tender.source)}/${encodeURIComponent(tender.external_id)}/details/refresh`, {
      method: 'POST',
    })
      .then((response) => response.ok ? response.json() : Promise.reject(new Error('Не удалось обновить детали')))
      .then((payload) => {
        const nextTender = payload.tender || tender
        onTenderRefresh(nextTender)
        setDocumentRecords(nextTender.document_records || [])
        setAnalysis(nextTender.analysis || null)
        setProductProfiles(nextTender.product_profiles || [])
        setProductProfileSummary(nextTender.product_profile_summary || null)
        setEconomics(nextTender.economics || null)
        setSelectedProfileIndex(0)
        const summary = payload.summary || {}
        setDetailStatus(
          payload.refreshed
            ? `${options.automatic ? 'Автообновление: ' : 'Обновлено: '}позиций ${summary.items_count || 0}, документов ${summary.documents_count || 0}, профилей ${summary.product_profiles_count || 0}`
            : payload.message || 'Источник не отдал новые детали'
        )
      })
      .catch((err) => setDetailStatus(err.message))
      .finally(() => setRefreshingDetails(false))
  }

  function rebuildProductProfiles() {
    setProfilesLoading(true)
    fetch(`/api/tenders/${encodeURIComponent(tender.source)}/${encodeURIComponent(tender.external_id)}/product-profiles/rebuild`, {
      method: 'POST',
    })
      .then((response) => response.ok ? response.json() : Promise.reject(new Error('Не удалось обновить товарные профили')))
      .then((payload) => {
        setProductProfiles(payload.product_profiles || [])
        setProductProfileSummary(payload.summary || null)
        setSelectedProfileIndex(0)
      })
      .catch((err) => {
        setProductProfileSummary((current) => current || { total: productProfiles.length })
        window.alert(err.message)
      })
      .finally(() => setProfilesLoading(false))
  }

  function saveProfileEconomics(profile, economicsInputs) {
    if (!profile?.position_index) return
    setSavingEconomicsPosition(profile.position_index)
    setDetailStatus('')
    fetch(`/api/tenders/${encodeURIComponent(tender.source)}/${encodeURIComponent(tender.external_id)}/product-profiles/${profile.position_index}/economics`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(economicsInputs),
    })
      .then((response) => response.ok ? response.json() : Promise.reject(new Error('Не удалось сохранить экономику')))
      .then((nextTender) => {
        onTenderRefresh(nextTender)
        setProductProfiles(nextTender.product_profiles || [])
        setProductProfileSummary(nextTender.product_profile_summary || null)
        setEconomics(nextTender.economics || null)
        setDetailStatus('Экономика обновлена')
      })
      .catch((err) => setDetailStatus(err.message))
      .finally(() => setSavingEconomicsPosition(null))
  }

  function saveSupplierOption(profile, supplierOption) {
    if (!profile?.position_index) return null
    setSavingSupplierOptionPosition(profile.position_index)
    setDetailStatus('')
    return fetch(`/api/tenders/${encodeURIComponent(tender.source)}/${encodeURIComponent(tender.external_id)}/product-profiles/${profile.position_index}/supplier-options`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(supplierOption),
    })
      .then((response) => response.ok ? response.json() : Promise.reject(new Error('Не удалось сохранить поставщика')))
      .then((nextTender) => {
        onTenderRefresh(nextTender)
        setProductProfiles(nextTender.product_profiles || [])
        setProductProfileSummary(nextTender.product_profile_summary || null)
        setEconomics(nextTender.economics || null)
        setDetailStatus('Поставщик добавлен')
        return nextTender
      })
      .catch((err) => {
        setDetailStatus(err.message)
        throw err
      })
      .finally(() => setSavingSupplierOptionPosition(null))
  }

  const statusMessages = [detailStatus, notifyStatus, downloadStatus, extractStatus].filter(Boolean)
  const tabs = [
    { id: 'overview', label: 'Обзор' },
    { id: 'products', label: `Товары ${productProfiles.length || tender.items?.length || 0}` },
    { id: 'documents', label: `Документы ${documentRecords.length}` },
    { id: 'analysis', label: 'Анализ' },
    { id: 'economics', label: 'Экономика' },
    { id: 'workflow', label: 'Статус' },
  ]

  return (
    <div className="details">
      <div className="details-header">
        <div className="details-title-row">
          <div className="panel-title"><Building2 size={18} /> Карточка</div>
          <span className={`workflow-chip ${tender.workflow_status || 'new'}`}>
            {workflowLabels[tender.workflow_status] || 'Новая'}
          </span>
        </div>
        <h2>{tender.title}</h2>
        <div className="detail-pills">
          <span>{sourceLabels[tender.source] || tender.source}</span>
          <span>{formatMoney(tender.price)}</span>
          <span>{formatDate(tender.deadline_at)}</span>
        </div>
      </div>

      <TenderDecisionSummary tender={tender} economics={economics} />

      <div className="detail-actions" aria-label="Действия с закупкой">
        <div className="details-action-group primary-actions">
          <a className="detail-action primary" href={tender.url} target="_blank" rel="noreferrer">
            <ExternalLink size={15} /> Источник
          </a>
          <button disabled={refreshingDetails} onClick={() => refreshDetails()} type="button">
            <RefreshCcw size={15} /> {refreshingDetails ? 'Обновляю' : 'Обновить'}
          </button>
        </div>
        <div className="details-action-group secondary-actions">
          <button disabled={downloading} onClick={downloadDocuments} type="button">
            <FileText size={15} /> {downloading ? 'Качаю' : 'Документы'}
          </button>
          <button disabled={extracting} onClick={extractDocumentText} type="button">
            {extracting ? 'Читаю' : 'Текст'}
          </button>
          <button disabled={analyzing} onClick={analyzeTender} type="button">
            {analyzing ? 'Анализ' : 'Анализ'}
          </button>
          <a
            className="detail-action"
            href={`/api/tenders/${encodeURIComponent(tender.source)}/${encodeURIComponent(tender.external_id)}/report.docx`}
          >
            Word
          </a>
          <button disabled={sending} onClick={sendToTelegram} type="button">
            <Bell size={15} /> {sending ? 'Отправка' : 'TG'}
          </button>
        </div>
      </div>

      {statusMessages.length > 0 && (
        <div className="status-stack">
          {statusMessages.map((message) => <p className="inline-status" key={message}>{message}</p>)}
        </div>
      )}

      <nav className="detail-tabs" aria-label="Разделы карточки">
        {tabs.map((tab) => (
          <button
            className={activeTab === tab.id ? 'active' : ''}
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            type="button"
          >
            {tab.label}
          </button>
        ))}
      </nav>

      <div className="detail-tab-panel">
        {activeTab === 'overview' && (
          <TenderOverviewTab tender={tender} raw={raw} />
        )}

        {activeTab === 'products' && (
          <section className="detail-section active product-profile-section">
            <div className="section-heading-row">
              <h3>Товары</h3>
              <button className="secondary-button compact" disabled={profilesLoading} onClick={rebuildProductProfiles} type="button">
                {profilesLoading ? 'Обновление...' : 'Обновить профили'}
              </button>
            </div>
            <ProductTabSummary
              summary={productProfileSummary}
              total={productProfiles.length}
              itemsCount={(tender.items || []).length}
            />
            {productProfiles.length ? (
              <div className="profile-layout">
                <div className="profile-list" role="listbox" aria-label="Товарные профили">
                  {productProfiles.map((profile, index) => (
                    <button
                      className={index === selectedProfileIndex ? 'profile-row selected' : 'profile-row'}
                      key={`${profile.position_index}-${profile.product_name}-${index}`}
                      onClick={() => setSelectedProfileIndex(index)}
                      type="button"
                    >
                      <span className="profile-position">#{profile.position_index || index + 1}</span>
                      <span className="profile-name">{profile.product_name || 'Без названия'}</span>
                      <span className="profile-meta quantity">{formatQuantity(profile.quantity, profile.unit)}</span>
                      <span className="profile-meta classifier">{profile.classifier_type || 'код'} {profile.classifier_code || profile.okpd2 || 'не найден'}</span>
                      <span className={`profile-status ${profile.profile_status || 'draft'}`}>{profileStatusLabel(profile.profile_status)}</span>
                    </button>
                  ))}
                </div>
                <ProductProfileDetail
                  profile={productProfiles[selectedProfileIndex]}
                  onEconomicsSave={saveProfileEconomics}
                  onSupplierOptionSave={saveSupplierOption}
                  savingEconomics={savingEconomicsPosition === productProfiles[selectedProfileIndex]?.position_index}
                  savingSupplierOption={savingSupplierOptionPosition === productProfiles[selectedProfileIndex]?.position_index}
                />
              </div>
            ) : (
              <p className="muted-text">Товарные профили пока не сформированы.</p>
            )}
            <TenderItems items={tender.items || []} />
          </section>
        )}

        {activeTab === 'documents' && (
          <section className="detail-section active">
            <div className="section-heading-row">
              <h3>Документы</h3>
            </div>
            <DocumentStatusSummary
              documents={documentRecords}
              downloading={downloading}
              extracting={extracting}
              onDownload={downloadDocuments}
              onExtract={extractDocumentText}
            />
            {documentRecords.length ? (
              <div className="document-table">
                {documentRecords.map((document) => (
                  <div className="document-row" key={document.url}>
                    <div>
                      <a href={document.url} target="_blank" rel="noreferrer">
                        {document.name || documentLabel(document.url)}
                      </a>
                      <span>{document.document_type || 'тип не указан'}</span>
                      {document.text_content && (
                        <details className="document-preview-toggle">
                          <summary>Показать извлеченный текст</summary>
                          <p className="document-preview">{documentTextPreview(document.text_content)}</p>
                        </details>
                      )}
                      {document.text_error && <p className="document-error">{document.text_error}</p>}
                    </div>
                    <div className="document-row-status">
                      <strong className={`download-status ${document.local_path ? 'downloaded' : 'missing'}`}>
                        {document.local_path ? 'скачан' : 'не скачан'}
                      </strong>
                      <em className={`document-status ${document.text_status || 'pending'}`}>
                        {documentStatusLabel(document.text_status)}
                      </em>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p>Документы пока не найдены в карточке.</p>
            )}
          </section>
        )}

        {activeTab === 'analysis' && (
          <AnalysisTabPanel analysis={analysis} analyzing={analyzing} onAnalyze={analyzeTender} />
        )}

        {activeTab === 'economics' && (
          <EconomicsTabPanel tender={tender} economics={economics} />
        )}

        {activeTab === 'workflow' && (
          <WorkflowTabPanel
            tender={tender}
            raw={raw}
            note={note}
            saving={saving}
            onNoteChange={setNote}
            onSaveWorkflow={saveWorkflow}
          />
        )}
      </div>
    </div>
  )
}

function TenderOverviewTab({ tender, raw }) {
  const law = tender.law || raw.federalLawName || raw.SourcePlatformName || 'не найден'
  const category = tender.category || raw.CategoryName || 'не найдена'

  return (
    <section className="detail-section active overview-tab">
      <div className="tab-lead">
        <div>
          <span>Паспорт закупки</span>
          <strong>{tender.external_id}</strong>
          <p>{tender.customer || 'заказчик не указан'}</p>
        </div>
        <div className="tab-lead-facts">
          <span>{tender.region || 'регион не указан'}</span>
          <span>{law}</span>
        </div>
      </div>
      <div className="overview-brief-grid">
        <Info label="Площадка" value={sourceLabels[tender.source] || tender.source} />
        <Info label="Статус площадки" value={tender.status || 'не указан'} />
        <Info label="Категория" value={category} />
        <Info label="ОКПД2" value={tender.okpd2 || raw.Koz2Value || 'не найден'} />
      </div>
    </section>
  )
}

function ProductTabSummary({ summary, total, itemsCount }) {
  const data = summary || {}
  const positionTotal = data.total ?? total ?? itemsCount ?? 0
  const ready = data.ready ?? 0
  const needsReview = data.needs_review ?? 0
  const matched = data.matched ?? 0

  return (
    <div className="product-tab-summary tab-summary-grid" aria-label="Сводка товарных профилей">
      <SummaryMetric value={positionTotal} label="позиций" />
      <SummaryMetric value={ready} label="готовы" />
      <SummaryMetric value={needsReview} label="проверить" />
      <SummaryMetric value={matched} label="найдены" />
    </div>
  )
}

function DocumentStatusSummary({ documents, downloading, extracting, onDownload, onExtract }) {
  const counts = documentStatusCounts(documents)

  return (
    <div className="document-status-summary" aria-label="Сводка документов">
      <div className="document-status-metrics tab-summary-grid">
        <SummaryMetric value={counts.total} label="всего" />
        <SummaryMetric value={counts.downloaded} label="скачано" />
        <SummaryMetric value={counts.ok} label="текст" />
        <SummaryMetric value={counts.attention} label="проверить" />
      </div>
      <div className="document-status-actions">
        <button className="secondary-button compact" disabled={downloading} onClick={onDownload} type="button">
          {downloading ? 'Качаю...' : 'Скачать'}
        </button>
        <button className="secondary-button compact" disabled={extracting || !counts.downloaded} onClick={onExtract} type="button">
          {extracting ? 'Читаю...' : 'Извлечь текст'}
        </button>
      </div>
    </div>
  )
}

function AnalysisTabPanel({ analysis, analyzing, onAnalyze }) {
  const requirementsCount = analysis?.requirements?.length || 0
  const risksCount = (analysis?.risks?.length || 0) + (analysis?.red_flags?.length || 0)
  const checklistCount = analysis?.checklist?.length || 0

  return (
    <section className="detail-section active analysis-section">
      <div className="section-heading-row">
        <h3>Выжимка ТЗ</h3>
        <button className="secondary-button compact" disabled={analyzing} onClick={onAnalyze} type="button">
          {analyzing ? 'Анализ...' : 'Проанализировать'}
        </button>
      </div>
      <div className="analysis-tab-summary tab-summary-grid" aria-label="Сводка анализа ТЗ">
        <SummaryMetric value={analysis ? analysisStatusLabel(analysis.status) : 'нет анализа'} label="статус" />
        <SummaryMetric value={analysis ? formatConfidence(analysis.confidence) : 'нет'} label="уверенность" />
        <SummaryMetric value={requirementsCount} label="требований" />
        <SummaryMetric value={risksCount} label="рисков" />
        <SummaryMetric value={checklistCount} label="пунктов" />
      </div>
      {analysis ? (
        <div className="analysis-card">
          <p>{analysis.summary}</p>
          <AnalysisChecklist items={analysis.checklist} />
          <AnalysisList title="Требования" items={analysis.requirements} empty="Явные требования пока не найдены" />
          <AnalysisList title="Риски" items={analysis.risks} empty="Явные риски пока не найдены" />
          <AnalysisList title="Красные флаги" items={analysis.red_flags} empty="Критичные признаки пока не найдены" danger />
        </div>
      ) : (
        <p className="muted-text">Сначала извлеки текст документов, затем запусти анализ ТЗ.</p>
      )}
    </section>
  )
}

function EconomicsTabPanel({ tender, economics }) {
  const missingInputs = economics?.missing_cost_inputs?.length || 0
  const displayedRevenue = economics?.revenue ?? tender?.price

  return (
    <section className="detail-section active economics-section">
      <div className="section-heading-row">
        <h3>Экономика</h3>
      </div>
      <div className="economics-tab-summary tab-summary-grid" aria-label="Сводка экономики">
        <SummaryMetric value={economics ? economicsStatusLabel(economics.status) : 'не рассчитана'} label="статус" />
        <SummaryMetric value={formatMoney(displayedRevenue)} label="НМЦК" />
        <SummaryMetric value={formatMoney(economics?.estimated_total_cost)} label="затраты" />
        <SummaryMetric value={economics ? formatPercent(economics.margin_percent) : 'нет'} label="маржа" />
        <SummaryMetric value={missingInputs} label="цен добавить" />
      </div>
      <EconomicsSummary economics={economics} tender={tender} />
    </section>
  )
}

function WorkflowTabPanel({ tender, raw, note, saving, onNoteChange, onSaveWorkflow }) {
  const currentStatus = tender.workflow_status || 'new'
  const noteState = note?.trim() ? 'есть' : 'нет'

  return (
    <section className="detail-section active workflow-section">
      <div className="section-heading-row">
        <h3>Рабочий статус</h3>
      </div>
      <div className="workflow-status-summary tab-summary-grid" aria-label="Сводка рабочего статуса">
        <SummaryMetric value={workflowLabels[currentStatus] || 'Новая'} label="текущий статус" />
        <SummaryMetric value={noteState} label="заметка" />
        <SummaryMetric value={formatDate(tender.deadline_at)} label="срок" />
      </div>
      <div className="workflow-actions">
        {Object.entries(workflowLabels).map(([status, label]) => (
          <button
            className={status === currentStatus ? 'active' : ''}
            disabled={saving}
            key={status}
            onClick={() => onSaveWorkflow(status)}
            type="button"
          >
            {label}
          </button>
        ))}
      </div>
      <div className="workflow-note-panel">
        <label className="note-editor">
          Заметка
          <textarea
            value={note}
            onChange={(event) => onNoteChange(event.target.value)}
            placeholder="Например: проверить доставку, сертификаты, маржу."
          />
        </label>
        <button className="secondary-button" disabled={saving} onClick={() => onSaveWorkflow()} type="button">
          {saving ? 'Сохранение...' : 'Сохранить заметку'}
        </button>
      </div>
      <details className="debug-details">
        <summary>Сырые признаки</summary>
        <div className="raw-grid">
          <Info label="Закон" value={raw.federalLawName || raw.SourcePlatformName || 'не найден'} />
          <Info label="ОКПД2" value={tender.okpd2 || raw.Koz2Value || 'не найден'} />
          <Info label="Категория" value={tender.category || raw.CategoryName || 'не найдена'} />
        </div>
      </details>
    </section>
  )
}

function SummaryMetric({ value, label }) {
  return (
    <span>
      <strong>{value}</strong>
      <em className="summary-label">{label}</em>
    </span>
  )
}

function TenderDecisionSummary({ tender, economics }) {
  const marginValue = Number(economics?.margin_percent)
  const marginText = Number.isFinite(marginValue) ? formatPercent(marginValue) : 'нужны цены'
  const economicsText = economics ? `${economicsStatusLabel(economics.status)} · ${marginText}` : 'экономика не рассчитана'
  const nextStep = tenderDecisionNextStep(tender, economics)

  return (
    <section className="decision-summary" aria-label="Краткое решение по закупке">
      <div className="decision-summary-grid">
        <Info label="НМЦК" value={formatMoney(tender.price)} />
        <Info label="Срок" value={formatDate(tender.deadline_at)} />
        <Info label="Заказчик" value={tender.customer || 'не указан'} />
        <Info label="Экономика" value={economicsText} />
        <Info label="Статус" value={workflowLabels[tender.workflow_status] || 'Новая'} />
        <Info label="Следующий шаг" value={nextStep} />
      </div>
    </section>
  )
}

function EconomicsSummary({ economics, tender }) {
  if (!economics) {
    return (
      <p className="muted-text">
        {tender?.price ? 'НМЦК подтянута из карточки закупки. Добавь себестоимость по позициям, чтобы посчитать маржу.' : 'Черновик экономики пока не рассчитан.'}
      </p>
    )
  }

  const missingInputs = economics.missing_cost_inputs || []
  const riskTypes = economics.risk_types || []
  const items = economics.items || []

  return (
    <div className="economics-card">
      <div className="analysis-status-row">
        <strong>{economicsStatusLabel(economics.status)}</strong>
        <span>Маржа: {formatPercent(economics.margin_percent)}</span>
      </div>
      {economics.recommendation && <p>{economics.recommendation}</p>}
      <div className="economics-grid">
        <Info label="НМЦК" value={formatMoney(economics.revenue)} />
        <Info label="Себестоимость" value={formatMoney(economics.supplier_cost)} />
        <Info label="Резерв риска" value={`${formatMoney(economics.risk_reserve)} · ${formatPercent(economics.risk_reserve_rate_percent)}`} />
        <Info label="Итого затраты" value={formatMoney(economics.estimated_total_cost)} />
        <Info label="Маржа" value={`${formatMoney(economics.gross_margin)} · ${formatPercent(economics.margin_percent)}`} />
        <Info label="Риски исполнения" value={riskTypes.length ? riskTypes.join(', ') : 'нет'} />
      </div>
      {missingInputs.length > 0 && (
        <div className="economics-warning">
          <strong>Нужны цены</strong>
          <p>{missingInputs.join(', ')}</p>
        </div>
      )}
      {items.length > 0 && (
        <div className="economics-items">
          {items.map((item, index) => (
            <div className="economics-item" key={`${item.product_name}-${index}`}>
              <strong>{item.product_name}</strong>
              <span>{formatQuantity(item.quantity, item.unit)}</span>
              <span>{formatMoney(item.total_cost)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function ProfileSummary({ summary, total }) {
  const data = summary || { total }
  return (
    <div className="profile-summary-grid">
      <Info label="Всего позиций" value={data.total ?? total ?? 0} />
      <Info label="Готовы" value={data.ready ?? 0} />
      <Info label="Проверить" value={data.needs_review ?? 0} />
      <Info label="Найдены" value={data.matched ?? 0} />
      <Info label="Посчитаны" value={data.priced ?? 0} />
      <Info label="Отклонены" value={data.rejected ?? 0} />
    </div>
  )
}

function ProductProfileDetail({
  profile,
  onEconomicsSave,
  onSupplierOptionSave,
  savingEconomics = false,
  savingSupplierOption = false,
}) {
  const [activeProfileMode, setActiveProfileMode] = useState('overview')

  useEffect(() => {
    setActiveProfileMode('overview')
  }, [profile?.position_index])

  if (!profile) {
    return <div className="profile-detail muted-text">Выбери позицию из списка</div>
  }

  const documentEvidence = (profile.evidence || []).filter((item) => item?.field === 'document_requirement')
  const classifierLabel = `${profile.classifier_type || 'тип не указан'} ${profile.classifier_code || 'код не найден'}`

  return (
    <div className="profile-detail">
      <div className="profile-detail-header">
        <div>
          <span>Позиция #{profile.position_index || '—'}</span>
          <h4>{profile.product_name || 'Без названия'}</h4>
        </div>
        <strong className={`profile-status ${profile.profile_status || 'draft'}`}>
          {profileStatusLabel(profile.profile_status)}
        </strong>
      </div>

      <nav className="product-detail-tabs" aria-label="Разделы товарного профиля">
        {productDetailModes.map((mode) => (
          <button
            className={activeProfileMode === mode.id ? 'active' : ''}
            key={mode.id}
            onClick={() => setActiveProfileMode(mode.id)}
            type="button"
          >
            {mode.label}
          </button>
        ))}
      </nav>

      {activeProfileMode === 'overview' && (
        <>
          <section className="profile-block">
            <h5>Идентификация позиции</h5>
            <div className="profile-detail-grid">
              <Info label="Детализированное наименование" value={profile.details || 'не найдено'} />
              <Info label="Количество" value={formatQuantity(profile.quantity, profile.unit)} />
              <Info label="Цена за ед." value={formatMoney(profile.unit_price)} />
              <Info label="Сумма позиции" value={formatMoney(profile.total_price)} />
              <Info label="ОКПД2" value={profile.okpd2 || 'не найден'} />
              <Info label="Классификатор площадки" value={classifierLabel} />
            </div>
          </section>

          <section className="profile-block">
            <h5>Пакет для поиска товара</h5>
            <AnalysisList title="Поисковые фразы" items={profile.search_phrases || []} empty="Поисковые фразы пока не сформированы" />
            <AnalysisList title="Стоп-слова" items={profile.stop_words || []} empty="Стоп-слова пока не заданы" danger />
          </section>
        </>
      )}

      {activeProfileMode === 'pricing' && (
        <ProductEconomicsForm profile={profile} onSave={onEconomicsSave} saving={savingEconomics} />
      )}

      {activeProfileMode === 'suppliers' && (
        <ProductSupplierOptionsForm profile={profile} onSave={onSupplierOptionSave} saving={savingSupplierOption} />
      )}

      {activeProfileMode === 'requirements' && (
        <>
          <section className="profile-block">
            <h5>Требования и документы</h5>
            <AnalysisList title="Характеристики из карточки и ТЗ" items={profile.required_characteristics || []} empty="Характеристики пока не найдены" />
            <AnalysisList title="Стандарты" items={profile.standards || []} empty="ГОСТ/ТУ пока не найдены" />
            <AnalysisList title="Сертификаты и документы" items={profile.cert_documents || []} empty="Сертификаты/декларации пока не найдены" />
            <AnalysisList title="Поставка и исполнение" items={formatFulfillmentRequirements(profile.fulfillment_requirements || [])} empty="Требования к поставке и исполнению пока не найдены" />
            <AnalysisList title="Страна происхождения" items={profile.origin_country_requirements || []} empty="Требования по стране пока не найдены" />
          </section>

          <section className="profile-block">
            <h5>Подтверждения из ТЗ</h5>
            {documentEvidence.length ? (
              <div className="evidence-list">
                {documentEvidence.map((item, index) => (
                  <div className="evidence-row" key={`${item.source}-${index}`}>
                    <span>{item.source || 'документ'}</span>
                    <p>{item.value}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="muted-text">Связанные фрагменты ТЗ пока не найдены.</p>
            )}
          </section>
        </>
      )}
    </div>
  )
}

function ProductEconomicsForm({ profile, onSave, saving = false }) {
  const economics = profile?.raw_payload?.economics || {}
  const [values, setValues] = useState(() => economicsFormValues(economics))

  useEffect(() => {
    setValues(economicsFormValues(economics))
  }, [profile?.position_index, profile?.raw_payload])

  function updateField(name, value) {
    setValues((current) => ({ ...current, [name]: value }))
  }

  function submitEconomics(event) {
    event.preventDefault()
    if (!onSave) return
    onSave(profile, values)
  }

  return (
    <form className="economics-input-form" onSubmit={submitEconomics}>
      <div className="profile-block-heading">
        <h5>Себестоимость</h5>
        <button className="secondary-button compact" disabled={saving || !onSave} type="submit">
          {saving ? 'Сохраняю...' : 'Сохранить'}
        </button>
      </div>
      <div className="economics-input-grid">
        <label>
          <span>За единицу</span>
          <input
            inputMode="decimal"
            name="unit_cost"
            onChange={(event) => updateField('unit_cost', event.target.value)}
            placeholder="0"
            value={values.unit_cost}
          />
        </label>
        <label>
          <span>Логистика</span>
          <input
            inputMode="decimal"
            name="logistics_cost"
            onChange={(event) => updateField('logistics_cost', event.target.value)}
            placeholder="0"
            value={values.logistics_cost}
          />
        </label>
        <label>
          <span>Документы</span>
          <input
            inputMode="decimal"
            name="documents_cost"
            onChange={(event) => updateField('documents_cost', event.target.value)}
            placeholder="0"
            value={values.documents_cost}
          />
        </label>
        <label>
          <span>Прочее</span>
          <input
            inputMode="decimal"
            name="other_costs"
            onChange={(event) => updateField('other_costs', event.target.value)}
            placeholder="0"
            value={values.other_costs}
          />
        </label>
      </div>
    </form>
  )
}

function economicsFormValues(economics = {}) {
  return {
    unit_cost: economics.unit_cost ?? '',
    logistics_cost: economics.logistics_cost ?? '',
    documents_cost: economics.documents_cost ?? '',
    other_costs: economics.other_costs ?? '',
  }
}

function ProductSupplierOptionsForm({ profile, onSave, saving = false }) {
  const supplierOptions = Array.isArray(profile?.raw_payload?.supplier_options)
    ? profile.raw_payload.supplier_options
    : []
  const [values, setValues] = useState(() => supplierOptionFormValues())

  useEffect(() => {
    setValues(supplierOptionFormValues())
  }, [profile?.position_index])

  function updateField(name, value) {
    setValues((current) => ({ ...current, [name]: value }))
  }

  function submitSupplierOption(event) {
    event.preventDefault()
    if (!onSave) return
    const result = onSave(profile, values)
    if (result?.then) {
      result.then(() => setValues(supplierOptionFormValues())).catch(() => {})
      return
    }
    setValues(supplierOptionFormValues())
  }

  return (
    <section className="profile-block supplier-options-block">
      <form className="supplier-input-form" onSubmit={submitSupplierOption}>
        <div className="profile-block-heading">
          <h5>Поставщики</h5>
          <button className="secondary-button compact" disabled={saving || !onSave || !hasSupplierOptionInput(values)} type="submit">
            {saving ? 'Сохраняю...' : 'Добавить'}
          </button>
        </div>
        <div className="supplier-input-grid">
          <label>
            <span>Поставщик</span>
            <input
              name="name"
              onChange={(event) => updateField('name', event.target.value)}
              placeholder="Название"
              value={values.name}
            />
          </label>
          <label>
            <span>Ссылка</span>
            <input
              name="url"
              onChange={(event) => updateField('url', event.target.value)}
              placeholder="https://"
              value={values.url}
            />
          </label>
          <label>
            <span>Цена за ед.</span>
            <input
              inputMode="decimal"
              name="unit_price"
              onChange={(event) => updateField('unit_price', event.target.value)}
              placeholder="0"
              value={values.unit_price}
            />
          </label>
          <label>
            <span>Наличие</span>
            <select
              name="availability"
              onChange={(event) => updateField('availability', event.target.value)}
              value={values.availability}
            >
              <option value="unknown">Неясно</option>
              <option value="in_stock">В наличии</option>
              <option value="on_request">Под заказ</option>
              <option value="not_available">Нет</option>
            </select>
          </label>
          <label>
            <span>Статус</span>
            <select
              name="status"
              onChange={(event) => updateField('status', event.target.value)}
              value={values.status}
            >
              <option value="candidate">Кандидат</option>
              <option value="suitable">Подходит</option>
              <option value="rejected">Не подходит</option>
            </select>
          </label>
        </div>
        <label className="supplier-note-field">
          <span>Заметка</span>
          <textarea
            name="note"
            onChange={(event) => updateField('note', event.target.value)}
            placeholder="Условия, НДС, доставка, ограничения"
            value={values.note}
          />
        </label>
      </form>

      {supplierOptions.length ? (
        <div className="supplier-options-list">
          {supplierOptions.map((option, index) => (
            <div className="supplier-option-row" key={`${option.url || option.name || 'supplier'}-${index}`}>
              <div>
                {option.url ? (
                  <a href={option.url} target="_blank" rel="noreferrer">{option.name || option.url}</a>
                ) : (
                  <strong>{option.name || 'Поставщик'}</strong>
                )}
                {option.note && <p>{option.note}</p>}
              </div>
              <span>{formatMoney(option.unit_price)}</span>
              <em>{supplierAvailabilityLabel(option.availability)} · {supplierStatusLabel(option.status)}</em>
            </div>
          ))}
        </div>
      ) : (
        <p className="muted-text">Кандидаты поставщиков пока не добавлены.</p>
      )}
    </section>
  )
}

function supplierOptionFormValues() {
  return {
    name: '',
    url: '',
    unit_price: '',
    availability: 'unknown',
    status: 'candidate',
    note: '',
  }
}

function hasSupplierOptionInput(values) {
  return Boolean(values.name || values.url || values.unit_price || values.note)
}

function TenderItems({ items }) {
  if (!items.length) {
    return <p className="muted-text">Позиции из карточки пока не найдены.</p>
  }

  return (
    <details className="source-items">
      <summary>Позиции из карточки ({items.length})</summary>
      <div className="items-list">
        {items.map((item) => (
          <div className="item-card" key={`${item.position_index}-${item.name}`}>
            <div className="item-title">
              <span>№{item.position_index}</span>
              <strong>{item.name}</strong>
            </div>
            {item.details && <p>{item.details}</p>}
            <div className="item-facts">
              <Info label="Кол-во" value={formatAmount(item.quantity, item.unit)} />
              <Info label="Цена за ед." value={formatMoney(item.unit_price)} />
              <Info label="Сумма" value={formatMoney(item.total_price)} />
              <Info label="Классификатор" value={item.classifier_code || item.okpd2 || 'не найден'} />
            </div>
          </div>
        ))}
      </div>
    </details>
  )
}

function Info({ label, value }) {
  return (
    <div className="info">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}

function AnalysisList({ title, items = [], empty, danger = false }) {
  const normalizedItems = normalizeListItems(items)
  return (
    <div className={danger ? 'analysis-list danger' : 'analysis-list'}>
      <span>{title}</span>
      {normalizedItems.length ? (
        <ul>
          {normalizedItems.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      ) : (
        <p>{empty}</p>
      )}
    </div>
  )
}

function AnalysisChecklist({ items = [] }) {
  const normalizedItems = (Array.isArray(items) ? items : [])
    .filter((item) => item && typeof item === 'object' && item.label)

  if (!normalizedItems.length) return null

  return (
    <div className="analysis-checklist">
      <div className="analysis-checklist-header">
        <span>Проверочный список</span>
        <strong>{normalizedItems.length}</strong>
      </div>
      <div className="analysis-checklist-list">
        {normalizedItems.map((item, index) => (
          <article className={`analysis-checklist-row severity-${item.severity || 'medium'}`} key={`${item.label}-${index}`}>
            <div className="analysis-checklist-main">
              <strong>{item.label}</strong>
              <div className="analysis-checklist-tags">
                <span>{analysisCategoryLabel(item.category)}</span>
                <span>{analysisSeverityLabel(item.severity)}</span>
              </div>
            </div>
            {item.evidence && <p>{item.evidence}</p>}
          </article>
        ))}
      </div>
    </div>
  )
}

function normalizeListItems(items = []) {
  return (Array.isArray(items) ? items : [items])
    .map((item) => {
      if (item === null || item === undefined || item === '') return ''
      if (typeof item === 'string') return item
      if (typeof item === 'number') return String(item)
      return JSON.stringify(item)
    })
    .filter(Boolean)
}

function formatFulfillmentRequirements(items = []) {
  return (Array.isArray(items) ? items : [])
    .filter((item) => item && typeof item === 'object' && item.value)
    .map((item) => {
      const typeLabel = fulfillmentRequirementTypeLabel(item.type)
      const source = item.source ? ` · ${item.source}` : ''
      return `${typeLabel}: ${item.value}${source}`
    })
}

function fulfillmentRequirementTypeLabel(type) {
  const labels = {
    acceptance: 'приемка',
    delivery: 'доставка',
    packaging: 'упаковка',
    warranty: 'гарантия',
  }
  return labels[type] || type || 'исполнение'
}

function analysisCategoryLabel(category) {
  const labels = {
    acceptance: 'приемка',
    contract: 'контракт',
    delivery: 'доставка',
    documents: 'документы',
    financial: 'финансы',
    legal: 'право',
    national_regime: 'нацрежим',
    standards: 'стандарты',
  }
  return labels[category] || category || 'общее'
}

function analysisSeverityLabel(severity) {
  const labels = {
    high: 'важно',
    medium: 'проверить',
    low: 'низкий риск',
  }
  return labels[severity] || severity || 'проверить'
}

function shouldAutoRefreshDetails(tender) {
  if (!tender?.source || !tender?.external_id) return false
  if (Array.isArray(tender.items) && tender.items.length > 0) return false
  return ['mosreg_market', 'moscow_supplier_portal'].includes(tender.source)
}

function formatMoney(value) {
  const number = Number(value)
  if (!Number.isFinite(number)) return 'не указана'
  return new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB', maximumFractionDigits: 0 }).format(number)
}

function formatAmount(quantity, unit) {
  const number = Number(quantity)
  const amount = Number.isFinite(number)
    ? new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 4 }).format(number)
    : 'не указано'
  return unit ? `${amount} ${unit}` : amount
}

function formatQuantity(quantity, unit) {
  return formatAmount(quantity, unit)
}

function profileStatusLabel(status) {
  return {
    draft: 'Черновик',
    needs_review: 'Проверить',
    ready: 'Готов',
    searching: 'Поиск',
    matched: 'Найдено',
    priced: 'Расчет',
    rejected: 'Отклонено',
  }[status] || 'Черновик'
}

function formatConfidence(value) {
  const number = Number(value)
  if (!Number.isFinite(number)) return 'не указана'
  return `${Math.round(number * 100)}%`
}

function analysisStatusLabel(status) {
  return {
    needs_review: 'Нужна проверка',
    interesting: 'Интересно',
    skipped: 'Пропустить',
  }[status] || status || 'Нужна проверка'
}

function economicsStatusLabel(status) {
  return {
    interesting: 'Интересно',
    manual_review: 'Проверить',
    low_margin: 'Низкая маржа',
    needs_costs: 'Нужны цены',
    needs_price: 'Нужна НМЦК',
  }[status] || status || 'Проверить'
}

function tenderDecisionNextStep(tender, economics) {
  if (!economics) return 'обновить детали и цены'
  if (economics.status === 'needs_costs') return 'добавить себестоимость'
  if (economics.status === 'needs_price') return 'проверить НМЦК'
  if (economics.status === 'low_margin') return 'оценить отказ'
  if ((tender.product_profiles || []).some((profile) => !profile.raw_payload?.supplier_options?.length)) {
    return 'добавить поставщиков'
  }
  if (economics.status === 'interesting') return 'вести в работу'
  return 'проверить риски'
}

function supplierAvailabilityLabel(value) {
  return {
    unknown: 'наличие неясно',
    in_stock: 'в наличии',
    on_request: 'под заказ',
    not_available: 'нет',
  }[value] || value || 'наличие неясно'
}

function supplierStatusLabel(value) {
  return {
    candidate: 'кандидат',
    suitable: 'подходит',
    rejected: 'не подходит',
  }[value] || value || 'кандидат'
}

function formatPercent(value) {
  const number = Number(value)
  if (!Number.isFinite(number)) return 'не указано'
  return `${new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 2 }).format(number)}%`
}

function formatDateTime(value) {
  if (!value) return 'нет'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

function formatDate(value) {
  if (!value) return 'не указан'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat('ru-RU', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }).format(date)
}

function formatDbCell(value) {
  if (value === null || value === undefined || value === '') return '—'
  if (typeof value === 'number') return new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 4 }).format(value)
  const text = typeof value === 'string' ? value : JSON.stringify(value)
  return text.length > 180 ? `${text.slice(0, 180)}...` : text
}

function documentLabel(url) {
  try {
    const parsed = new URL(url)
    const queryName = parsed.searchParams.get('fileName') || parsed.searchParams.get('name')
    if (queryName) return queryName
    const fileName = decodeURIComponent(parsed.pathname.split('/').filter(Boolean).pop() || '')
    return fileName && fileName.includes('.') ? fileName : url
  } catch {
    return url
  }
}

function documentStatusLabel(status) {
  return {
    pending: 'ожидает',
    downloaded: 'скачан, текст не извлечен',
    ok: 'текст извлечен',
    empty: 'текст не найден',
    unsupported: 'формат не поддержан',
    missing_file: 'файл не найден',
  }[status] || status || 'ожидает'
}

function documentStatusCounts(documents) {
  return (documents || []).reduce((counts, document) => {
    const status = document.text_status || 'pending'
    counts.total += 1
    if (document.local_path) counts.downloaded += 1
    if (status === 'ok') counts.ok += 1
    if (status !== 'ok') counts.attention += 1
    return counts
  }, { total: 0, downloaded: 0, ok: 0, attention: 0 })
}

function documentTextPreview(value) {
  const text = String(value || '').replace(/\s+/g, ' ').trim()
  return text.length > 420 ? `${text.slice(0, 420)}...` : text
}

function documentRecordsForTender(tender) {
  if (tender.document_records?.length) return tender.document_records
  return (tender.documents || []).map((url, index) => ({
    document_index: index + 1,
    name: documentLabel(url),
    document_type: '',
    url,
    local_path: '',
    text_status: 'pending',
  }))
}

function safeJson(value) {
  try {
    return JSON.parse(value || '{}')
  } catch {
    return {}
  }
}

function splitFilterValues(value) {
  return String(value || '')
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
}

function optionLabel(options, value) {
  return options.find((option) => option.value === value)?.label || value
}

function filterSummary(filters) {
  const chips = []
  const sources = splitFilterValues(filters.source)
  chips.push(sources.length ? sources.map((source) => sourceLabels[source] || source).join(' + ') : 'Все площадки')
  chips.push(filters.law || 'Все законы')
  chips.push(filters.status === 'active' ? 'Только активные' : filters.status || 'Все статусы')
  if (filters.region) chips.push(filters.region)
  if (filters.okpd2) chips.push(`ОКПД2: ${filters.okpd2}`)
  if (filters.source_family) chips.push(`Тип источника: ${optionLabel(sourceFamilyOptions, filters.source_family)}`)
  if (filters.procedure_type) chips.push(`Процедура: ${optionLabel(procedureTypeOptions, filters.procedure_type)}`)
  if (filters.customer_inn) chips.push(`ИНН: ${filters.customer_inn}`)
  if (filters.min_price || filters.max_price) {
    chips.push(`Цена: ${filters.min_price || 0} - ${filters.max_price || '∞'}`)
  }
  if (filters.q) chips.push(`Поиск: ${filters.q}`)
  return chips
}

export default App
