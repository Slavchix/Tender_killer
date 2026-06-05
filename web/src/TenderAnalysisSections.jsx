import { CheckCircle2, EyeOff, ShieldOff, Star } from 'lucide-react'
import {
  normalizeListItems,
  analysisCategoryLabel,
  analysisSeverityLabel,
  documentStatusLabel,
} from './formatters'

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

export function AnalysisSectionBody({ sectionId, analysis, documents = [], onFeedback, savingFeedbackId }) {
  const sections = visibleMajorAnalysisSections(analysis, documents)
  const section = sections.find((item) => item.id === sectionId) || sections[0]
  if (!section) {
    return (
      <div className="analysis-card operator-section default">
        <p className="muted-text">В анализе пока нет условий для отображения.</p>
      </div>
    )
  }
  return <AnalysisOperatorSection section={section} onFeedback={onFeedback} savingFeedbackId={savingFeedbackId} />
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
    count: section?.count ?? analysisItemCount(items),
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
      count: analysisItemCount(items),
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

function AnalysisOperatorSection({ section, onFeedback, savingFeedbackId }) {
  const items = displayableAnalysisItems(section.items)
  const documentSummary = items.find((item) => item.type === 'document_summary')
  const analysisItems = items.filter(isAnalysisFactItem)

  return (
    <div className={`analysis-card operator-section ${section.tone || 'default'}`}>
      <div className="analysis-checklist-header">
        <span>{section.title}</span>
        <strong>{section.count ?? analysisItems.length}</strong>
      </div>
      {documentSummary && <DocumentSummaryItem item={documentSummary} />}
      {analysisItems.length ? (
        <div className="analysis-checklist-list">
          {analysisItems.map((item, index) => {
            const sourceLabel = item.source_label || item.source
            const sourceBinding = analysisSourceBinding(item)
            const confidenceLevel = analysisConfidenceLevel(item)
            return (
              <article className={`analysis-checklist-row severity-${item.severity || 'medium'} feedback-${item.feedback_state || 'none'}`} key={item.id || `${item.label}-${index}`}>
                <div className="analysis-checklist-main">
                  <strong>{item.label}</strong>
                  <div className="analysis-checklist-tags">
                    {analysisItemTags(item).map((tag) => (
                      <span key={tag}>{tag}</span>
                    ))}
                  </div>
                </div>
                <AnalysisFeedbackControls
                  disabled={!item.id || !onFeedback || savingFeedbackId === item.id}
                  item={item}
                  onFeedback={onFeedback}
                />
                {item.description && <p>{item.description}</p>}
                {item.operator_action && <em className="analysis-evidence-impact">{item.operator_action}</em>}
                {item.impact && item.impact !== item.operator_action && <em className="analysis-evidence-impact">{item.impact}</em>}
                {sourceLabel && (
                  <div className="analysis-source-context" aria-label="Источник">
                    <div className="analysis-source-meta">
                      <span className={`analysis-source-binding-${sourceBinding.level}`}>{sourceBinding.label}</span>
                      <span className={`analysis-confidence-${confidenceLevel.level}`}>{confidenceLevel.label}</span>
                    </div>
                    <strong>{sourceLabel}</strong>
                    {sourceBinding.detail && <p>{sourceBinding.detail}</p>}
                    {confidenceLevel.detail && <p>{confidenceLevel.detail}</p>}
                    {item.source_context && <p>{item.source_context}</p>}
                    {item.fragment && <p>{item.fragment}</p>}
                  </div>
                )}
              </article>
            )
          })}
        </div>
      ) : (
        !documentSummary && <p className="muted-text">{section.empty}</p>
      )}
    </div>
  )
}

function analysisSourceBinding(item) {
  const binding = item?.source_binding && typeof item.source_binding === 'object' ? item.source_binding : {}
  const level = cleanAnalysisText(binding.level) || (item?.needs_review ? 'unbound' : hasRealAnalysisSource(item) ? 'context' : 'inferred')
  return {
    level,
    label: cleanAnalysisText(binding.label) || sourceBindingLabel(level),
    detail: cleanAnalysisText(binding.detail),
  }
}

function sourceBindingLabel(level) {
  if (level === 'explicit') return 'источник подтвержден'
  if (level === 'context') return 'источник по контексту'
  if (level === 'unbound') return 'нужна ручная проверка'
  return 'вывод без источника'
}

function analysisConfidenceLevel(item) {
  const confidence = item?.confidence_level && typeof item.confidence_level === 'object' ? item.confidence_level : {}
  const level = cleanAnalysisText(confidence.level) || (item?.needs_review ? 'low' : item?.source_context && item?.fragment ? 'high' : 'medium')
  return {
    level,
    label: cleanAnalysisText(confidence.label) || confidenceLevelLabel(level),
    detail: cleanAnalysisText(confidence.detail),
  }
}

function confidenceLevelLabel(level) {
  if (level === 'high') return 'уверенность высокая'
  if (level === 'low') return 'уверенность низкая'
  return 'уверенность средняя'
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

function analysisItemTags(item) {
  const tags = [
    analysisCategoryLabel(item.category),
    analysisSeverityLabel(item.severity),
    item.feedback_label || '',
    item.status ? operatorStatusLabel(item.status) : '',
    item.price_impact && item.price_impact !== 'none' ? priceImpactLabel(item.price_impact) : '',
  ].filter(Boolean)
  return [...new Set(tags)]
}

const ANALYSIS_FEEDBACK_ACTIONS = [
  { state: 'confirmed', label: 'Подтвердить', icon: CheckCircle2 },
  { state: 'important', label: 'Важно', icon: Star },
  { state: 'not_risk', label: 'Не риск', icon: ShieldOff },
  { state: 'ignored', label: 'Скрыть', icon: EyeOff },
]

function AnalysisFeedbackControls({ item, onFeedback, disabled = false }) {
  if (!onFeedback || !item?.id) return null
  return (
    <div className="analysis-feedback-actions" aria-label="Метки анализа">
      {ANALYSIS_FEEDBACK_ACTIONS.map((action) => {
        const Icon = action.icon
        const active = item.feedback_state === action.state
        return (
          <button
            aria-label={action.label}
            className={active ? 'active' : ''}
            disabled={disabled}
            key={action.state}
            onClick={() => onFeedback(item.id, active ? 'clear' : action.state)}
            title={action.label}
            type="button"
          >
            <Icon aria-hidden="true" size={15} strokeWidth={2.4} />
          </button>
        )
      })}
    </div>
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
    const key = semanticAnalysisItemKey(item)
    const current = bestByKey.get(key)
    if (!current) {
      orderedKeys.push(key)
      bestByKey.set(key, item)
      return
    }
    if (analysisItemQuality(item) > analysisItemQuality(current)) {
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
  if (kind === 'subject') return Boolean(specificAnalysisText(item, true))
  return analysisItemQuality(item) > 0
}

function analysisItemQuality(item) {
  let score = 0
  const sourceContext = cleanAnalysisText(item?.source_context)
  const fragment = cleanAnalysisText(item?.fragment)
  const specific = specificAnalysisText(item)
  if (sourceContext) score += 90
  if (fragment && isRelevantAnalysisText(item, fragment)) score += 80
  if (hasRealAnalysisSource(item) && (!fragment || isRelevantAnalysisText(item, fragment) || sourceContext)) score += 45
  if (specific && isRelevantAnalysisText(item, specific)) score += 35
  return score
}

function semanticAnalysisItemKey(item) {
  const kind = item?.kind || item?.type || 'item'
  if (kind === 'document_summary' || kind === 'subject') {
    return `${kind}:${normalizedAnalysisText(item?.id || item?.label)}`
  }
  const family = analysisSemanticFamily(item)
  if (family) return `semantic:${family}`
  const detail = analysisItemQuality(item) > 0 ? normalizedAnalysisText(item?.fragment || item?.value) : ''
  return `${kind}:${normalizedAnalysisText(item?.label)}:${detail}`
}

function analysisSemanticFamily(item) {
  const category = cleanAnalysisText(item?.category)
  const text = normalizedAnalysisText(item?.label)
  if (category === 'national_regime' || text.includes('национальн') || text.includes('страна происхожд') || text.includes('страны происхожд') || text.includes('1875')) {
    return 'national_regime'
  }
  if (category === 'legal' && (text.includes('сро') || text.includes('лиценз') || text.includes('саморегулируем'))) {
    return 'license_sro'
  }
  if (text.includes('обеспечение исполнения') || text.includes('независим') || text.includes('гарант')) {
    return 'contract_security'
  }
  return ''
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

function isRelevantAnalysisText(item, value) {
  const text = normalizedAnalysisText(value)
  if (!text) return false
  const family = analysisSemanticFamily(item)
  if (family === 'national_regime') {
    return text.includes('национальн') || text.includes('страна происхожд') || text.includes('страны происхожд') || text.includes('1875')
  }
  if (family === 'license_sro') {
    return text.includes('сро') || text.includes('лиценз') || text.includes('саморегулируем')
  }
  if (family === 'contract_security') {
    return text.includes('обеспечение исполнения') || text.includes('независим') || text.includes('гарант')
  }
  const tokens = meaningfulAnalysisTokens(item?.label)
  if (!tokens.length) return true
  if (cleanAnalysisText(item?.label).includes('/') || tokens.length === 1) {
    return tokens.some((token) => text.includes(token))
  }
  return tokens.every((token) => text.includes(token))
}

function meaningfulAnalysisTokens(label) {
  return normalizedAnalysisText(label)
    .split(' ')
    .filter((token) => token.length >= 4)
}

function cleanAnalysisText(value) {
  if (value === null || value === undefined) return ''
  return String(value).replace(/\s+/g, ' ').trim()
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
