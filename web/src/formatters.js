export function normalizeListItems(items = []) {
  return (Array.isArray(items) ? items : [items])
    .map((item) => {
      if (item === null || item === undefined || item === '') return ''
      if (typeof item === 'string') return item
      if (typeof item === 'number') return String(item)
      return JSON.stringify(item)
    })
    .filter(Boolean)
}

export function formatFulfillmentRequirements(items = []) {
  return (Array.isArray(items) ? items : [])
    .filter((item) => item && typeof item === 'object' && item.value)
    .map((item) => {
      const typeLabel = fulfillmentRequirementTypeLabel(item.type)
      const source = item.source ? ` · ${item.source}` : ''
      return `${typeLabel}: ${item.value}${source}`
    })
}

export function fulfillmentRequirementTypeLabel(type) {
  const labels = {
    acceptance: 'приемка',
    delivery: 'доставка',
    packaging: 'упаковка',
    warranty: 'гарантия',
  }
  return labels[type] || type || 'исполнение'
}

export function analysisCategoryLabel(category) {
  const labels = {
    acceptance: 'приемка',
    contract: 'контракт',
    delivery: 'доставка',
    documents: 'документы',
    financial: 'финансы',
    legal: 'право',
    national_regime: 'нацрежим',
    standards: 'стандарты',
  }
  return labels[category] || category || 'общее'
}

export function analysisSeverityLabel(severity) {
  const labels = {
    high: 'важно',
    medium: 'проверить',
    low: 'низкий риск',
  }
  return labels[severity] || severity || 'проверить'
}

export function shouldAutoRefreshDetails(tender) {
  if (!tender?.source || !tender?.external_id) return false
  if (Array.isArray(tender.items) && tender.items.length > 0) return false
  return ['mosreg_market', 'moscow_supplier_portal'].includes(tender.source)
}

export function formatMoney(value) {
  const number = Number(value)
  if (!Number.isFinite(number)) return 'не указана'
  return new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB', maximumFractionDigits: 0 }).format(number)
}

export function formatSignedMoney(value) {
  const number = Number(value)
  if (!Number.isFinite(number)) return 'не указана'
  const sign = number > 0 ? '+' : ''
  return `${sign}${formatMoney(number)}`
}

export function formatSignedPercent(value) {
  const number = Number(value)
  if (!Number.isFinite(number)) return 'не указано'
  const sign = number > 0 ? '+' : ''
  return `${sign}${new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 2 }).format(number)}%`
}

export function formatPriceChangeDirection(change) {
  const direction = change?.direction || 'changed'
  if (change?.price_kind === 'current_offer') {
    if (direction === 'decreased') return 'участник снизил цену'
    if (direction === 'increased') return 'участник повысил цену'
    return 'цена участника изменилась'
  }
  if (direction === 'decreased') return 'НМЦК снизилась'
  if (direction === 'increased') return 'НМЦК выросла'
  return 'НМЦК изменилась'
}

export function formatAmount(quantity, unit) {
  const number = Number(quantity)
  const amount = Number.isFinite(number)
    ? new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 4 }).format(number)
    : 'не указано'
  return unit ? `${amount} ${unit}` : amount
}

export function formatQuantity(quantity, unit) {
  return formatAmount(quantity, unit)
}

export function profileStatusLabel(status) {
  return {
    draft: 'Черновик',
    needs_review: 'Проверить',
    ready: 'Готов',
    searching: 'Поиск',
    matched: 'Найдено',
    priced: 'Расчет',
    rejected: 'Отклонено',
  }[status] || 'Черновик'
}

export function formatConfidence(value) {
  const number = Number(value)
  if (!Number.isFinite(number)) return 'не указана'
  return `${Math.round(number * 100)}%`
}

export function analysisStatusLabel(status) {
  return {
    needs_review: 'Нужна проверка',
    interesting: 'Интересно',
    skipped: 'Пропустить',
  }[status] || status || 'Нужна проверка'
}

