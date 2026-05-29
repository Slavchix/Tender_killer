import { useEffect, useState } from 'react'
import {
  SupplierCatalogHealthPanel,
  SupplierCatalogPresetControls,
} from './TenderEconomicsSupplierCatalogs'

export function SupplierInputForm({
  profile,
  supplierOptions = [],
  supplierSearchQueries = [],
  onSave,
  onAutoSelect,
  onSearchPrepare,
  onPresetSave,
  onDiscoveryRun,
  onDiscoveryUrlRun,
  supplierCatalogHealth,
  supplierCatalogHealthLoading = false,
  supplierCatalogHealthError = '',
  onSupplierCatalogHealthRefresh,
  saving = false,
  preparingSearch = false,
  savingPresets = false,
  discoveringDiscovery = false,
  autoSelecting = false,
}) {
  const [values, setValues] = useState(() => supplierOptionFormValues())

  useEffect(() => {
    setValues(supplierOptionFormValues())
  }, [profile?.position_index])

  function updateField(name, value) {
    setValues((current) => ({ ...current, [name]: value }))
  }

  function submitSupplierOption(event) {
    event.preventDefault()
    if (!onSave) return
    const result = onSave(profile, supplierOptionPayload(values, supplierSearchQueries))
    if (result?.then) {
      result.then(() => setValues(supplierOptionFormValues())).catch(() => {})
      return
    }
    setValues(supplierOptionFormValues())
  }

  return (
    <form className="supplier-input-form" onSubmit={submitSupplierOption}>
      <div className="profile-block-heading">
        <h5>Поставщики</h5>
        <div className="profile-block-actions">
          <button
            className="secondary-button compact"
            disabled={preparingSearch || !onSearchPrepare}
            onClick={() => ignoreSupplierActionError(onSearchPrepare?.(profile))}
            type="button"
          >
            {preparingSearch ? 'Готовлю...' : 'Подготовить поиск'}
          </button>
          <button
            className="secondary-button compact"
            disabled={discoveringDiscovery || !onDiscoveryRun || !supplierSearchQueries.length}
            onClick={() => ignoreSupplierActionError(onDiscoveryRun?.(profile))}
            type="button"
          >
            {discoveringDiscovery ? 'Ищу...' : 'Найти кандидатов'}
          </button>
          <button
            className="secondary-button compact"
            disabled={discoveringDiscovery || !onDiscoveryUrlRun || !values.url}
            onClick={() => ignoreSupplierActionError(onDiscoveryUrlRun?.(profile, supplierUrlDiscoveryPayload(values, supplierSearchQueries)))}
            type="button"
          >
            {discoveringDiscovery ? 'Проверяю...' : 'Проверить ссылку'}
          </button>
          <button
            className="secondary-button compact"
            disabled={autoSelecting || !onAutoSelect || !supplierOptions.length}
            onClick={() => ignoreSupplierActionError(onAutoSelect?.(profile))}
            type="button"
          >
            {autoSelecting ? 'Выбираю...' : 'Лучший в расчет'}
          </button>
          <button className="secondary-button compact" disabled={saving || !onSave || !hasSupplierOptionInput(values)} type="submit">
            {saving ? 'Сохраняю...' : 'Добавить'}
          </button>
        </div>
      </div>
      <SupplierCatalogPresetControls
        profile={profile}
        saving={savingPresets}
        onPresetSave={onPresetSave}
      />
      <SupplierCatalogHealthPanel
        supplierCatalogHealth={supplierCatalogHealth}
        loading={supplierCatalogHealthLoading}
        error={supplierCatalogHealthError}
        onRefresh={onSupplierCatalogHealthRefresh}
      />
      <div className="supplier-input-grid">
        <label>
          <span>Запрос-источник</span>
          <select
            name="source_query"
            onChange={(event) => updateField('source_query', event.target.value)}
            value={values.source_query}
          >
            <option value="">Без привязки</option>
            {supplierSearchQueries.map((item) => (
              <option key={`${item.priority}-${item.query}`} value={item.query}>
                {item.query}
              </option>
            ))}
          </select>
        </label>
        <label>
          <span>Поставщик</span>
          <input
            name="name"
            onChange={(event) => updateField('name', event.target.value)}
            placeholder="Название"
            value={values.name}
          />
        </label>
        <label>
          <span>Ссылка</span>
          <input
            name="url"
            onChange={(event) => updateField('url', event.target.value)}
            placeholder="https://"
            value={values.url}
          />
        </label>
        <label>
          <span>Наличие</span>
          <select
            name="availability"
            onChange={(event) => updateField('availability', event.target.value)}
            value={values.availability}
          >
            <option value="unknown">Неясно</option>
            <option value="in_stock">В наличии</option>
            <option value="on_request">Под заказ</option>
            <option value="not_available">Нет</option>
          </select>
        </label>
        <label>
          <span>Статус</span>
          <select
            name="status"
            onChange={(event) => updateField('status', event.target.value)}
            value={values.status}
          >
            <option value="candidate">Кандидат</option>
            <option value="suitable">Подходит</option>
            <option value="rejected">Не подходит</option>
          </select>
        </label>
      </div>
      <label className="supplier-note-field">
        <span>Заметка</span>
        <textarea
          name="note"
          onChange={(event) => updateField('note', event.target.value)}
          placeholder="Условия, НДС, доставка, ограничения"
          value={values.note}
        />
      </label>
    </form>
  )
}

function ignoreSupplierActionError(result) {
  if (result?.catch) {
    result.catch(() => {})
  }
}

function supplierOptionFormValues() {
  return {
    name: '',
    url: '',
    availability: 'unknown',
    status: 'candidate',
    source_query: '',
    note: '',
  }
}

function supplierOptionPayload(values, searchQueries = []) {
  const payload = { ...values }
  const selectedQuery = searchQueries.find((item) => item.query === values.source_query)
  if (selectedQuery) {
    payload.source_kind = selectedQuery.kind || ''
  }
  return payload
}

function supplierUrlDiscoveryPayload(values, searchQueries = []) {
  const payload = { url: values.url }
  if (values.source_query) {
    payload.source_query = values.source_query
    payload.source_kind = supplierSourceKind(values.source_query, searchQueries)
  }
  return payload
}

function supplierSourceKind(sourceQuery, searchQueries = []) {
  const selectedQuery = searchQueries.find((item) => item.query === sourceQuery)
  return selectedQuery?.kind || ''
}

function hasSupplierOptionInput(values) {
  return Boolean(values.name || values.url || values.note)
}
