import {
  confidenceLevelLabel,
  evidenceQualityLabel,
  sourceAuthorityLabel,
  sourceBindingLabel,
  sourceDocumentRoleLabel,
  sourceRoleConfidenceLabel,
  sourceTextQualityLabel,
  sourceTopicLabel,
} from './analysisFactSourceLabels'
import { cleanAnalysisText, normalizedAnalysisText, uniqueAnalysisTexts } from './analysisTextUtils'

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

function fallbackEvidenceQualityLevel(item) {
  if (item?.conflict_flags?.length) return 'conflict'
  if (item?.expected_missing) return 'missing'
  const sourceBinding = analysisSourceBinding(item)
  const confidenceLevel = analysisConfidenceLevel(item)
  if (sourceBinding.level === 'explicit' && confidenceLevel.level === 'high') return 'exact'
  if (sourceBinding.level === 'explicit' || sourceBinding.level === 'context') return 'context'
  return 'inferred'
}

function hasRealAnalysisSource(item) {
  const source = cleanAnalysisText(item?.source_label || item?.source || item?.document_name)
  return Boolean(source && !normalizedAnalysisText(source).includes(normalizedAnalysisText('Документ не привязан')))
}
