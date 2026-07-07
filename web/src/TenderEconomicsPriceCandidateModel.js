import {
  candidatePassportSourceLabel,
  candidatePassportMatchLabel,
  candidatePassportRuleLabel,
  candidatePassportUnitPackLabel,
  candidatePassportVatLabel,
  candidatePassportDeliveryLabel,
  formatSourceKindLabel,
  formatQuantity,
} from './TenderEconomicsPriceCandidateLabels'

// Reason labels such as product_family_mismatch and score_reasons live in TenderEconomicsPriceCandidateLabels.
export {
  candidateBestReasonItems,
  candidatePassportAvailability,
  candidatePassportDeliveryLabel,
  candidatePassportMatchLabel,
  candidatePassportNextActionLabel,
  candidatePassportRuleLabel,
  candidatePassportSourceLabel,
  candidatePassportTerms,
  candidatePassportUnitPackLabel,
  candidatePassportVatLabel,
  candidateSourceLabel,
  formatQuantity,
  formatSourceKindLabel,
  priceCandidateDecisionReasonLabel,
  priceCandidateFlagLabel,
  priceCandidateQualityLabel,
  priceCandidateReasonItems,
  priceCandidateReasonLabel,
} from './TenderEconomicsPriceCandidateLabels'

export function candidateQueueBuckets(priceCandidates = []) {
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

export function comparePriceCandidates(left, right) {
  const leftAuto = left?.auto_eligible ? 1 : 0
  const rightAuto = right?.auto_eligible ? 1 : 0
  if (leftAuto !== rightAuto) return rightAuto - leftAuto
  const scoreDelta = Number(right?.score || 0) - Number(left?.score || 0)
  if (scoreDelta !== 0) return scoreDelta
  return Number(left?.unit_price || Number.POSITIVE_INFINITY) - Number(right?.unit_price || Number.POSITIVE_INFINITY)
}

export function candidatePassportFacts(passport = {}) {
  return [
    { id: 'source', label: 'Источник', value: formatSourceKindLabel(passport.source_label) || candidatePassportSourceLabel(passport) },
    { id: 'reuse', label: 'Повтор', value: candidatePassportReuseLabel(passport.reuse) },
    { id: 'freshness', label: 'Свежесть', value: passport.freshness_label || passport.observed_at || 'нет даты' },
    { id: 'match', label: 'Совпадение', value: candidatePassportMatchLabel(passport) },
    { id: 'rule', label: 'Правило', value: candidatePassportRuleLabel(passport) },
    { id: 'unit_pack', label: 'Ед./упак.', value: passport.unit_pack_label || candidatePassportUnitPackLabel(passport) },
    { id: 'vat', label: 'НДС', value: passport.vat_label || candidatePassportVatLabel(passport.vat_mode) },
    { id: 'delivery', label: 'Доставка', value: passport.delivery_label || candidatePassportDeliveryLabel(passport) },
    {
      id: 'evidence',
      label: 'Доказательство',
      value: passport.evidence_label || (passport.evidence_url || passport.source_url ? 'карточка товара' : 'нужно'),
      href: passport.evidence_url || passport.source_url || '',
    },
  ].filter((fact) => fact.value)
}

export function candidatePassportReuseLabel(reuse = {}) {
  if (!reuse || typeof reuse !== 'object') return ''
  const source = reuse.source_tender_external_id ? `закупка ${reuse.source_tender_external_id}` : 'прошлая закупка'
  const unit = reuse.unit_match === true ? 'единица совпадает' : 'единицу проверить'
  const pack = reuse.pack_quantity != null ? `упак. ${formatQuantity(reuse.pack_quantity)}` : 'упаковку проверить'
  return `Повтор цены: ${source} · ${unit} · ${pack}`
}

export function candidatePricingPassport(candidate = {}, profile = {}) {
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
    source_kind: passport.source_kind ?? candidate.source_kind ?? candidate.raw_payload?.source_kind,
    source_label: passport.source_label ?? '',
    observed_at: passport.observed_at ?? candidate.observed_at ?? candidate.raw_payload?.observed_at,
    freshness_label: passport.freshness_label ?? '',
    match_confidence: passport.match_confidence ?? candidate.confidence ?? 'needs_review',
    match_reasons: Array.isArray(passport.match_reasons) ? passport.match_reasons : Array.isArray(candidate.match_reasons) ? candidate.match_reasons : [],
    unit_pack_label: passport.unit_pack_label ?? '',
    vat_label: passport.vat_label ?? '',
    delivery_label: passport.delivery_label ?? '',
    evidence_url: passport.evidence_url ?? candidate.source_url ?? candidate.url,
    evidence_label: passport.evidence_label ?? '',
    provider: passport.provider ?? candidate.provider,
    supplier_name: passport.supplier_name ?? candidate.supplier_name,
    source_url: passport.source_url ?? candidate.source_url ?? candidate.url,
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
    funnel_steps: Array.isArray(passport.funnel_steps) ? passport.funnel_steps : [],
    trusted_supplier_rule: passport.trusted_supplier_rule && typeof passport.trusted_supplier_rule === 'object'
      ? passport.trusted_supplier_rule
      : null,
    rule_label: passport.rule_label ?? '',
    reuse: passport.reuse ?? candidate.price_memory?.reuse ?? candidate.raw_payload?.price_memory?.reuse ?? null,
    next_action: passport.next_action ?? 'review_required',
    summary: passport.summary,
  }
}

export function candidateNeedsManualPrice(candidate = {}) {
  return Boolean(candidate?.manual_price_required || candidate?.raw_payload?.manual_price_required)
    || (String(candidate?.source_kind || '').toLowerCase() === 'manual_product_url' && numberOrNull(candidate?.unit_price) == null)
}

export function priceBreaksForCandidate(candidate = {}) {
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

export function selectedPriceBreakForCandidate(candidate = {}) {
  const selected = candidate.selected_price_break || candidate.raw_payload?.selected_price_break
  if (!selected || typeof selected !== 'object') return null
  const count = numberOrNull(selected.count)
  const price = numberOrNull(selected.price ?? selected.unit_price)
  return count != null && price != null ? { count, price } : null
}

export function samePriceBreak(left, right) {
  if (!left || !right) return false
  return Number(left.count) === Number(right.count) && Number(left.price) === Number(right.price)
}

export function formatSupplierStock(candidate = {}) {
  const stock = numberOrNull(candidate.stock_quantity ?? candidate.raw_payload?.stock_quantity)
  const preorder = numberOrNull(candidate.preorder_quantity ?? candidate.raw_payload?.preorder_quantity)
  const parts = []
  if (stock != null) parts.push(`Склад: ${formatQuantity(stock)} шт.`)
  if (preorder != null) parts.push(`Под заказ: ${formatQuantity(preorder)} шт.`)
  return parts.join(' · ')
}

export function numberOrNull(value) {
  const number = Number(value)
  return Number.isFinite(number) ? number : null
}
