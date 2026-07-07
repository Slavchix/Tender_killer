import { CandidateDecisionTrace, CandidatePricePassport } from './TenderEconomicsPriceCandidatePassport'
import { priceComparisonForUnitPrice } from './TenderEconomicsPriceComparison'
import { formatMoney, formatQuantity as formatTenderQuantity, supplierConfidenceLabel } from './formatters'
import {
  candidateNeedsManualPrice,
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

export function PriceCandidateCard({
  candidate,
  profile,
  busy = false,
  tenderUnitPrice = null,
  onConfirm,
  onReject,
}) {
  const confirmed = candidate.review_status === 'confirmed'
  const rejected = candidate.review_status === 'rejected'
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
}

function ignorePriceCandidateActionError(result) {
  if (result?.catch) {
    result.catch(() => {})
  }
}
