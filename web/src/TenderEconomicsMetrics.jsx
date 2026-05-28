import {
  economicsStatusLabel,
  formatMoney,
  formatPercent,
  marketStateValue,
  nmcPriceValue,
  participantBidValue,
} from './formatters'
import { SummaryMetric } from './TenderDetailsShared'

export function TenderEconomicsMetrics({ tender, economics }) {
  const marketState = economics?.market_state || tender?.market_state
  const missingInputs = economics?.missing_cost_inputs?.length || 0
  const displayedRevenue = economics?.revenue ?? marketState?.nmc_price ?? tender?.price
  const revenueLabel = economics?.revenue_kind === 'current_offer' ? 'Цена участника' : 'НМЦК'

  return (
    <div className="economics-tab-summary tab-summary-grid" aria-label="Сводка экономики">
      <SummaryMetric value={economics ? economicsStatusLabel(economics.status) : 'не рассчитана'} label="статус" />
      <SummaryMetric value={nmcPriceValue(tender, marketState)} label="НМЦК" />
      <SummaryMetric value={participantBidValue(economics?.market_state || tender?.market_state)} label="ставка участника" />
      <SummaryMetric value={marketStateValue(economics?.market_state || tender?.market_state)} label="рынок" />
      <SummaryMetric value={formatMoney(displayedRevenue)} label={revenueLabel} />
      <SummaryMetric value={formatMoney(economics?.estimated_total_cost)} label="затраты" />
      <SummaryMetric value={formatMoney(economics?.break_even_price)} label="безубыток" />
      <SummaryMetric value={economics ? formatPercent(economics.margin_percent) : 'нет'} label="маржа" />
      <SummaryMetric value={missingInputs} label="цен добавить" />
    </div>
  )
}
