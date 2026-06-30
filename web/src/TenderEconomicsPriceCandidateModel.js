import { supplierConfidenceLabel } from './formatters'

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

export function candidatePassportSourceLabel(passport = {}) {
  const source = formatSourceKindLabel(passport.provider || passport.supplier_name) || 'источник'
  const sourceKind = formatSourceKindLabel(passport.source_kind)
  return sourceKind && sourceKind !== source ? `${source} · ${sourceKind}` : source
}

export function candidateSourceLabel(candidate = {}) {
  return formatSourceKindLabel(candidate.provider || candidate.source_kind || candidate.supplier_name) || 'источник не указан'
}

export function formatSourceKindLabel(value) {
  const text = String(value || '').trim()
  if (!text) return ''
  const labels = {
    catalog_search: 'Каталог поставщика',
    catalog_komus: 'Комус',
    catalog_lemanapro: 'Lemana Pro',
    catalog_officemag: 'OfficeMag',
    catalog_petrovich: 'Петрович',
    catalog_vseinstrumenti: 'ВсеИнструменты',
    feed: 'Прайс',
    manual_feed: 'Прайс',
    manual_price: 'Ручная проверка',
    manual_product_url: 'Ссылка на товар',
    manual_quote: 'КП',
    price_memory: 'Память цен',
    price_book: 'Прайс',
    price_book_feed: 'Прайс',
    quote: 'КП',
    [`supplier_${['discovery'].join('_')}`]: 'Поиск поставщика',
  }
  const normalized = text.toLowerCase()
  if (normalized.startsWith('operator_')) {
    return `внесено оператором: ${formatSourceKindLabel(normalized.slice('operator_'.length))}`
  }
  if (labels[normalized]) return labels[normalized]
  const parts = text
    .split(/\s*[·-]\s*/)
    .map((part) => {
      const partKey = part.trim().toLowerCase()
      return labels[partKey] || part.trim().replace(/_/g, ' ')
    })
    .filter(Boolean)
  if (parts.length > 1) return [...new Set(parts)].join(' · ')
  return text.replace(/_/g, ' ')
}

export function candidatePassportMatchLabel(passport = {}) {
  const confidence = supplierConfidenceLabel(passport.match_confidence || passport.confidence || 'needs_review')
  const reasons = Array.isArray(passport.match_reasons) ? passport.match_reasons : []
  return reasons.length ? `${confidence} · ${reasons.slice(0, 2).map(priceCandidateReasonLabel).join(', ')}` : confidence
}

export function candidatePassportRuleLabel(passport = {}) {
  if (passport.rule_label) return passport.rule_label
  const rule = passport.trusted_supplier_rule
  if (!rule || typeof rule !== 'object') return ''
  const parts = []
  if (rule.vat_mode === 'vat_included_by_rule') parts.push('НДС включен')
  if (rule.delivery_rate_percent != null) parts.push(`доставка +${formatQuantity(rule.delivery_rate_percent)}%`)
  return parts.length ? `правило поставщика: ${parts.join(', ')}` : ''
}

export function candidatePassportUnitPackLabel(passport = {}) {
  const parts = []
  if (passport.quantity != null || passport.unit) {
    parts.push(`${passport.quantity != null ? formatQuantity(passport.quantity) : ''} ${passport.unit || 'ед.'}`.trim())
  }
  if (passport.pack_quantity != null) parts.push(`упак. ${formatQuantity(passport.pack_quantity)}`)
  return parts.join(' · ') || 'единица не ясна'
}

export function candidatePassportVatLabel(vatMode) {
  const vat = String(vatMode || '').toLowerCase()
  if (vat.includes('included') || vat.includes('nds_included')) return 'НДС включен'
  if (vat === 'no_vat') return 'без НДС'
  if (vat) return 'НДС уточнить'
  return 'НДС не указан'
}

export function candidatePassportDeliveryLabel(passport = {}) {
  return passport.delivery_note ? 'доставка ясна' : 'доставку уточнить'
}

export function candidatePassportAvailability(passport = {}) {
  if (passport.stock_quantity != null) return `склад ${formatQuantity(passport.stock_quantity)}`
  if (passport.preorder_quantity != null) return `заказ ${formatQuantity(passport.preorder_quantity)}`
  const availability = String(passport.availability || '').toLowerCase()
  if (availability.includes('stock') || availability.includes('available')) return 'в наличии'
  if (availability.includes('unavailable') || availability.includes('out_of_stock')) return 'нет'
  return 'проверить'
}

