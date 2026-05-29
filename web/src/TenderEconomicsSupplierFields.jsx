export function SupplierInputFields({ values, supplierSearchQueries = [], onFieldChange }) {
  function updateField(name, value) {
    onFieldChange?.(name, value)
  }

  return (
    <>
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
    </>
  )
}

export function supplierOptionFormValues() {
  return {
    name: '',
    url: '',
    availability: 'unknown',
    status: 'candidate',
    source_query: '',
    note: '',
  }
}

export function supplierOptionPayload(values, searchQueries = []) {
  const payload = { ...values }
  const selectedQuery = searchQueries.find((item) => item.query === values.source_query)
  if (selectedQuery) {
    payload.source_kind = selectedQuery.kind || ''
  }
  return payload
}

export function supplierUrlDiscoveryPayload(values, searchQueries = []) {
  const payload = { url: values.url }
  if (values.source_query) {
    payload.source_query = values.source_query
    payload.source_kind = supplierSourceKind(values.source_query, searchQueries)
  }
  return payload
}

export function supplierSourceKind(sourceQuery, searchQueries = []) {
  const selectedQuery = searchQueries.find((item) => item.query === sourceQuery)
  return selectedQuery?.kind || ''
}

export function hasSupplierOptionInput(values) {
  return Boolean(values.name || values.url || values.note)
}
