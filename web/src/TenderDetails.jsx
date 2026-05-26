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
  formatFulfillmentRequirements,
  shouldAutoRefreshDetails,
  formatMoney,
  formatSignedMoney,
  formatSignedPercent,
  formatPriceChangeDirection,
  formatAmount,
  formatQuantity,
  profileStatusLabel,
  economicsStatusLabel,
  tenderDecisionNextStep,
  formatPercent,
  formatDate,
  documentRecordsForTender,
} from './formatters'
import { productDetailModes, sourceLabels, workflowLabels } from './constants'
import { Info, SummaryMetric } from './TenderDetailsShared'
import { TenderOverviewTab } from './TenderOverviewTab'
import { TenderDocumentsTab } from './TenderDocumentsTab'
import { AnalysisList, TenderAnalysisTab } from './TenderAnalysisTab'
import { TenderEconomicsTab } from './TenderEconomicsTab'

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

function safeJson(value) {
  try {
    return JSON.parse(value || '{}')
  } catch {
    return {}
  }
}
