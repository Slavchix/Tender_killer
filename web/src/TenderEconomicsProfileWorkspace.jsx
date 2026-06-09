import { useState } from 'react'

import { ProductAutoEconomicsPanel } from './TenderEconomicsAuto'
import { ProductEconomicsForm } from './TenderEconomicsCostForm'
import { ProductEconomicsAssumptionsForm } from './TenderEconomicsForms'
import { SupplierDiscoveryPreview, SupplierSearchPreview } from './TenderEconomicsSupplierDiscovery'
import { ProductSupplierOptionsForm } from './TenderEconomicsSuppliers'
import { tenderReferenceTotalPrice, tenderReferenceUnitPrice } from './TenderEconomicsPriceComparison'
import { formatMoney, formatQuantity } from './formatters'

export function TenderEconomicsProfileWorkspace({
  economics,
  selectedEconomicsProfile,
  selectedEconomicsProfileIndex = 0,
  onEconomicsSave,
  onEconomicsAssumptionsSave,
  onSupplierOptionSelect,
  onSupplierDiscoveryImport,
  onSupplierSearchPrepare,
  onSupplierDiscoveryRun,
  onSupplierUrlDiscoveryRun,
  onSupplierManualPriceStage,
  onPriceCandidateConfirm,
  onPriceCandidateReject,
  onAutoEconomicsRun,
  onAutoEconomicsAccept,
  savingEconomics = false,
  savingAssumptions = false,
  savingSupplierOption = false,
  importingSupplierCandidate = false,
  reviewingPriceCandidateId = null,
  preparingSupplierSearch = false,
  discoveringSupplier = false,
  autoEstimating = false,
  acceptingAutoEconomics = false,
}) {
  const positionTenderPrice = formatPositionTenderPrice(selectedEconomicsProfile)

  return (
    <>
      <main className="economics-workbench-main">
        <section className="economics-position-card">
          <span>Позиция #{selectedEconomicsProfile.position_index || selectedEconomicsProfileIndex + 1}</span>
          <strong>{selectedEconomicsProfile.product_name || 'Без названия'}</strong>
          <small>
            {formatQuantity(selectedEconomicsProfile.quantity, selectedEconomicsProfile.unit)}
            {positionTenderPrice ? ` · ${positionTenderPrice}` : ''}
          </small>
        </section>
        <ProductSupplierOptionsForm
          profile={selectedEconomicsProfile}
          onSelect={onSupplierOptionSelect}
          onPriceCandidateConfirm={onPriceCandidateConfirm}
          onPriceCandidateReject={onPriceCandidateReject}
          saving={savingSupplierOption}
          reviewingPriceCandidateId={reviewingPriceCandidateId}
        />
        <ManualSupplierPricePanel
          selectedEconomicsProfile={selectedEconomicsProfile}
          importingSupplierCandidate={importingSupplierCandidate}
          preparingSupplierSearch={preparingSupplierSearch}
          discoveringSupplier={discoveringSupplier}
          onSupplierDiscoveryImport={onSupplierDiscoveryImport}
          onSupplierSearchPrepare={onSupplierSearchPrepare}
          onSupplierDiscoveryRun={onSupplierDiscoveryRun}
          onSupplierUrlDiscoveryRun={onSupplierUrlDiscoveryRun}
          onSupplierManualPriceStage={onSupplierManualPriceStage}
        />
      </main>
      <aside className="economics-side-panel">
        <details className="economics-side-section" open>
          <summary>Расчет позиции</summary>
          <ProductAutoEconomicsPanel
            profile={selectedEconomicsProfile}
            onRun={onAutoEconomicsRun}
            onAccept={onAutoEconomicsAccept}
            saving={autoEstimating}
            accepting={acceptingAutoEconomics}
          />
          <ProductEconomicsForm profile={selectedEconomicsProfile} onSave={onEconomicsSave} saving={savingEconomics} />
        </details>
        <details className="economics-side-section">
          <summary>Допущения и резервы</summary>
          <ProductEconomicsAssumptionsForm
            item={economics?.items?.[selectedEconomicsProfileIndex]}
            profile={selectedEconomicsProfile}
            onSave={onEconomicsAssumptionsSave}
            saving={savingAssumptions}
          />
        </details>
      </aside>
    </>
  )
}

