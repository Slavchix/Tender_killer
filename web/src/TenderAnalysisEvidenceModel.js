export function buildDocumentEvidenceItems(analysis, documents = []) {
  const checklist = Array.isArray(analysis?.checklist) ? analysis.checklist : []

  return checklist
    .filter((item) => item?.evidence)
    .map((item, index) => ({
      id: `${item.label || 'evidence'}-${index}`,
      label: item.label || 'Фрагмент документа',
      category: item.category || 'general',
      severity: item.severity || 'medium',
      typeLabel: evidenceTypeLabel(item.category),
      importanceLabel: evidenceImportanceLabel(item.severity),
      documentName: resolveEvidenceDocumentName(item, documents),
      fragment: item.evidence,
      impact: evidenceImpactLabel(item),
    }))
}

export function evidenceTypeLabel(category) {
  return {
    documents: 'Документы',
    delivery: 'Сроки и поставка',
    acceptance: 'Приемка',
    standards: 'ГОСТ/ТУ',
    contract: 'Контракт',
    financial: 'Финансы',
    national_regime: 'Нацрежим',
    legal: 'Юридическое',
  }[category] || 'Условие'
}

export function evidenceImportanceLabel(severity) {
  return {
    high: 'важно',
    medium: 'проверить',
    low: 'к сведению',
  }[severity] || 'проверить'
}

export function evidenceImpactLabel(item = {}) {
  if (item.severity === 'high') return 'Может повлиять на решение, цену или возможность участия.'

  return {
    documents: 'Проверь, какие документы нужно приложить или получить у поставщика.',
    delivery: 'Сверь сроки с доступностью товара и логистикой.',
    acceptance: 'Учти порядок приемки при оценке исполнения.',
    standards: 'Сверь соответствие товара стандартам до расчета экономики.',
    contract: 'Учти условие в рисках исполнения и договорной подготовке.',
    financial: 'Учти в стоп-цене, резерве и решении по участию.',
    national_regime: 'Проверь ограничения происхождения и реестровые требования.',
    legal: 'Проверь допуски, лицензии или ограничения до участия.',
  }[item.category] || 'Проверь фрагмент перед принятием решения.'
}

export function resolveEvidenceDocumentName(item = {}, documents = []) {
  if (item.document_name) return item.document_name
  if (item.source) return item.source

  const readyDocuments = documents.filter((document) => document.text_status === 'ok')
  if (readyDocuments.length === 1) {
    return readyDocuments[0].name || readyDocuments[0].url || 'Документ'
  }

  return 'Документ не привязан'
}
