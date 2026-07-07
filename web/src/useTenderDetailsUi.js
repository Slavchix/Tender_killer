import { useEffect, useState } from 'react'

export function useTenderDetailsUi({
  tender,
  notifyStatus,
  downloadStatus,
  extractStatus,
  setNotifyStatus,
}) {
  const [detailStatus, setDetailStatus] = useState('')

  useEffect(() => {
    setNotifyStatus('')
    setDetailStatus('')
  }, [tender.source, tender.external_id])

  const statusMessages = [detailStatus, notifyStatus, downloadStatus, extractStatus].filter(Boolean)

  return {
    detailStatus,
    setDetailStatus,
    statusMessages,
  }
}
