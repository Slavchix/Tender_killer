export function cleanAnalysisText(value) {
  if (value === null || value === undefined) return ''
  return String(value).replace(/\s+/g, ' ').trim()
}

export function normalizedAnalysisText(value) {
  return cleanAnalysisText(value)
    .toLocaleLowerCase('ru-RU')
    .replace(/[^\wа-яё]+/giu, ' ')
    .replace(/\s+/g, ' ')
    .trim()
}

export function uniqueAnalysisTexts(values) {
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
