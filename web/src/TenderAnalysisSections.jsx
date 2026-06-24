import { useState } from 'react'
import { Ban, CheckCircle2, ClipboardCheck, XCircle } from 'lucide-react'
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

function AnalysisViewControls({ totalCount, viewMode, onViewModeChange }) {
  return (
    <div className="analysis-view-controls" aria-label="Настройки отображения анализа">
      <div className="analysis-mode-toggle" role="group" aria-label="Детализация">
        <button
          className={viewMode !== 'detailed' ? 'active' : ''}
          onClick={() => onViewModeChange?.('compact')}
          type="button"
        >
          Кратко
        </button>
        <button
          className={viewMode === 'detailed' ? 'active' : ''}
          onClick={() => onViewModeChange?.('detailed')}
          type="button"
        >
          Подробно
        </button>
      </div>
      <div className="analysis-filter-chips" role="group" aria-label="Фильтр фактов">
        <span className="active">
          <span>Все</span>
          <strong>{totalCount || 0}</strong>
        </span>
      </div>
    </div>
  )
}

function AnalysisFactCard({ item, detailed = false, onEvidenceSelect, onFeedback, savingFeedbackId, weak = false }) {
  const sourceLabel = item.source_label || item.source
  const sourceBinding = analysisSourceBinding(item)
  const confidenceLevel = analysisConfidenceLevel(item)
  const evidenceQuality = analysisEvidenceQuality(item)
  const sourceAuthority = analysisSourceAuthority(item)
  const interpretation = item.interpretation && typeof item.interpretation === 'object' ? item.interpretation : {}
  const summary = cleanAnalysisText(item.operator_summary) || cleanAnalysisText(item.description)
  const operatorCheck = cleanAnalysisText(item.operator_check) || cleanAnalysisText(item.operator_action)
  const impact = cleanAnalysisText(item.impact)
  const weakReason = cleanAnalysisText(item.weak_reason)
  const compactSentence = compactAnalysisFactSentence(item, interpretation)
  const sourceNotes = uniqueAnalysisTexts([sourceBinding.detail, confidenceLevel.detail, evidenceQuality.detail])
  const detailParts = [
    cleanAnalysisText(interpretation.found) ? ['Что найдено', cleanAnalysisText(interpretation.found)] : null,
    cleanAnalysisText(interpretation.meaning) || summary ? ['Что означает', cleanAnalysisText(interpretation.meaning) || summary] : null,
    cleanAnalysisText(interpretation.impact) || impact ? ['Влияние', cleanAnalysisText(interpretation.impact) || impact] : null,
    cleanAnalysisText(interpretation.action) || operatorCheck ? ['Что сделать', cleanAnalysisText(interpretation.action) || operatorCheck] : null,
  ].filter(Boolean)
  const sourceDetail = Boolean(
    sourceLabel ||
    sourceBinding.detail ||
    confidenceLevel.detail ||
    evidenceQuality.detail ||
    sourceAuthority.hasContext ||
    item.source_context ||
    item.fragment
  )
  return (
    <article className={`analysis-checklist-row severity-${item.severity || 'medium'} feedback-${item.feedback_state || 'none'}${weak ? ' weak' : ''}`}>
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
      {sourceDetail && onEvidenceSelect ? (
        <button className="analysis-evidence-link" onClick={() => onEvidenceSelect(item)} type="button">
          Источник
        </button>
      ) : null}
      <div className="analysis-fact-body">
        {!detailed && compactSentence ? (
          <p className="analysis-fact-line compact">
            <span>{compactSentence}</span>
          </p>
        ) : detailParts.length ? (
          <div className="analysis-fact-detail-grid">
            {detailParts.map(([label, value]) => (
              <section key={label}>
                <strong>{label}</strong>
                <p>{value}</p>
              </section>
            ))}
          </div>
        ) : null}
        {weakReason && (
          <p className="analysis-fact-warning">
            <span>Ограничение</span>
            {weakReason}
          </p>
        )}
        {item.feedback_comment && (
          <p className="analysis-feedback-note">
            <span>Комментарий оператора</span>
            {item.feedback_comment}
          </p>
        )}
        {Array.isArray(item.feedback_history) && item.feedback_history.length ? (
          <details className="analysis-feedback-history">
            <summary>История исправлений</summary>
            <ul>
              {item.feedback_history.slice(-3).map((entry, index) => (
                <li key={`${entry.changed_at || index}-${entry.to_state || index}`}>
                  {feedbackHistoryText(entry)}
                </li>
              ))}
            </ul>
          </details>
        ) : null}
      </div>
      {detailed && sourceDetail && (
        <details className="analysis-source-context" aria-label="Источник" open>
          <summary>
            <span>Источник</span>
            <strong>{sourceLabel || sourceBinding.label}</strong>
          </summary>
          <div className="analysis-source-meta">
            <span className={`analysis-source-binding-${sourceBinding.level}`}>{sourceBinding.label}</span>
            <span className={`analysis-confidence-${confidenceLevel.level}`}>{confidenceLevel.label}</span>
            <span className={`analysis-evidence-quality-${evidenceQuality.level}`}>{evidenceQuality.label}</span>
            {sourceAuthority.hasContext && (
              <span className={`analysis-source-authority-${sourceAuthority.level}`}>{sourceAuthority.label}</span>
            )}
          </div>
          {sourceNotes.map((note) => (
            <p key={note}>{note}</p>
          ))}
          {sourceAuthority.hasContext && (
            <div className="analysis-source-authority">
              <span>{sourceAuthority.label}</span>
              <p>{sourceAuthority.detail}</p>
            </div>
          )}
          {item.source_context && <p>{item.source_context}</p>}
          {item.fragment && <p>{item.fragment}</p>}
        </details>
      )}
    </article>
  )
}

