import { useEffect, useRef, useState } from 'react'
import { Bell, Building2, ExternalLink, FileText, RefreshCcw } from 'lucide-react'
import {
  acceptProfileAutoEconomics as acceptProfileAutoEconomicsRequest,
  addProfileSupplierOption,
  autoSelectProfileSupplierOption,
  downloadTenderDocuments,
  extractTenderDocumentText,
  rebuildTenderProductProfiles,
  refreshTenderDetails,
  runProfileAutoEconomics as runProfileAutoEconomicsRequest,
  runTenderAnalysis,
  saveProfileEconomics as saveProfileEconomicsRequest,
  saveProfileEconomicsAssumptions as saveProfileEconomicsAssumptionsRequest,
  saveTenderWorkflow,
  selectProfileSupplierOption,
  sendTenderNotification,
} from './api'
import {
  shouldAutoRefreshDetails,
  formatMoney,
  formatDate,
  documentRecordsForTender,
} from './formatters'
import { sourceLabels, workflowLabels } from './constants'
import { PriceChangeBanner, TenderDecisionSummary } from './TenderDecisionSummary'
import { TenderOverviewTab } from './TenderOverviewTab'
import { TenderProductsTab } from './TenderProductsTab'
import { TenderDocumentsTab } from './TenderDocumentsTab'
import { TenderAnalysisTab } from './TenderAnalysisTab'
import { TenderEconomicsTab } from './TenderEconomicsTab'
import { WorkflowTabPanel } from './TenderWorkflowTab'

export function TenderDetails({ tender, onTenderRefresh, onWorkflowUpdate }) {
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
          <TenderProductsTab
            tender={tender}
            productProfiles={productProfiles}
            productProfileSummary={productProfileSummary}
            selectedProfileIndex={selectedProfileIndex}
            onSelectedProfileIndexChange={setSelectedProfileIndex}
            profilesLoading={profilesLoading}
            onRebuildProductProfiles={rebuildProductProfiles}
          />
        )}

        {activeTab === 'documents' && (
          <TenderDocumentsTab
            documents={documentRecords}
            downloading={downloading}
            extracting={extracting}
            onDownload={downloadDocuments}
            onExtract={extractDocumentText}
          />
        )}

        {activeTab === 'analysis' && (
          <TenderAnalysisTab analysis={analysis} analyzing={analyzing} onAnalyze={analyzeTender} />
        )}

        {activeTab === 'economics' && (
          <TenderEconomicsTab
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

function safeJson(value) {
  try {
    return JSON.parse(value || '{}')
  } catch {
    return {}
  }
}
