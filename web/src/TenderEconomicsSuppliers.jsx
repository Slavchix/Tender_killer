import { useEffect, useState } from 'react'
import {
  formatMoney,
  supplierAvailabilityLabel,
  supplierConfidenceLabel,
  supplierStatusLabel,
} from './formatters'
import {
  SupplierCatalogHealthPanel,
  SupplierCatalogPresetControls,
} from './TenderEconomicsSupplierCatalogs'

export function ProductSupplierOptionsForm({
  profile,
  onSave,
  onSelect,
  onAutoSelect,
  onDiscoveryImport,
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
    <section className="profile-block supplier-options-block">
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

      <SupplierSearchPreview search={supplierSearch} />
      <SupplierDiscoveryPreview
        discovery={supplierDiscovery}
        importing={importingDiscovery}
        onImport={(candidateIndex) => onDiscoveryImport?.(profile, candidateIndex)}
      />

      {supplierOptions.length ? (
        <div className="supplier-options-list">
          {supplierOptions.map((option, index) => (
            <div
              className={option.status === 'selected' ? 'supplier-option-row selected' : 'supplier-option-row'}
              key={`${option.url || option.name || 'supplier'}-${index}`}
            >
              <div>
                {option.url ? (
                  <a href={option.url} target="_blank" rel="noreferrer">{option.name || option.url}</a>
                ) : (
                  <strong>{option.name || 'Поставщик'}</strong>
                )}
                {option.note && <p>{option.note}</p>}
                {option.source_query && <p>Запрос: {option.source_query}</p>}
              </div>
              <span>{formatMoney(option.unit_price)}</span>
              <em>{supplierAvailabilityLabel(option.availability)} · {supplierStatusLabel(option.status)}</em>
              <button
                className="supplier-select-button"
                disabled={saving || !onSelect || option.status === 'selected'}
                onClick={() => ignoreSupplierActionError(onSelect?.(profile, index))}
                type="button"
              >
                {option.status === 'selected' ? 'В расчете' : 'В расчет'}
              </button>
            </div>
          ))}
        </div>
      ) : (
        <p className="muted-text">Кандидаты поставщиков пока не добавлены.</p>
      )}
    </section>
  )
}

function SupplierDiscoveryPreview({ discovery, importing = false, onImport }) {
  const candidates = Array.isArray(discovery?.candidates) ? discovery.candidates : []
  const diagnostics = Array.isArray(discovery?.collector_diagnostics) ? discovery.collector_diagnostics : []
  const noCandidates = discovery?.status === 'no_candidates'
  if (!candidates.length && !diagnostics.length) return null

  return (
    <div className="supplier-discovery-preview">
      <span>{noCandidates && !candidates.length ? 'Кандидаты не найдены' : 'Найденные кандидаты'}</span>
      {noCandidates && !candidates.length && <p>Смотри диагностику ниже: она показывает, какие каталоги и страницы проверялись.</p>}
      <SupplierDiscoveryDiagnostics diagnostics={diagnostics} />
      {candidates.length > 0 && candidates.map((candidate, index) => {
        const imported = candidate.review_status === 'imported'
        const confidenceReasons = Array.isArray(candidate.confidence_reasons) ? candidate.confidence_reasons : []
        return (
          <div className={imported ? 'supplier-discovery-row imported' : 'supplier-discovery-row'} key={`${candidate.url || candidate.name || 'candidate'}-${index}`}>
            <div>
              {candidate.url ? (
                <a href={candidate.url} target="_blank" rel="noreferrer">{candidate.name || candidate.url}</a>
              ) : (
                <strong>{candidate.name || 'Поставщик'}</strong>
              )}
              {candidate.source_query && <p>Запрос: {candidate.source_query}</p>}
              {candidate.provider && <p>{candidate.provider}</p>}
              <p>
                {supplierConfidenceLabel(candidate.confidence)}
                {confidenceReasons.length ? ` · ${confidenceReasons.join(', ')}` : ''}
              </p>
            </div>
            <span>{formatMoney(candidate.unit_price)}</span>
            <button
              className="secondary-button compact"
              disabled={importing || imported || !onImport}
              onClick={() => ignoreSupplierActionError(onImport?.(index))}
              type="button"
            >
              {imported ? 'Добавлен' : 'Добавить'}
            </button>
          </div>
        )
      })}
    </div>
  )
}

function ignoreSupplierActionError(result) {
  if (result?.catch) {
    result.catch(() => {})
  }
}

function SupplierDiscoveryDiagnostics({ diagnostics }) {
  if (!Array.isArray(diagnostics) || !diagnostics.length) return null

  return (
    <div className="supplier-discovery-diagnostics">
      {diagnostics.map((diagnostics, index) => {
        const errors = Array.isArray(diagnostics.errors) ? diagnostics.errors : []
        return (
          <section key={`${diagnostics.provider || 'collector'}-${index}`}>
            <strong>{diagnostics.provider || 'collector'}</strong>
            <div className="supplier-discovery-metrics">
              <span>Запросы: {diagnostics.queries_seen || 0}</span>
              <span>Ссылки: {diagnostics.links_seen || 0}</span>
              <span>Пропущено: {diagnostics.links_skipped || 0}</span>
              <span>Страницы: {diagnostics.pages_fetched || 0}</span>
              <span>Кандидаты: {diagnostics.candidates_found || 0}</span>
            </div>
            {errors.length ? <p>{errors.join(' · ')}</p> : null}
          </section>
        )
      })}
    </div>
  )
}

function SupplierSearchPreview({ search }) {
  const queries = Array.isArray(search?.queries) ? search.queries : []
  if (!queries.length) return null

  return (
    <div className="supplier-search-preview">
      <span>Запросы для поиска</span>
      <div>
        {queries.map((item) => (
          <section key={`${item.kind}-${item.priority}-${item.query}`}>
            <code>{item.query}</code>
            <div className="supplier-search-links">
              {(Array.isArray(item.quick_links) ? item.quick_links : []).map((link) => (
                <a href={link.url} key={`${item.query}-${link.label}`} target="_blank" rel="noreferrer">
                  {link.label}
                </a>
              ))}
            </div>
          </section>
        ))}
      </div>
    </div>
  )
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