export function candidatePassportTerms(passport = {}) {
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

export function candidatePassportNextActionLabel(action) {
  return {
    already_confirmed: 'уже принята',
    do_not_accept: 'не принимать',
    ready_to_confirm: 'можно принять',
    rejected: 'отклонена',
    review_required: 'проверить',
  }[action] || 'проверить'
}

export function candidateBestReasonItems(candidate = {}) {
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

export function priceCandidateDecisionReasonLabel(reason) {
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
    supplier_identity: 'Поставщик указан',
    unit_price: 'Цена за единицу',
    manual_feed: 'Прайс',
    manual_price: 'Ручная проверка',
    manual_product_url: 'Ссылка на товар',
    manual_quote: 'КП',
    weak_signal: 'слабый сигнал',
  }
  return labels[reason] || priceCandidateReasonLabel(reason)
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

export function formatQuantity(value) {
  return Number.isInteger(value) ? String(value) : String(value).replace('.', ',')
}

export function numberOrNull(value) {
  const number = Number(value)
  return Number.isFinite(number) ? number : null
}

export function priceCandidateReasonItems(...values) {
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

export function priceCandidateReasonLabel(reason) {
  const labels = {
    availability_unknown: '\u043f\u0440\u043e\u0432\u0435\u0440\u0438\u0442\u044c \u043d\u0430\u043b\u0438\u0447\u0438\u0435',
    brand_match: '\u0431\u0440\u0435\u043d\u0434 \u0441\u043e\u0432\u043f\u0430\u043b',
    color_match: '\u0446\u0432\u0435\u0442 \u0441\u043e\u0432\u043f\u0430\u043b',
    delivery_needs_review: '\u043f\u0440\u043e\u0432\u0435\u0440\u0438\u0442\u044c \u0434\u043e\u0441\u0442\u0430\u0432\u043a\u0443',
    delivery_pickup_only: '\u0441\u0430\u043c\u043e\u0432\u044b\u0432\u043e\u0437',
    delivery_unknown: '\u043f\u0440\u043e\u0432\u0435\u0440\u0438\u0442\u044c \u0434\u043e\u0441\u0442\u0430\u0432\u043a\u0443',
    dimension_match: '\u0440\u0430\u0437\u043c\u0435\u0440 \u0441\u043e\u0432\u043f\u0430\u043b',
    dimension_mismatch: '\u0440\u0430\u0437\u043c\u0435\u0440 \u043d\u0435 \u0441\u043e\u0432\u043f\u0430\u043b',
    family_modifier_mismatch: '\u0443\u0442\u043e\u0447\u043d\u0435\u043d\u0438\u0435 \u0442\u043e\u0432\u0430\u0440\u0430 \u043d\u0435 \u0441\u043e\u0432\u043f\u0430\u043b\u043e',
    [`from_${['supplier', 'discovery'].join('_')}`]: '\u043d\u0430\u0439\u0434\u0435\u043d\u043e \u043f\u043e\u0438\u0441\u043a\u043e\u043c',
    material_match: '\u043c\u0430\u0442\u0435\u0440\u0438\u0430\u043b \u0441\u043e\u0432\u043f\u0430\u043b',
    material_mismatch: '\u043c\u0430\u0442\u0435\u0440\u0438\u0430\u043b \u043d\u0435 \u0441\u043e\u0432\u043f\u0430\u043b',
    minimum_order_amount: '\u043c\u0438\u043d\u0438\u043c\u0430\u043b\u044c\u043d\u0430\u044f \u0441\u0443\u043c\u043c\u0430',
    minimum_order_quantity: '\u043c\u0438\u043d\u0438\u043c\u0430\u043b\u044c\u043d\u044b\u0439 \u0437\u0430\u043a\u0430\u0437',
    model_match: '\u043c\u043e\u0434\u0435\u043b\u044c \u0441\u043e\u0432\u043f\u0430\u043b\u0430',
    manual_feed: 'Прайс',
    manual_price: 'ручная проверка',
    manual_product_url: 'ссылка на товар',
    manual_quote: 'КП',
    provider_present: 'поставщик указан',
    pack_quantity_normalized: '\u0443\u043f\u0430\u043a\u043e\u0432\u043a\u0430 \u043f\u0435\u0440\u0435\u0441\u0447\u0438\u0442\u0430\u043d\u0430',
    pack_quantity_unknown: '\u043f\u0440\u043e\u0432\u0435\u0440\u0438\u0442\u044c \u0443\u043f\u0430\u043a\u043e\u0432\u043a\u0443',
    paper_format_match: '\u0444\u043e\u0440\u043c\u0430\u0442 \u0441\u043e\u0432\u043f\u0430\u043b',
    paper_format_mismatch: '\u0444\u043e\u0440\u043c\u0430\u0442 \u043d\u0435 \u0441\u043e\u0432\u043f\u0430\u043b',
    paper_sheet_count_match: '\u043b\u0438\u0441\u0442\u043e\u0432 \u0441\u043e\u0432\u043f\u0430\u043b\u043e',
    paper_sheet_count_mismatch: '\u043b\u0438\u0441\u0442\u043e\u0432 \u043d\u0435 \u0441\u043e\u0432\u043f\u0430\u043b\u043e',
    piece_pack_count_match: '\u0444\u0430\u0441\u043e\u0432\u043a\u0430 \u0441\u043e\u0432\u043f\u0430\u043b\u0430',
    piece_pack_count_mismatch: '\u0444\u0430\u0441\u043e\u0432\u043a\u0430 \u043d\u0435 \u0441\u043e\u0432\u043f\u0430\u043b\u0430',
    price_break_selected: '\u0441\u0442\u0443\u043f\u0435\u043d\u044c \u0446\u0435\u043d\u044b \u0432\u044b\u0431\u0440\u0430\u043d\u0430',
    price_memory: 'Память цен',
    product_family_match: '\u0442\u0438\u043f \u0442\u043e\u0432\u0430\u0440\u0430 \u0441\u043e\u0432\u043f\u0430\u043b',
    product_family_mismatch: '\u0442\u0438\u043f \u0442\u043e\u0432\u0430\u0440\u0430 \u043d\u0435 \u0441\u043e\u0432\u043f\u0430\u043b',
    product_name_mismatch: '\u0442\u043e\u0432\u0430\u0440 \u043d\u0435 \u0441\u043e\u0432\u043f\u0430\u043b',
    profile_intent_match: '\u043f\u043e\u0437\u0438\u0446\u0438\u044f \u0441\u043e\u0432\u043f\u0430\u043b\u0430',
    strict_source_query: '\u0442\u043e\u0447\u043d\u044b\u0439 \u0437\u0430\u043f\u0440\u043e\u0441',
    supplier_default_delivery: 'доставка по правилу',
    supplier_default_vat_included: 'НДС по правилу',
    token_overlap: '\u0442\u0435\u0440\u043c\u0438\u043d\u044b \u0441\u043e\u0432\u043f\u0430\u043b\u0438',
    supplier_identity: 'поставщик указан',
    unit_price: 'цена за единицу',
    unit_mismatch: '\u043f\u0440\u043e\u0432\u0435\u0440\u0438\u0442\u044c \u0435\u0434\u0438\u043d\u0438\u0446\u0443',
    vat_normalized: '\u041d\u0414\u0421 \u043f\u0435\u0440\u0435\u0441\u0447\u0438\u0442\u0430\u043d',
    vat_not_included: '\u041d\u0414\u0421 \u0441\u0432\u0435\u0440\u0445\u0443',
    vat_unknown: '\u043f\u0440\u043e\u0432\u0435\u0440\u0438\u0442\u044c \u041d\u0414\u0421',
    volume_match: '\u043e\u0431\u044a\u0435\u043c \u0441\u043e\u0432\u043f\u0430\u043b',
    volume_mismatch: '\u043e\u0431\u044a\u0435\u043c \u043d\u0435 \u0441\u043e\u0432\u043f\u0430\u043b',
    weight_match: '\u0432\u0435\u0441 \u0441\u043e\u0432\u043f\u0430\u043b',
    weight_mismatch: '\u0432\u0435\u0441 \u043d\u0435 \u0441\u043e\u0432\u043f\u0430\u043b',
  }
  return labels[reason] || String(reason || '').replace(/_/g, ' ')
}

export function priceCandidateQualityLabel(status) {
  return {
    ready: 'готова к расчету',
    review: 'проверить',
    blocked: 'не брать автоматически',
  }[status] || 'качество не проверено'
}

export function priceCandidateFlagLabel(flag = {}) {
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
    product_family_mismatch: 'тип товара не совпал',
    product_name_mismatch: 'товар не совпал',
    unit_mismatch: 'единица не совпадает',
    vat_not_included: 'НДС не включен',
    vat_unknown: 'НДС не ясен',
  }
  return labels[flag.id] || flag.label || flag.id || 'проверить'
}
