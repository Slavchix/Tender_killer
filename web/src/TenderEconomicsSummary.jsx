import {
  economicsStatusLabel,
  formatMoney,
  formatPercent,
  formatQuantity,
  marketStateCaption,
  marketStateValue,
  nmcPriceValue,
  participantBidValue,
} from './formatters'
import { Info } from './TenderDetailsShared'
import { BidScenarioStrip, ParticipationDecisionCard } from './TenderEconomicsDecisionScenarios'

export function EconomicsSummary({ economics, tender }) {
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
  const analysisCostDrivers = economics.analysis_cost_drivers || []
  const analysisReserveHint = economics.analysis_reserve_hint || {}
  const marketState = economics.market_state || tender?.market_state
  const revenueLabel = economics.revenue_kind === 'current_offer' ? 'Цена участника' : 'НМЦК'

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
        <Info label="НМЦК" value={nmcPriceValue(tender, marketState)} />
        <Info label="Ставка участника" value={participantBidValue(marketState)} />
        <Info label={revenueLabel === 'Цена участника' ? 'Расчет от ставки' : 'Расчет от НМЦК'} value={formatMoney(economics.revenue)} />
        <Info label="Рынок" value={`${marketStateValue(marketState)} · ${marketStateCaption(economics?.market_state || tender?.market_state)}`} />
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
      {analysisCostDrivers.length > 0 && (
        <div className="analysis-cost-drivers">
          <div className="analysis-status-row">
            <strong>Факторы из ТЗ</strong>
            <span>подсказка резерва: {formatPercent(analysisReserveHint.rate_percent)}</span>
          </div>
          <div className="analysis-cost-driver-list">
            {analysisCostDrivers.slice(0, 5).map((driver, index) => (
              <div className="analysis-cost-driver" key={`${driver.label}-${index}`}>
                <strong>{driver.label}</strong>
                <span>{driver.category || 'general'} · {driver.severity || 'medium'}</span>
                {(driver.impact || driver.source) && <em>{driver.impact || driver.source}</em>}
              </div>
            ))}
          </div>
        </div>
      )}
      {items.length > 0 && (
        <div className="economics-items">
          {items.map((item, index) => (
            <div className="economics-item" key={`${item.product_name}-${index}`}>
              <strong>{item.product_name}</strong>
              <span>{formatQuantity(item.quantity, item.unit)}</span>
              <span>{item.unit_cost != null ? `${formatMoney(item.unit_cost)} за ед.` : 'цена не указана'}</span>
              <span>{formatMoney(item.total_cost)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
