import { buildLegacyAnalysisSections } from './analysisLegacyAdapter'
import { cleanAnalysisText, normalizedAnalysisText } from './analysisTextUtils'

export const MAJOR_ANALYSIS_SECTIONS = [
  { id: 'decision_risks', title: 'Итог и риски', empty: 'Критичных условий и ручных проверок пока не найдено.' },
  { id: 'product_compliance', title: 'Товар и документы', empty: 'Требования к товару и документам пока не найдены.' },
  { id: 'fulfillment_terms', title: 'Поставка и исполнение', empty: 'Условия поставки и исполнения пока не найдены.' },
  { id: 'acceptance_payment', title: 'Приемка, документы и оплата', empty: 'Условия приемки, документов и оплаты пока не найдены.' },
]

export function analysisSectionItems(analysis, documents = []) {
  return visibleMajorAnalysisSections(analysis, documents).map((section) => ({
    id: section.id,
    title: section.title,
    value: section.count ?? section.items?.length ?? 0,
  }))
}

export function visibleMajorAnalysisSections(analysis, documents = []) {
  const sections = buildMajorAnalysisSections(analysis, documents).map(normalizeVisibleAnalysisSection)
  const visibleSections = sections.filter(analysisSectionHasContent)
  return visibleSections.length ? visibleSections : sections.slice(0, 1)
}

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

function analysisSectionHasContent(section) {
  const items = Array.isArray(section?.items) ? section.items : []
  return items.some(isAnalysisFactItem)
}

function normalizeVisibleAnalysisSection(section) {
  const items = displayableAnalysisItems(section?.items)
  return {
    ...section,
    count: analysisItemCount(items),
    items,
  }
}

function buildMajorAnalysisSections(analysis, documents = []) {
  const operatorView = analysis?.operator_view
  const operatorSections = Array.isArray(operatorView?.major_blocks)
    ? operatorView.major_blocks
    : Array.isArray(operatorView?.sections)
      ? operatorView.sections
      : []
  if (operatorView?.version === 3 && operatorSections.length) {
    const conditionGroups = Array.isArray(operatorView?.condition_groups?.items)
      ? operatorView.condition_groups.items
      : []
    return operatorSections.map((section) => normalizeOperatorSection(section, conditionGroups))
  }
  return buildLegacyAnalysisSections(analysis, documents, MAJOR_ANALYSIS_SECTIONS)
}

function normalizeOperatorSection(section, conditionGroups = []) {
  const conditionGroupsByFactId = conditionGroupByFactId(conditionGroups)
  const items = Array.isArray(section?.items)
    ? section.items.map((item) => normalizeBackendAnalysisItem(item, conditionGroupsByFactId))
    : []
  return {
    id: section?.id || 'unknown',
    title: section?.title || 'Раздел анализа',
    count: section?.count ?? analysisItemCount(items),
    tone: section?.tone || 'default',
    empty: section?.empty || 'В разделе пока нет подтвержденных пунктов.',
    backend_contract: true,
    items,
  }
}

function conditionGroupByFactId(conditionGroups = []) {
  const groupsByFactId = new Map()
  ;(Array.isArray(conditionGroups) ? conditionGroups : []).forEach((group) => {
    if (!group || typeof group !== 'object') return
    const factIds = [group.primary_fact_id, ...(Array.isArray(group.related_fact_ids) ? group.related_fact_ids : [])]
    factIds.forEach((factId) => {
      const id = cleanAnalysisText(factId)
      if (id && !groupsByFactId.has(id)) groupsByFactId.set(id, group)
    })
  })
  return groupsByFactId
}

function normalizeBackendAnalysisItem(item, conditionGroupsByFactId) {
  if (!item || typeof item !== 'object') return item
  const conditionGroup = conditionGroupsByFactId.get(cleanAnalysisText(item.id))
  return {
    ...item,
    backend_contract: true,
    condition_family: cleanAnalysisText(item.condition_family) || cleanAnalysisText(conditionGroup?.family),
    condition_group_label: cleanAnalysisText(conditionGroup?.label),
    condition_group_status: cleanAnalysisText(conditionGroup?.status),
  }
}

function analysisItemCount(items) {
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
