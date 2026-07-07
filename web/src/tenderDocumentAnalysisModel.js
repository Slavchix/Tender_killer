export function documentTenderKey(tender) {
  return `${tender.source}/${tender.external_id}`
}

export function isCurrentRequest(requestRef, requestId, requestTenderKey, currentTenderKeyRef) {
  return requestRef.current === requestId && currentTenderKeyRef.current === requestTenderKey
}

export function buildDownloadDocumentsStatus(payload) {
  const skipped = payload.skipped || 0
  const firstError = payload.failed?.[0]?.error
  const statusParts = [`Скачано: ${payload.downloaded || 0}`]
  if (skipped) statusParts.push(`уже скачано: ${skipped}`)
  if (payload.failed?.length) {
    statusParts.push(`ошибок: ${payload.failed.length}${firstError ? `: ${firstError}` : ''}`)
  }
  return statusParts.join(', ')
}

export function buildExtractDocumentTextStatus(payload) {
  const firstError = payload.failed?.[0]?.error
  return `Извлечено: ${payload.extracted || 0}${payload.failed?.length ? `, ошибок: ${payload.failed.length}${firstError ? `: ${firstError}` : ''}` : ''}`
}

export function buildAnalysisErrorState(message) {
  return {
    summary: message,
    requirements: [],
    risks: [],
    red_flags: ['ошибка анализа'],
    checklist: [],
    status: 'needs_review',
    confidence: 0,
  }
}
