import { formatMoney, supplierConfidenceLabel } from './formatters'

export function SupplierDiscoveryPreview({ discovery, importing = false, diagnosticsOpen = false, onImport }) {
  const candidates = Array.isArray(discovery?.candidates) ? discovery.candidates : []
  const diagnostics = Array.isArray(discovery?.collector_diagnostics) ? discovery.collector_diagnostics : []
  const noCandidates = discovery?.status === 'no_candidates'
  if (!candidates.length && !diagnostics.length) return null

  return (
    <div className="supplier-discovery-preview">
      <span>{noCandidates && !candidates.length ? 'Кандидаты не найдены' : 'Найденные кандидаты'}</span>
      {noCandidates && !candidates.length && <p>Цена не прочиталась автоматически. Открой ссылку вручную или внеси цену из КП/прайса.</p>}
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
              onClick={() => ignoreDiscoveryActionError(onImport?.(index))}
              type="button"
            >
              {imported ? 'Добавлен' : 'Добавить'}
            </button>
          </div>
        )
      })}
      {diagnostics.length > 0 && (
        <details className="technical-discovery-details" open={diagnosticsOpen}>
          <summary>Техническая диагностика</summary>
          <SupplierDiscoveryDiagnostics diagnostics={diagnostics} />
        </details>
      )}
    </div>
  )
}

function SupplierDiscoveryDiagnostics({ diagnostics }) {
  if (!Array.isArray(diagnostics) || !diagnostics.length) return null

  return (
    <div className="supplier-discovery-diagnostics">
      {diagnostics.map((diagnostics, index) => {
        const errors = Array.isArray(diagnostics.errors) ? diagnostics.errors : []
        const compactErrors = compactDiscoveryErrors(errors)
        const rejectionReasons = compactIntentRejectionReasons(diagnostics.intent_rejection_reasons)
        const runState = formatDiscoveryRunState(diagnostics)
        return (
          <section key={`${diagnostics.provider || 'collector'}-${index}`}>
            <strong>{diagnostics.provider || 'collector'}</strong>
            {runState && (
              <p className={`supplier-discovery-run-state ${diagnostics.run_state || 'checked'}`}>
                {runState}
              </p>
            )}
            <div className="supplier-discovery-metrics">
              <span>Запросы: {diagnostics.queries_seen || 0}</span>
              <span>Ссылки: {diagnostics.links_seen || 0}</span>
              <span>Пропущено: {diagnostics.links_skipped || 0}</span>
              <span>Страницы: {diagnostics.pages_fetched || 0}</span>
              <span>Кандидаты: {diagnostics.candidates_found || 0}</span>
            </div>
            {rejectionReasons.length ? (
              <ul className="supplier-discovery-rejection-reasons">
                {rejectionReasons.map((reason) => (
                  <li key={`${diagnostics.provider || 'collector'}-${reason.id}`}>
                    {reason.label}: {reason.count}
                  </li>
                ))}
              </ul>
            ) : null}
            {compactErrors.length ? (
              <ul className="supplier-discovery-errors">
                {compactErrors.map((error) => (
                  <li key={`${diagnostics.provider || 'collector'}-${error.label}`} title={error.raw}>
                    {error.label}
                  </li>
                ))}
              </ul>
            ) : null}
          </section>
        )
      })}
    </div>
  )
}

function formatDiscoveryRunState(diagnostics = {}) {
  if (diagnostics.run_state !== 'skipped') return ''
  if (diagnostics.skip_reason === 'not_relevant_for_profile') {
    return 'Пропущен: каталог не подходит этой позиции'
  }
  return 'Пропущен'
}

function compactIntentRejectionReasons(reasons) {
  if (!reasons || typeof reasons !== 'object') return []
  return Object.entries(reasons)
    .map(([id, count]) => ({
      id,
      count: Number(count) || 0,
      label: formatIntentRejectionReason(id),
    }))
    .filter((reason) => reason.count > 0)
    .sort((left, right) => right.count - left.count || left.label.localeCompare(right.label))
    .slice(0, 5)
}

function formatIntentRejectionReason(reason) {
  const labels = {
    brand_mismatch: 'бренд',
    color_mismatch: 'цвет',
    dimension_mismatch: 'размер',
    material_mismatch: 'материал',
    piece_pack_count_mismatch: 'фасовка',
    product_family_mismatch: 'тип товара',
    product_name_mismatch: 'название',
    volume_mismatch: 'объем',
    weight_mismatch: 'вес',
  }
  return labels[reason] || reason
}

function compactDiscoveryErrors(errors) {
  const seen = new Set()
  return errors
    .map((error) => formatDiscoveryError(error))
    .filter((error) => {
      if (!error.label || seen.has(error.label)) return false
      seen.add(error.label)
      return true
    })
    .slice(0, 3)
}

function formatDiscoveryError(error) {
  const raw = String(error || '')
  const normalized = raw.toLowerCase()
  if (normalized.includes('access_blocked') || normalized.includes('browser_fetch_error')) {
    return {
      label: 'Сайт требует браузерную проверку. Добавь ссылку на товар вручную или открой каталог в браузере.',
      raw,
    }
  }
  if (normalized.includes('timed out') || normalized.includes('timeout')) {
    return {
      label: 'Каталог не успел ответить. Повтори поиск позже или добавь ссылку на товар вручную.',
      raw,
    }
  }
  if (normalized.includes('network') || normalized.includes('winerror')) {
    return {
      label: 'Сеть не дала прочитать каталог. Проверь интернет или добавь ссылку на товар вручную.',
      raw,
    }
  }
  return {
    label: raw.length > 140 ? `${raw.slice(0, 140)}...` : raw,
    raw,
  }
}

export function SupplierSearchPreview({ search, compact = false }) {
  const queries = Array.isArray(search?.queries) ? search.queries : []
  if (!queries.length) return null
  const catalogSearchLinks = uniqueCatalogSearchLinks(queries)

  return (
    <div className="supplier-search-preview">
      <span>Запросы для поиска</span>
      {catalogSearchLinks.length > 0 && (
        <section className="supplier-search-catalog-links">
          <strong>Ручная проверка по каталогам</strong>
          <div className="supplier-search-links">
            {catalogSearchLinks.map((link) => (
              <a href={link.url} key={link.key} target="_blank" rel="noreferrer">
                {link.label}
              </a>
            ))}
          </div>
        </section>
      )}
      {compact ? (
        <details className="technical-discovery-details">
          <summary>Поисковые формулировки</summary>
          <SupplierSearchQueries queries={queries} />
        </details>
      ) : (
        <SupplierSearchQueries queries={queries} />
      )}
    </div>
  )
}

function SupplierSearchQueries({ queries }) {
  return (
    <div className="supplier-search-query-list">
      {queries.map((item) => (
        <section key={`${item.kind}-${item.priority}-${item.query}`}>
          <code>{item.query}</code>
        </section>
      ))}
    </div>
  )
}

function uniqueCatalogSearchLinks(queries) {
  const links = []
  const seen = new Set()
  queries.forEach((item) => {
    const quickLinks = Array.isArray(item.quick_links) ? item.quick_links : []
    quickLinks.forEach((link) => {
      if (link?.link_kind !== 'catalog_search' || !link.url) return
      const key = String(link.provider || link.preset_id || link.label || link.url).toLowerCase()
      if (seen.has(key)) return
      seen.add(key)
      links.push({
        ...link,
        key,
        label: link.label || link.provider || 'Каталог',
      })
    })
  })
  return links
}

function ignoreDiscoveryActionError(result) {
  if (result?.catch) {
    result.catch(() => {})
  }
}
