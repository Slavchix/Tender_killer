import { formatMoney, formatPercent } from './formatters'
import { Info } from './TenderDetailsShared'

export function DecisionEngineV2Panel({ decision }) {
  if (!decision) return null
  const finalCard = decision.final_decision_card || null
  const safeBid = decision.safe_bid || {}
  const policy = decision.auto_price_policy || {}
  const benchmark = decision.historical_benchmark || {}
  const blockers = Array.isArray(decision.blockers) ? decision.blockers.filter(Boolean) : []
  const risks = Array.isArray(decision.risks) ? decision.risks.filter(Boolean) : []

  return (
    <section className="economics-decision-v2" aria-label="Решение экономики">
      <div className="analysis-status-row">
        <strong>Решение экономики</strong>
        <span>{formatParticipationGate(decision.can_participate)}</span>
      </div>
      <FinalDecisionCard card={finalCard} />
      {decision.one_line_explanation && <p className="economics-decision-one-line">{decision.one_line_explanation}</p>}
      <div className="economics-grid">
        <Info label="Безопасная ставка" value={formatMoney(safeBid.amount)} />
        <Info label="Минимальная маржа" value={formatPercent(decision.minimum_margin_percent)} />
        <Info label="Текущая маржа" value={formatPercent(decision.current_margin_percent)} />
        <Info label="Буфер снижения" value={formatDiscountBuffer(decision.discount_buffer)} />
        <Info label="Автоцены" value={formatAutoPricePolicy(policy)} />
        <Info label="История" value={formatHistoricalBenchmark(benchmark)} />
      </div>
      {(blockers.length > 0 || risks.length > 0 || benchmark.note) && (
        <div className="economics-decision-notes">
          {blockers.length > 0 && <p><strong>Блокирует:</strong> {blockers.slice(0, 3).join(', ')}</p>}
          {risks.length > 0 && <p><strong>Риски:</strong> {risks.slice(0, 3).join(', ')}</p>}
          {benchmark.note && <p>{benchmark.note}</p>}
        </div>
      )}
    </section>
  )
}

function FinalDecisionCard({ card }) {
  if (!card) return null
  const reasons = Array.isArray(card.primary_reasons) ? card.primary_reasons.filter(Boolean).slice(0, 3) : []
  const blockers = Array.isArray(card.blockers) ? card.blockers.filter(Boolean).slice(0, 3) : []
  return (
    <div className={`economics-final-decision-card ${card.tone || 'review'}`} aria-label="Короткое решение экономики">
      <div>
        <strong>{card.headline || 'Нужна проверка'}</strong>
        <span>{[card.margin_text, card.buffer_text].filter(Boolean).join(' · ')}</span>
      </div>
      {reasons.length > 0 && <p>{reasons.join(' · ')}</p>}
      {blockers.length > 0 && <p><b>Блокирует:</b> {blockers.join(' · ')}</p>}
      {card.next_action && <em>{card.next_action}</em>}
    </div>
  )
}

function formatParticipationGate(value) {
  if (value === true) return 'можно участвовать'
  if (value === false) return 'не участвовать'
  return 'нужна проверка'
}

function formatDiscountBuffer(buffer) {
  if (!buffer) return 'нет данных'
  const amount = formatMoney(buffer.amount)
  const percent = formatPercent(buffer.percent)
  return `${amount} · ${percent}`
}

function formatAutoPricePolicy(policy) {
  if (!policy) return 'ручная проверка'
  if (policy.level === 'small_review_only_auto_search') return `до ${policy.position_limit || 5}: review-only автопоиск`
  if (policy.level === 'large_manual_sources') return 'прайс/КП/ссылка/быстрые ссылки'
  return 'сначала уточнить позиции'
}

function formatHistoricalBenchmark(benchmark) {
  if (!benchmark || benchmark.status === 'no_history') return 'нет истории'
  const delta = Number(benchmark.delta_percent)
  const deltaText = Number.isFinite(delta) ? ` · ${formatPercent(delta)}` : ''
  return `${formatMoney(benchmark.typical_price)} типично${deltaText}`
}