export function economicsStatusLabel(status) {
  return {
    interesting: 'Интересно',
    manual_review: 'Проверить',
    low_margin: 'Низкая маржа',
    needs_costs: 'Нужны цены',
    needs_price: 'Нужна НМЦК',
  }[status] || status || 'Проверить'
}

export function economicsDecisionLabel(economics) {
  if (!economics) return 'нет расчета'
  if (economics?.participation_decision?.label) return economics.participation_decision.label
  return economicsStatusLabel(economics?.status)
}

export function marketStateValue(marketState) {
  const currentOffer = Number(marketState?.current_offer_price)
  const bidCount = Number(marketState?.bid_count)
  const bidText = formatBidCount(bidCount)
  if (Number.isFinite(currentOffer)) return bidText ? `${formatMoney(currentOffer)} · ${bidText}` : formatMoney(currentOffer)
  const participantCount = Number(marketState?.participant_count)
  if (Number.isFinite(bidCount) && bidCount > 0) return `${bidText}, цена скрыта`
  if (marketState?.status === 'no_participants' || participantCount === 0) return 'участников нет'
  if (Number.isFinite(participantCount) && participantCount > 0) return `${participantCount} участн., цена скрыта`
  return 'нет данных'
}

export function participantBidValue(marketState) {
  const currentOffer = Number(marketState?.current_offer_price)
  const bidCount = Number(marketState?.bid_count)
  const bidText = formatBidCount(bidCount)
  if (Number.isFinite(currentOffer)) return bidText ? `${formatMoney(currentOffer)} · ${bidText}` : formatMoney(currentOffer)
  const participantCount = Number(marketState?.participant_count)
  if (Number.isFinite(bidCount) && bidCount > 0) return `цена скрыта · ${bidText}`
  if (marketState?.status === 'no_participants' || participantCount === 0) return 'участников нет'
  if (Number.isFinite(participantCount) && participantCount > 0) return 'цена скрыта'
  return 'нет данных'
}

export function marketStateCaption(marketState) {
  const participantCount = Number(marketState?.participant_count)
  const bidCount = Number(marketState?.bid_count)
  if (Number.isFinite(Number(marketState?.current_offer_price))) {
    if (Number.isFinite(bidCount) && bidCount > 0) {
      return bidCount > 1 ? `минимальная из ${formatBidCount(bidCount)}` : formatBidCount(bidCount)
    }
    return Number.isFinite(participantCount) ? `участников: ${participantCount}` : 'цена участника'
  }
  if (marketState?.status === 'no_participants' || participantCount === 0) return 'ставок нет'
  if (Number.isFinite(participantCount) && participantCount > 0) return 'участники есть, цена не раскрыта'
  return 'рыночных данных нет'
}

function formatBidCount(value) {
  if (!Number.isFinite(value) || value <= 0) return ''
  const count = Math.round(value)
  const mod10 = count % 10
  const mod100 = count % 100
  if (mod10 === 1 && mod100 !== 11) return `${count} ставка`
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return `${count} ставки`
  return `${count} ставок`
}

export function tenderDecisionNextStep(tender, economics) {
  if (!economics) return 'обновить детали и цены'
  if (economics.status === 'needs_costs') return 'добавить себестоимость'
  if (economics.status === 'needs_price') return 'проверить НМЦК'
  if (economics.status === 'low_margin') return 'оценить отказ'
  if ((tender.product_profiles || []).some((profile) => !profile.raw_payload?.supplier_options?.length)) {
    return 'добавить поставщиков'
  }
  if (economics.status === 'interesting') return 'вести в работу'
  return 'проверить риски'
}

export function supplierAvailabilityLabel(value) {
  return {
    unknown: 'наличие неясно',
    in_stock: 'в наличии',
    on_request: 'под заказ',
    not_available: 'нет',
  }[value] || value || 'наличие неясно'
}

