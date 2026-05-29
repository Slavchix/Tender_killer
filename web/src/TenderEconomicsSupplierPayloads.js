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
