import { useEffect, useRef, useState } from 'react'
import { Building2 } from 'lucide-react'
import {
  refreshTenderDetails,
  sendTenderNotification,
} from './api'
import {
  shouldAutoRefreshDetails,
  formatMoney,
  formatDate,
} from './formatters'
import { sourceLabels, workflowLabels } from './constants'
import { TenderDetailActions } from './TenderDetailActions'
import { PriceChangeBanner, TenderDecisionSummary } from './TenderDecisionSummary'
import { TenderOverviewTab } from './TenderOverviewTab'
import { TenderProductsTab } from './TenderProductsTab'
import { TenderDocumentsTab } from './TenderDocumentsTab'
import { TenderAnalysisTab } from './TenderAnalysisTab'
import { TenderEconomicsTab } from './TenderEconomicsTab'
import { WorkflowTabPanel } from './TenderWorkflowTab'
import { useTenderDocumentAnalysis } from './useTenderDocumentAnalysis'
import { useTenderProductProfiles } from './useTenderProductProfiles'
import { useTenderWorkflow } from './useTenderWorkflow'

export function TenderDetails({ tender, onTenderRefresh, onWorkflowUpdate }) {
  const raw = safeJson(tender.raw_payload_json)
  const autoRefreshKey = useRef('')
  const [activeTab, setActiveTab] = useState('overview')
  const [sending, setSending] = useState(false)
  const [refreshingDetails, setRefreshingDetails] = useState(false)
  const [notifyStatus, setNotifyStatus] = useState('')
  const [detailStatus, setDetailStatus] = useState('')
  const { note, setNote, saving, saveWorkflow } = useTenderWorkflow(tender, onWorkflowUpdate)
  const {
    productProfiles,
    productProfileSummary,
    economics,
    selectedProfileIndex,
    setSelectedProfileIndex,
    profilesLoading,
    savingEconomicsPosition,
    savingAssumptionsPosition,
    savingSupplierOptionPosition,
    autoSelectingSupplierPosition,
    autoEstimatingPosition,
    acceptingAutoEconomicsPosition,
    applyProductTenderState,
    rebuildProductProfiles,
    saveProfileEconomics,
    saveProfileEconomicsAssumptions,
    saveSupplierOption,
    selectSupplierOption,
    autoSelectSupplierOption,
    runProfileAutoEconomics,
    acceptProfileAutoEconomics,
  } = useTenderProductProfiles(tender, onTenderRefresh, setDetailStatus)
  const {
    documentRecords,
    setDocumentRecords,
    analysis,
    setAnalysis,
    downloading,
    extracting,
    analyzing,
    downloadStatus,
    extractStatus,
    downloadDocuments,
    extractDocumentText,
    analyzeTender,
  } = useTenderDocumentAnalysis(tender)

  useEffect(() => {
    setActiveTab('overview')
    setNotifyStatus('')
    setDetailStatus('')
  }, [tender.source, tender.external_id, tender.workflow_note, tender.analysis, tender.product_profiles, tender.product_profile_summary, tender.economics])

  useEffect(() => {
    const key = `${tender.source}/${tender.external_id}`
    if (!shouldAutoRefreshDetails(tender) || autoRefreshKey.current === key) return
    autoRefreshKey.current = key
    refreshDetails({ automatic: true })
  }, [tender.source, tender.external_id, tender.items?.length])

  function sendToTelegram() {
    setSending(true)
    setNotifyStatus('')
    sendTenderNotification(tender)
      .then((payload) => setNotifyStatus(payload.message || (payload.sent ? 'Отправлено в Telegram' : 'Telegram не настроен')))
      .catch((err) => setNotifyStatus(err.message))
      .finally(() => setSending(false))
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
        applyProductTenderState(nextTender)
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

      <TenderDetailActions
        tender={tender}
        refreshingDetails={refreshingDetails}
        downloading={downloading}
        extracting={extracting}
        analyzing={analyzing}
        sending={sending}
        onRefreshDetails={refreshDetails}
        onDownloadDocuments={downloadDocuments}
        onExtractDocumentText={extractDocumentText}
        onAnalyzeTender={analyzeTender}
        onSendToTelegram={sendToTelegram}
      />

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
