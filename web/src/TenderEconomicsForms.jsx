import { useEffect, useState } from 'react'
import { formatMoney } from './formatters'
import { Info } from './TenderDetailsShared'

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

  const summary = economicsAssumptionsSummary(values, item)

  return (
    <form className="economics-assumptions-form economics-collapsible-section" onSubmit={submitAssumptions}>
      <details>
        <summary className="economics-collapsible-summary">
          <span>Допущения</span>
          <strong>{summary}</strong>
        </summary>
        <div className="economics-collapsible-body">
          <div className="profile-block-heading">
            <p>НДС, резерв и целевую маржу раскрывай только когда нужно уточнить итоговый расчет.</p>
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
        </div>
      </details>
    </form>
  )
}

function economicsAssumptionsFormValues(assumptions = {}) {
  return {
    vat_mode: assumptions.vat_mode || 'unknown',
    vat_rate_percent: assumptions.vat_rate_percent ?? '',
    risk_reserve_percent: assumptions.risk_reserve_percent ?? '',
    target_margin_percent: assumptions.target_margin_percent ?? '',
  }
}

function economicsAssumptionsSummary(values, item) {
  const margin = values.target_margin_percent === '' ? '15' : values.target_margin_percent
  const reserve = values.risk_reserve_percent === '' ? '0' : values.risk_reserve_percent
  const total = item?.estimated_total_cost ? ` · итог ${formatMoney(item.estimated_total_cost)}` : ''
  return `маржа ${margin}% · резерв ${reserve}%${total}`
}
