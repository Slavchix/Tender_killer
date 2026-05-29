import { formatMoney, formatPercent } from './formatters'

export function ParticipationDecisionCard({ decision }) {
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

export function BidScenarioStrip({ scenarios = [] }) {
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
