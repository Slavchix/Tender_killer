import {
  analysisCategoryLabel,
  analysisSeverityLabel,
  documentStatusLabel,
} from './formatters'
import { cleanAnalysisText, normalizedAnalysisText, uniqueAnalysisTexts } from './analysisTextUtils'

export function isWeakAnalysisFact(item) {
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

export function compactAnalysisFactSentence(item, interpretation = {}) {
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

export function analysisSourceBinding(item) {
  const binding = item?.source_binding && typeof item.source_binding === 'object' ? item.source_binding : {}
  const level = cleanAnalysisText(binding.level) || (item?.needs_review ? 'unbound' : hasRealAnalysisSource(item) ? 'context' : 'inferred')
  return {
    level,
    label: cleanAnalysisText(binding.label) || sourceBindingLabel(level),
    detail: cleanAnalysisText(binding.detail),
  }
}

export function analysisConfidenceLevel(item) {
  const confidence = item?.confidence_level && typeof item.confidence_level === 'object' ? item.confidence_level : {}
  const level = cleanAnalysisText(confidence.level) || (item?.needs_review ? 'low' : item?.source_context && item?.fragment ? 'high' : 'medium')
  return {
    level,
    label: cleanAnalysisText(confidence.label) || confidenceLevelLabel(level),
    detail: cleanAnalysisText(confidence.detail),
  }
}

export function analysisEvidenceQuality(item) {
  const quality = item?.evidence_quality && typeof item.evidence_quality === 'object' ? item.evidence_quality : {}
  const level = cleanAnalysisText(quality.level) || fallbackEvidenceQualityLevel(item)
  return {
    level,
    label: cleanAnalysisText(quality.label) || evidenceQualityLabel(level),
    detail: cleanAnalysisText(quality.detail),
  }
}

export function analysisSourceAuthority(item) {
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

function isBlockerAnalysisFact(item) {
  return Boolean(item?.is_blocker || item?.kind === 'blocker' || item?.kind === 'red_flag' || item?.severity === 'high' && item?.category !== 'subject')
}

function sourceBindingLabel(level) {
  if (level === 'explicit') return 'источник подтвержден'
  if (level === 'context') return 'источник по контексту'
  if (level === 'unbound') return 'нужна ручная проверка'
  return 'вывод без источника'
}

function confidenceLevelLabel(level) {
  if (level === 'high') return 'уверенность высокая'
  if (level === 'low') return 'уверенность низкая'
  return 'уверенность средняя'
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

function hasRealAnalysisSource(item) {
  const source = cleanAnalysisText(item?.source_label || item?.source || item?.document_name)
  return Boolean(source && !normalizedAnalysisText(source).includes(normalizedAnalysisText('Документ не привязан')))
}
