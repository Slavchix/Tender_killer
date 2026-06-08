import { SupplierOptionsList } from './TenderEconomicsSupplierOptions'
import { priceComparisonForUnitPrice, tenderReferenceUnitPrice } from './TenderEconomicsPriceComparison'
import { formatMoney, formatQuantity as formatTenderQuantity, supplierConfidenceLabel } from './formatters'

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
  const visiblePriceCandidates = priceCandidates.filter((candidate) => {
    const reviewStatus = String(candidate?.review_status || 'pending').toLowerCase()
    const qualityStatus = String(candidate?.quality_status || '').toLowerCase()
    return reviewStatus === 'pending' && qualityStatus !== 'blocked'
  })
  const showSupplierOptions = supplierOptions.length > 0 && visiblePriceCandidates.length === 0
  const showEmptyState = visiblePriceCandidates.length === 0 && supplierOptions.length === 0

  return (
    <section className="profile-block supplier-options-block">
      <PriceCandidatesList
        profile={profile}
        price_candidates={visiblePriceCandidates}
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
      <p>Запусти поиск цен сверху. Статусы каталогов и источников смотри на дашборде.</p>
    </div>
  )
}

function PriceCandidatesList({
  profile,
  price_candidates = [],
  reviewingPriceCandidateId = null,
  onConfirm,
  onReject,
}) {
  if (!price_candidates.length) return null
  const tenderUnitPrice = tenderReferenceUnitPrice(profile)

  return (
    <div className="price-candidates-list">
      <div className="price-candidates-heading">
        <span>Кандидаты цен</span>
        <em>{price_candidates.length}</em>
      </div>
      {price_candidates.map((candidate) => {
        const confirmed = candidate.review_status === 'confirmed'
        const rejected = candidate.review_status === 'rejected'
        const busy = reviewingPriceCandidateId === candidate.id
        const qualityFlags = Array.isArray(candidate.quality_flags) ? candidate.quality_flags : []
        const stockText = formatSupplierStock(candidate)
        const profileQuantity = numberOrNull(profile?.quantity)
        const candidateUnitPrice = numberOrNull(candidate.unit_price)
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
                {candidate.provider || 'источник не указан'}
                {candidate.score != null ? ` · score ${candidate.score}` : ''}
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
              <strong>{formatMoney(candidate.unit_price)}</strong>
              <small>за ед.</small>
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
                disabled={busy || confirmed || rejected || !onConfirm}
                onClick={() => ignorePriceCandidateActionError(onConfirm?.(candidate))}
                type="button"
              >
                {confirmed ? 'Принята' : 'Принять цену'}
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

function priceBreaksForCandidate(candidate = {}) {
  const rawBreaks = Array.isArray(candidate.price_breaks)
    ? candidate.price_breaks
    : Array.isArray(candidate.raw_payload?.price_breaks)
      ? candidate.raw_payload.price_breaks
      : []
  return rawBreaks
    .map((item) => ({
      count: numberOrNull(item?.count),
      price: numberOrNull(item?.price ?? item?.unit_price),
    }))
    .filter((item) => item.count != null && item.count > 0 && item.price != null && item.price > 0)
    .sort((left, right) => left.count - right.count || left.price - right.price)
}

function selectedPriceBreakForCandidate(candidate = {}) {
  const selected = candidate.selected_price_break || candidate.raw_payload?.selected_price_break
  if (!selected || typeof selected !== 'object') return null
  const count = numberOrNull(selected.count)
  const price = numberOrNull(selected.price ?? selected.unit_price)
  return count != null && price != null ? { count, price } : null
}

function samePriceBreak(left, right) {
  if (!left || !right) return false
  return Number(left.count) === Number(right.count) && Number(left.price) === Number(right.price)
}

function formatSupplierStock(candidate = {}) {
  const stock = numberOrNull(candidate.stock_quantity ?? candidate.raw_payload?.stock_quantity)
  const preorder = numberOrNull(candidate.preorder_quantity ?? candidate.raw_payload?.preorder_quantity)
  const parts = []
  if (stock != null) parts.push(`Склад: ${formatQuantity(stock)} шт.`)
  if (preorder != null) parts.push(`Под заказ: ${formatQuantity(preorder)} шт.`)
  return parts.join(' · ')
}

function formatQuantity(value) {
  return Number.isInteger(value) ? String(value) : String(value).replace('.', ',')
}

function numberOrNull(value) {
  const number = Number(value)
  return Number.isFinite(number) ? number : null
}

function priceCandidateQualityLabel(status) {
  return {
    ready: 'готова к расчету',
    review: 'проверить',
    blocked: 'не брать автоматически',
  }[status] || 'качество не проверено'
}

function priceCandidateFlagLabel(flag = {}) {
  const labels = {
    availability_unavailable: 'нет в наличии',
    availability_unknown: 'наличие не подтверждено',
    candidate_rejected: 'отклонена',
    currency_non_rub: 'не рублевая цена',
    delivery_needs_review: 'проверить доставку',
    delivery_pickup_only: 'только самовывоз',
    delivery_unknown: 'доставка не ясна',
    minimum_order_amount: 'минимальная сумма заказа',
    minimum_order_quantity: 'минимальный заказ',
    pack_quantity_invalid: 'ошибка упаковки',
    pack_quantity_unknown: 'упаковка/единица не ясна',
    price_missing: 'нет цены',
    unit_mismatch: 'единица не совпадает',
    vat_not_included: 'НДС не включен',
    vat_unknown: 'НДС не ясен',
  }
  return labels[flag.id] || flag.label || flag.id || 'проверить'
}

function ignorePriceCandidateActionError(result) {
  if (result?.catch) {
    result.catch(() => {})
  }
}
