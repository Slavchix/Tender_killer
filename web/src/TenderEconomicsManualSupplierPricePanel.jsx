import { useState } from 'react'
import { SupplierDiscoveryPreview, SupplierSearchPreview } from './TenderEconomicsSupplierDiscovery'

export function ManualSupplierPricePanel({
  selectedEconomicsProfile,
  importingSupplierCandidate = false,
  preparingSupplierSearch = false,
  discoveringSupplier = false,
  onSupplierDiscoveryImport,
  onSupplierSearchPrepare,
  onSupplierManualPriceStage,
}) {
  const [manualPriceMode, setManualPriceMode] = useState('links')
  const [manualSourceKind, setManualSourceKind] = useState('quote')
  const [manualSupplierName, setManualSupplierName] = useState('')
  const [manualUnitPrice, setManualUnitPrice] = useState('')
  const [manualEvidenceUrl, setManualEvidenceUrl] = useState('')
  const [manualPriceNote, setManualPriceNote] = useState('')
  const rawPayload = selectedEconomicsProfile?.raw_payload || {}
  const supplierSearch = rawPayload.supplier_search
  const supplierDiscovery = rawPayload.supplier_discovery
  const sourceQuery = (
    selectedEconomicsProfile?.normalized_name
    || selectedEconomicsProfile?.product_name
    || `позиция ${selectedEconomicsProfile?.position_index || ''}`
  ).trim()
  const canSubmitManualPrice = Number(manualUnitPrice) > 0 && Boolean(onSupplierManualPriceStage) && !discoveringSupplier

  function handleManualPriceSubmit(event) {
    event.preventDefault()
    const unitPrice = Number(manualUnitPrice)
    if (!(unitPrice > 0) || !onSupplierManualPriceStage) return
    const sourceKind = manualSourceKind === 'feed' ? 'manual_feed' : manualSourceKind === 'manual' ? 'manual_price' : 'manual_quote'
    const supplierName = manualSupplierName.trim()
    const candidate = {
      name: selectedEconomicsProfile?.product_name || sourceQuery,
      supplier_name: supplierName || manualSourceLabel(manualSourceKind),
      provider: sourceKind,
      source_kind: sourceKind,
      source_query: sourceQuery,
      unit_price: unitPrice,
      currency: 'RUB',
      confidence: 'needs_review',
      confidence_reasons: [`operator_${sourceKind}`],
      note: manualPriceNote.trim() || manualSourceLabel(manualSourceKind),
    }
    const evidenceUrl = manualEvidenceUrl.trim()
    if (evidenceUrl) {
      candidate.url = evidenceUrl
      candidate.source_url = evidenceUrl
    }
    const result = onSupplierManualPriceStage?.(selectedEconomicsProfile, candidate)
    if (result?.then) {
      result
        .then(() => {
          setManualSupplierName('')
          setManualUnitPrice('')
          setManualEvidenceUrl('')
          setManualPriceNote('')
        })
        .catch(() => {})
    }
  }

  return (
    <section className="supplier-manual-price-panel" id="supplier-manual-price-panel">
      <div className="supplier-manual-price-heading">
        <div>
          <span>Добавить цену</span>
          <p>Быстрые ссылки или КП/прайс. Цена попадет в кандидаты и не изменит расчет без подтверждения.</p>
        </div>
      </div>
      <div className="supplier-manual-mode-tabs" role="tablist" aria-label="Способ добавления цены">
        <button
          className={manualPriceMode === 'links' ? 'active' : ''}
          onClick={() => setManualPriceMode('links')}
          type="button"
        >
          Быстрые ссылки
        </button>
        <button
          className={manualPriceMode === 'quote' ? 'active' : ''}
          onClick={() => setManualPriceMode('quote')}
          type="button"
        >
          КП или прайс
        </button>
      </div>

      {manualPriceMode === 'quote' && (
        <form className="supplier-manual-candidate-form" onSubmit={handleManualPriceSubmit}>
          <label htmlFor="manual-price-source-select">Цена из КП, прайса или ручной проверки</label>
          <div className="supplier-manual-candidate-grid">
            <select
              id="manual-price-source-select"
              name="manual-price-source-select"
              onChange={(event) => setManualSourceKind(event.target.value)}
              value={manualSourceKind}
            >
              <option value="quote">КП</option>
              <option value="feed">Прайс</option>
              <option value="manual">Ручная проверка</option>
            </select>
            <input
              aria-label="Поставщик"
              onChange={(event) => setManualSupplierName(event.target.value)}
              placeholder="Поставщик"
              type="text"
              value={manualSupplierName}
            />
            <input
              id="manual-price-unit-input"
              min="0"
              name="manual-price-unit-input"
              onChange={(event) => setManualUnitPrice(event.target.value)}
              placeholder="Цена за ед."
              step="0.01"
              type="number"
              value={manualUnitPrice}
            />
            <input
              aria-label="Ссылка на источник"
              onChange={(event) => setManualEvidenceUrl(event.target.value)}
              placeholder="Ссылка на КП/прайс"
              type="url"
              value={manualEvidenceUrl}
            />
          </div>
          <textarea
            aria-label="Комментарий к цене"
            onChange={(event) => setManualPriceNote(event.target.value)}
            placeholder="Условия, НДС, доставка, упаковка"
            rows={2}
            value={manualPriceNote}
          />
          <button className="secondary-button compact" disabled={!canSubmitManualPrice} type="submit">
            {discoveringSupplier ? 'Сохраняю...' : 'Добавить кандидата'}
          </button>
        </form>
      )}

      {manualPriceMode === 'links' && (
        <div className="supplier-manual-links-mode">
          <button
            className="secondary-button compact"
            disabled={preparingSupplierSearch || !onSupplierSearchPrepare}
            onClick={() => ignoreManualPriceActionError(onSupplierSearchPrepare?.(selectedEconomicsProfile))}
            type="button"
          >
            {preparingSupplierSearch ? 'Готовлю...' : 'Подготовить ссылки'}
          </button>
          <SupplierSearchPreview search={supplierSearch} compact={manualPriceMode === 'links'} />
        </div>
      )}

      <SupplierDiscoveryPreview
        discovery={supplierDiscovery}
        diagnosticsOpen={false}
        importing={importingSupplierCandidate}
        onImport={(candidateIndex) => onSupplierDiscoveryImport?.(selectedEconomicsProfile, candidateIndex)}
      />
    </section>
  )
}

function ignoreManualPriceActionError(result) {
  if (result?.catch) {
    result.catch(() => {})
  }
}

function manualSourceLabel(sourceKind) {
  if (sourceKind === 'feed') return 'Прайс'
  if (sourceKind === 'manual') return 'Ручная проверка'
  return 'Коммерческое предложение'
}
