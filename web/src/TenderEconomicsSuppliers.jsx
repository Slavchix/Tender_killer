import {
  SupplierDiscoveryPreview,
  SupplierSearchPreview,
} from './TenderEconomicsSupplierDiscovery'
import { SupplierInputForm } from './TenderEconomicsSupplierInputForm'
import { SupplierOptionsList } from './TenderEconomicsSupplierOptions'
import { formatMoney, supplierConfidenceLabel } from './formatters'

export function ProductSupplierOptionsForm({
  profile,
  onSave,
  onSelect,
  onAutoSelect,
  onDiscoveryImport,
  onPriceCandidateConfirm,
  onPriceCandidateReject,
  onSearchPrepare,
  onPresetSave,
  onDiscoveryRun,
  onDiscoveryUrlRun,
  supplierCatalogHealth,
  supplierCatalogHealthLoading = false,
  supplierCatalogHealthError = '',
  onSupplierCatalogHealthRefresh,
  saving = false,
  importingDiscovery = false,
  reviewingPriceCandidateId = null,
  preparingSearch = false,
  savingPresets = false,
  discoveringDiscovery = false,
  autoSelecting = false,
}) {
  const supplierOptions = Array.isArray(profile?.raw_payload?.supplier_options)
    ? profile.raw_payload.supplier_options
    : []
  const supplierSearch = profile?.raw_payload?.supplier_search || null
  const supplierDiscovery = profile?.raw_payload?.supplier_discovery || null
  const supplierSearchQueries = Array.isArray(supplierSearch?.queries) ? supplierSearch.queries : []
  const priceCandidates = Array.isArray(profile?.price_candidates) ? profile.price_candidates : []
  const visiblePriceCandidates = priceCandidates.filter((candidate) => {
    const reviewStatus = String(candidate?.review_status || 'pending').toLowerCase()
    const qualityStatus = String(candidate?.quality_status || '').toLowerCase()
    return reviewStatus === 'pending' && qualityStatus !== 'blocked'
  })
  const showDiscoveryPreview = visiblePriceCandidates.length === 0
  const showSupplierOptions = supplierOptions.length > 0 && visiblePriceCandidates.length === 0

  return (
    <section className="profile-block supplier-options-block">
      <PriceCandidatesList
        price_candidates={visiblePriceCandidates}
        reviewingPriceCandidateId={reviewingPriceCandidateId}
        onConfirm={(candidate) => onPriceCandidateConfirm?.(profile, candidate)}
        onReject={(candidate) => onPriceCandidateReject?.(profile, candidate)}
      />
      <SupplierInputForm
        profile={profile}
        supplierOptions={supplierOptions}
        supplierSearchQueries={supplierSearchQueries}
        onSave={onSave}
        onAutoSelect={onAutoSelect}
        onSearchPrepare={onSearchPrepare}
        onPresetSave={onPresetSave}
        onDiscoveryRun={onDiscoveryRun}
        onDiscoveryUrlRun={onDiscoveryUrlRun}
        supplierCatalogHealth={supplierCatalogHealth}
        supplierCatalogHealthLoading={supplierCatalogHealthLoading}
        supplierCatalogHealthError={supplierCatalogHealthError}
        onSupplierCatalogHealthRefresh={onSupplierCatalogHealthRefresh}
        saving={saving}
        preparingSearch={preparingSearch}
        savingPresets={savingPresets}
        discoveringDiscovery={discoveringDiscovery}
        autoSelecting={autoSelecting}
      />
      <SupplierSearchPreview search={supplierSearch} />
      {showDiscoveryPreview && (
        <SupplierDiscoveryPreview
          discovery={supplierDiscovery}
          importing={importingDiscovery}
          onImport={(candidateIndex) => onDiscoveryImport?.(profile, candidateIndex)}
        />
      )}
      {showSupplierOptions && (
        <SupplierOptionsList
          supplierOptions={supplierOptions}
          saving={saving}
          onSelect={(optionIndex) => onSelect?.(profile, optionIndex)}
        />
      )}
    </section>
  )
}