function compactAnalysisFactSentence(item, interpretation = {}) {
  const label = cleanAnalysisText(item?.label) || 'Условие'
  const candidates = [
    interpretation?.found,
    item?.value,
    item?.fragment,
    item?.source_context,
    item?.evidence_summary,
  ]
  const specific = candidates
    .map((value) => cleanAnalysisText(value))
    .find((value) => isSpecificCompactFactText(label, value))
  if (specific) {
    return `${label} — ${compactFactText(specific)}`
  }
  return `${label} — точная формулировка в извлеченном тексте не найдена.`
}

function isSpecificCompactFactText(label, value) {
  if (!value) return false
  const normalizedValue = normalizedAnalysisText(value)
  const normalizedLabel = normalizedAnalysisText(label)
  if (!normalizedValue || normalizedValue === normalizedLabel) return false
  if (normalizedValue.length < 8 && !/\d/.test(normalizedValue) && !normalizedValue.includes('нет')) return false
  const genericPrefixes = [
    'это влияет',
    'это условие',
    'нужно понять',
    'условие нужно',
    'проверить',
    'найден возможный признак',
    'практический смысл',
  ]
  return !genericPrefixes.some((prefix) => normalizedValue.startsWith(prefix))
}

function compactFactText(value) {
  const text = cleanAnalysisText(value)
  const sentenceEnd = text.search(/[.!?](\s|$)/)
  const sentence = sentenceEnd > 20 ? text.slice(0, sentenceEnd + 1) : text
  if (sentence.length <= 220) return sentence
  return `${sentence.slice(0, 219).trim()}…`
}

function isWeakAnalysisFact(item) {
  if (isBlockerAnalysisFact(item)) return false
  const sourceBinding = analysisSourceBinding(item)
  const confidenceLevel = analysisConfidenceLevel(item)
  return (
    item.display_tier === 'weak' ||
    item.needs_review ||
    sourceBinding.level === 'unbound' ||
    sourceBinding.level === 'inferred' ||
    confidenceLevel.level === 'low'
  )
}

