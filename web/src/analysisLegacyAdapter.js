import {
  dedupeItems,
  legacyAnalysisItemCount,
  legacyItem,
  normalizeReasonList,
} from './analysisLegacyItemModel'

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
