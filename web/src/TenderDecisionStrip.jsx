import {
  documentStatusCounts,
  economicsStatusLabel,
  formatMoney,
  formatPercent,
  nmcPriceValue,
  participantBidValue,
  tenderDecisionLabel,
} from './formatters'
import { SummaryMetric } from './TenderDetailsShared'

export function TenderDecisionStrip({ tender, economics, productProfiles = [], documents = [], analysis }) {
  const decisionMetrics = tender.decision?.metrics || {}
  const margin = Number(decisionMetrics.margin_percent ?? economics?.margin_percent)
  const marginText = Number.isFinite(margin) ? formatPercent(margin) : 'нужны цены'
  const stopPrice = tender.decision?.limit_price ?? economics?.minimum_margin_price ?? economics?.break_even_price ?? economics?.interesting_price
  const documentCounts = documentStatusCounts(documents)
  const decisionBlockers = Array.isArray(tender.decision?.blockers) ? tender.decision.blockers.length : null
  const riskCount = decisionBlockers ?? (analysis?.risks?.length || 0) + (analysis?.red_flags?.length || 0)
  const positionTotal = numericMetric(decisionMetrics.positions_total, productProfiles.length || tender.items?.length || 0)
  const readyProductsFallback = productProfiles.filter((profile) => {
    const raw = profile.raw_payload || {}
    return raw.economics || raw.selected_supplier_option != null
  }).length
  const readyProducts = numericMetric(decisionMetrics.positions_priced, readyProductsFallback)
  const documentsReady = numericMetric(decisionMetrics.documents_ready, documentCounts.ok)
  const documentsTotal = numericMetric(decisionMetrics.documents_total, documents.length)

  return (
    <section className="decision-strip" aria-label="Решение по закупке">
      <div className="decision-strip-grid">
        <SummaryMetric value={tenderDecisionLabel(tender, economics)} label="решение" />
        <SummaryMetric value={nmcPriceValue(tender, economics?.market_state || tender.market_state)} label="НМЦК" />
        <SummaryMetric value={participantBidValue(economics?.market_state || tender.market_state)} label="ставка участника" />
        <SummaryMetric value={Number.isFinite(margin) ? marginText : economicsStatusLabel(economics?.status)} label="маржа" />
        <SummaryMetric value={formatMoney(stopPrice)} label="стоп-цена" />
        <SummaryMetric value={`${readyProducts}/${positionTotal}`} label="позиции" />
        <SummaryMetric value={riskCount} label="риски" />
        <SummaryMetric value={`${documentsReady}/${documentsTotal}`} label="документы" />
      </div>
    </section>
  )
}

function numericMetric(value, fallback) {
  const number = Number(value)
  return Number.isFinite(number) ? number : fallback
}
