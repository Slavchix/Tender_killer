import { formatMoney } from './formatters'

export function tenderReferenceUnitPrice(profile) {
  const rawPayload = profile?.raw_payload && typeof profile.raw_payload === 'object'
    ? profile.raw_payload
    : {}
  const directUnitPrice = firstPositiveNumber(
    profile?.unit_price,
    rawPayload.unit_price,
    rawPayload.tender_unit_price,
    rawPayload.position_unit_price,
  )
  if (directUnitPrice != null) return directUnitPrice

  const totalPrice = firstPositiveNumber(
    profile?.total_price,
    rawPayload.total_price,
    rawPayload.tender_total_price,
    rawPayload.position_total_price,
  )
  const quantity = firstPositiveNumber(profile?.quantity, rawPayload.quantity)
  if (totalPrice != null && quantity != null) {
    return totalPrice / quantity
  }
  return null
}

export function tenderReferenceTotalPrice(profile) {
  const rawPayload = profile?.raw_payload && typeof profile.raw_payload === 'object'
    ? profile.raw_payload
    : {}
  const directTotalPrice = firstPositiveNumber(
    profile?.total_price,
    rawPayload.total_price,
    rawPayload.tender_total_price,
    rawPayload.position_total_price,
  )
  if (directTotalPrice != null) return directTotalPrice

  const unitPrice = tenderReferenceUnitPrice(profile)
  const quantity = firstPositiveNumber(profile?.quantity, rawPayload.quantity)
  if (unitPrice != null && quantity != null) {
    return unitPrice * quantity
  }
  return null
}

export function priceComparisonForUnitPrice(unitPrice, tenderUnitPrice) {
  const price = positiveNumber(unitPrice)
  const reference = positiveNumber(tenderUnitPrice)
  if (price == null || reference == null) return null

  const diff = price - reference
  if (Math.abs(diff) < 0.005) {
    return { tone: 'same', label: 'как в тендере' }
  }

  const absoluteDiff = Math.abs(diff)
  const percent = reference > 0 ? (absoluteDiff / reference) * 100 : null
  const percentText = percent != null ? ` (${formatPercent(percent)})` : ''
  if (diff < 0) {
    return {
      tone: 'cheaper',
      label: `дешевле на ${formatMoney(absoluteDiff)}${percentText}`,
    }
  }
  return {
    tone: 'expensive',
    label: `дороже на ${formatMoney(absoluteDiff)}${percentText}`,
  }
}

function firstPositiveNumber(...values) {
  for (const value of values) {
    const number = positiveNumber(value)
    if (number != null) return number
  }
  return null
}

function positiveNumber(value) {
  const number = Number(value)
  return Number.isFinite(number) && number > 0 ? number : null
}

function formatPercent(value) {
  const rounded = value >= 10 ? Math.round(value) : Math.round(value * 10) / 10
  return `${String(rounded).replace('.', ',')}%`
}
