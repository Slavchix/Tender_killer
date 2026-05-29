import { useEffect, useRef, useState } from 'react'
import {
  downloadTenderDocuments,
  extractTenderDocumentText,
  runTenderAnalysis,
} from './api'
import { documentRecordsForTender } from './formatters'

export function useTenderDocumentAnalysis(tender) {
  const currentTenderKey = documentTenderKey(tender)
  const currentTenderKeyRef = useRef(currentTenderKey)
  const downloadRequestRef = useRef(null)
  const extractRequestRef = useRef(null)
  const analysisRequestRef = useRef(null)
  const prepareRequestRef = useRef(null)
  const [documentRecords, setDocumentRecords] = useState(documentRecordsForTender(tender))
  const [analysis, setAnalysis] = useState(tender.analysis || null)
  const [downloading, setDownloading] = useState(false)
  const [extracting, setExtracting] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [preparingAnalysis, setPreparingAnalysis] = useState(false)
  const [downloadStatus, setDownloadStatus] = useState('')
  const [extractStatus, setExtractStatus] = useState('')

  currentTenderKeyRef.current = currentTenderKey

  useEffect(() => {
    downloadRequestRef.current = null
    extractRequestRef.current = null
    analysisRequestRef.current = null
    prepareRequestRef.current = null
    setDocumentRecords(documentRecordsForTender(tender))
    setAnalysis(tender.analysis || null)
    setDownloading(false)
    setExtracting(false)
    setAnalyzing(false)
    setPreparingAnalysis(false)
    setDownloadStatus('')
    setExtractStatus('')
  }, [tender.source, tender.external_id, tender.analysis, tender.document_records, tender.documents])

  function downloadDocuments() {
    const requestTenderKey = currentTenderKeyRef.current
    const requestId = Symbol('download-documents')
    downloadRequestRef.current = requestId
    setDownloading(true)
    setDownloadStatus('')
    return downloadTenderDocuments(tender)
      .then((payload) => {
        if (!isCurrentRequest(downloadRequestRef, requestId, requestTenderKey, currentTenderKeyRef)) return
        setDocumentRecords(payload.document_records || [])
        const skipped = payload.skipped || 0
        const firstError = payload.failed?.[0]?.error
        const statusParts = [`Скачано: ${payload.downloaded || 0}`]
        if (skipped) statusParts.push(`уже скачано: ${skipped}`)
        if (payload.failed?.length) {
          statusParts.push(`ошибок: ${payload.failed.length}${firstError ? `: ${firstError}` : ''}`)
        }
        setDownloadStatus(statusParts.join(', '))
      })
      .catch((err) => {
        if (!isCurrentRequest(downloadRequestRef, requestId, requestTenderKey, currentTenderKeyRef)) return
        setDownloadStatus(err.message)
      })
      .finally(() => {
        if (!isCurrentRequest(downloadRequestRef, requestId, requestTenderKey, currentTenderKeyRef)) return
        setDownloading(false)
      })
  }

  function extractDocumentText() {
    const requestTenderKey = currentTenderKeyRef.current
    const requestId = Symbol('extract-document-text')
    extractRequestRef.current = requestId
    setExtracting(true)
    setExtractStatus('')
    return extractTenderDocumentText(tender)
      .then((payload) => {
        if (!isCurrentRequest(extractRequestRef, requestId, requestTenderKey, currentTenderKeyRef)) return
        setDocumentRecords(payload.document_records || [])
        const firstError = payload.failed?.[0]?.error
        setExtractStatus(
          `Извлечено: ${payload.extracted || 0}${payload.failed?.length ? `, ошибок: ${payload.failed.length}${firstError ? `: ${firstError}` : ''}` : ''}`
        )
      })
      .catch((err) => {
        if (!isCurrentRequest(extractRequestRef, requestId, requestTenderKey, currentTenderKeyRef)) return
        setExtractStatus(err.message)
      })
      .finally(() => {
        if (!isCurrentRequest(extractRequestRef, requestId, requestTenderKey, currentTenderKeyRef)) return
        setExtracting(false)
      })
  }

  function analyzeTender() {
    const requestTenderKey = currentTenderKeyRef.current
    const requestId = Symbol('analyze-tender')
    analysisRequestRef.current = requestId
    setAnalyzing(true)
    return runTenderAnalysis(tender)
      .then((payload) => {
        if (!isCurrentRequest(analysisRequestRef, requestId, requestTenderKey, currentTenderKeyRef)) return
        setAnalysis(payload.analysis || null)
      })
      .catch((err) => {
        if (!isCurrentRequest(analysisRequestRef, requestId, requestTenderKey, currentTenderKeyRef)) return
        setAnalysis({
          summary: err.message,
          requirements: [],
          risks: [],
          red_flags: ['ошибка анализа'],
          checklist: [],
          status: 'needs_review',
          confidence: 0,
        })
      })
      .finally(() => {
        if (!isCurrentRequest(analysisRequestRef, requestId, requestTenderKey, currentTenderKeyRef)) return
        setAnalyzing(false)
      })
  }

  async function prepareTenderAnalysis() {
    const requestTenderKey = currentTenderKeyRef.current
    const requestId = Symbol('prepare-analysis')
    prepareRequestRef.current = requestId
    setPreparingAnalysis(true)
    try {
      await downloadDocuments()
      if (!isCurrentRequest(prepareRequestRef, requestId, requestTenderKey, currentTenderKeyRef)) return
      await extractDocumentText()
      if (!isCurrentRequest(prepareRequestRef, requestId, requestTenderKey, currentTenderKeyRef)) return
      await analyzeTender()
    } finally {
      if (!isCurrentRequest(prepareRequestRef, requestId, requestTenderKey, currentTenderKeyRef)) return
      setPreparingAnalysis(false)
    }
  }

  return {
    documentRecords,
    setDocumentRecords,
    analysis,
    setAnalysis,
    downloading,
    extracting,
    analyzing,
    preparingAnalysis,
    downloadStatus,
    extractStatus,
    downloadDocuments,
    extractDocumentText,
    analyzeTender,
    prepareTenderAnalysis,
  }
}

function documentTenderKey(tender) {
  return `${tender.source}/${tender.external_id}`
}

function isCurrentRequest(requestRef, requestId, requestTenderKey, currentTenderKeyRef) {
  return requestRef.current === requestId && currentTenderKeyRef.current === requestTenderKey
}