function isBlockerAnalysisFact(item) {
  return Boolean(item?.is_blocker || item?.kind === 'blocker' || item?.kind === 'red_flag' || item?.severity === 'high' && item?.category !== 'subject')
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

function analysisEvidenceQuality(item) {
  const quality = item?.evidence_quality && typeof item.evidence_quality === 'object' ? item.evidence_quality : {}
  const level = cleanAnalysisText(quality.level) || fallbackEvidenceQualityLevel(item)
  return {
    level,
    label: cleanAnalysisText(quality.label) || evidenceQualityLabel(level),
    detail: cleanAnalysisText(quality.detail),
  }
}

function analysisSourceAuthority(item) {
  const level = cleanAnalysisText(item?.context_source_authority)
  const documentRole = cleanAnalysisText(item?.context_document_role)
  const roleConfidence = cleanAnalysisText(item?.context_document_role_confidence)
  const sourcePriority = uniqueAnalysisTexts(Array.isArray(item?.context_source_priority) ? item.context_source_priority : [])
  const topics = uniqueAnalysisTexts(Array.isArray(item?.context_topics) ? item.context_topics : [])
  const mismatchFlags = uniqueAnalysisTexts(Array.isArray(item?.context_mismatch_flags) ? item.context_mismatch_flags : [])
  const textQuality = cleanAnalysisText(item?.context_text_quality)
  const reason = cleanAnalysisText(item?.context_source_reason)
  const details = uniqueAnalysisTexts([
    reason,
    documentRole ? `Роль документа: ${sourceDocumentRoleLabel(documentRole)}${roleConfidence ? ` (${sourceRoleConfidenceLabel(roleConfidence)})` : ''}` : '',
    sourcePriority.length ? `Приоритет источника: ${sourcePriority.map(sourceTopicLabel).join(', ')}` : '',
    topics.length ? `Темы документа: ${topics.map(sourceTopicLabel).join(', ')}` : '',
    mismatchFlags.length ? `Риски контекста: ${mismatchFlags.join(', ')}` : '',
    textQuality ? `Качество текста: ${sourceTextQualityLabel(textQuality)}` : '',
  ])
  return {
    level: level || 'unknown',
    label: sourceAuthorityLabel(level),
    detail: details.join(' · ') || 'Источник связан с контекстной картой документов.',
    hasContext: Boolean(level || documentRole || sourcePriority.length || topics.length || mismatchFlags.length || textQuality || reason),
  }
}

function sourceAuthorityLabel(level) {
  if (level === 'primary_for_topic') return 'главный источник по теме'
  if (level === 'primary_document') return 'основной документ'
  if (level === 'supporting_document') return 'вспомогательный источник'
  return 'контекст источника'
}

function sourceDocumentRoleLabel(role) {
  if (role === 'technical_spec' || role === 'technical_specification') return 'ТЗ'
  if (role === 'technical_spec_appendix') return 'приложение к ТЗ'
  if (role === 'contract_project') return 'проект контракта'
  if (role === 'pik_obligations_payment') return 'ПИК, оплата и приемка'
  if (role === 'participant_requirements') return 'требования к участнику'
  if (role === 'unsupported_primary') return 'основной документ без текста'
  if (role === 'other') return 'другой документ'
  return role
}

function sourceTopicLabel(topic) {
  const labels = {
    acceptance_documents: 'приемочные документы',
    acceptance_process: 'приемка',
    advance: 'аванс',
    certificates_closing_docs: 'сертификаты и закрывающие',
    contract_security: 'обеспечение контракта',
    delivery_place: 'место поставки',
    delivery_schedule: 'срок поставки',
    logistics_responsibility: 'логистика',
    participant_requirements: 'требования к участнику',
    payment_terms: 'условия оплаты',
    penalties: 'штрафы',
    technical_characteristics: 'характеристики',
    warranty: 'гарантия',
  }
  return labels[topic] || topic
}

function sourceRoleConfidenceLabel(value) {
  if (value === 'high') return 'уверенно'
  if (value === 'medium') return 'средняя уверенность'
  if (value === 'low') return 'низкая уверенность'
  return value
}

function sourceTextQualityLabel(value) {
  if (value === 'ok') return 'текст извлечен'
  if (value === 'empty') return 'текст пустой'
  if (value === 'short') return 'мало текста'
  if (value === 'unsupported') return 'формат не прочитан'
  return value
}

function fallbackEvidenceQualityLevel(item) {
  if (item?.conflict_flags?.length) return 'conflict'
  if (item?.expected_missing) return 'missing'
  const sourceBinding = analysisSourceBinding(item)
  const confidenceLevel = analysisConfidenceLevel(item)
  if (sourceBinding.level === 'explicit' && confidenceLevel.level === 'high') return 'exact'
  if (sourceBinding.level === 'explicit' || sourceBinding.level === 'context') return 'context'
  return 'inferred'
}

function evidenceQualityLabel(level) {
  if (level === 'exact') return 'точное доказательство'
  if (level === 'context') return 'контекст источника'
  if (level === 'conflict') return 'противоречие'
  if (level === 'missing') return 'не найдено'
  return 'вывод без источника'
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
  { state: 'correct', label: 'верно', icon: CheckCircle2 },
  { state: 'incorrect', label: 'неверно', icon: XCircle },
  { state: 'not_applicable', label: 'не относится к заявке', icon: Ban },
  { state: 'needs_manual_review', label: 'требует ручной проверки', icon: ClipboardCheck },
]

function AnalysisFeedbackControls({ item, onFeedback, disabled = false }) {
  const [comment, setComment] = useState(item.feedback_comment || '')
  if (!onFeedback || !item?.id) return null
  return (
    <div className="analysis-feedback-panel">
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
              onClick={() => onFeedback(item.id, active ? 'clear' : action.state, comment)}
              title={action.label}
              type="button"
            >
              <Icon aria-hidden="true" size={15} strokeWidth={2.4} />
            </button>
          )
        })}
      </div>
      <input
        className="analysis-feedback-comment"
        disabled={disabled}
        onChange={(event) => setComment(event.target.value)}
        placeholder="Комментарий оператора"
        type="text"
        value={comment}
      />
    </div>
  )
}

function feedbackHistoryText(entry = {}) {
  const toState = feedbackStateLabel(entry.to_state)
  const fromState = feedbackStateLabel(entry.from_state)
  const comment = cleanAnalysisText(entry.comment)
  const changedAt = cleanAnalysisText(entry.changed_at)
  const transition = fromState ? `${fromState} → ${toState}` : toState
  return [transition, comment, changedAt].filter(Boolean).join(' · ')
}

function feedbackStateLabel(state) {
  if (state === 'correct') return 'верно'
  if (state === 'incorrect') return 'неверно'
  if (state === 'not_applicable') return 'не относится к заявке'
  if (state === 'needs_manual_review') return 'требует ручной проверки'
  return cleanAnalysisText(state)
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
