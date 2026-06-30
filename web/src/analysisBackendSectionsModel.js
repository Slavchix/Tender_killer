import { cleanAnalysisText } from './analysisTextUtils'

export function buildBackendAnalysisSections(operatorSections = [], conditionGroups = []) {
  const conditionGroupsByFactId = conditionGroupByFactId(conditionGroups)
  return (Array.isArray(operatorSections) ? operatorSections : []).map((section) => (
    normalizeOperatorSection(section, conditionGroupsByFactId)
  ))
}

function normalizeOperatorSection(section, conditionGroupsByFactId = new Map()) {
  const items = Array.isArray(section?.items)
    ? section.items.map((item) => normalizeBackendAnalysisItem(item, conditionGroupsByFactId))
    : []
  return {
    id: section?.id || 'unknown',
    title: section?.title || 'Раздел анализа',
    count: section?.count ?? items.length,
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
