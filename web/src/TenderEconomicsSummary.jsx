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
      {items.length > 0 && (
        <div className="economics-items">
          {items.map((item, index) => (
            <div className="economics-item" key={`${item.product_name}-${index}`}>
              <strong>{item.product_name}</strong>
              <span>{formatQuantity(item.quantity, item.unit)}</span>
              <span>{formatMoney(item.total_cost)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function ParticipationDecisionCard({ decision }) {
  if (!decision) return null

  return (
    <section className={`participation-decision ${decision.status || ''}`} aria-label="Решение по участию">
      <div>
        <span>Решение по участию</span>
        <strong>{decision.label || 'проверить'}</strong>
      </div>
      <div>
        <span>Лимит</span>
        <strong>{formatMoney(decision.limit_price)}</strong>
      </div>
      {decision.recommendation && <p>{decision.recommendation}</p>}
    </section>
  )
}

function BidScenarioStrip({ scenarios = [] }) {
  if (!scenarios.length) return null

  return (
    <section className="bid-scenario-strip" aria-label="Сценарии цены участия">
      <div className="profile-block-heading">
        <h5>Сценарии цены</h5>
      </div>
      <div className="bid-scenario-grid">
        {scenarios.map((scenario) => (
          <div className={`bid-scenario ${scenario.id || ''}`} key={scenario.id || scenario.label}>
            <span>{scenario.label}</span>
            <strong>{formatMoney(scenario.price)}</strong>
            <em>{formatMoney(scenario.margin_amount)} · {formatPercent(scenario.margin_percent)}</em>
          </div>
        ))}
      </div>
    </section>
  )
}
