import { analysisConfidenceLevel, analysisSourceBinding } from './analysisFactSourceModel'

export { compactAnalysisFactSentence } from './analysisFactCompactTextModel'
export {
  analysisConfidenceLevel,
  analysisEvidenceQuality,
  analysisSourceAuthority,
  analysisSourceBinding,
} from './analysisFactSourceModel'
export { analysisItemTags } from './analysisFactTagModel'

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

function isBlockerAnalysisFact(item) {
  return Boolean(item?.is_blocker || item?.kind === 'blocker' || item?.kind === 'red_flag' || item?.severity === 'high' && item?.category !== 'subject')
}
