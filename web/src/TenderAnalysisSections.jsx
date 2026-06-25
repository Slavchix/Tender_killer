import {
  normalizeListItems,
  analysisCategoryLabel,
  analysisSeverityLabel,
} from './formatters'
import { AnalysisFactCard, isWeakAnalysisFact } from './AnalysisFactCard'
import { AnalysisViewControls } from './AnalysisViewControls'
import { buildLegacyAnalysisSections } from './analysisLegacyAdapter'

export const MAJOR_ANALYSIS_SECTIONS = [
  { id: 'decision_risks', title: 'Итог и риски', empty: 'Критичных условий и ручных проверок пока не найдено.' },
  { id: 'product_compliance', title: 'Товар и документы', empty: 'Требования к товару и документам пока не найдены.' },
  { id: 'fulfillment_terms', title: 'Поставка и исполнение', empty: 'Условия поставки и исполнения пока не найдены.' },
  { id: 'acceptance_payment', title: 'Приемка, документы и оплата', empty: 'Условия приемки, документов и оплаты пока не найдены.' },
]

const ANALYSIS_COMPACT_LIMIT = 3

export function analysisSectionItems(analysis, documents = []) {
  return visibleMajorAnalysisSections(analysis, documents).map((section) => ({
    id: section.id,
    title: section.title,
    value: section.count ?? section.items?.length ?? 0,
  }))
}

export function AnalysisSectionRail({ sections, selectedSection, onSelectSection }) {
  return (
    <aside className="analysis-section-rail" aria-label="Разделы анализа">
      {sections.map((section) => (
        <AnalysisSectionRailItem
          active={selectedSection === section.id}
          key={section.id}
          onClick={() => onSelectSection(section.id)}
          title={section.title}
          value={section.value}
        />
      ))}
    </aside>
  )
}

export function AnalysisSectionBody({
  sectionId,
  analysis,
  documents = [],
  viewMode = 'compact',
  onViewModeChange,
  onEvidenceSelect,
  onFeedback,
  savingFeedbackId,
}) {
  const sections = visibleMajorAnalysisSections(analysis, documents)
  const section = sections.find((item) => item.id === sectionId) || sections[0]
  if (!section) {
    return (
      <div className="analysis-card operator-section default">
        <p className="muted-text">В анализе пока нет условий для отображения.</p>
      </div>
    )
  }
  return (
    <AnalysisOperatorSection
      section={section}
      viewMode={viewMode}
      onViewModeChange={onViewModeChange}
      onEvidenceSelect={onEvidenceSelect}
      onFeedback={onFeedback}
      savingFeedbackId={savingFeedbackId}
    />
  )
}

function visibleMajorAnalysisSections(analysis, documents = []) {
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
    const sectionMap = new Map(operatorSections.map((section) => [section.id, section]))
    return MAJOR_ANALYSIS_SECTIONS.map((definition) => normalizeOperatorSection(sectionMap.get(definition.id), definition, conditionGroups))
  }
  return buildLegacyAnalysisSections(analysis, documents, MAJOR_ANALYSIS_SECTIONS)
}