function PriceCandidatesList({
  price_candidates = [],
  reviewingPriceCandidateId = null,
  onConfirm,
  onReject,
}) {
  if (!price_candidates.length) return null

  return (
    <div className="price-candidates-list">
      <div className="price-candidates-heading">
        <span>Кандидаты цен</span>
        <em>{price_candidates.length}</em>
      </div>
      {price_candidates.map((candidate) => {
        const confirmed = candidate.review_status === 'confirmed'
        const rejected = candidate.review_status === 'rejected'
        const busy = reviewingPriceCandidateId === candidate.id
        const qualityFlags = Array.isArray(candidate.quality_flags) ? candidate.quality_flags : []
        const stockText = formatSupplierStock(candidate)
        return (
          <div
            className={`price-candidate-row ${candidate.review_status || 'pending'} quality-${candidate.quality_status || 'unknown'}`}
            key={candidate.id || `${candidate.source_url || candidate.product_name}-${candidate.unit_price}`}
          >
            <div>
              {candidate.source_url ? (
                <a href={candidate.source_url} target="_blank" rel="noreferrer">
                  {candidate.product_name || candidate.source_url}
                </a>
              ) : (
                <strong>{candidate.product_name || candidate.supplier_name || 'Кандидат цены'}</strong>
              )}
              <p>
                {candidate.provider || 'источник не указан'}
                {candidate.score != null ? ` · score ${candidate.score}` : ''}
                {candidate.confidence ? ` · ${supplierConfidenceLabel(candidate.confidence)}` : ''}
                {candidate.quality_status ? ` · ${priceCandidateQualityLabel(candidate.quality_status)}` : ''}
                {candidate.auto_eligible ? ' · авто готово' : ''}
              </p>
              {candidate.source_query && <p>Запрос: {candidate.source_query}</p>}
              {stockText && <p>{stockText}</p>}
              {qualityFlags.length > 0 && (
                <ul className="price-candidate-flags">
                  {qualityFlags.slice(0, 4).map((flag) => (
                    <li className={flag.severity || 'review'} key={flag.id || flag.label}>
                      {priceCandidateFlagLabel(flag)}
                    </li>
                  ))}
                </ul>
              )}
            </div>
            <span>{formatMoney(candidate.unit_price)}</span>
            <div className="price-candidate-actions">
              <button
                className="secondary-button compact"
                disabled={busy || confirmed || rejected || !onConfirm}
                onClick={() => ignorePriceCandidateActionError(onConfirm?.(candidate))}
                type="button"
              >
                {confirmed ? 'Принята' : 'Принять цену'}
              </button>
              <button
                className="secondary-button compact"
                disabled={busy || confirmed || rejected || !onReject}
                onClick={() => ignorePriceCandidateActionError(onReject?.(candidate))}
                type="button"
              >
                {rejected ? 'Отклонена' : 'Отклонить'}
              </button>
            </div>
          </div>
        )
      })}
    </div>
  )
}

function formatSupplierStock(candidate = {}) {
  const stock = numberOrNull(candidate.stock_quantity ?? candidate.raw_payload?.stock_quantity)
  const preorder = numberOrNull(candidate.preorder_quantity ?? candidate.raw_payload?.preorder_quantity)
  const parts = []
  if (stock != null) parts.push(`Склад: ${formatQuantity(stock)} шт.`)
  if (preorder != null) parts.push(`Под заказ: ${formatQuantity(preorder)} шт.`)
  return parts.join(' · ')
}

function formatQuantity(value) {
  return Number.isInteger(value) ? String(value) : String(value).replace('.', ',')
}

function numberOrNull(value) {
  const number = Number(value)
  return Number.isFinite(number) ? number : null
}

function priceCandidateQualityLabel(status) {
  return {
    ready: 'готова к расчету',
    review: 'проверить',
    blocked: 'не брать автоматически',
  }[status] || 'качество не проверено'
}

function priceCandidateFlagLabel(flag = {}) {
  const labels = {
    availability_unavailable: 'нет в наличии',
    availability_unknown: 'наличие не подтверждено',
    candidate_rejected: 'отклонена',
    currency_non_rub: 'не рублевая цена',
    delivery_needs_review: 'проверить доставку',
    delivery_pickup_only: 'только самовывоз',
    delivery_unknown: 'доставка не ясна',
    minimum_order_amount: 'минимальная сумма заказа',
    minimum_order_quantity: 'минимальный заказ',
    pack_quantity_invalid: 'ошибка упаковки',
    pack_quantity_unknown: 'упаковка/единица не ясна',
    price_missing: 'нет цены',
    unit_mismatch: 'единица не совпадает',
    vat_not_included: 'НДС не включен',
    vat_unknown: 'НДС не ясен',
  }
  return labels[flag.id] || flag.label || flag.id || 'проверить'
}

function ignorePriceCandidateActionError(result) {
  if (result?.catch) {
    result.catch(() => {})
  }
}
