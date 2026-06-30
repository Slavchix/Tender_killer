import { formatMoney } from './formatters'

export function economicsFormValues(economics = {}) {
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

export function economicsCostSummary(priceSource, landedPreview) {
  if (landedPreview?.landedCost != null) return formatMoney(landedPreview.landedCost)
  if (priceSource?.unit_price != null) return `цена ${formatMoney(priceSource.unit_price)}`
  return 'раскрыть при необходимости'
}

export function buildLandedCostPreview(profile, values) {
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

export function buildServiceCostPreview(values) {
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
    caption = `${formatMoney(serviceRate)} x ${serviceVolume}`
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

export function finiteNumber(value) {
  if (value === null || value === undefined || value === '') return null
  const number = Number(String(value).replace(/\s/g, '').replace(',', '.'))
  return Number.isFinite(number) && number >= 0 ? number : null
}

export function positiveNumber(value) {
  const number = finiteNumber(value)
  return number !== null && number > 0 ? number : null
}
