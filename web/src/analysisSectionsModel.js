import { buildLegacyAnalysisSections } from './analysisLegacyAdapter'
import { buildBackendAnalysisSections } from './analysisBackendSectionsModel'
import {
  analysisItemCount,
  displayableAnalysisItems,
  isAnalysisFactItem,
} from './analysisItemDisplayModel'

export { displayableAnalysisItems, isAnalysisFactItem } from './analysisItemDisplayModel'

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
    return buildBackendAnalysisSections(operatorSections, conditionGroups)
  }
  return buildLegacyAnalysisSections(analysis, documents, MAJOR_ANALYSIS_SECTIONS)
}
