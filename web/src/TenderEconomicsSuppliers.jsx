import { useMemo, useState } from 'react'
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
      <p>Подготовь quick links, вставь manual URL товара или внеси цену из feed/КП после проверки.</p>
    </div>
  )
}

function candidateQueueBuckets(priceCandidates = []) {
  const buckets = {
    ready: [],
    review: [],
    blocked: [],
  }
  ;(Array.isArray(priceCandidates) ? priceCandidates : []).forEach((candidate) => {
    const reviewStatus = String(candidate?.review_status || 'pending').toLowerCase()
    if (reviewStatus !== 'pending') return
    const qualityStatus = String(candidate?.quality_status || '').toLowerCase()
    if (qualityStatus === 'blocked') {
      buckets.blocked.push(candidate)
    } else if (candidate?.auto_eligible || qualityStatus === 'ready') {
      buckets.ready.push(candidate)
    } else {
      buckets.review.push(candidate)
    }
  })
  Object.values(buckets).forEach((bucket) => bucket.sort(comparePriceCandidates))
  return buckets
}

function comparePriceCandidates(left, right) {
  const leftAuto = left?.auto_eligible ? 1 : 0
  const rightAuto = right?.auto_eligible ? 1 : 0
  if (leftAuto !== rightAuto) return rightAuto - leftAuto
  const scoreDelta = Number(right?.score || 0) - Number(left?.score || 0)
  if (scoreDelta !== 0) return scoreDelta
  return Number(left?.unit_price || Number.POSITIVE_INFINITY) - Number(right?.unit_price || Number.POSITIVE_INFINITY)
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
  const blocked = qualityStatus === 'blocked'

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
        disabled={busy || blocked || !onConfirm}
        onClick={() => ignorePriceCandidateActionError(onConfirm?.(candidate))}
        type="button"
      >
        {manualPriceRequired ? 'Внести цену' : blocked ? 'Нужна проверка' : 'Принять'}
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
      {!compact && (
        <small>
          Проверки: {positiveCount} ок
          {issueCount > 0 ? ` · ${issueCount} уточнить` : ' · без замечаний'}
        </small>
      )}
    </div>
  )
}

function candidatePricingPassport(candidate = {}, profile = {}) {
  if (!candidate || typeof candidate !== 'object') return null
  const passport = candidate.pricing_passport && typeof candidate.pricing_passport === 'object'
    ? candidate.pricing_passport
    : {}
  const unitPrice = numberOrNull(passport.unit_price ?? candidate.unit_price)
  const quantity = numberOrNull(passport.quantity ?? profile?.quantity)
  const totalPrice = numberOrNull(passport.total_price) ?? (
    unitPrice != null && quantity != null ? unitPrice * quantity : null
  )
  if (unitPrice == null && totalPrice == null && !passport.summary) return null

  return {
    ...passport,
    unit_price: unitPrice,
    total_price: totalPrice,
    quantity,
    unit: passport.unit ?? candidate.unit ?? profile?.unit,
    availability: passport.availability ?? candidate.availability ?? candidate.raw_payload?.availability,
    vat_mode: passport.vat_mode ?? candidate.vat_mode ?? candidate.raw_payload?.vat_mode,
    delivery_note: passport.delivery_note ?? candidate.delivery_note ?? candidate.raw_payload?.delivery_note,
    stock_quantity: numberOrNull(passport.stock_quantity ?? candidate.stock_quantity ?? candidate.raw_payload?.stock_quantity),
    preorder_quantity: numberOrNull(passport.preorder_quantity ?? candidate.preorder_quantity ?? candidate.raw_payload?.preorder_quantity),
    pack_quantity: numberOrNull(passport.pack_quantity ?? candidate.pack_quantity ?? candidate.raw_payload?.pack_quantity),
    quality_status: passport.quality_status ?? candidate.quality_status ?? 'review',
    positive_checks: Array.isArray(passport.positive_checks) ? passport.positive_checks : [],
    review_checks: Array.isArray(passport.review_checks) ? passport.review_checks : [],
    block_checks: Array.isArray(passport.block_checks) ? passport.block_checks : [],
    next_action: passport.next_action ?? 'review_required',
    summary: passport.summary,
  }
}

