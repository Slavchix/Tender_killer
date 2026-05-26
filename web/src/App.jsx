import { useEffect, useMemo, useRef, useState } from 'react'
import {
  Bell,
  Building2,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
  FileText,
  PlayCircle,
  RefreshCcw,
} from 'lucide-react'
import {
  acceptProfileAutoEconomics as acceptProfileAutoEconomicsRequest,
  addProfileSupplierOption,
  autoSelectProfileSupplierOption,
  downloadTenderDocuments,
  extractTenderDocumentText,
  fetchSourceStatus,
  fetchTenderDetail,
  fetchTenderPage,
  rebuildTenderProductProfiles,
  refreshTenderDetails,
  runProfileAutoEconomics as runProfileAutoEconomicsRequest,
  runSearch as runSearchRequest,
  runTenderAnalysis,
  saveProfileEconomics as saveProfileEconomicsRequest,
  saveProfileEconomicsAssumptions as saveProfileEconomicsAssumptionsRequest,
  saveTenderWorkflow,
  selectProfileSupplierOption,
  sendTenderNotification,
} from './api'
import {
  normalizeListItems,
  formatFulfillmentRequirements,
  analysisCategoryLabel,
  analysisSeverityLabel,
  shouldAutoRefreshDetails,
  formatMoney,
  formatSignedMoney,
  formatSignedPercent,
  formatPriceChangeDirection,
  formatAmount,
  formatQuantity,
  profileStatusLabel,
  formatConfidence,
  analysisStatusLabel,
  economicsStatusLabel,
  tenderDecisionNextStep,
  supplierAvailabilityLabel,
  supplierStatusLabel,
  supplierConfidenceLabel,
  taxModeLabel,
  formatCostDriver,
  formatPercent,
  formatDate,
  documentLabel,
  documentStatusLabel,
  documentStatusCounts,
  documentTextPreview,
  documentRecordsForTender,
} from './formatters'
import { DashboardView } from './Dashboard'
import { DatabaseView } from './DatabaseView'
import { FiltersPanel } from './FiltersPanel'
import { TenderList } from './TenderList'
import './styles.css'
import {
  sourceLabels,
  workflowLabels,
  viewLabels,
  navItems,
  sourceFamilyOptions,
  procedureTypeOptions,
  initialFilters,
  defaultTenderPageLimit,
  tenderPageLimitOptions,
  productDetailModes,
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
          return stillVisible ? current : items[0] || null
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
    runSearchRequest({ filters: nextFilters })
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
        <FiltersPanel
          activeFilterChips={activeFilterChips}
          filters={filters}
          filtersCollapsed={filtersCollapsed}
          onApplyFilters={applyFilters}
          onClearFilters={clearFilters}
          onToggleCollapsed={() => setFiltersCollapsed((current) => !current)}
          onToggleMultiFilter={toggleMultiFilter}
          onUpdateFilter={updateFilter}
        />

        <TenderList
          error={error}
          loading={loading}
          onNextPage={() => goToOffset(tenderPage.next_offset)}
          onPageLimitChange={changePageLimit}
          onPreviousPage={() => goToOffset(tenderPage.previous_offset)}
          onTenderSelect={setSelected}
          onWorkflowFilterChange={setWorkflowFilter}
          page={tenderPage}
          pageLimit={pageLimit}
          pageLimitOptions={tenderPageLimitOptions}
          selectedTender={selected}
          tenders={tenders}
          workflowStatus={filters.workflow_status}
        />

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
  const [savingAssumptionsPosition, setSavingAssumptionsPosition] = useState(null)
  const [savingSupplierOptionPosition, setSavingSupplierOptionPosition] = useState(null)
  const [autoSelectingSupplierPosition, setAutoSelectingSupplierPosition] = useState(null)
  const [autoEstimatingPosition, setAutoEstimatingPosition] = useState(null)
  const [acceptingAutoEconomicsPosition, setAcceptingAutoEconomicsPosition] = useState(null)

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
    setSavingAssumptionsPosition(null)
    setSavingSupplierOptionPosition(null)
    setAutoSelectingSupplierPosition(null)
    setAutoEstimatingPosition(null)
    setAcceptingAutoEconomicsPosition(null)
  }, [tender.source, tender.external_id, tender.workflow_note, tender.analysis, tender.product_profiles, tender.product_profile_summary, tender.economics])

  useEffect(() => {
    const key = `${tender.source}/${tender.external_id}`
    if (!shouldAutoRefreshDetails(tender) || autoRefreshKey.current === key) return
    autoRefreshKey.current = key
    refreshDetails({ automatic: true })
  }, [tender.source, tender.external_id, tender.items?.length])

  function saveWorkflow(workflowStatus = tender.workflow_status || 'new', workflowNote = note) {
    setSaving(true)
    saveTenderWorkflow(tender, {
      workflow_status: workflowStatus,
      workflow_note: workflowNote,
    })
      .then(onWorkflowUpdate)
      .finally(() => setSaving(false))
  }

  function sendToTelegram() {
    setSending(true)
    setNotifyStatus('')
    sendTenderNotification(tender)
      .then((payload) => setNotifyStatus(payload.message || (payload.sent ? 'Отправлено в Telegram' : 'Telegram не настроен')))
      .catch((err) => setNotifyStatus(err.message))
      .finally(() => setSending(false))
  }

  function downloadDocuments() {
    setDownloading(true)
    setDownloadStatus('')
    downloadTenderDocuments(tender)
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
    extractTenderDocumentText(tender)
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
    runTenderAnalysis(tender)
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
    refreshTenderDetails(tender)
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
    rebuildTenderProductProfiles(tender)
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
    saveProfileEconomicsRequest(tender, profile, economicsInputs)
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

  function saveProfileEconomicsAssumptions(profile, assumptionsInputs) {
    if (!profile?.position_index) return null
    setSavingAssumptionsPosition(profile.position_index)
    setDetailStatus('')
    return saveProfileEconomicsAssumptionsRequest(tender, profile, assumptionsInputs)
      .then((nextTender) => {
        onTenderRefresh(nextTender)
        setProductProfiles(nextTender.product_profiles || [])
        setProductProfileSummary(nextTender.product_profile_summary || null)
        setEconomics(nextTender.economics || null)
        setDetailStatus('Допущения экономики обновлены')
        return nextTender
      })
      .catch((err) => {
        setDetailStatus(err.message)
        throw err
      })
      .finally(() => setSavingAssumptionsPosition(null))
  }

  function saveSupplierOption(profile, supplierOption) {
    if (!profile?.position_index) return null
    setSavingSupplierOptionPosition(profile.position_index)
    setDetailStatus('')
    return addProfileSupplierOption(tender, profile, supplierOption)
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

  function selectSupplierOption(profile, optionIndex) {
    if (!profile?.position_index) return null
    setSavingSupplierOptionPosition(profile.position_index)
    setDetailStatus('')
    return selectProfileSupplierOption(tender, profile, optionIndex)
      .then((nextTender) => {
        onTenderRefresh(nextTender)
        setProductProfiles(nextTender.product_profiles || [])
        setProductProfileSummary(nextTender.product_profile_summary || null)
        setEconomics(nextTender.economics || null)
        setDetailStatus('Поставщик взят в расчет')
        return nextTender
      })
      .catch((err) => {
        setDetailStatus(err.message)
        throw err
      })
      .finally(() => setSavingSupplierOptionPosition(null))
  }

  function autoSelectSupplierOption(profile) {
    if (!profile?.position_index) return null
    setAutoSelectingSupplierPosition(profile.position_index)
    setDetailStatus('')
    return autoSelectProfileSupplierOption(tender, profile)
      .then((nextTender) => {
        onTenderRefresh(nextTender)
        setProductProfiles(nextTender.product_profiles || [])
        setProductProfileSummary(nextTender.product_profile_summary || null)
        setEconomics(nextTender.economics || null)
        setDetailStatus('Лучший поставщик взят в расчет')
        return nextTender
      })
      .catch((err) => {
        setDetailStatus(err.message)
        throw err
      })
      .finally(() => setAutoSelectingSupplierPosition(null))
  }

  function runProfileAutoEconomics(profile) {
    if (!profile?.position_index) return null
    setAutoEstimatingPosition(profile.position_index)
    setDetailStatus('')
    return runProfileAutoEconomicsRequest(tender, profile)
      .then((nextTender) => {
        onTenderRefresh(nextTender)
        setProductProfiles(nextTender.product_profiles || [])
        setProductProfileSummary(nextTender.product_profile_summary || null)
        setEconomics(nextTender.economics || null)
        setDetailStatus('Авторасчет обновлен')
        return nextTender
      })
      .catch((err) => {
        setDetailStatus(err.message)
        throw err
      })
      .finally(() => setAutoEstimatingPosition(null))
  }

  function acceptProfileAutoEconomics(profile) {
    if (!profile?.position_index) return null
    setAcceptingAutoEconomicsPosition(profile.position_index)
    setDetailStatus('')
    return acceptProfileAutoEconomicsRequest(tender, profile)
      .then((nextTender) => {
        onTenderRefresh(nextTender)
        setProductProfiles(nextTender.product_profiles || [])
        setProductProfileSummary(nextTender.product_profile_summary || null)
        setEconomics(nextTender.economics || null)
        setDetailStatus('Авторасчет принят в экономику')
        return nextTender
      })
      .catch((err) => {
        setDetailStatus(err.message)
        throw err
      })
      .finally(() => setAcceptingAutoEconomicsPosition(null))
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
      <PriceChangeBanner change={tender.price_change} />

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
          <EconomicsTabPanel
            tender={tender}
            economics={economics}
            productProfiles={productProfiles}
            selectedEconomicsProfileIndex={selectedProfileIndex}
            onSelectedEconomicsProfileChange={setSelectedProfileIndex}
            onEconomicsSave={saveProfileEconomics}
            onEconomicsAssumptionsSave={saveProfileEconomicsAssumptions}
            onSupplierOptionSave={saveSupplierOption}
            onSupplierOptionSelect={selectSupplierOption}
            onSupplierOptionAutoSelect={autoSelectSupplierOption}
            onAutoEconomicsRun={runProfileAutoEconomics}
            onAutoEconomicsAccept={acceptProfileAutoEconomics}
            savingEconomicsPosition={savingEconomicsPosition}
            savingAssumptionsPosition={savingAssumptionsPosition}
            savingSupplierOptionPosition={savingSupplierOptionPosition}
            autoSelectingSupplierPosition={autoSelectingSupplierPosition}
            autoEstimatingPosition={autoEstimatingPosition}
            acceptingAutoEconomicsPosition={acceptingAutoEconomicsPosition}
          />
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

function EconomicsTabPanel({
  tender,
  economics,
  productProfiles = [],
  selectedEconomicsProfileIndex = 0,
  onSelectedEconomicsProfileChange,
  onEconomicsSave,
  onEconomicsAssumptionsSave,
  onSupplierOptionSave,
  onSupplierOptionSelect,
  onSupplierOptionAutoSelect,
  onAutoEconomicsRun,
  onAutoEconomicsAccept,
  savingEconomicsPosition = null,
  savingAssumptionsPosition = null,
  savingSupplierOptionPosition = null,
  autoSelectingSupplierPosition = null,
  autoEstimatingPosition = null,
  acceptingAutoEconomicsPosition = null,
}) {
  const missingInputs = economics?.missing_cost_inputs?.length || 0
  const displayedRevenue = economics?.revenue ?? tender?.price
  const profiles = productProfiles || []
  const selectedEconomicsProfile = profiles[selectedEconomicsProfileIndex] || profiles[0] || null
  const selectedPosition = selectedEconomicsProfile?.position_index
  const savingEconomics = savingEconomicsPosition === selectedPosition
  const savingAssumptions = savingAssumptionsPosition === selectedPosition
  const savingSupplierOption = savingSupplierOptionPosition === selectedPosition
  const autoSelectingSupplier = autoSelectingSupplierPosition === selectedPosition
  const autoEstimating = autoEstimatingPosition === selectedPosition
  const acceptingAutoEconomics = acceptingAutoEconomicsPosition === selectedPosition

  return (
    <section className="detail-section active economics-section">
      <div className="section-heading-row">
        <h3>Экономика</h3>
      </div>
      <div className="economics-tab-summary tab-summary-grid" aria-label="Сводка экономики">
        <SummaryMetric value={economics ? economicsStatusLabel(economics.status) : 'не рассчитана'} label="статус" />
        <SummaryMetric value={formatMoney(displayedRevenue)} label="НМЦК" />
        <SummaryMetric value={formatMoney(economics?.estimated_total_cost)} label="затраты" />
        <SummaryMetric value={formatMoney(economics?.break_even_price)} label="безубыток" />
        <SummaryMetric value={economics ? formatPercent(economics.margin_percent) : 'нет'} label="маржа" />
        <SummaryMetric value={missingInputs} label="цен добавить" />
      </div>
      <EconomicsSummary economics={economics} tender={tender} />
      <div className="economics-workbench">
        <div className="economics-position-list" role="listbox" aria-label="Позиции для экономики">
          {profiles.length ? profiles.map((profile, index) => {
            const supplierOptions = Array.isArray(profile.raw_payload?.supplier_options)
              ? profile.raw_payload.supplier_options
              : []
            const profileEconomics = profile.raw_payload?.economics || {}
            const costValue = profileEconomics.total_cost ?? profileEconomics.unit_cost
            return (
              <button
                className={index === selectedEconomicsProfileIndex ? 'profile-row selected' : 'profile-row'}
                key={`${profile.position_index}-${profile.product_name}-${index}`}
                onClick={() => onSelectedEconomicsProfileChange?.(index)}
                type="button"
              >
                <span className="profile-position">#{profile.position_index || index + 1}</span>
                <span className="profile-name">{profile.product_name || 'Без названия'}</span>
                <span className="profile-meta quantity">{formatQuantity(profile.quantity, profile.unit)}</span>
                <span className="profile-meta classifier">
                  {costValue ? `себестоимость ${formatMoney(costValue)}` : `${supplierOptions.length} поставщиков`}
                </span>
                <span className={`profile-status ${profile.profile_status || 'draft'}`}>{profileStatusLabel(profile.profile_status)}</span>
              </button>
            )
          }) : (
            <p className="muted-text">Товарные позиции пока не сформированы.</p>
          )}
        </div>
        <div className="economics-position-panel">
          {selectedEconomicsProfile ? (
            <>
              <div className="economics-position-heading">
                <span>Позиция #{selectedEconomicsProfile.position_index || selectedEconomicsProfileIndex + 1}</span>
                <strong>{selectedEconomicsProfile.product_name || 'Без названия'}</strong>
              </div>
              <ProductAutoEconomicsPanel
                profile={selectedEconomicsProfile}
                onRun={onAutoEconomicsRun}
                onAccept={onAutoEconomicsAccept}
                saving={autoEstimating}
                accepting={acceptingAutoEconomics}
              />
              <ProductEconomicsForm profile={selectedEconomicsProfile} onSave={onEconomicsSave} saving={savingEconomics} />
              <ProductEconomicsAssumptionsForm
                item={economics?.items?.[selectedEconomicsProfileIndex]}
                profile={selectedEconomicsProfile}
                onSave={onEconomicsAssumptionsSave}
                saving={savingAssumptions}
              />
              <ProductSupplierOptionsForm
                profile={selectedEconomicsProfile}
                onSave={onSupplierOptionSave}
                onSelect={onSupplierOptionSelect}
                onAutoSelect={onSupplierOptionAutoSelect}
                saving={savingSupplierOption}
                autoSelecting={autoSelectingSupplier}
              />
            </>
          ) : (
            <p className="muted-text">Сначала обнови детали закупки, чтобы появились товарные позиции.</p>
          )}
        </div>
      </div>
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

function PriceChangeBanner({ change }) {
  if (!change) return null
  const previousPrice = Number(change.previous_price)
  const currentPrice = Number(change.current_price)
  if (!Number.isFinite(previousPrice) || !Number.isFinite(currentPrice)) return null

  const delta = Number(change.delta)
  const deltaPercent = Number(change.delta_percent)
  const kindLabel = change.price_kind === 'current_offer' ? 'Цена участника' : 'НМЦК'
  const percentText = Number.isFinite(deltaPercent) ? ` · ${formatSignedPercent(deltaPercent)}` : ''

  return (
    <section className={`price-change-banner ${change.direction || 'changed'}`} aria-label="Изменение цены">
      <div className="price-change-copy">
        <span>{kindLabel}</span>
        <strong>{formatPriceChangeDirection(change)}</strong>
      </div>
      <div className="price-change-values">
        <span>было {formatMoney(previousPrice)}</span>
        <span>стало {formatMoney(currentPrice)}</span>
        {Number.isFinite(delta) && (
          <strong className="price-change-delta">
            {formatSignedMoney(delta)}{percentText}
          </strong>
        )}
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
  const bidScenarios = economics.bid_scenarios || []
  const participationDecision = economics.participation_decision || null

  return (
    <div className="economics-card">
      <div className="analysis-status-row">
        <strong>{economicsStatusLabel(economics.status)}</strong>
        <span>Маржа: {formatPercent(economics.margin_percent)}</span>
      </div>
      {economics.recommendation && <p>{economics.recommendation}</p>}
      <ParticipationDecisionCard decision={participationDecision} />
      <BidScenarioStrip scenarios={bidScenarios} />
      <div className="economics-grid">
        <Info label="НМЦК" value={formatMoney(economics.revenue)} />
        <Info label="Себестоимость" value={formatMoney(economics.supplier_cost)} />
        <Info label="Резерв риска" value={`${formatMoney(economics.risk_reserve)} · ${formatPercent(economics.risk_reserve_rate_percent)}`} />
        <Info label="Итого затраты" value={formatMoney(economics.estimated_total_cost)} />
        <Info label="Безубыток" value={formatMoney(economics.break_even_price)} />
        <Info label="Минимальная ставка" value={formatMoney(economics.minimum_margin_price)} />
        <Info label="Интересная ставка" value={formatMoney(economics.interesting_price)} />
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

function ParticipationDecisionCard({ decision }) {
  if (!decision) return null

  return (
    <section className={`participation-decision ${decision.status || ''}`} aria-label="Решение по участию">
      <div>
        <span>Решение по участию</span>
        <strong>{decision.label || 'проверить'}</strong>
      </div>
      <div>
        <span>Лимит</span>
        <strong>{formatMoney(decision.limit_price)}</strong>
      </div>
      {decision.recommendation && <p>{decision.recommendation}</p>}
    </section>
  )
}

function BidScenarioStrip({ scenarios = [] }) {
  if (!scenarios.length) return null

  return (
    <section className="bid-scenario-strip" aria-label="Сценарии цены участия">
      <div className="profile-block-heading">
        <h5>Сценарии цены</h5>
      </div>
      <div className="bid-scenario-grid">
        {scenarios.map((scenario) => (
          <div className={`bid-scenario ${scenario.id || ''}`} key={scenario.id || scenario.label}>
            <span>{scenario.label}</span>
            <strong>{formatMoney(scenario.price)}</strong>
            <em>{formatMoney(scenario.margin_amount)} · {formatPercent(scenario.margin_percent)}</em>
          </div>
        ))}
      </div>
    </section>
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

function ProductProfileDetail({ profile }) {
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
  const priceSource = profile?.raw_payload?.economics_price_source || null
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
      <EconomicsPriceSource source={priceSource} />
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

function EconomicsPriceSource({ source }) {
  if (!source) return null
  const supplier = source.supplier_name || source.supplier_url || 'поставщик'
  const mode = source.selection === 'manual_selected' ? 'выбран вручную' : 'выбран автоматически'

  return (
    <div className={`price-source-note ${source.confidence || 'needs_review'}`}>
      <span>Источник цены</span>
      <strong>{supplier} · {formatMoney(source.unit_price)}</strong>
      <em>{mode} · {supplierConfidenceLabel(source.confidence)}</em>
    </div>
  )
}

function ProductEconomicsAssumptionsForm({ profile, item, onSave, saving = false }) {
  const assumptions = profile?.raw_payload?.economics_assumptions || {}
  const [values, setValues] = useState(() => economicsAssumptionsFormValues(assumptions))

  useEffect(() => {
    setValues(economicsAssumptionsFormValues(assumptions))
  }, [profile?.position_index, profile?.raw_payload])

  function updateField(name, value) {
    setValues((current) => ({ ...current, [name]: value }))
  }

  function submitAssumptions(event) {
    event.preventDefault()
    if (!onSave) return
    onSave(profile, values)
  }

  return (
    <form className="economics-assumptions-form" onSubmit={submitAssumptions}>
      <div className="profile-block-heading">
        <h5>Допущения</h5>
        <button className="secondary-button compact" disabled={saving || !onSave} type="submit">
          {saving ? 'Сохраняю...' : 'Сохранить'}
        </button>
      </div>
      <div className="economics-input-grid">
        <label>
          <span>НДС</span>
          <select name="vat_mode" onChange={(event) => updateField('vat_mode', event.target.value)} value={values.vat_mode}>
            <option value="unknown">проверить</option>
            <option value="vat_included">включен</option>
            <option value="vat_excluded">сверху</option>
            <option value="no_vat">без НДС</option>
          </select>
        </label>
        <label>
          <span>Ставка НДС, %</span>
          <input
            inputMode="decimal"
            name="vat_rate_percent"
            onChange={(event) => updateField('vat_rate_percent', event.target.value)}
            placeholder="20"
            value={values.vat_rate_percent}
          />
        </label>
        <label>
          <span>Резерв, %</span>
          <input
            inputMode="decimal"
            name="risk_reserve_percent"
            onChange={(event) => updateField('risk_reserve_percent', event.target.value)}
            placeholder="0"
            value={values.risk_reserve_percent}
          />
        </label>
        <label>
          <span>Целевая маржа, %</span>
          <input
            inputMode="decimal"
            name="target_margin_percent"
            onChange={(event) => updateField('target_margin_percent', event.target.value)}
            placeholder="15"
            value={values.target_margin_percent}
          />
        </label>
      </div>
      <div className="assumptions-preview">
        <Info label="НДС сверху" value={formatMoney(item?.vat_cost)} />
        <Info label="Резерв позиции" value={formatMoney(item?.position_risk_reserve)} />
        <Info label="Итого позиция" value={formatMoney(item?.estimated_total_cost)} />
        <Info label="Целевая цена" value={formatMoney(item?.target_price)} />
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

function economicsAssumptionsFormValues(assumptions = {}) {
  return {
    vat_mode: assumptions.vat_mode || 'unknown',
    vat_rate_percent: assumptions.vat_rate_percent ?? '',
    risk_reserve_percent: assumptions.risk_reserve_percent ?? '',
    target_margin_percent: assumptions.target_margin_percent ?? '',
  }
}

function ProductAutoEconomicsPanel({ profile, onRun, onAccept, saving = false, accepting = false }) {
  const estimate = profile?.raw_payload?.economics_auto || null
  const costDrivers = Array.isArray(estimate?.cost_drivers) ? estimate.cost_drivers : []
  const needsReview = Array.isArray(estimate?.needs_review) ? estimate.needs_review : []

  return (
    <section className="auto-economics-panel">
      <div className="profile-block-heading">
        <h5>Авторасчет</h5>
        <div className="auto-economics-actions">
          <button className="secondary-button compact" disabled={saving || !onRun} onClick={() => onRun?.(profile)} type="button">
            {saving ? 'Расчет...' : 'Рассчитать'}
          </button>
          <button className="secondary-button compact" disabled={accepting || !estimate || !onAccept} onClick={() => onAccept?.(profile)} type="button">
            {accepting ? 'Применяю...' : 'Принять в расчет'}
          </button>
        </div>
      </div>
      {estimate ? (
        <>
          <div className="auto-economics-metrics">
            <Info label="Итого" value={formatMoney(estimate.estimated_total_cost)} />
            <Info label="Скрытые расходы" value={formatMoney(estimate.hidden_costs_total)} />
            <Info label="Резерв" value={formatMoney(estimate.risk_reserve)} />
            <Info label="НДС" value={taxModeLabel(estimate.tax_mode, estimate.vat_rate_percent)} />
            <Info label="Уверенность" value={formatConfidence(estimate.confidence)} />
          </div>
          {estimate.manual_inputs_present && (
            <p className="auto-economics-note">Ручная экономика уже заполнена, авторасчет сохранен как черновик.</p>
          )}
          <p className="auto-economics-note">Авторасчет заполнит пустые допущения по НДС, резерву и марже.</p>
          <AnalysisList
            title="Факторы расходов"
            items={costDrivers.map(formatCostDriver)}
            empty="Скрытые расходы пока не найдены"
          />
          <AnalysisList
            title="Проверить вручную"
            items={needsReview}
            empty="Критичных проверок пока нет"
            danger={needsReview.length > 0}
          />
        </>
      ) : (
        <p className="muted-text">Черновик авторасчета пока не построен.</p>
      )}
    </section>
  )
}

function ProductSupplierOptionsForm({ profile, onSave, onSelect, onAutoSelect, saving = false, autoSelecting = false }) {
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
          <div className="profile-block-actions">
            <button
              className="secondary-button compact"
              disabled={autoSelecting || !onAutoSelect || !supplierOptions.length}
              onClick={() => onAutoSelect?.(profile)}
              type="button"
            >
              {autoSelecting ? 'Выбираю...' : 'Лучший в расчет'}
            </button>
            <button className="secondary-button compact" disabled={saving || !onSave || !hasSupplierOptionInput(values)} type="submit">
              {saving ? 'Сохраняю...' : 'Добавить'}
            </button>
          </div>
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
            <div
              className={option.status === 'selected' ? 'supplier-option-row selected' : 'supplier-option-row'}
              key={`${option.url || option.name || 'supplier'}-${index}`}
            >
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
              <button
                className="supplier-select-button"
                disabled={saving || !onSelect || option.status === 'selected'}
                onClick={() => onSelect?.(profile, index)}
                type="button"
              >
                {option.status === 'selected' ? 'В расчете' : 'В расчет'}
              </button>
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
