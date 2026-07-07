import { useEffect, useRef, useState } from 'react'
import { importTenderMarketState } from './api'

const MARKET_IMPORT_TIMEOUT_MS = 15000

export function useTenderMarketStateImport({
  tender,
  onTenderRefresh,
  setDetailStatus,
  applyProductTenderState,
}) {
  const [marketImportText, setMarketImportText] = useState('')
  const [importingMarketState, setImportingMarketState] = useState(false)
  const activeImportRef = useRef(null)

  useEffect(() => {
    activeImportRef.current?.abort()
    activeImportRef.current = null
    setMarketImportText('')
    setImportingMarketState(false)
    return () => {
      activeImportRef.current?.abort()
      activeImportRef.current = null
    }
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
    activeImportRef.current?.abort()
    const controller = new AbortController()
    const timeoutId = window.setTimeout(() => controller.abort(), MARKET_IMPORT_TIMEOUT_MS)
    activeImportRef.current = controller
    setImportingMarketState(true)
    setDetailStatus('')
    return importTenderMarketState(tender, payload, { signal: controller.signal })
      .then((nextTender) => {
        onTenderRefresh(nextTender)
        applyProductTenderState(nextTender, { resetSelection: false })
        setMarketImportText('')
        setDetailStatus('Ставка импортирована')
        return nextTender
      })
      .catch((err) => {
        if (activeImportRef.current === controller) {
          setDetailStatus(err.message)
        }
      })
      .finally(() => {
        window.clearTimeout(timeoutId)
        if (activeImportRef.current === controller) {
          activeImportRef.current = null
          setImportingMarketState(false)
        }
      })
  }

  return {
    marketImportText,
    setMarketImportText,
    importingMarketState,
    importMarketState,
  }
}