function ManualSupplierPricePanel({
  selectedEconomicsProfile,
  importingSupplierCandidate = false,
  preparingSupplierSearch = false,
  discoveringSupplier = false,
  onSupplierDiscoveryImport,
  onSupplierSearchPrepare,
  onSupplierUrlDiscoveryRun,
  onSupplierManualPriceStage,
}) {
  const [manualProductUrl, setManualProductUrl] = useState('')
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
    || `position ${selectedEconomicsProfile?.position_index || ''}`
  ).trim()
  const canSubmitManualUrl = Boolean(manualProductUrl.trim()) && Boolean(onSupplierUrlDiscoveryRun) && !discoveringSupplier
  const canSubmitManualPrice = Number(manualUnitPrice) > 0 && Boolean(onSupplierManualPriceStage) && !discoveringSupplier

  function handleManualUrlSubmit(event) {
    event.preventDefault()
    const url = manualProductUrl.trim()
    if (!url || !onSupplierUrlDiscoveryRun) return
    const result = onSupplierUrlDiscoveryRun?.(selectedEconomicsProfile, {
      url,
      source_query: sourceQuery,
      label: 'Manual product URL',
    })
    if (result?.then) {
      result.then(() => setManualProductUrl('')).catch(() => {})
    }
  }

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
    <section className="supplier-manual-price-panel">
      <div className="supplier-manual-price-heading">
        <div>
          <span>Ручная цена поставщика</span>
          <p>Для крупных закупок используй quick links/manual URL/feed или коммерческое предложение.</p>
        </div>
        <button
          className="secondary-button compact"
          disabled={preparingSupplierSearch || !onSupplierSearchPrepare}
          onClick={() => ignoreManualPriceActionError(onSupplierSearchPrepare?.(selectedEconomicsProfile))}
          type="button"
        >
          {preparingSupplierSearch ? 'Готовлю...' : 'Quick links'}
        </button>
      </div>
      <form className="supplier-manual-url-form" onSubmit={handleManualUrlSubmit}>
        <label htmlFor="manual-product-url-input">Ссылка на публичную карточку товара</label>
        <div>
          <input
            id="manual-product-url-input"
            name="manual-product-url-input"
            onChange={(event) => setManualProductUrl(event.target.value)}
            placeholder="https://supplier.example/catalog/product"
            type="url"
            value={manualProductUrl}
          />
          <button className="secondary-button compact" disabled={!canSubmitManualUrl} type="submit">
            {discoveringSupplier ? 'Проверяю...' : 'Проверить'}
          </button>
        </div>
      </form>
      <form className="supplier-manual-candidate-form" onSubmit={handleManualPriceSubmit}>
        <label htmlFor="manual-price-source-select">Источник цены</label>
        <div className="supplier-manual-candidate-grid">
          <select
            id="manual-price-source-select"
            name="manual-price-source-select"
            onChange={(event) => setManualSourceKind(event.target.value)}
            value={manualSourceKind}
          >
            <option value="quote">КП</option>
            <option value="feed">Прайс/feed</option>
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
      <p className="supplier-manual-price-note">
        Feed/quote путь остается review-first: цена попадает в кандидаты и не меняет экономику до подтверждения.
      </p>
      <SupplierSearchPreview search={supplierSearch} />
      <SupplierDiscoveryPreview
        discovery={supplierDiscovery}
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
  if (sourceKind === 'feed') return 'Прайс/feed'
  if (sourceKind === 'manual') return 'Ручная проверка'
  return 'Коммерческое предложение'
}

function formatPositionTenderPrice(profile) {
  const unitPrice = tenderReferenceUnitPrice(profile)
  const totalPrice = tenderReferenceTotalPrice(profile)
  const parts = []
  if (unitPrice != null) parts.push(`цена тендера ${formatMoney(unitPrice)}`)
  if (totalPrice != null) parts.push(`сумма ${formatMoney(totalPrice)}`)
  return parts.join(' · ')
}