function normalizeOperatorSection(section, definition, conditionGroups = []) {
  const conditionGroupsByFactId = conditionGroupByFactId(conditionGroups)
  const items = Array.isArray(section?.items)
    ? section.items.map((item) => normalizeBackendAnalysisItem(item, conditionGroupsByFactId))
    : []
  return {
    id: definition.id,
    title: section?.title || definition.title,
    count: section?.count ?? analysisItemCount(items),
    tone: section?.tone || 'default',
    empty: section?.empty || definition.empty,
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

function AnalysisOperatorSection({
  section,
  viewMode = 'compact',
  onViewModeChange,
  onEvidenceSelect,
  onFeedback,
  savingFeedbackId,
}) {
  const items = displayableAnalysisItems(section.items)
  const documentSummary = items.find((item) => item.type === 'document_summary')
  const analysisItems = items.filter(isAnalysisFactItem)
  const primaryItems = analysisItems.filter((item) => !isWeakAnalysisFact(item))
  const weakItems = analysisItems.filter(isWeakAnalysisFact)
  const compact = viewMode !== 'detailed'
  const visiblePrimaryItems = compact ? primaryItems.slice(0, ANALYSIS_COMPACT_LIMIT) : primaryItems
  const hiddenPrimaryItems = compact ? primaryItems.slice(ANALYSIS_COMPACT_LIMIT) : []

  return (
    <div className={`analysis-card operator-section ${section.tone || 'default'}`}>
      <div className="analysis-checklist-header">
        <span>{section.title}</span>
        <strong>{section.count ?? analysisItems.length}</strong>
      </div>
      {documentSummary && <DocumentSummaryItem item={documentSummary} />}
      {analysisItems.length ? (
        <>
          <AnalysisViewControls
            totalCount={analysisItems.length}
            viewMode={viewMode}
            onViewModeChange={onViewModeChange}
          />
          <div className="analysis-checklist-list">
            {visiblePrimaryItems.map((item, index) => (
              <AnalysisFactCard
                detailed={!compact}
                item={item}
                key={item.id || `${item.label}-${index}`}
                onEvidenceSelect={onEvidenceSelect}
                onFeedback={onFeedback}
                savingFeedbackId={savingFeedbackId}
              />
            ))}
            {hiddenPrimaryItems.length ? (
              <details className="analysis-hidden-facts">
                <summary>Показать еще {hiddenPrimaryItems.length}</summary>
                <div className="analysis-checklist-list">
                  {hiddenPrimaryItems.map((item, index) => (
                    <AnalysisFactCard
                      detailed={!compact}
                      item={item}
                      key={item.id || `${item.label}-hidden-${index}`}
                      onEvidenceSelect={onEvidenceSelect}
                      onFeedback={onFeedback}
                      savingFeedbackId={savingFeedbackId}
                    />
                  ))}
                </div>
              </details>
            ) : null}
            {weakItems.length ? (
              <details className="analysis-weak-facts" open={!compact}>
                <summary>Слабые совпадения / ручная проверка ({weakItems.length})</summary>
                <div className="analysis-checklist-list">
                  {weakItems.map((item, index) => (
                    <AnalysisFactCard
                      detailed={!compact}
                      item={item}
                      key={item.id || `${item.label}-weak-${index}`}
                      onEvidenceSelect={onEvidenceSelect}
                      onFeedback={onFeedback}
                      savingFeedbackId={savingFeedbackId}
                      weak
                    />
                  ))}
                </div>
              </details>
            ) : null}
            {!analysisItems.length && <p className="muted-text">В анализе пока нет подтвержденных пунктов.</p>}
          </div>
        </>
      ) : (
        !documentSummary && <p className="muted-text">{section.empty}</p>
      )}
    </div>
  )
}

function DocumentSummaryItem({ item }) {
  const documents = Array.isArray(item.documents) ? item.documents : []
  return (
    <details className="analysis-document-summary">
      <summary>
        <strong>{item.label}</strong>
        <span>{item.description}</span>
      </summary>
      {documents.length ? (
        <ul>
          {documents.map((document) => (
            <li key={document}>{document}</li>
          ))}
        </ul>
      ) : null}
    </details>
  )
}

function analysisItemCount(items) {
  return displayableAnalysisItems(items).filter(isAnalysisFactItem).length
}

function displayableAnalysisItems(items = []) {
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

function isDisplayableContainerItem(item) {
  if (!item || typeof item !== 'object') return false
  if (item.type === 'document_summary') return true
  return isDisplayableAnalysisItem(item)
}

function isAnalysisFactItem(item) {
  return isDisplayableAnalysisItem(item) && item.type !== 'document' && item.type !== 'document_summary'
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

function cleanAnalysisText(value) {
  if (value === null || value === undefined) return ''
  return String(value).replace(/\s+/g, ' ').trim()
}

function uniqueAnalysisTexts(values) {
  const seen = new Set()
  return values
    .map((value) => cleanAnalysisText(value))
    .filter((value) => {
      if (!value) return false
      const key = normalizedAnalysisText(value)
      if (seen.has(key)) return false
      seen.add(key)
      return true
    })
}

function normalizedAnalysisText(value) {
  return cleanAnalysisText(value)
    .toLocaleLowerCase('ru-RU')
    .replace(/[^\wа-яё]+/giu, ' ')
    .replace(/\s+/g, ' ')
    .trim()
}

function AnalysisSectionRailItem({ title, value, active = false, onClick }) {
  return (
    <button
      aria-pressed={active}
      className={active ? 'analysis-section-item active' : 'analysis-section-item'}
      onClick={onClick}
      type="button"
    >
      <strong>{title}</strong>
      <span>{value}</span>
    </button>
  )
}

export function AnalysisList({ title, items = [], empty, danger = false }) {
  const normalizedItems = normalizeListItems(items)

  return (
    <div className={danger ? 'analysis-list danger' : 'analysis-list'}>
      <span>{title}</span>
      {normalizedItems.length ? (
        <ul>
          {normalizedItems.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      ) : (
        <p>{empty}</p>
      )}
    </div>
  )
}

export function AnalysisChecklist({ items = [] }) {
  const normalizedItems = (Array.isArray(items) ? items : [])
    .filter((item) => item && typeof item === 'object' && item.label)

  if (!normalizedItems.length) return null

  return (
    <div className="analysis-checklist">
      <div className="analysis-checklist-header">
        <span>Проверочный список</span>
        <strong>{normalizedItems.length}</strong>
      </div>
      <div className="analysis-checklist-list">
        {normalizedItems.map((item, index) => (
          <article className={`analysis-checklist-row severity-${item.severity || 'medium'}`} key={`${item.label}-${index}`}>
            <div className="analysis-checklist-main">
              <strong>{item.label}</strong>
              <div className="analysis-checklist-tags">
                <span>{analysisCategoryLabel(item.category)}</span>
                <span>{analysisSeverityLabel(item.severity)}</span>
              </div>
            </div>
            {item.evidence && <p>{item.evidence}</p>}
          </article>
        ))}
      </div>
    </div>
  )
}
