import {
  normalizeListItems,
  analysisCategoryLabel,
  analysisSeverityLabel,
  documentStatusCounts,
  documentStatusLabel,
} from './formatters'

export const MAJOR_ANALYSIS_SECTIONS = [
  { id: 'decision_risks', title: 'Итог и риски', empty: 'Критичных условий и ручных проверок пока не найдено.' },
  { id: 'product_compliance', title: 'Товар и документы', empty: 'Требования к товару и документам пока не найдены.' },
  { id: 'fulfillment_terms', title: 'Поставка и исполнение', empty: 'Условия поставки и исполнения пока не найдены.' },
  { id: 'acceptance_payment', title: 'Приемка, документы и оплата', empty: 'Условия приемки, документов и оплаты пока не найдены.' },
]

export function analysisSectionItems(analysis, documents = []) {
  return buildMajorAnalysisSections(analysis, documents).map((section) => ({
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

export function AnalysisSectionBody({ sectionId, analysis, documents = [] }) {
  const sections = buildMajorAnalysisSections(analysis, documents)
  const section = sections.find((item) => item.id === sectionId) || sections[0]
  return <AnalysisOperatorSection section={section} />
}

function buildMajorAnalysisSections(analysis, documents = []) {
  const operatorView = analysis?.operator_view
  const operatorSections = Array.isArray(operatorView?.major_blocks)
    ? operatorView.major_blocks
    : Array.isArray(operatorView?.sections)
      ? operatorView.sections
      : []
  if (operatorView?.version === 3 && operatorSections.length) {
    const sectionMap = new Map(operatorSections.map((section) => [section.id, section]))
    return MAJOR_ANALYSIS_SECTIONS.map((definition) => normalizeOperatorSection(sectionMap.get(definition.id), definition))
  }
  return legacyMajorSections(analysis, documents)
}

function normalizeOperatorSection(section, definition) {
  const items = Array.isArray(section?.items) ? section.items : []
  return {
    id: definition.id,
    title: section?.title || definition.title,
    count: section?.count ?? items.length,
    tone: section?.tone || 'default',
    empty: section?.empty || definition.empty,
    items,
  }
}

function legacyMajorSections(analysis, documents = []) {
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

  return MAJOR_ANALYSIS_SECTIONS.map((definition) => {
    const items = dedupeItems(buckets[definition.id]).sort((left, right) => (right.priority || 0) - (left.priority || 0))
    return {
      ...definition,
      count: items.length,
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

function legacyItem(item) {
  const label = item.label || 'Условие'
  const category = item.category || 'general'
  const severity = item.severity || 'medium'
  const source = item.source || ''
  return {
    id: item.id || `${item.kind || item.type || 'item'}:${label}`,
    type: item.type || item.kind || 'item',
    kind: item.kind || item.type || 'item',
    label,
    value: item.value || '',
    description: item.description || item.value || '',
    category,
    severity,
    source,
    source_label: item.source_label || source,
    source_context: item.source_context || '',
    fragment: item.fragment || '',
    impact: item.impact || '',
    operator_action: item.operator_action || fallbackOperatorAction(category),
    price_impact: item.price_impact || 'none',
    priority: item.priority || fallbackPriority(item, severity),
    status: item.status,
    is_blocker: Boolean(item.is_blocker) || severity === 'high' && ['legal', 'national_regime'].includes(category),
    is_price_factor: Boolean(item.is_price_factor) || ['acceptance', 'contract', 'delivery', 'financial', 'payment'].includes(category),
    needs_review: Boolean(item.needs_review),
  }
}

function fallbackOperatorAction(category) {
  if (['acceptance', 'financial', 'payment'].includes(category)) return 'Проверить приемку, документы и оплату.'
  if (['contract', 'delivery'].includes(category)) return 'Проверить условия поставки и исполнения.'
  if (['documents', 'standards'].includes(category)) return 'Проверить подтверждающие документы.'
  return 'Проверить условие перед решением.'
}

function fallbackPriority(item, severity) {
  if (item.needs_review) return 95
  if (item.is_blocker || severity === 'high') return 90
  if (item.kind === 'execution_term') return 60
  return 40
}

function dedupeItems(items) {
  const seen = new Set()
  return items.filter((item) => {
    const key = `${item.kind}:${item.label}:${item.fragment || item.value || ''}`.toLowerCase()
    if (seen.has(key)) return false
    seen.add(key)
    return true
  })
}

function AnalysisOperatorSection({ section }) {
  const items = Array.isArray(section.items) ? section.items : []

  return (
    <div className={`analysis-card operator-section ${section.tone || 'default'}`}>
      <div className="analysis-checklist-header">
        <span>{section.title}</span>
        <strong>{section.count ?? items.length}</strong>
      </div>
      {items.length ? (
        <div className="analysis-checklist-list">
          {items.map((item, index) => {
            const sourceLabel = item.source_label || item.source
            return (
              <article className={`analysis-checklist-row severity-${item.severity || 'medium'}`} key={item.id || `${item.label}-${index}`}>
                <div className="analysis-checklist-main">
                  <strong>{item.label}</strong>
                  <div className="analysis-checklist-tags">
                    <span>{analysisCategoryLabel(item.category)}</span>
                    <span>{analysisSeverityLabel(item.severity)}</span>
                    {item.status && <span>{operatorStatusLabel(item.status)}</span>}
                    {item.price_impact && item.price_impact !== 'none' && <span>{priceImpactLabel(item.price_impact)}</span>}
                  </div>
                </div>
                {item.description && <p>{item.description}</p>}
                {item.operator_action && <em className="analysis-evidence-impact">{item.operator_action}</em>}
                {item.impact && item.impact !== item.operator_action && <em className="analysis-evidence-impact">{item.impact}</em>}
                {sourceLabel && (
                  <div className="analysis-source-context">
                    <span>Источник</span>
                    <strong>{sourceLabel}</strong>
                    {item.source_context && <p>{item.source_context}</p>}
                    {item.fragment && <p>{item.fragment}</p>}
                  </div>
                )}
              </article>
            )
          })}
        </div>
      ) : (
        <p className="muted-text">{section.empty}</p>
      )}
    </div>
  )
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

function normalizeReasonList(items) {
  return (Array.isArray(items) ? items : [])
    .map((item) => {
      if (typeof item === 'string') return item
      if (item && typeof item === 'object') return item.label || item.text || item.value || ''
      return ''
    })
    .map((item) => item.trim())
    .filter(Boolean)
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
