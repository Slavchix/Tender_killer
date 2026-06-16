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

export function ParticipationCalculationCard({ calculation }) {
  if (!calculation) return null

  const metrics = [
    ['Ставка', formatMoney(calculation.current_price)],
    ['Стоп-цена', formatMoney(calculation.stop_price)],
    ['Прибыль', formatMoney(calculation.profit)],
    ['Запас', formatMoney(calculation.headroom_to_stop_price)],
    ['Резерв', formatMoney(calculation.risk_reserve)],
    ['Обеспечение', formatMoney(calculation.security_amount)],
  ]

  return (
    <section className={`participation-calculation-card ${calculation.status || ''}`} aria-label="Расчет участия">
      <div className="participation-calculation-heading">
        <span>Расчет участия</span>
        <strong>{calculation.label || 'проверить'}</strong>
      </div>
      <div className="participation-calculation-grid">
        {metrics.map(([label, value]) => (
          <div key={label}>
            <span>{label}</span>
            <strong>{value}</strong>
          </div>
        ))}
      </div>
      {calculation.reason && <p>{calculation.reason}</p>}
      <small>
        Цель {formatPercent(calculation.target_margin_percent)} · запас до безубытка {formatMoney(calculation.headroom_to_break_even)}
      </small>
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
          <div className={`bid-scenario ${scenario.id || ''} ${scenario.role || ''} ${scenario.is_current ? 'current' : ''}`} key={scenario.id || scenario.label}>
            <span>{scenario.label}</span>
            <strong>{formatMoney(scenario.price)}</strong>
            <small>{scenarioRoleLabel(scenario.role)}{scenario.is_current ? ' · сейчас' : ''}</small>
            <em>{formatMoney(scenario.profit ?? scenario.margin_amount)} · {formatPercent(scenario.margin_percent)}</em>
          </div>
        ))}
      </div>
    </section>
  )
}

function scenarioRoleLabel(role) {
  return {
    threshold: 'порог',
    target: 'цель',
    reference: 'ориентир',
    aggressive: 'агрессивно',
    current: 'текущее',
  }[role] || 'сценарий'
}