function candidatePassportAvailability(passport = {}) {
  if (passport.stock_quantity != null) return `склад ${formatQuantity(passport.stock_quantity)}`
  if (passport.preorder_quantity != null) return `заказ ${formatQuantity(passport.preorder_quantity)}`
  const availability = String(passport.availability || '').toLowerCase()
  if (availability.includes('stock') || availability.includes('available')) return 'в наличии'
  if (availability.includes('unavailable') || availability.includes('out_of_stock')) return 'нет'
  return 'проверить'
}

function candidatePassportTerms(passport = {}) {
  const parts = []
  const vat = String(passport.vat_mode || '').toLowerCase()
  if (vat.includes('included') || vat.includes('nds_included')) {
    parts.push('НДС включен')
  } else if (vat) {
    parts.push('НДС уточнить')
  }
  if (passport.delivery_note) parts.push('доставка ясна')
  if (passport.pack_quantity != null) parts.push(`упак. ${formatQuantity(passport.pack_quantity)}`)
  return parts.slice(0, 3).join(' · ') || 'условия проверить'
}

function candidatePassportNextActionLabel(action) {
  return {
    already_confirmed: 'уже принята',
    do_not_accept: 'не принимать',
    ready_to_confirm: 'можно принять',
    rejected: 'отклонена',
    review_required: 'проверить',
  }[action] || 'проверить'
}

function candidateBestReasonItems(candidate = {}) {
  const items = []
  const pushReason = (id, tone = 'neutral') => {
    const label = priceCandidateDecisionReasonLabel(id)
    if (label && !items.some((item) => item.label === label)) {
      items.push({ label, tone })
    }
  }
  ;(Array.isArray(candidate.score_reasons) ? candidate.score_reasons : []).forEach((reason) => pushReason(reason, 'match'))
  ;(Array.isArray(candidate.match_reasons) ? candidate.match_reasons : []).forEach((reason) => pushReason(reason, 'match'))
  const flags = Array.isArray(candidate.quality_flags) ? candidate.quality_flags : []
  flags.forEach((flag) => {
    const tone = flag?.severity === 'block' ? 'risk' : 'review'
    const label = priceCandidateFlagLabel(flag)
    if (label && !items.some((item) => item.label === label)) {
      items.push({ label, tone })
    }
  })
  if (!items.length && candidate.quality_status) {
    pushReason(`quality_${candidate.quality_status}`, candidate.quality_status === 'blocked' ? 'risk' : 'review')
  }
  return items
}

function priceCandidateDecisionReasonLabel(reason) {
  const labels = {
    confirmed: 'уже принято',
    source_url: 'есть ссылка',
    high_confidence: 'высокая уверенность',
    medium_confidence: 'средняя уверенность',
    has_price: 'есть цена',
    quality_ready: 'готово к расчету',
    quality_review: 'нужна проверка',
    quality_blocked: 'не брать автоматически',
    strict_source_query: 'точный запрос',
    profile_intent_match: 'позиция совпала',
    lower_price: 'ниже рынка',
    provider_present: 'поставщик указан',
    weak_signal: 'слабый сигнал',
  }
  return labels[reason] || priceCandidateReasonLabel(reason)
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
              <CandidatePricePassport candidate={candidate} profile={profile} />
              <CandidateDecisionTrace candidate={candidate} />
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

function candidateNeedsManualPrice(candidate = {}) {
  return Boolean(candidate?.manual_price_required || candidate?.raw_payload?.manual_price_required)
    || (String(candidate?.source_kind || '').toLowerCase() === 'manual_product_url' && numberOrNull(candidate?.unit_price) == null)
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
