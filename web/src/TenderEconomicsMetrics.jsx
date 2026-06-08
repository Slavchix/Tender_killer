import {
  economicsStatusLabel,
  formatMoney,
  formatPercent,
  marketStateValue,
  nmcPriceValue,
  participantBidValue,
} from './formatters'
import { SummaryMetric } from './TenderDetailsShared'

export function TenderEconomicsMetrics({ tender, economics, profiles = [] }) {
  const marketState = economics?.market_state || tender?.market_state
  const stats = readinessStats(profiles)
  const totalPositions = stats.total
  const readyPositions = stats.ready
  const candidateCount = stats.candidates
  const missingInputs = economics?.missing_cost_inputs?.length || Math.max(totalPositions - readyPositions, 0)
  const displayedRevenue = economics?.revenue ?? marketState?.nmc_price ?? tender?.price
  const revenueLabel = economics?.revenue_kind === 'current_offer' ? 'Цена участника' : 'НМЦК'

  return (
    <div className="economics-tab-summary economics-command-summary tab-summary-grid" aria-label="Сводка экономики">
      <SummaryMetric value={economics ? economicsStatusLabel(economics.status) : 'не рассчитана'} label="статус" />
      <SummaryMetric value={nmcPriceValue(tender, marketState)} label="НМЦК" />
      <SummaryMetric value={`${readyPositions}/${totalPositions}`} label="цены" />
      <SummaryMetric value={candidateCount} label="кандидаты" />
      <SummaryMetric value={formatMoney(economics?.estimated_total_cost)} label="затраты" />
      <SummaryMetric value={economics ? formatPercent(economics.margin_percent) : 'нет'} label="маржа" />
      <SummaryMetric value={missingInputs} label="цен добавить" />
      <SummaryMetric value={participantBidValue(economics?.market_state || tender?.market_state)} label="ставка" />
      <SummaryMetric value={marketStateValue(economics?.market_state || tender?.market_state)} label="рынок" />
      <SummaryMetric value={formatMoney(displayedRevenue)} label={revenueLabel} />
    </div>
  )
}

function readinessStats(profiles = []) {
  const items = Array.isArray(profiles) ? profiles : []
  return items.reduce((stats, profile) => {
    const economics = profile?.raw_payload?.economics || {}
    const unitCost = Number(economics.unit_cost || 0)
    const totalCost = Number(economics.total_cost || 0)
    const priceCandidates = Array.isArray(profile?.price_candidates) ? profile.price_candidates : []
    stats.total += 1
    if (unitCost > 0 || totalCost > 0) {
      stats.ready += 1
    }
    stats.candidates += priceCandidates.filter((candidate) => {
      const reviewStatus = String(candidate?.review_status || 'pending').toLowerCase()
      const qualityStatus = String(candidate?.quality_status || '').toLowerCase()
      return reviewStatus === 'pending' && qualityStatus !== 'blocked'
    }).length
    return stats
  }, { total: 0, ready: 0, candidates: 0 })
}
