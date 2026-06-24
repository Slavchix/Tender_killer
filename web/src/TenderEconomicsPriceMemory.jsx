import { useEffect, useState } from 'react'
import { archivePriceMemoryEntry, fetchPriceMemory } from './api'
import { formatDateTime, formatMoney, supplierConfidenceLabel, taxModeLabel } from './formatters'

const DEFAULT_MEMORY_LIMIT = 12
const EMPTY_PRICE_MEMORY = { summary: {}, entries: [] }

export function TenderEconomicsPriceMemory({ limit = DEFAULT_MEMORY_LIMIT }) {
  const [priceMemory, setPriceMemory] = useState(EMPTY_PRICE_MEMORY)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [archivingId, setArchivingId] = useState(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError('')
    fetchPriceMemory(limit)
      .then((payload) => {
        if (!cancelled) setPriceMemory(payload.price_memory || EMPTY_PRICE_MEMORY)
      })
      .catch((err) => {
        if (!cancelled) setError(err.message)
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [limit])

  function reloadMemory() {
    setLoading(true)
    setError('')
    return fetchPriceMemory(limit)
      .then((payload) => setPriceMemory(payload.price_memory || EMPTY_PRICE_MEMORY))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }

  function archiveEntry(entry) {
    if (!entry?.id || archivingId) return null
    const reason = window.prompt('Почему убрать цену из памяти?', entry.archive_reason || '')
    if (reason === null) return null
    setArchivingId(entry.id)
    setError('')
    return archivePriceMemoryEntry(entry.id, { reason: reason.trim() })
      .then((payload) => setPriceMemory(payload.price_memory || EMPTY_PRICE_MEMORY))
      .catch((err) => setError(err.message))
      .finally(() => setArchivingId(null))
  }

  const summary = priceMemory.summary || {}
  const entries = Array.isArray(priceMemory.entries) ? priceMemory.entries : []
  const activeCount = Number(summary.active_count || 0)
  const archivedCount = Number(summary.archived_count || 0)

  return (
    <details className="economics-card price-memory-panel">
      <summary>
        <span>Память цен</span>
        <em>
          {loading ? 'загрузка' : `активных ${activeCount} · архив ${archivedCount}`}
        </em>
      </summary>
      <div className="price-memory-body">
        <div className="price-memory-toolbar">
          <p>Здесь лежат подтвержденные цены, которые система может предлагать похожим позициям.</p>
          <button className="secondary-button compact" disabled={loading} onClick={reloadMemory} type="button">
            Обновить
          </button>
        </div>
        {error && <p className="price-memory-error">{error}</p>}
        {!loading && entries.length === 0 && <p className="muted-text">Память цен пока пустая.</p>}
        {entries.length > 0 && (
          <div className="price-memory-list" aria-label="Память подтвержденных цен">
            {entries.map((entry) => (
              <PriceMemoryRow
                archiving={archivingId === entry.id}
                entry={entry}
                key={entry.id}
                onArchive={() => archiveEntry(entry)}
              />
            ))}
          </div>
        )}
      </div>
    </details>
  )
}

function PriceMemoryRow({ entry, archiving = false, onArchive }) {
  const archived = entry.entry_status === 'archived'
  return (
    <div className={`price-memory-row ${archived ? 'archived' : 'active'}`}>
      <div className="price-memory-main">
        <strong>{entry.product_name || 'Товар без названия'}</strong>
        <span>
          {(entry.supplier_name || entry.provider || 'поставщик не указан')} · {entry.unit || 'ед.'}
        </span>
        <em>
          {sourceLabel(entry.source_kind)} · {supplierConfidenceLabel(entry.confidence)} · {taxModeLabel(entry.vat_mode)}
        </em>
      </div>
      <div className="price-memory-meta">
        <strong>{formatMoney(entry.unit_price)}</strong>
        <span>{formatDateTime(entry.updated_at || entry.confirmed_at)}</span>
        {archived && <em>{entry.archive_reason || 'архив'}</em>}
      </div>
      <button className="secondary-button compact" disabled={archived || archiving} onClick={onArchive} type="button">
        {archiving ? 'Убираю...' : archived ? 'Убрана' : 'Убрать'}
      </button>
    </div>
  )
}

function sourceLabel(sourceKind) {
  return {
    manual_feed: 'прайс',
    price_book_feed: 'прайс',
    price_memory: 'память',
    supplier_discovery: 'каталог',
    supplier_manual_url: 'ссылка',
  }[sourceKind] || sourceKind || 'источник'
}
