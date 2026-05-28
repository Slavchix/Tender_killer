import { documentStatusCounts, economicsStatusLabel, formatMoney, formatPercent, participantBidValue } from './formatters'
import { SummaryMetric } from './TenderDetailsShared'

export function TenderDecisionStrip({ tender, economics, productProfiles = [], documents = [], analysis }) {
  const margin = Number(economics?.margin_percent)
  const marginText = Number.isFinite(margin) ? formatPercent(margin) : 'нужны цены'
  const stopPrice = economics?.minimum_margin_price ?? economics?.break_even_price ?? economics?.interesting_price
  const documentCounts = documentStatusCounts(documents)
  const riskCount = (analysis?.risks?.length || 0) + (analysis?.red_flags?.length || 0)
  const positionTotal = productProfiles.length || tender.items?.length || 0
  const readyProducts = productProfiles.filter((profile) => {
    const raw = profile.raw_payload || {}
    return raw.economics || raw.selected_supplier_option != null
  }).length

  return (
    <section className="decision-strip" aria-label="Решение по закупке">
      <div className="decision-strip-grid">
        <SummaryMetric value={decisionLabel(tender, economics, analysis)} label="решение" />
        <SummaryMetric value={formatMoney(tender.price)} label="НМЦК" />
        <SummaryMetric value={participantBidValue(economics?.market_state || tender.market_state)} label="ставка участника" />
        <SummaryMetric value={economics ? marginText : economicsStatusLabel(economics?.status)} label="маржа" />
        <SummaryMetric value={formatMoney(stopPrice)} label="стоп-цена" />
        <SummaryMetric value={`${readyProducts}/${positionTotal}`} label="позиции" />
        <SummaryMetric value={riskCount} label="риски" />
        <SummaryMetric value={`${documentCounts.ok}/${documents.length}`} label="документы" />
      </div>
    </section>
  )
}

function decisionLabel(tender, economics, analysis) {
  if (economics?.participation_decision?.label) return economics.participation_decision.label
  if ((analysis?.red_flags?.length || 0) > 0) return 'Проверить риски'
  if (Number.isFinite(Number(economics?.margin_percent))) return 'Можно считать'
  if (tender.workflow_status === 'skipped' || tender.workflow_status === 'archive') return 'Пропустить'
  return 'Не готово'
}
