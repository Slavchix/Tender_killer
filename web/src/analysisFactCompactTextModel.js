import { cleanAnalysisText, normalizedAnalysisText } from './analysisTextUtils'

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
