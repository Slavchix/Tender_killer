import { cleanAnalysisText, normalizedAnalysisText } from './analysisTextUtils'

export function displayableAnalysisItems(items = []) {
  const bestByKey = new Map()
  const orderedKeys = []
  ;(Array.isArray(items) ? items : []).forEach((item) => {
    if (!isDisplayableContainerItem(item)) return
    const key = item?.backend_contract ? backendAnalysisItemKey(item) : legacyAnalysisItemKey(item)
    const current = bestByKey.get(key)
    if (!current) {
      orderedKeys.push(key)
      bestByKey.set(key, item)
      return
    }
    if (!item?.backend_contract && legacyAnalysisItemRank(item) > legacyAnalysisItemRank(current)) {
      bestByKey.set(key, item)
    }
  })
  return orderedKeys.map((key) => bestByKey.get(key)).filter(Boolean)
}

export function isAnalysisFactItem(item) {
  return isDisplayableAnalysisItem(item) && item.type !== 'document' && item.type !== 'document_summary'
}

export function analysisItemCount(items) {
  return displayableAnalysisItems(items).filter(isAnalysisFactItem).length
}

function isDisplayableContainerItem(item) {
  if (!item || typeof item !== 'object') return false
  if (item.type === 'document_summary') return true
  return isDisplayableAnalysisItem(item)
}

function isDisplayableAnalysisItem(item) {
  if (!item || typeof item !== 'object') return false
  const kind = item.kind || item.type
  if (kind === 'document' || kind === 'document_summary') return false
  if (item.backend_contract) return item.display_tier !== 'hidden'
  if (kind === 'subject') return Boolean(specificAnalysisText(item, true))
  return legacyAnalysisItemRank(item) > 0
}

function legacyAnalysisItemRank(item) {
  let score = 0
  const sourceContext = cleanAnalysisText(item?.source_context)
  const fragment = cleanAnalysisText(item?.fragment)
  const specific = specificAnalysisText(item)
  if (sourceContext) score += 90
  if (fragment) score += 80
  if (hasRealAnalysisSource(item)) score += 45
  if (specific) score += 35
  if (item?.needs_review || item?.expected_missing || Array.isArray(item?.conflict_flags) && item.conflict_flags.length) score += 20
  return score
}

function backendAnalysisItemKey(item) {
  const kind = item?.kind || item?.type || 'item'
  const id = cleanAnalysisText(item?.id)
  if (id) return `${kind}:${id}`
  const family = backendConditionFamily(item)
  return `${kind}:${family || normalizedAnalysisText(item?.label)}:${normalizedAnalysisText(item?.fragment || item?.value || item?.source_context)}`
}

function backendConditionFamily(item) {
  const families = Array.isArray(item?.condition_families) ? item.condition_families : []
  return cleanAnalysisText(item?.condition_family || families[0] || '')
}

function legacyAnalysisItemKey(item) {
  const kind = item?.kind || item?.type || 'item'
  if (kind === 'document_summary' || kind === 'subject') {
    return `${kind}:${normalizedAnalysisText(item?.id || item?.label)}`
  }
  return `${kind}:${normalizedAnalysisText(item?.label)}:${normalizedAnalysisText(item?.fragment || item?.value || item?.source_context)}`
}

function specificAnalysisText(item, allowDescription = false) {
  const label = normalizedAnalysisText(item?.label)
  const fields = allowDescription ? ['value', 'description'] : ['value']
  for (const field of fields) {
    const value = cleanAnalysisText(item?.[field])
    if (value && normalizedAnalysisText(value) !== label) return value
  }
  return ''
}

function hasRealAnalysisSource(item) {
  const source = cleanAnalysisText(item?.source_label || item?.source || item?.document_name)
  return Boolean(source && !normalizedAnalysisText(source).includes(normalizedAnalysisText('Документ не привязан')))
}
