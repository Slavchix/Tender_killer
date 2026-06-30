import { useMemo, useState } from 'react'
import { SupplierOptionsList } from './TenderEconomicsSupplierOptions'
import { priceComparisonForUnitPrice, tenderReferenceUnitPrice } from './TenderEconomicsPriceComparison'
import { formatMoney, formatQuantity as formatTenderQuantity, supplierConfidenceLabel } from './formatters'
import {
  candidateBestReasonItems,
  candidateNeedsManualPrice,
  candidatePassportAvailability,
  candidatePassportFacts,
  candidatePassportNextActionLabel,
  candidatePassportTerms,
  candidatePricingPassport,
  candidateQueueBuckets,
  candidateSourceLabel,
  formatQuantity,
  formatSupplierStock,
  numberOrNull,
  priceBreaksForCandidate,
  priceCandidateFlagLabel,
  priceCandidateQualityLabel,
  priceCandidateReasonItems,
  priceCandidateReasonLabel,
  selectedPriceBreakForCandidate,
  samePriceBreak,
} from './TenderEconomicsPriceCandidateModel'

export function ProductSupplierOptionsForm({
  profile,
  onSelect,
  onPriceCandidateConfirm,
  onPriceCandidateReject,
  saving = false,
  reviewingPriceCandidateId = null,
}) {
  const supplierOptions = Array.isArray(profile?.raw_payload?.supplier_options)
    ? profile.raw_payload.supplier_options
    : []
  const priceCandidates = Array.isArray(profile?.price_candidates) ? profile.price_candidates : []
  const candidateBuckets = candidateQueueBuckets(priceCandidates)
  const queuedCandidateCount = candidateBuckets.ready.length + candidateBuckets.review.length + candidateBuckets.blocked.length
  const showSupplierOptions = supplierOptions.length > 0 && queuedCandidateCount === 0
  const showEmptyState = queuedCandidateCount === 0 && supplierOptions.length === 0

  return (
    <section className="profile-block supplier-options-block">
      <PriceCandidateQueue
        profile={profile}
        price_candidates={priceCandidates}
        reviewingPriceCandidateId={reviewingPriceCandidateId}
        onConfirm={(candidate) => onPriceCandidateConfirm?.(profile, candidate)}
        onReject={(candidate) => onPriceCandidateReject?.(profile, candidate)}
      />
      {showSupplierOptions && (
        <SupplierOptionsList
          profile={profile}
          supplierOptions={supplierOptions}
          saving={saving}
          onSelect={(optionIndex) => onSelect?.(profile, optionIndex)}
        />
      )}
      {showEmptyState && <PriceCandidatesEmptyState />}
    </section>
  )
}

function PriceCandidatesEmptyState() {
  return (
    <div className="price-candidates-empty">
      <strong>Кандидатов цен пока нет</strong>
      <p>Подготовь быстрые ссылки, вставь ссылку на товар или внеси цену из прайса/КП после проверки.</p>
    </div>
  )
}


function BestPriceCandidate({
  profile,
  candidate,
  tenderUnitPrice,
  busy = false,
  onConfirm,
}) {
  const candidateUnitPrice = numberOrNull(candidate?.unit_price)
  const profileQuantity = numberOrNull(profile?.quantity)
  const totalCost = profileQuantity != null && candidateUnitPrice != null
    ? profileQuantity * candidateUnitPrice
    : null
  const priceComparison = priceComparisonForUnitPrice(candidateUnitPrice, tenderUnitPrice)
  const qualityStatus = String(candidate?.quality_status || 'review').toLowerCase()
  const manualPriceRequired = candidateNeedsManualPrice(candidate)
  const candidateUrl = String(candidate?.source_url || candidate?.url || '').trim()
  const blocked = qualityStatus === 'blocked'
  const handlePrimaryAction = () => {
    if (manualPriceRequired) {
      if (candidateUrl) {
        window.open(candidateUrl, '_blank', 'noopener,noreferrer')
      }
      return
    }
    ignorePriceCandidateActionError(onConfirm?.(candidate))
  }

  return (
    <div className={`best-price-candidate quality-${qualityStatus}`}>
      <div>
        <span>{manualPriceRequired ? 'Ссылка сохранена' : 'Лучший кандидат'}</span>
        <strong>{manualPriceRequired ? 'нужна цена' : formatMoney(candidate?.unit_price)}</strong>
        <p>
          {candidate?.product_name || candidate?.supplier_name || 'Кандидат цены'}
          {manualPriceRequired ? ' · цена не прочиталась автоматически' : totalCost != null ? ` · ${formatMoney(totalCost)} итого` : ''}
        </p>
        <CandidateDecisionTrace candidate={candidate} compact />
        <CandidatePricePassport candidate={candidate} profile={profile} compact />
        {priceComparison && <em className={priceComparison.tone}>{priceComparison.label}</em>}
      </div>
      <button
        className="secondary-button compact"
        disabled={busy || blocked || (!manualPriceRequired && !onConfirm) || (manualPriceRequired && !candidateUrl)}
        onClick={handlePrimaryAction}
        type="button"
      >
        {manualPriceRequired ? 'Открыть ссылку' : blocked ? 'Нужна проверка' : 'Принять'}
      </button>
    </div>
  )
}

