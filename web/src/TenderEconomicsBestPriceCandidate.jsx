import { CandidateDecisionTrace, CandidatePricePassport } from './TenderEconomicsPriceCandidatePassport'
import { priceComparisonForUnitPrice } from './TenderEconomicsPriceComparison'
import { formatMoney } from './formatters'
import { candidateNeedsManualPrice, numberOrNull } from './TenderEconomicsPriceCandidateModel'

export function BestPriceCandidate({
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
    ignoreBestPriceCandidateActionError(onConfirm?.(candidate))
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

function ignoreBestPriceCandidateActionError(result) {
  if (result?.catch) {
    result.catch(() => {})
  }
}
