export function buildDocumentEvidenceItems(analysis, documents = []) {
  const evidenceItems = Array.isArray(analysis?.evidence_items) ? analysis.evidence_items : []

  return evidenceItems
    .filter((item) => item?.fragment)
    .map((item, index) => ({
      id: item.id || `${item.label || 'evidence'}-${index}`,
      label: item.label || 'Фрагмент документа',
      category: item.category || 'general',
      severity: item.severity || 'medium',
      typeLabel: item.type_label || 'Условие',
      importanceLabel: item.importance_label || 'проверить',
      documentName: item.document_name || 'Документ не привязан',
      fragment: item.fragment,
      impact: item.impact || 'Проверь фрагмент перед принятием решения.',
    }))
}

export function resolveEvidenceDrilldown(value, evidenceIndex = {}) {
  if (!value) return null
  if (typeof value === 'string') return evidenceByFactId(value, evidenceIndex)
  const drilldownId = value.evidence_drilldown_id || value.drilldown_id
  if (drilldownId) return evidenceById(drilldownId, evidenceIndex) || value
  if (value.fact_id) return evidenceByFactId(value.fact_id, evidenceIndex) || value
  if (value.id) return evidenceById(value.id, evidenceIndex) || value
  return value
}

export function evidenceIndexItems(evidenceIndex = {}) {
  return Array.isArray(evidenceIndex.items) ? evidenceIndex.items : []
}

export function uniqueEvidenceNotes(values) {
  const seen = new Set()
  return values
    .map((value) => String(value || '').trim())
    .filter((value) => {
      if (!value) return false
      const key = value.toLowerCase()
      if (seen.has(key)) return false
      seen.add(key)
      return true
    })
}

function evidenceByFactId(factId, evidenceIndex = {}) {
  const itemId = evidenceIndex?.by_fact_id?.[factId] || factId
  return evidenceById(itemId, evidenceIndex)
}

function evidenceById(id, evidenceIndex = {}) {
  return evidenceIndexItems(evidenceIndex).find((item) => item.id === id) || null
}