function CandidateDecisionTrace({ candidate, compact = false }) {
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

function CandidatePricePassport({ candidate, profile, compact = false }) {
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


function PriceCandidateQueue({
  profile,
  price_candidates = [],
  reviewingPriceCandidateId = null,
  onConfirm,
  onReject,
}) {
  const buckets = useMemo(() => candidateQueueBuckets(price_candidates), [price_candidates])
  const [activeBucket, setActiveBucket] = useState('ready')
  const preferredBucket = buckets.ready.length ? 'ready' : buckets.review.length ? 'review' : 'blocked'
  const selectedBucket = buckets[activeBucket]?.length ? activeBucket : preferredBucket
  const visibleCandidates = buckets[selectedBucket] || []
  const queuedCandidateCount = buckets.ready.length + buckets.review.length + buckets.blocked.length
  const bestCandidate = buckets.ready[0] || buckets.review[0] || buckets.blocked[0] || null
  if (!queuedCandidateCount) return null
  const tenderUnitPrice = tenderReferenceUnitPrice(profile)

  return (
    <div className="price-candidates-list price-candidate-queue">
      <div className="price-candidates-heading">
        <span>Кандидаты цен</span>
        <em>{queuedCandidateCount}</em>
      </div>
      {bestCandidate && (
        <BestPriceCandidate
          busy={reviewingPriceCandidateId === bestCandidate.id}
          candidate={bestCandidate}
          onConfirm={onConfirm}
          profile={profile}
          tenderUnitPrice={tenderUnitPrice}
        />
      )}
      <div className="candidate-queue-tabs" aria-label="Очередь кандидатов цен">
        {[
          ['ready', 'Готовые', buckets.ready.length],
          ['review', 'Проверить', buckets.review.length],
          ['blocked', 'Блок', buckets.blocked.length],
        ].map(([id, label, count]) => (
          <button
            className={selectedBucket === id ? 'active' : ''}
            disabled={count === 0}
            key={id}
            onClick={() => setActiveBucket(id)}
            type="button"
          >
            {label} <span>{count}</span>
          </button>
        ))}
      </div>
      {visibleCandidates.map((candidate) => {
        const confirmed = candidate.review_status === 'confirmed'
        const rejected = candidate.review_status === 'rejected'
        const busy = reviewingPriceCandidateId === candidate.id
        const qualityFlags = Array.isArray(candidate.quality_flags) ? candidate.quality_flags : []
        const matchReasons = priceCandidateReasonItems(candidate.match_reasons, candidate.raw_payload?.match_reasons)
        const reviewReasons = priceCandidateReasonItems(
          candidate.risk_reasons,
          candidate.raw_payload?.risk_reasons,
          qualityFlags.map((flag) => flag.id || flag.label),
        )
        const stockText = formatSupplierStock(candidate)
        const profileQuantity = numberOrNull(profile?.quantity)
        const candidateUnitPrice = numberOrNull(candidate.unit_price)
        const manualPriceRequired = candidateNeedsManualPrice(candidate)
        const priceComparison = priceComparisonForUnitPrice(candidateUnitPrice, tenderUnitPrice)
        const totalCost = profileQuantity != null && candidateUnitPrice != null
          ? profileQuantity * candidateUnitPrice
          : null
        const priceBreaks = priceBreaksForCandidate(candidate)
        const selectedPriceBreak = selectedPriceBreakForCandidate(candidate)
        return (
          <div
            className={`price-candidate-row ${candidate.review_status || 'pending'} quality-${candidate.quality_status || 'unknown'}`}
            key={candidate.id || `${candidate.source_url || candidate.product_name}-${candidate.unit_price}`}
          >
            <div>
              {candidate.source_url ? (
                <a href={candidate.source_url} target="_blank" rel="noreferrer">
                  {candidate.product_name || candidate.source_url}
                </a>
              ) : (
                <strong>{candidate.product_name || candidate.supplier_name || 'Кандидат цены'}</strong>
              )}
              <p>
                {candidateSourceLabel(candidate)}
                {candidate.score != null ? ` · оценка ${candidate.score}` : ''}
                {candidate.confidence ? ` · ${supplierConfidenceLabel(candidate.confidence)}` : ''}
                {candidate.quality_status ? ` · ${priceCandidateQualityLabel(candidate.quality_status)}` : ''}
                {candidate.auto_eligible ? ' · авто готово' : ''}
              </p>
              <p className="price-candidate-quantity-line">
                Количество в закупке: <strong>{formatTenderQuantity(profile?.quantity, profile?.unit)}</strong>
                {totalCost != null ? ` · Итого по позиции: ${formatMoney(totalCost)}` : ''}
              </p>
              {stockText && <p>{stockText}</p>}
              {priceBreaks.length > 0 && (
                <div className="price-break-strip" aria-label="Ценовые ступени поставщика">
                  {priceBreaks.map((priceBreak) => (
                    <span
                      className={samePriceBreak(priceBreak, selectedPriceBreak) ? 'selected' : ''}
                      key={`${priceBreak.count}-${priceBreak.price}`}
                    >
                      от {formatQuantity(priceBreak.count)} шт.: {formatMoney(priceBreak.price)}
                    </span>
                  ))}
                </div>
              )}
              {selectedPriceBreak && (
                <p className="price-candidate-selected-break">
                  В расчет выбрана ступень от {formatQuantity(selectedPriceBreak.count)} шт.
                </p>
              )}
              <CandidatePricePassport candidate={candidate} profile={profile} />
              <CandidateDecisionTrace candidate={candidate} />
              {(matchReasons.length > 0 || reviewReasons.length > 0) && (
                <div className="price-candidate-reasons" aria-label="Причины совпадения кандидата">
                  {matchReasons.slice(0, 5).map((reason) => (
                    <span className="match" key={`match-${reason}`}>
                      {priceCandidateReasonLabel(reason)}
                    </span>
                  ))}
                  {reviewReasons.slice(0, 5).map((reason) => (
                    <span className="risk" key={`risk-${reason}`}>
                      {priceCandidateReasonLabel(reason)}
                    </span>
                  ))}
                </div>
              )}
              {qualityFlags.length > 0 && (
                <ul className="price-candidate-flags">
                  {qualityFlags.slice(0, 4).map((flag) => (
                    <li className={flag.severity || 'review'} key={flag.id || flag.label}>
                      {priceCandidateFlagLabel(flag)}
                    </li>
                  ))}
                </ul>
              )}
            </div>
            <div className="price-candidate-price-summary">
              <strong>{manualPriceRequired ? 'нужна цена' : formatMoney(candidate.unit_price)}</strong>
              <small>{manualPriceRequired ? 'ссылка сохранена' : 'за ед.'}</small>
              {tenderUnitPrice != null && (
                <em className="price-candidate-reference-price">Тендер: {formatMoney(tenderUnitPrice)}</em>
              )}
              {priceComparison && (
                <em className={`price-candidate-price-delta ${priceComparison.tone}`}>
                  {priceComparison.label}
                </em>
              )}
              {totalCost != null && <em>{formatMoney(totalCost)} итого</em>}
            </div>
            <div className="price-candidate-actions">
              <button
                className="secondary-button compact"
                disabled={busy || confirmed || rejected || manualPriceRequired || !onConfirm}
                onClick={() => ignorePriceCandidateActionError(onConfirm?.(candidate))}
                type="button"
              >
                {manualPriceRequired ? 'Внеси цену вручную' : confirmed ? 'Принята' : 'Принять цену'}
              </button>
              <button
                className="secondary-button compact"
                disabled={busy || confirmed || rejected || !onReject}
                onClick={() => ignorePriceCandidateActionError(onReject?.(candidate))}
                type="button"
              >
                {rejected ? 'Отклонена' : 'Отклонить'}
              </button>
            </div>
          </div>
        )
      })}
    </div>
  )
}


function ignorePriceCandidateActionError(result) {
  if (result?.catch) {
    result.catch(() => {})
  }
}
