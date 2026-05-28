import { useEffect, useState } from 'react'
import { formatMoney, supplierConfidenceLabel } from './formatters'
import { Info } from './TenderDetailsShared'

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

export function ProductEconomicsAssumptionsForm({ profile, item, onSave, saving = false }) {
  const assumptions = profile?.raw_payload?.economics_assumptions || {}
  const [values, setValues] = useState(() => economicsAssumptionsFormValues(assumptions))

  useEffect(() => {
    setValues(economicsAssumptionsFormValues(assumptions))
  }, [profile?.position_index, profile?.raw_payload])

  function updateField(name, value) {
    setValues((current) => ({ ...current, [name]: value }))
  }

  function submitAssumptions(event) {
    event.preventDefault()
    if (!onSave) return
    onSave(profile, values)
  }

  return (
    <form className="economics-assumptions-form" onSubmit={submitAssumptions}>
      <div className="profile-block-heading">
        <h5>Допущения</h5>
        <button className="secondary-button compact" disabled={saving || !onSave} type="submit">
          {saving ? 'Сохраняю...' : 'Сохранить'}
        </button>
      </div>
      <div className="economics-input-grid">
        <label>
          <span>НДС</span>
          <select name="vat_mode" onChange={(event) => updateField('vat_mode', event.target.value)} value={values.vat_mode}>
            <option value="unknown">проверить</option>
            <option value="vat_included">включен</option>
            <option value="vat_excluded">сверху</option>
            <option value="no_vat">без НДС</option>
          </select>
        </label>
        <label>
          <span>Ставка НДС, %</span>
          <input
            inputMode="decimal"
            name="vat_rate_percent"
            onChange={(event) => updateField('vat_rate_percent', event.target.value)}
            placeholder="20"
            value={values.vat_rate_percent}
          />
        </label>
        <label>
          <span>Резерв, %</span>
          <input
            inputMode="decimal"
            name="risk_reserve_percent"
            onChange={(event) => updateField('risk_reserve_percent', event.target.value)}
            placeholder="0"
            value={values.risk_reserve_percent}
          />
        </label>
        <label>
          <span>Целевая маржа, %</span>
          <input
            inputMode="decimal"
            name="target_margin_percent"
            onChange={(event) => updateField('target_margin_percent', event.target.value)}
            placeholder="15"
            value={values.target_margin_percent}
          />
        </label>
      </div>
      <div className="assumptions-preview">
        <Info label="НДС сверху" value={formatMoney(item?.vat_cost)} />
        <Info label="Резерв позиции" value={formatMoney(item?.position_risk_reserve)} />
        <Info label="Итого позиция" value={formatMoney(item?.estimated_total_cost)} />
        <Info label="Целевая цена" value={formatMoney(item?.target_price)} />
      </div>
    </form>
  )
}

function economicsFormValues(economics = {}) {
  return {
    unit_cost: economics.unit_cost ?? '',
    logistics_cost: economics.logistics_cost ?? '',
    documents_cost: economics.documents_cost ?? '',
    other_costs: economics.other_costs ?? '',
  }
}

function economicsAssumptionsFormValues(assumptions = {}) {
  return {
    vat_mode: assumptions.vat_mode || 'unknown',
    vat_rate_percent: assumptions.vat_rate_percent ?? '',
    risk_reserve_percent: assumptions.risk_reserve_percent ?? '',
    target_margin_percent: assumptions.target_margin_percent ?? '',
  }
}
