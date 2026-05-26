import { useEffect, useState } from 'react'

export function useTenderDetailsUi({
  tender,
  notifyStatus,
  downloadStatus,
  extractStatus,
  setNotifyStatus,
}) {
  const raw = safeJson(tender.raw_payload_json)
  const [activeTab, setActiveTab] = useState('overview')
  const [detailStatus, setDetailStatus] = useState('')

  useEffect(() => {
    setActiveTab('overview')
    setNotifyStatus('')
    setDetailStatus('')
  }, [tender.source, tender.external_id])

  const statusMessages = [detailStatus, notifyStatus, downloadStatus, extractStatus].filter(Boolean)

  return {
    raw,
    activeTab,
    setActiveTab,
    detailStatus,
    setDetailStatus,
    statusMessages,
  }
}

function safeJson(value) {
  try {
    return JSON.parse(value || '{}')
  } catch {
    return {}
  }
}
