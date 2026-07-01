export function legacyItem(item) {
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

export function legacyAnalysisItemCount(items) {
  return (Array.isArray(items) ? items : []).filter((item) => item?.kind !== 'document' && item?.type !== 'document').length
}

export function dedupeItems(items) {
  const seen = new Set()
  return items.filter((item) => {
    const key = `${item.kind}:${item.label}:${item.fragment || item.value || ''}`.toLowerCase()
    if (seen.has(key)) return false
    seen.add(key)
    return true
  })
}

export function normalizeReasonList(items) {
  return (Array.isArray(items) ? items : [])
    .map((item) => {
      if (typeof item === 'string') return item
      if (item && typeof item === 'object') return item.label || item.text || item.value || ''
      return ''
    })
    .map((item) => item.trim())
    .filter(Boolean)
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
