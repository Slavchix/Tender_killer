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

  function updateCostModel(value) {
    setValues((current) => {
      if (value === 'service') {
        return {
          ...current,
          cost_model: 'service',
          unit_cost: '',
          unit_cost_basis: 'tender_unit',
          pack_quantity: '',
          logistics_cost: '',
          packaging_cost: '',
        }
      }
      return {
        ...current,
        cost_model: 'product',
        service_rate: '',
        service_volume: '',
        service_minimum: '',
        service_logistics_cost: '',
        service_equipment_cost: '',
      }
    })
  }

  function submitEconomics(event) {
    event.preventDefault()
    if (!onSave) return
    onSave(profile, values)
  }

  const isServiceCostModel = values.cost_model === 'service'
  const landedPreview = buildLandedCostPreview(profile, values)
  const summary = economicsCostSummary(priceSource, landedPreview)

  return (
    <form className="economics-input-form economics-collapsible-section" onSubmit={submitEconomics}>
      <details>
        <summary className="economics-collapsible-summary">
          <span>Себестоимость</span>
          <strong>{summary}</strong>
        </summary>
        <div className="economics-collapsible-body">
          <div className="profile-block-heading">
            <p>Ручные затраты раскрывай, когда нужно уточнить полную себестоимость после цены из быстрых ссылок, КП или прайса.</p>
            <button className="secondary-button compact" disabled={saving || !onSave} type="submit">
              {saving ? 'Сохраняю...' : 'Сохранить'}
            </button>
          </div>
          <EconomicsPriceSource source={priceSource} />
          <div className="economics-input-grid">
            <label>
              <span>Модель затрат</span>
              <select
                name="cost_model"
                onChange={(event) => updateCostModel(event.target.value)}
                value={values.cost_model}
              >
                <option value="product">Товар</option>
                <option value="service">Услуга</option>
              </select>
            </label>
            {isServiceCostModel ? (
              <ServiceCostFields values={values} onChange={updateField} />
            ) : (
              <ProductCostFields values={values} onChange={updateField} />
            )}
          </div>
          {landedPreview && (
            <div className="economics-landed-preview">
              <span>Итого себестоимость</span>
              <strong>{formatMoney(landedPreview.landedCost)}</strong>
              <em>{landedPreview.caption}</em>
            </div>
          )}
        </div>
      </details>
    </form>
  )
}

function ProductCostFields({ values, onChange }) {
  return (
    <>
      <label>
        <span>Режим цены</span>
        <select
          name="unit_cost_basis"
          onChange={(event) => onChange('unit_cost_basis', event.target.value)}
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
          onChange={(event) => onChange('unit_cost', event.target.value)}
          placeholder="0"
          value={values.unit_cost}
        />
      </label>
      <label>
        <span>В упаковке</span>
        <input
          inputMode="decimal"
          name="pack_quantity"
          onChange={(event) => onChange('pack_quantity', event.target.value)}
          placeholder="1"
          value={values.pack_quantity}
        />
      </label>
      <label>
        <span>Логистика</span>
        <input
          inputMode="decimal"
          name="logistics_cost"
          onChange={(event) => onChange('logistics_cost', event.target.value)}
          placeholder="0"
          value={values.logistics_cost}
        />
      </label>
      <CommonCostFields values={values} onChange={onChange} includePackaging />
    </>
  )
}

function ServiceCostFields({ values, onChange }) {
  return (
    <>
      <label>
        <span>Тариф</span>
        <input
          inputMode="decimal"
          name="service_rate"
          onChange={(event) => onChange('service_rate', event.target.value)}
          placeholder="0"
          value={values.service_rate}
        />
      </label>
      <label>
        <span>Объем</span>
        <input
          inputMode="decimal"
          name="service_volume"
          onChange={(event) => onChange('service_volume', event.target.value)}
          placeholder="1"
          value={values.service_volume}
        />
      </label>
      <label>
        <span>Минимум</span>
        <input
          inputMode="decimal"
          name="service_minimum"
          onChange={(event) => onChange('service_minimum', event.target.value)}
          placeholder="0"
          value={values.service_minimum}
        />
      </label>
      <label>
        <span>Логистика/выезд</span>
        <input
          inputMode="decimal"
          name="service_logistics_cost"
          onChange={(event) => onChange('service_logistics_cost', event.target.value)}
          placeholder="0"
          value={values.service_logistics_cost}
        />
      </label>
      <label>
        <span>Техника</span>
        <input
          inputMode="decimal"
          name="service_equipment_cost"
          onChange={(event) => onChange('service_equipment_cost', event.target.value)}
          placeholder="0"
          value={values.service_equipment_cost}
        />
      </label>
      <CommonCostFields values={values} onChange={onChange} />
    </>
  )
}

