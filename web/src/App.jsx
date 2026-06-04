import { useEffect, useMemo, useState } from 'react'
import {
  Bell,
  ChevronLeft,
  ChevronRight,
  PlayCircle,
  RefreshCcw,
} from 'lucide-react'
import {
  fetchDashboardQueues,
  fetchSourceStatus,
  fetchTenderDetail,
  fetchTenderPage,
  runSearch as runSearchRequest,
} from './api'
import { DashboardView } from './Dashboard'
import { DatabaseView } from './DatabaseView'
import { FiltersPanel } from './FiltersPanel'
import { TenderList } from './TenderList'
import { TenderDetails } from './TenderDetails'
import './styles.css'
import {
  sourceLabels,
  workflowLabels,
  viewLabels,
  navItems,
  deadlineOptions,
  sourceFamilyOptions,
  procedureTypeOptions,
  initialFilters,
  defaultTenderPageLimit,
  tenderPageLimitOptions,
  initialTenderPage,
} from './constants'

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
  const [dashboardQueues, setDashboardQueues] = useState(null)
  const [dashboardQueueError, setDashboardQueueError] = useState('')
  const [pageOffset, setPageOffset] = useState(0)
  const [pageLimit, setPageLimit] = useState(defaultTenderPageLimit)
  const [tenderPage, setTenderPage] = useState(initialTenderPage)

  useEffect(() => {
    loadTenders(appliedFilters, pageOffset)
  }, [appliedFilters, pageOffset, pageLimit])

  useEffect(() => {
    loadDashboardQueues(appliedFilters)
  }, [appliedFilters])

  useEffect(() => {
    loadSourceStatus()
  }, [])

  useEffect(() => {
    if (!selected) {
      setDetails(null)
      return
    }
    fetchTenderDetail(selected.source, selected.external_id)
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
    return fetchTenderPage(params)
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
          return stillVisible ? current : null
        })
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }

  function loadSourceStatus() {
    setSourceStatusError('')
    return fetchSourceStatus()
      .then((payload) => setSourceStatus(payload.sources || []))
      .catch((err) => setSourceStatusError(err.message))
  }

  function loadDashboardQueues(nextAppliedFilters = appliedFilters) {
    setDashboardQueueError('')
    const params = new URLSearchParams()
    Object.entries(nextAppliedFilters || {}).forEach(([key, value]) => {
      if (value) params.set(key, value)
    })
    return fetchDashboardQueues(params)
      .then(setDashboardQueues)
      .catch((err) => setDashboardQueueError(err.message))
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

  function openTenderDetails(tender) {
    setError('')
    setSelected(tender)
  }

  function closeTenderDetails() {
    setSelected(null)
    setDetails(null)
  }

  function changeView(nextView) {
    setView(nextView)
    if (nextView !== 'tenders') {
      closeTenderDetails()
    }
  }

  function updateTenderWorkflow(updatedTender) {
    setDetails(updatedTender)
    setSelected((current) => (
      current?.source === updatedTender.source && current?.external_id === updatedTender.external_id
        ? { ...current, workflow_status: updatedTender.workflow_status, workflow_note: updatedTender.workflow_note }
        : current
    ))
    setTenders((current) => current.map((item) => (
      item.source === updatedTender.source && item.external_id === updatedTender.external_id
        ? {
            ...item,
            workflow_status: updatedTender.workflow_status,
            workflow_note: updatedTender.workflow_note,
          }
        : item
    )))
    loadDashboardQueues()
  }

  function updateTenderDetails(updatedTender) {
    setDetails(updatedTender)
    setSelected((current) => (
      current?.source === updatedTender.source && current?.external_id === updatedTender.external_id
        ? {
            ...current,
            title: updatedTender.title,
            customer: updatedTender.customer,
            price: updatedTender.price,
            status: updatedTender.status,
            deadline_at: updatedTender.deadline_at,
            documents_count: updatedTender.document_records?.length || updatedTender.documents?.length || 0,
            items_count: updatedTender.items?.length || 0,
            workflow_status: updatedTender.workflow_status,
            workflow_note: updatedTender.workflow_note,
            market_state: updatedTender.market_state,
            economics: updatedTender.economics,
            analysis: updatedTender.analysis,
            decision: updatedTender.decision,
          }
        : current
    ))
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
            market_state: updatedTender.market_state,
            economics: updatedTender.economics,
            analysis: updatedTender.analysis,
            decision: updatedTender.decision,
          }
        : item
    )))
    loadDashboardQueues()
  }

  function runSearch() {
    const nextFilters = { ...filters }
    setSearching(true)
    setError('')
    setSearchSummary('')
    setSelected(null)
    setPageOffset(0)
    setAppliedFilters(nextFilters)
    runSearchRequest({ filters: nextFilters })
      .then((payload) => {
        const stats = payload.stats || {}
        setSearchSummary(
          `Fetched=${stats.fetched || 0} Saved=${stats.saved || 0} Matched=${stats.matched || 0} Notified=${stats.notified || 0} Telegram=${payload.notifications_enabled ? 'on' : 'off'}`
        )
        loadSourceStatus()
        loadDashboardQueues(nextFilters)
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
                  onClick={() => changeView(item.id)}
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
              <button className="icon-button" onClick={() => { loadTenders(); loadDashboardQueues() }} title="Обновить список">
                <RefreshCcw size={18} />
              </button>
              <span className="status-pill"><Bell size={16} /> Telegram: уведомления</span>
            </div>
          </header>

          {view === 'dashboard' && (
            <DashboardView
              dashboardQueueError={dashboardQueueError}
              dashboardQueues={dashboardQueues}
              error={error}
              onOpenTenders={() => changeView('tenders')}
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
            <section className={selected ? 'workspace tender-detail-screen' : 'workspace tender-list-screen'}>
              {selected ? (
                <>
                  <div className="detail-screen-toolbar">
                    <button className="secondary-button compact detail-back-button" onClick={closeTenderDetails} type="button">
                      <ChevronLeft size={16} />
                      <span>Назад</span>
                    </button>
                    <div className="detail-screen-heading">
                      <span>Карточка закупки</span>
                      <strong>{selected.title}</strong>
                    </div>
                  </div>
                  <section className="tender-detail-card">
                    {details ? (
                      <TenderDetails tender={details} onTenderRefresh={updateTenderDetails} onWorkflowUpdate={updateTenderWorkflow} />
                    ) : error ? (
                      <div className="error-box">{error}</div>
                    ) : (
                      <div className="empty-state">Загружаю карточку закупки...</div>
                    )}
                  </section>
                </>
              ) : (
                <>
                  <FiltersPanel
                    activeFilterChips={activeFilterChips}
                    collapsed={filtersCollapsed}
                    filters={filters}
                    onApplyFilters={applyFilters}
                    onClearFilters={clearFilters}
                    onToggleCollapsed={() => setFiltersCollapsed((current) => !current)}
                    onUpdateFilter={updateFilter}
                    variant="top"
                  />

                  <TenderList
                    error={error}
                    loading={loading}
                    onNextPage={() => goToOffset(tenderPage.next_offset)}
                    onPageLimitChange={changePageLimit}
                    onPreviousPage={() => goToOffset(tenderPage.previous_offset)}
                    onTenderSelect={openTenderDetails}
                    onWorkflowFilterChange={setWorkflowFilter}
                    page={tenderPage}
                    pageLimit={pageLimit}
                    pageLimitOptions={tenderPageLimitOptions}
                    selectedTender={selected}
                    tenders={tenders}
                    workflowStatus={filters.workflow_status}
                  />

                </>
              )}
            </section>
          )}
        </section>
      </div>
    </main>
  )
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
  if (filters.deadline_days) chips.push(`Дедлайн ≤ ${optionLabel(deadlineOptions, filters.deadline_days)}`)
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
