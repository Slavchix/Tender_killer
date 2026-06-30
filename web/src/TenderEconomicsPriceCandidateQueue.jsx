import { useMemo, useState } from 'react'
import { BestPriceCandidate } from './TenderEconomicsBestPriceCandidate'
import { CandidateDecisionTrace, CandidatePricePassport } from './TenderEconomicsPriceCandidatePassport'
import { priceComparisonForUnitPrice, tenderReferenceUnitPrice } from './TenderEconomicsPriceComparison'
import { formatMoney, formatQuantity as formatTenderQuantity, supplierConfidenceLabel } from './formatters'
import {
  candidateNeedsManualPrice,
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

export function PriceCandidateQueue({
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