function CommonCostFields({ values, onChange, includePackaging = false }) {
  return (
    <>
      <label>
        <span>Документы</span>
        <input
          inputMode="decimal"
          name="documents_cost"
          onChange={(event) => onChange('documents_cost', event.target.value)}
          placeholder="0"
          value={values.documents_cost}
        />
      </label>
      {includePackaging && (
        <label>
          <span>Упаковка</span>
          <input
            inputMode="decimal"
            name="packaging_cost"
            onChange={(event) => onChange('packaging_cost', event.target.value)}
            placeholder="0"
            value={values.packaging_cost}
          />
        </label>
      )}
      <label>
        <span>Прочее</span>
        <input
          inputMode="decimal"
          name="other_costs"
          onChange={(event) => onChange('other_costs', event.target.value)}
          placeholder="0"
          value={values.other_costs}
        />
      </label>
    </>
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
    cost_model: economics.cost_model === 'service' ? 'service' : 'product',
    unit_cost: economics.unit_cost ?? '',
    unit_cost_basis: economics.unit_cost_basis ?? 'tender_unit',
    pack_quantity: economics.pack_quantity ?? '',
    logistics_cost: economics.logistics_cost ?? '',
    documents_cost: economics.documents_cost ?? '',
    packaging_cost: economics.packaging_cost ?? '',
    other_costs: economics.other_costs ?? '',
    service_rate: economics.service_rate ?? '',
    service_volume: economics.service_volume ?? '',
    service_minimum: economics.service_minimum ?? '',
    service_logistics_cost: economics.service_logistics_cost ?? '',
    service_equipment_cost: economics.service_equipment_cost ?? '',
  }
}

function economicsCostSummary(priceSource, landedPreview) {
  if (landedPreview?.landedCost != null) return formatMoney(landedPreview.landedCost)
  if (priceSource?.unit_price != null) return `цена ${formatMoney(priceSource.unit_price)}`
  return 'раскрыть при необходимости'
}

function buildLandedCostPreview(profile, values) {
  if (values.cost_model === 'service') {
    return buildServiceCostPreview(values)
  }
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

function buildServiceCostPreview(values) {
  const serviceRate = finiteNumber(values.service_rate)
  const serviceVolume = positiveNumber(values.service_volume)
  const serviceMinimum = finiteNumber(values.service_minimum) || 0
  const logisticsCost = finiteNumber(values.service_logistics_cost) || 0
  const equipmentCost = finiteNumber(values.service_equipment_cost) || 0
  const documentsCost = finiteNumber(values.documents_cost) || 0
  const otherCosts = finiteNumber(values.other_costs) || 0
  const extraCosts = logisticsCost + equipmentCost + documentsCost + otherCosts

  let directCost = null
  let caption = 'услуга не посчитана'
  if (serviceRate !== null && serviceVolume !== null) {
    directCost = serviceRate * serviceVolume
    caption = `${formatMoney(serviceRate)} × ${serviceVolume}`
  }
  if (directCost !== null || serviceMinimum > 0) {
    directCost = Math.max(directCost || 0, serviceMinimum)
    if (serviceMinimum > 0) {
      caption = `${caption}; минимум ${formatMoney(serviceMinimum)}`
    }
  }

  if (directCost === null && extraCosts <= 0) return null
  return {
    landedCost: (directCost || 0) + extraCosts,
    caption: `${caption}; доп. затраты ${formatMoney(extraCosts)}`,
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
