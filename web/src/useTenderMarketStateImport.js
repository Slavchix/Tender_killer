import { useEffect, useState } from 'react'
import { importTenderMarketState } from './api'

export function useTenderMarketStateImport({
  tender,
  onTenderRefresh,
  setDetailStatus,
  applyProductTenderState,
}) {
  const [marketImportText, setMarketImportText] = useState('')
  const [importingMarketState, setImportingMarketState] = useState(false)

  useEffect(() => {
    setMarketImportText('')
    setImportingMarketState(false)
  }, [tender.source, tender.external_id])

  function importMarketState(event) {
    event?.preventDefault()
    let payload
    try {
      payload = JSON.parse(marketImportText || '{}')
    } catch {
      setDetailStatus('JSON ответа не прочитан')
      return null
    }
    setImportingMarketState(true)
    setDetailStatus('')
    return importTenderMarketState(tender, payload)
      .then((nextTender) => {
        onTenderRefresh(nextTender)
        applyProductTenderState(nextTender, { resetSelection: false })
        setMarketImportText('')
        setDetailStatus('Ставка импортирована')
        return nextTender
      })
      .catch((err) => {
        setDetailStatus(err.message)
      })
      .finally(() => setImportingMarketState(false))
  }

  return {
    marketImportText,
    setMarketImportText,
    importingMarketState,
    importMarketState,
  }
}
