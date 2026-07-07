import {
  analysisConfidenceLevel,
  analysisEvidenceQuality,
  analysisItemTags,
  analysisSourceAuthority,
  analysisSourceBinding,
  compactAnalysisFactSentence,
} from './analysisFactModel'
import { cleanAnalysisText, uniqueAnalysisTexts } from './analysisTextUtils'

export function buildAnalysisFactView(item = {}) {
  const sourceLabel = item.source_label || item.source
  const sourceBinding = analysisSourceBinding(item)
  const confidenceLevel = analysisConfidenceLevel(item)
  const evidenceQuality = analysisEvidenceQuality(item)
  const sourceAuthority = analysisSourceAuthority(item)
  const interpretation = item.interpretation && typeof item.interpretation === 'object' ? item.interpretation : {}
  const detailParts = buildAnalysisFactDetailParts(item, interpretation)
  const sourceNotes = uniqueAnalysisTexts([sourceBinding.detail, confidenceLevel.detail, evidenceQuality.detail])

  return {
    compactSentence: compactAnalysisFactSentence(item, interpretation),
    confidenceLevel,
    detailParts,
    evidenceQuality,
    feedbackComment: cleanAnalysisText(item.feedback_comment),
    feedbackHistory: Array.isArray(item.feedback_history) ? item.feedback_history : [],
    sourceAuthority,
    sourceBinding,
    sourceDetail: hasAnalysisFactSourceDetail(item, sourceLabel, sourceBinding, confidenceLevel, evidenceQuality, sourceAuthority),
    sourceLabel,
    sourceNotes,
    tags: analysisItemTags(item),
    weakReason: cleanAnalysisText(item.weak_reason),
  }
}

function buildAnalysisFactDetailParts(item, interpretation = {}) {
  const summary = cleanAnalysisText(item.operator_summary) || cleanAnalysisText(item.description)
  const operatorCheck = cleanAnalysisText(item.operator_check) || cleanAnalysisText(item.operator_action)
  const impact = cleanAnalysisText(item.impact)

  return [
    cleanAnalysisText(interpretation.found) ? ['Что найдено', cleanAnalysisText(interpretation.found)] : null,
    cleanAnalysisText(interpretation.meaning) || summary ? ['Что означает', cleanAnalysisText(interpretation.meaning) || summary] : null,
    cleanAnalysisText(interpretation.impact) || impact ? ['Влияние', cleanAnalysisText(interpretation.impact) || impact] : null,
    cleanAnalysisText(interpretation.action) || operatorCheck ? ['Что сделать', cleanAnalysisText(interpretation.action) || operatorCheck] : null,
  ].filter(Boolean)
}

function hasAnalysisFactSourceDetail(item, sourceLabel, sourceBinding, confidenceLevel, evidenceQuality, sourceAuthority) {
  return Boolean(
    sourceLabel ||
    sourceBinding.detail ||
    confidenceLevel.detail ||
    evidenceQuality.detail ||
    sourceAuthority.hasContext ||
    item.source_context ||
    item.fragment
  )
}
