import { supplierConfidenceLabel } from './formatters'

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
    availability_unknown: 'проверить наличие',
    brand_match: 'бренд совпал',
    color_match: 'цвет совпал',
    delivery_needs_review: 'проверить доставку',
    delivery_pickup_only: 'самовывоз',
    delivery_unknown: 'проверить доставку',
    dimension_match: 'размер совпал',
    dimension_mismatch: 'размер не совпал',
    family_modifier_mismatch: 'уточнение товара не совпало',
    [`from_${['supplier', 'discovery'].join('_')}`]: 'найдено поиском',
    material_match: 'материал совпал',
    material_mismatch: 'материал не совпал',
    minimum_order_amount: 'минимальная сумма',
    minimum_order_quantity: 'минимальный заказ',
    model_match: 'модель совпала',
    manual_feed: 'Прайс',
    manual_price: 'ручная проверка',
    manual_product_url: 'ссылка на товар',
    manual_quote: 'КП',
    provider_present: 'поставщик указан',
    pack_quantity_normalized: 'упаковка пересчитана',
    pack_quantity_unknown: 'проверить упаковку',
    paper_format_match: 'формат совпал',
    paper_format_mismatch: 'формат не совпал',
    paper_sheet_count_match: 'листов совпало',
    paper_sheet_count_mismatch: 'листов не совпало',
    piece_pack_count_match: 'фасовка совпала',
    piece_pack_count_mismatch: 'фасовка не совпала',
    price_break_selected: 'ступень цены выбрана',
    price_memory: 'Память цен',
    product_family_match: 'тип товара совпал',
    product_family_mismatch: 'тип товара не совпал',
    product_name_mismatch: 'товар не совпал',
    profile_intent_match: 'позиция совпала',
    strict_source_query: 'точный запрос',
    supplier_default_delivery: 'доставка по правилу',
    supplier_default_vat_included: 'НДС по правилу',
    token_overlap: 'термины совпали',
    supplier_identity: 'поставщик указан',
    unit_price: 'цена за единицу',
    unit_mismatch: 'проверить единицу',
    vat_normalized: 'НДС пересчитан',
    vat_not_included: 'НДС сверху',
    vat_unknown: 'проверить НДС',
    volume_match: 'объем совпал',
    volume_mismatch: 'объем не совпал',
    weight_match: 'вес совпал',
    weight_mismatch: 'вес не совпал',
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

export function formatQuantity(value) {
  return Number.isInteger(value) ? String(value) : String(value).replace('.', ',')
}
