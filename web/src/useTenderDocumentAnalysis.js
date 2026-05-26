import { useEffect, useState } from 'react'
import {
  downloadTenderDocuments,
  extractTenderDocumentText,
  runTenderAnalysis,
} from './api'
import { documentRecordsForTender } from './formatters'

export function useTenderDocumentAnalysis(tender) {
  const [documentRecords, setDocumentRecords] = useState(documentRecordsForTender(tender))
  const [analysis, setAnalysis] = useState(tender.analysis || null)
  const [downloading, setDownloading] = useState(false)
  const [extracting, setExtracting] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [downloadStatus, setDownloadStatus] = useState('')
  const [extractStatus, setExtractStatus] = useState('')

  useEffect(() => {
    setDocumentRecords(documentRecordsForTender(tender))
    setAnalysis(tender.analysis || null)
    setDownloadStatus('')
    setExtractStatus('')
  }, [tender.source, tender.external_id, tender.analysis, tender.document_records, tender.documents])

  function downloadDocuments() {
    setDownloading(true)
    setDownloadStatus('')
    downloadTenderDocuments(tender)
      .then((payload) => {
        setDocumentRecords(payload.document_records || [])
        const firstError = payload.failed?.[0]?.error
        setDownloadStatus(
          `Скачано: ${payload.downloaded || 0}${payload.failed?.length ? `, ошибок: ${payload.failed.length}${firstError ? `: ${firstError}` : ''}` : ''}`
        )
      })
      .catch((err) => setDownloadStatus(err.message))
      .finally(() => setDownloading(false))
  }

  function extractDocumentText() {
    setExtracting(true)
    setExtractStatus('')
    extractTenderDocumentText(tender)
      .then((payload) => {
        setDocumentRecords(payload.document_records || [])
        const firstError = payload.failed?.[0]?.error
        setExtractStatus(
          `Извлечено: ${payload.extracted || 0}${payload.failed?.length ? `, ошибок: ${payload.failed.length}${firstError ? `: ${firstError}` : ''}` : ''}`
        )
      })
      .catch((err) => setExtractStatus(err.message))
      .finally(() => setExtracting(false))
  }

  function analyzeTender() {
    setAnalyzing(true)
    runTenderAnalysis(tender)
      .then((payload) => setAnalysis(payload.analysis || null))
      .catch((err) => {
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
      .finally(() => setAnalyzing(false))
  }

  return {
    documentRecords,
    setDocumentRecords,
    analysis,
    setAnalysis,
    downloading,
    extracting,
    analyzing,
    downloadStatus,
    extractStatus,
    downloadDocuments,
    extractDocumentText,
    analyzeTender,
  }
}
