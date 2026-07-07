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
  const fallbackStats = readinessStats(profiles)
  const priceQuality = economics?.price_quality || null
  const totalPositions = priceQuality?.positions_total ?? fallbackStats.total
  const readyPositions = priceQuality?.positions_priced ?? fallbackStats.ready
  const candidateCount = priceQuality?.candidates_total ?? fallbackStats.candidates
  const missingInputs =
    priceQuality?.positions_missing ??
    (economics?.missing_cost_inputs?.length || Math.max(totalPositions - readyPositions, 0))
  const displayedRevenue = economics?.revenue ?? marketState?.nmc_price ?? tender?.price
  const revenueLabel = economics?.revenue_kind === 'current_offer' ? 'Цена участника' : 'НМЦК'
  const priceQualityMetric = qualityFunnelMetric(priceQuality)

  return (
    <div className="economics-tab-summary economics-command-summary tab-summary-grid" aria-label="Сводка экономики">
      <SummaryMetric value={economics ? economicsStatusLabel(economics.status) : 'не рассчитана'} label="статус" />
      <SummaryMetric value={nmcPriceValue(tender, marketState)} label="НМЦК" />
      <SummaryMetric value={`${readyPositions}/${totalPositions}`} label="цены" />
      <SummaryMetric value={candidateCount} label="кандидаты" />
      <SummaryMetric value={priceQualityMetric} label="проверка цен" />
      <SummaryMetric value={formatMoney(economics?.estimated_total_cost)} label="затраты" />
      <SummaryMetric value={economics ? formatPercent(economics.margin_percent) : 'нет'} label="маржа" />
      <SummaryMetric value={missingInputs} label="цен добавить" />
      <SummaryMetric value={participantBidValue(economics?.market_state || tender?.market_state)} label="ставка" />
      <SummaryMetric value={marketStateValue(economics?.market_state || tender?.market_state)} label="рынок" />
      <SummaryMetric value={formatMoney(displayedRevenue)} label={revenueLabel} />
    </div>
  )
}

function qualityFunnelMetric(priceQuality) {
  if (!priceQuality) return 'нет данных'
  const total = Number(priceQuality.candidates_total || 0)
  const ready = Number(priceQuality.candidates_ready || 0)
  const review = Number(priceQuality.candidates_review || 0)
  const blocked = Number(priceQuality.candidates_blocked || 0)
  if (!total) return 'нет кандидатов'
  if (blocked > 0) return `${review} проверить / ${blocked} блок`
  if (review > 0) return `${ready} готово / ${review} проверить`
  return `${ready} готово`
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
