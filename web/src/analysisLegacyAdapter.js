export function buildLegacyAnalysisSections(analysis, documents = [], definitions = []) {
  const buckets = {
    decision_risks: [],
    product_compliance: [],
    fulfillment_terms: [],
    acceptance_payment: [],
  }
  if (analysis?.summary) {
    buckets.product_compliance.push(legacyItem({
      id: 'subject:summary',
      kind: 'subject',
      label: 'Предмет',
      value: analysis.summary,
      category: 'subject',
    }))
  }

  normalizeReasonList(analysis?.red_flags).forEach((label) => {
    buckets.decision_risks.push(legacyItem({ kind: 'red_flag', label, category: 'legal', severity: 'high', is_blocker: true }))
  })
  normalizeReasonList(analysis?.risks).forEach((label) => {
    buckets.decision_risks.push(legacyItem({ kind: 'risk', label, category: 'general', severity: 'medium' }))
  })
  normalizeReasonList(analysis?.requirements).forEach((label) => {
    buckets.product_compliance.push(legacyItem({ kind: 'requirement', label, category: 'general', severity: 'medium' }))
  })
  ;(Array.isArray(analysis?.checklist) ? analysis.checklist : []).forEach((item, index) => {
    const normalized = legacyItem({
      id: item.id || `checklist:${index}`,
      kind: item.kind || 'requirement',
      label: item.label,
      value: item.value || item.evidence,
      fragment: item.fragment || item.evidence,
      category: item.category,
      severity: item.severity,
      source: item.document_name || item.source,
      source_label: item.source_label,
      source_context: item.source_context,
      impact: item.impact,
      is_blocker: item.is_blocker,
      is_price_factor: item.is_price_factor,
    })
    bucketForLegacyItem(normalized, buckets).push(normalized)
  })
  ;(Array.isArray(analysis?.execution_terms) ? analysis.execution_terms : []).forEach((item, index) => {
    const normalized = legacyItem({
      id: item.id || `execution_term:${item.type || index}`,
      kind: 'execution_term',
      label: item.label,
      value: item.value || item.evidence,
      fragment: item.fragment || item.evidence,
      category: item.category,
      severity: item.severity,
      source: item.document_name || item.source,
      source_label: item.source_label,
      source_context: item.source_context,
      impact: item.impact,
      is_price_factor: true,
    })
    bucketForLegacyItem(normalized, buckets).push(normalized)
  })

  documents.forEach((document, index) => {
    const status = document.text_status || 'pending'
    buckets.product_compliance.push(legacyItem({
      id: `document:${index + 1}`,
      kind: 'document',
      type: 'document',
      label: document.name || document.url || `Документ ${index + 1}`,
      category: document.document_type || 'documents',
      severity: status === 'ok' ? 'medium' : 'high',
      status: status === 'ok' ? 'ok' : 'attention',
      description: status === 'ok' ? 'Текст готов для анализа.' : 'Документ требует внимания или извлечения текста.',
    }))
  })

  return definitions.map((definition) => {
    const items = dedupeItems(buckets[definition.id]).sort((left, right) => (right.priority || 0) - (left.priority || 0))
    return {
      ...definition,
      count: legacyAnalysisItemCount(items),
      tone: definition.id === 'decision_risks' && items.length ? 'danger' : 'default',
      items,
    }
  })
}

function bucketForLegacyItem(item, buckets) {
  if (item.needs_review || item.is_blocker || ['blocker', 'risk', 'red_flag'].includes(item.kind)) return buckets.decision_risks
  if (['acceptance', 'financial', 'payment'].includes(item.category)) return buckets.acceptance_payment
  if (['contract', 'delivery'].includes(item.category) || item.kind === 'execution_term') return buckets.fulfillment_terms
  return buckets.product_compliance
}

function legacyItem(item) {
  const label = item.label || 'Условие'
  const category = item.category || 'general'
  const severity = item.severity || 'medium'
  const source = item.source || ''
  return {
    id: item.id || `${item.kind || item.type || 'item'}:${label}`,
    type: item.type || item.kind || 'item',
    kind: item.kind || item.type || 'item',
    label,
    value: item.value || '',
    description: item.description || item.value || '',
    category,
    severity,
    source,
    source_label: item.source_label || source,
    source_context: item.source_context || '',
    fragment: item.fragment || '',
    impact: item.impact || '',
    operator_action: item.operator_action || fallbackOperatorAction(category),
    price_impact: item.price_impact || 'none',
    priority: item.priority || fallbackPriority(item, severity),
    status: item.status,
    is_blocker: Boolean(item.is_blocker) || severity === 'high' && ['legal', 'national_regime'].includes(category),
    is_price_factor: Boolean(item.is_price_factor) || ['acceptance', 'contract', 'delivery', 'financial', 'payment'].includes(category),
    needs_review: Boolean(item.needs_review),
  }
}

function fallbackOperatorAction(category) {
  if (['acceptance', 'financial', 'payment'].includes(category)) return 'Проверить приемку, документы и оплату.'
  if (['contract', 'delivery'].includes(category)) return 'Проверить условия поставки и исполнения.'
  if (['documents', 'standards'].includes(category)) return 'Проверить подтверждающие документы.'
  return 'Проверить условие перед решением.'
}

function fallbackPriority(item, severity) {
  if (item.needs_review) return 95
  if (item.is_blocker || severity === 'high') return 90
  if (item.kind === 'execution_term') return 60
  return 40
}

function legacyAnalysisItemCount(items) {
  return (Array.isArray(items) ? items : []).filter((item) => item?.kind !== 'document' && item?.type !== 'document').length
}

function dedupeItems(items) {
  const seen = new Set()
  return items.filter((item) => {
    const key = `${item.kind}:${item.label}:${item.fragment || item.value || ''}`.toLowerCase()
    if (seen.has(key)) return false
    seen.add(key)
    return true
  })
}

function normalizeReasonList(items) {
  return (Array.isArray(items) ? items : [])
    .map((item) => {
      if (typeof item === 'string') return item
      if (item && typeof item === 'object') return item.label || item.text || item.value || ''
      return ''
    })
    .map((item) => item.trim())
    .filter(Boolean)
}
