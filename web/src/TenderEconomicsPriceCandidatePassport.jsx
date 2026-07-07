import { formatMoney } from './formatters'
import {
  candidateBestReasonItems,
  candidatePassportAvailability,
  candidatePassportFacts,
  candidatePassportNextActionLabel,
  candidatePassportTerms,
  candidatePricingPassport,
} from './TenderEconomicsPriceCandidateModel'

export function CandidateDecisionTrace({ candidate, compact = false }) {
  const reasons = candidateBestReasonItems(candidate)
  if (!reasons.length) return null
  const visibleReasons = compact ? reasons.slice(0, 3) : reasons.slice(0, 5)

  return (
    <div className="candidate-decision-trace" aria-label="Почему кандидат в этой очереди">
      {visibleReasons.map((reason) => (
        <span className={reason.tone || 'neutral'} key={`${reason.tone || 'neutral'}-${reason.label}`}>
          {reason.label}
        </span>
      ))}
    </div>
  )
}

export function CandidatePricePassport({ candidate, profile, compact = false }) {
  const passport = candidatePricingPassport(candidate, profile)
  if (!passport) return null
  const qualityStatus = String(passport.quality_status || 'review').toLowerCase()
  const positiveCount = passport.positive_checks.length
  const issueCount = passport.review_checks.length + passport.block_checks.length

  return (
    <div className={`price-candidate-passport ${qualityStatus} ${compact ? 'compact' : ''}`}>
      <strong>{passport.summary || candidatePassportNextActionLabel(passport.next_action)}</strong>
      <CandidatePricePassportSteps passport={passport} compact={compact} />
      <div className="price-candidate-passport-grid">
        <span>
          <b>Итого</b>
          <em>{formatMoney(passport.total_price)}</em>
        </span>
        <span>
          <b>Наличие</b>
          <em>{candidatePassportAvailability(passport)}</em>
        </span>
        <span>
          <b>Условия</b>
          <em>{candidatePassportTerms(passport)}</em>
        </span>
        <span>
          <b>Действие</b>
          <em>{candidatePassportNextActionLabel(passport.next_action)}</em>
        </span>
      </div>
      <CandidatePricePassportFacts passport={passport} compact={compact} />
      {!compact && (
        <small>
          Проверки: {positiveCount} ок
          {issueCount > 0 ? ` · ${issueCount} уточнить` : ' · без замечаний'}
        </small>
      )}
    </div>
  )
}

function CandidatePricePassportSteps({ passport, compact = false }) {
  const steps = Array.isArray(passport.funnel_steps) ? passport.funnel_steps : []
  if (!steps.length) return null
  const visibleSteps = compact ? steps.slice(0, 5) : steps

  return (
    <div className="price-candidate-passport-steps" aria-label="Воронка качества цены">
      {visibleSteps.map((step) => (
        <span className={step.status || 'review'} key={step.id || step.label}>
          {step.label}
        </span>
      ))}
    </div>
  )
}

function CandidatePricePassportFacts({ passport, compact = false }) {
  const facts = candidatePassportFacts(passport)
  if (!facts.length) return null
  const visibleFacts = compact ? facts.slice(0, 4) : facts

  return (
    <div className="price-candidate-passport-facts" aria-label="Паспорт цены">
      {visibleFacts.map((fact) => (
        <span key={fact.id}>
          <b>{fact.label}</b>
          {fact.href ? (
            <a href={fact.href} rel="noreferrer" target="_blank">{fact.value}</a>
          ) : (
            <em>{fact.value}</em>
          )}
        </span>
      ))}
    </div>
  )
}
