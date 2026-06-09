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
      <p>Подготовь quick links, вставь manual URL товара или внеси цену из feed/КП после проверки.</p>
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
        const matchReasons = priceCandidateReasonItems(candidate.match_reasons, candidate.raw_payload?.match_reasons)
        const reviewReasons = priceCandidateReasonItems(
          candidate.risk_reasons,
          candidate.raw_payload?.risk_reasons,
          qualityFlags.map((flag) => flag.id || flag.label),
        )
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
              {(matchReasons.length > 0 || reviewReasons.length > 0) && (
                <div className="price-candidate-reasons" aria-label="candidate match reasons">
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

function priceCandidateReasonItems(...values) {
  const items = []
  values.forEach((value) => {
    const list = Array.isArray(value) ? value : value ? [value] : []
    list.forEach((item) => {
      const text = String(item || '').trim()
      if (text && !items.includes(text)) items.push(text)
    })
  })
  return items
}

function priceCandidateReasonLabel(reason) {
  const labels = {
    availability_unknown: '\u043f\u0440\u043e\u0432\u0435\u0440\u0438\u0442\u044c \u043d\u0430\u043b\u0438\u0447\u0438\u0435',
    brand_match: '\u0431\u0440\u0435\u043d\u0434 \u0441\u043e\u0432\u043f\u0430\u043b',
    color_match: '\u0446\u0432\u0435\u0442 \u0441\u043e\u0432\u043f\u0430\u043b',
    delivery_needs_review: '\u043f\u0440\u043e\u0432\u0435\u0440\u0438\u0442\u044c \u0434\u043e\u0441\u0442\u0430\u0432\u043a\u0443',
    delivery_pickup_only: '\u0441\u0430\u043c\u043e\u0432\u044b\u0432\u043e\u0437',
    delivery_unknown: '\u043f\u0440\u043e\u0432\u0435\u0440\u0438\u0442\u044c \u0434\u043e\u0441\u0442\u0430\u0432\u043a\u0443',
    dimension_match: '\u0440\u0430\u0437\u043c\u0435\u0440 \u0441\u043e\u0432\u043f\u0430\u043b',
    [`from_${['supplier', 'discovery'].join('_')}`]: '\u043d\u0430\u0439\u0434\u0435\u043d\u043e \u043f\u043e\u0438\u0441\u043a\u043e\u043c',
    material_match: '\u043c\u0430\u0442\u0435\u0440\u0438\u0430\u043b \u0441\u043e\u0432\u043f\u0430\u043b',
    minimum_order_amount: '\u043c\u0438\u043d\u0438\u043c\u0430\u043b\u044c\u043d\u0430\u044f \u0441\u0443\u043c\u043c\u0430',
    minimum_order_quantity: '\u043c\u0438\u043d\u0438\u043c\u0430\u043b\u044c\u043d\u044b\u0439 \u0437\u0430\u043a\u0430\u0437',
    model_match: '\u043c\u043e\u0434\u0435\u043b\u044c \u0441\u043e\u0432\u043f\u0430\u043b\u0430',
    pack_quantity_normalized: '\u0443\u043f\u0430\u043a\u043e\u0432\u043a\u0430 \u043f\u0435\u0440\u0435\u0441\u0447\u0438\u0442\u0430\u043d\u0430',
    pack_quantity_unknown: '\u043f\u0440\u043e\u0432\u0435\u0440\u0438\u0442\u044c \u0443\u043f\u0430\u043a\u043e\u0432\u043a\u0443',
    paper_format_match: '\u0444\u043e\u0440\u043c\u0430\u0442 \u0441\u043e\u0432\u043f\u0430\u043b',
    paper_sheet_count_match: '\u043b\u0438\u0441\u0442\u043e\u0432 \u0441\u043e\u0432\u043f\u0430\u043b\u043e',
    piece_pack_count_match: '\u0444\u0430\u0441\u043e\u0432\u043a\u0430 \u0441\u043e\u0432\u043f\u0430\u043b\u0430',
    price_break_selected: '\u0441\u0442\u0443\u043f\u0435\u043d\u044c \u0446\u0435\u043d\u044b \u0432\u044b\u0431\u0440\u0430\u043d\u0430',
    product_family_match: '\u0442\u0438\u043f \u0442\u043e\u0432\u0430\u0440\u0430 \u0441\u043e\u0432\u043f\u0430\u043b',
    profile_intent_match: '\u043f\u043e\u0437\u0438\u0446\u0438\u044f \u0441\u043e\u0432\u043f\u0430\u043b\u0430',
    strict_source_query: '\u0442\u043e\u0447\u043d\u044b\u0439 \u0437\u0430\u043f\u0440\u043e\u0441',
    token_overlap: '\u0442\u0435\u0440\u043c\u0438\u043d\u044b \u0441\u043e\u0432\u043f\u0430\u043b\u0438',
    unit_mismatch: '\u043f\u0440\u043e\u0432\u0435\u0440\u0438\u0442\u044c \u0435\u0434\u0438\u043d\u0438\u0446\u0443',
    vat_normalized: '\u041d\u0414\u0421 \u043f\u0435\u0440\u0435\u0441\u0447\u0438\u0442\u0430\u043d',
    vat_not_included: '\u041d\u0414\u0421 \u0441\u0432\u0435\u0440\u0445\u0443',
    vat_unknown: '\u043f\u0440\u043e\u0432\u0435\u0440\u0438\u0442\u044c \u041d\u0414\u0421',
    volume_match: '\u043e\u0431\u044a\u0435\u043c \u0441\u043e\u0432\u043f\u0430\u043b',
    weight_match: '\u0432\u0435\u0441 \u0441\u043e\u0432\u043f\u0430\u043b',
  }
  return labels[reason] || String(reason || '').replace(/_/g, ' ')
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