export function supplierStatusLabel(value) {
  return {
    candidate: 'кандидат',
    selected: 'в расчете',
    suitable: 'подходит',
    rejected: 'не подходит',
  }[value] || value || 'кандидат'
}

export function supplierConfidenceLabel(value) {
  return {
    confirmed: 'подтверждено',
    high: 'высокая уверенность',
    medium: 'требует проверки',
    needs_review: 'требует проверки',
  }[value] || 'требует проверки'
}

export function taxModeLabel(mode, vatRate) {
  const labels = {
    no_vat: 'без НДС',
    unknown: 'проверить',
    vat_excluded: 'НДС сверху',
    vat_included: 'НДС включен',
  }
  const label = labels[mode] || mode || 'проверить'
  return vatRate === null || vatRate === undefined ? label : `${label} · ${formatPercent(vatRate)}`
}

export function formatCostDriver(driver) {
  if (!driver || typeof driver !== 'object') return ''
  const label = costDriverLabel(driver.type)
  return `${label}: ${formatMoney(driver.amount)} · ${formatPercent(driver.rate_percent)}`
}

export function costDriverLabel(type) {
  return {
    acceptance: 'приемка',
    certificates: 'сертификаты',
    contract_security: 'обеспечение',
    delivery: 'доставка',
    national_regime: 'нацрежим',
    packaging: 'упаковка',
    payment_delay: 'отсрочка оплаты',
    penalties: 'штрафы',
    short_deadline: 'короткий срок',
    unloading: 'разгрузка',
    warranty: 'гарантия',
  }[type] || type || 'расход'
}

export function formatPercent(value) {
  const number = Number(value)
  if (!Number.isFinite(number)) return 'не указано'
  return `${new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 2 }).format(number)}%`
}

export function formatDateTime(value) {
  if (!value) return 'нет'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

export function formatDate(value) {
  if (!value) return 'не указан'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat('ru-RU', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }).format(date)
}

export function formatDbCell(value) {
  if (value === null || value === undefined || value === '') return '—'
  if (typeof value === 'number') return new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 4 }).format(value)
  const text = typeof value === 'string' ? value : JSON.stringify(value)
  return text.length > 180 ? `${text.slice(0, 180)}...` : text
}

export function documentLabel(url) {
  try {
    const parsed = new URL(url)
    const queryName = parsed.searchParams.get('fileName') || parsed.searchParams.get('name')
    if (queryName) return queryName
    const fileName = decodeURIComponent(parsed.pathname.split('/').filter(Boolean).pop() || '')
    return fileName && fileName.includes('.') ? fileName : url
  } catch {
    return url
  }
}

export function documentStatusLabel(status) {
  return {
    pending: 'ожидает',
    downloaded: 'скачан, текст не извлечен',
    ok: 'текст извлечен',
    empty: 'текст не найден',
    unsupported: 'формат не поддержан',
    missing_file: 'файл не найден',
  }[status] || status || 'ожидает'
}

export function documentStatusCounts(documents) {
  return (documents || []).reduce((counts, document) => {
    const status = document.text_status || 'pending'
    counts.total += 1
    if (document.local_path) counts.downloaded += 1
    if (status === 'ok') counts.ok += 1
    if (status !== 'ok') counts.attention += 1
    return counts
  }, { total: 0, downloaded: 0, ok: 0, attention: 0 })
}

export function documentTextPreview(value) {
  const text = String(value || '').replace(/\s+/g, ' ').trim()
  return text.length > 420 ? `${text.slice(0, 420)}...` : text
}

export function documentRecordsForTender(tender) {
  if (tender.document_records?.length) return tender.document_records
  return (tender.documents || []).map((url, index) => ({
    document_index: index + 1,
    name: documentLabel(url),
    document_type: '',
    url,
    local_path: '',
    text_status: 'pending',
  }))
}
