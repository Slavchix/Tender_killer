import {
  analysisCategoryLabel,
  analysisSeverityLabel,
  documentStatusLabel,
} from './formatters'

export function analysisItemTags(item) {
  const tags = [
    analysisCategoryLabel(item.category),
    analysisSeverityLabel(item.severity),
    item.feedback_label || '',
    item.status ? operatorStatusLabel(item.status) : '',
    item.price_impact && item.price_impact !== 'none' ? priceImpactLabel(item.price_impact) : '',
  ].filter(Boolean)
  return [...new Set(tags)]
}

function operatorStatusLabel(status) {
  if (status === 'attention') return 'проверить'
  return documentStatusLabel(status)
}

function priceImpactLabel(value) {
  if (value === 'logistics') return 'логистика'
  if (value === 'working_capital') return 'деньги'
  if (value === 'documents') return 'документы'
  if (value === 'reserve') return 'резерв'
  if (value === 'compliance') return 'соответствие'
  return value
}
