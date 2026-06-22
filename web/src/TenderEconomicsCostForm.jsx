import { useEffect, useState } from 'react'
import { formatMoney, supplierConfidenceLabel } from './formatters'

export function ProductEconomicsForm({ profile, onSave, saving = false }) {
  const economics = profile?.raw_payload?.economics || {}
  const priceSource = profile?.raw_payload?.economics_price_source || null
  const [values, setValues] = useState(() => economicsFormValues(economics))

  useEffect(() => {
    setValues(economicsFormValues(economics))
  }, [profile?.position_index, profile?.raw_payload])

  function updateField(name, value) {
    setValues((current) => ({ ...current, [name]: value }))
  }

  function submitEconomics(event) {
    event.preventDefault()
    if (!onSave) return
    onSave(profile, values)
  }

  const landedPreview = buildLandedCostPreview(profile, values)

  return (
    <form className="economics-input-form" onSubmit={submitEconomics}>
      <div className="profile-block-heading">
        <h5>Себестоимость</h5>
        <button className="secondary-button compact" disabled={saving || !onSave} type="submit">
          {saving ? 'Сохраняю...' : 'Сохранить'}
        </button>
      </div>
      <EconomicsPriceSource source={priceSource} />
      <div className="economics-input-grid">
        <label>
          <span>Режим цены</span>
          <select
            name="unit_cost_basis"
            onChange={(event) => updateField('unit_cost_basis', event.target.value)}
            value={values.unit_cost_basis}
          >
            <option value="tender_unit">За единицу</option>
            <option value="supplier_pack">За упаковку</option>
          </select>
        </label>
        <label>
          <span>За единицу</span>
          <input
            inputMode="decimal"
            name="unit_cost"
            onChange={(event) => updateField('unit_cost', event.target.value)}
            placeholder="0"
            value={values.unit_cost}
          />
        </label>
        <label>
          <span>В упаковке</span>
          <input
            inputMode="decimal"
            name="pack_quantity"
            onChange={(event) => updateField('pack_quantity', event.target.value)}
            placeholder="1"
            value={values.pack_quantity}
          />
        </label>
        <label>
          <span>Логистика</span>
          <input
            inputMode="decimal"
            name="logistics_cost"
            onChange={(event) => updateField('logistics_cost', event.target.value)}
            placeholder="0"
            value={values.logistics_cost}
          />
        </label>
        <label>
          <span>Документы</span>
          <input
            inputMode="decimal"
            name="documents_cost"
            onChange={(event) => updateField('documents_cost', event.target.value)}
            placeholder="0"
            value={values.documents_cost}
          />
        </label>
        <label>
          <span>Упаковка</span>
          <input
            inputMode="decimal"
            name="packaging_cost"
            onChange={(event) => updateField('packaging_cost', event.target.value)}
            placeholder="0"
            value={values.packaging_cost}
          />
        </label>
        <label>
          <span>Прочее</span>
          <input
            inputMode="decimal"
            name="other_costs"
            onChange={(event) => updateField('other_costs', event.target.value)}
            placeholder="0"
            value={values.other_costs}
          />
        </label>
      </div>
      {landedPreview && (
        <div className="economics-landed-preview">
          <span>Итого себестоимость</span>
          <strong>{formatMoney(landedPreview.landedCost)}</strong>
          <em>{landedPreview.caption}</em>
        </div>
      )}
    </form>
  )
}

function EconomicsPriceSource({ source }) {
  if (!source) return null
  const supplier = source.supplier_name || source.supplier_url || 'поставщик'
  const mode = source.selection === 'manual_selected' ? 'выбран вручную' : 'выбран автоматически'

  return (
    <div className={`price-source-note ${source.confidence || 'needs_review'}`}>
      <span>Источник цены</span>
      <strong>{supplier} · {formatMoney(source.unit_price)}</strong>
      <em>{mode} · {supplierConfidenceLabel(source.confidence)}</em>
    </div>
  )
}

function economicsFormValues(economics = {}) {
  return {
    unit_cost: economics.unit_cost ?? '',
    unit_cost_basis: economics.unit_cost_basis ?? 'tender_unit',
    pack_quantity: economics.pack_quantity ?? '',
    logistics_cost: economics.logistics_cost ?? '',
    documents_cost: economics.documents_cost ?? '',
    packaging_cost: economics.packaging_cost ?? '',
    other_costs: economics.other_costs ?? '',
  }
}

function buildLandedCostPreview(profile, values) {
  const quantity = positiveNumber(profile?.quantity)
  const unitCost = finiteNumber(values.unit_cost)
  const packQuantity = positiveNumber(values.pack_quantity)
  const logisticsCost = finiteNumber(values.logistics_cost) || 0
  const documentsCost = finiteNumber(values.documents_cost) || 0
  const packagingCost = finiteNumber(values.packaging_cost) || 0
  const otherCosts = finiteNumber(values.other_costs) || 0
  const extraCosts = logisticsCost + documentsCost + packagingCost + otherCosts
  const unitCostBasis = values.unit_cost_basis === 'supplier_pack' ? 'supplier_pack' : 'tender_unit'

  let directCost = null
  let caption = 'товар не посчитан'
  if (unitCost !== null && quantity !== null) {
    if (unitCostBasis === 'supplier_pack' && packQuantity) {
      const procurementQuantity = Math.ceil(quantity / packQuantity)
      directCost = procurementQuantity * unitCost
      const normalizedUnitCost = directCost / quantity
      caption = `${procurementQuantity} уп.; ${formatMoney(normalizedUnitCost)} на ед.`
    } else {
      directCost = unitCost * quantity
      caption = `${formatMoney(unitCost)} на ед.; ${quantity}`
    }
  }

  if (directCost === null && extraCosts <= 0) return null
  return {
    landedCost: (directCost || 0) + extraCosts,
    caption: `${caption}; доб. затраты ${formatMoney(extraCosts)}`,
  }
}

function finiteNumber(value) {
  if (value === null || value === undefined || value === '') return null
  const number = Number(String(value).replace(/\s/g, '').replace(',', '.'))
  return Number.isFinite(number) && number >= 0 ? number : null
}

function positiveNumber(value) {
  const number = finiteNumber(value)
  return number !== null && number > 0 ? number : null
}
