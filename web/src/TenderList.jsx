import { CalendarClock, CircleDollarSign, FileText, Scale, TrendingUp, Users } from 'lucide-react'
import { sourceLabels, workflowLabels } from './constants'
import {
  analysisStatusLabel,
  economicsStatusLabel,
  formatDate,
  formatPercent,
  marketStateValue,
  nmcPriceValue,
  tenderDecisionLabel,
  tenderDecisionNextStep,
  tenderDecisionStatus,
} from './formatters'
import { PaginationBar } from './PaginationBar'

export function TenderList({
  error,
  loading,
  onNextPage,
  onPageLimitChange,
  onPreviousPage,
  onTenderSelect,
  onWorkflowFilterChange,
  page,
  pageLimit,
  pageLimitOptions,
  selectedTender,
  tenders,
  workflowStatus,
}) {
  return (
    <section className="tender-list">
      <div className="list-header">
        <h2>Закупки</h2>
        {loading && <span>обновление...</span>}
      </div>

      <div className="workflow-tabs">
        <button className={!workflowStatus ? 'active' : ''} onClick={() => onWorkflowFilterChange('')} type="button">
          Все
        </button>
        {Object.entries(workflowLabels).map(([status, label]) => (
          <button
            className={workflowStatus === status ? 'active' : ''}
            key={status}
            onClick={() => onWorkflowFilterChange(status)}
            type="button"
          >
            {label}
          </button>
        ))}
      </div>

      <PaginationBar
        loading={loading}
        onNext={onNextPage}
        onPageLimitChange={onPageLimitChange}
        onPrevious={onPreviousPage}
        page={page}
        pageLimit={pageLimit}
        pageLimitOptions={pageLimitOptions}
        shown={tenders.length}
      />

      {error && <div className="error-box">{error}</div>}

      <div className="rows">
        {tenders.map((tender) => (
          <TenderListItem
            isSelected={selectedTender?.source === tender.source && selectedTender?.external_id === tender.external_id}
            key={`${tender.source}-${tender.external_id}`}
            onTenderSelect={onTenderSelect}
            tender={tender}
          />
        ))}
      </div>
    </section>
  )
}

function TenderListItem({ isSelected, onTenderSelect, tender }) {
  const economicsStatus = tenderDecisionStatus(tender)

  return (
    <button
      className={`tender-row ${isSelected ? 'selected' : ''}`}
      onClick={() => onTenderSelect(tender)}
      type="button"
    >
      <div className="row-main">
        <span className="row-tags">
          <span className="source-chip">{sourceLabels[tender.source] || tender.source}</span>
          <span className={`workflow-chip ${tender.workflow_status || 'new'}`}>
            {workflowLabels[tender.workflow_status] || 'Новая'}
          </span>
          <span className={`economics-chip ${economicsStatus}`}>
            {tenderDecisionLabel(tender)}
          </span>
        </span>
        <strong>{tender.title}</strong>
        <span>{tender.customer || 'Заказчик не указан'}</span>
        <TenderListDecisionCues tender={tender} />
      </div>
      <div className="row-meta">
        <span><CircleDollarSign size={15} /> {nmcPriceValue(tender)}</span>
        <span><Users size={15} /> {marketStateValue(tender.market_state)}</span>
        <span><Scale size={15} /> {tender.law || 'закон не указан'}</span>
        <span><CalendarClock size={15} /> {formatDate(tender.deadline_at)}</span>
        <span><FileText size={15} /> {tender.documents_count}</span>
        <span>Позиций: {tender.items_count || 0}</span>
      </div>
    </button>
  )
}

function TenderListDecisionCues({ tender }) {
  return (
    <div className="row-insights">
      <span><TrendingUp size={14} /> {economicsInsight(tender)}</span>
      <span><FileText size={14} /> {analysisInsight(tender)}</span>
    </div>
  )
}

function economicsInsight(tender) {
  const economics = tender.economics
  const margin = Number(economics?.margin_percent)
  if (economics) {
    const marginText = Number.isFinite(margin) ? `маржа ${formatPercent(margin)}` : economicsStatusLabel(economics.status)
    return `Экономика: ${marginText}`
  }
  return `Экономика: ${tenderDecisionNextStep(tender, economics)}`
}

function analysisInsight(tender) {
  const analysis = tender.analysis
  if (!analysis) return 'Анализ: не запускался'
  const metrics = analysis.operator_view?.metrics || {}
  const risksCount = metrics.risks ?? ((analysis.risks?.length || 0) + (analysis.red_flags?.length || 0))
  return `Анализ: ${analysisStatusLabel(analysis.status)} · рисков ${risksCount}`
}
