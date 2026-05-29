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
