import { useEffect, useRef, useState } from 'react'
import { refreshTenderDetails } from './api'
import { shouldAutoRefreshDetails } from './formatters'

const AUTO_REFRESH_MESSAGE = 'Автоматически добираю позиции и классификаторы...'
const NO_DETAIL_CHANGE_MESSAGE = 'Источник не вернул новые детали; оставил сохраненные данные.'

export function useTenderRefreshDetails({
  tender,
  onTenderRefresh,
  setDetailStatus,
  setDocumentRecords,
  setAnalysis,
  applyProductTenderState,
}) {
  const autoRefreshKey = useRef('')
  const [refreshingDetails, setRefreshingDetails] = useState(false)

  useEffect(() => {
    const key = `${tender.source}/${tender.external_id}`
    if (!shouldAutoRefreshDetails(tender) || autoRefreshKey.current === key) return
    autoRefreshKey.current = key
    refreshDetails({ automatic: true })
  }, [tender.source, tender.external_id, tender.items?.length])

  function refreshDetails(options = {}) {
    setRefreshingDetails(true)
    setDetailStatus(options.automatic ? AUTO_REFRESH_MESSAGE : '')
    refreshTenderDetails(tender)
      .then((payload) => {
        const nextTender = payload.tender || tender
        onTenderRefresh(nextTender)
        setDocumentRecords(nextTender.document_records || [])
        setAnalysis(nextTender.analysis || null)
        applyProductTenderState(nextTender)
        const summary = payload.summary || {}
        if (!payload.refreshed && options.automatic) {
          setDetailStatus('')
          return
        }
        setDetailStatus(
          payload.refreshed
            ? `${options.automatic ? 'Автообновление: ' : 'Обновлено: '}позиций ${summary.items_count || 0}, документов ${summary.documents_count || 0}, профилей ${summary.product_profiles_count || 0}`
            : NO_DETAIL_CHANGE_MESSAGE
        )
      })
      .catch((err) => setDetailStatus(err.message))
      .finally(() => setRefreshingDetails(false))
  }

  return {
    refreshingDetails,
    refreshDetails,
  }
}
