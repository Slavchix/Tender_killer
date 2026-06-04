import { formatMoney, supplierConfidenceLabel } from './formatters'

export function SupplierDiscoveryPreview({ discovery, importing = false, onImport }) {
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
              onClick={() => ignoreDiscoveryActionError(onImport?.(index))}
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

function SupplierDiscoveryDiagnostics({ diagnostics }) {
  if (!Array.isArray(diagnostics) || !diagnostics.length) return null

  return (
    <div className="supplier-discovery-diagnostics">
      {diagnostics.map((diagnostics, index) => {
        const errors = Array.isArray(diagnostics.errors) ? diagnostics.errors : []
        const compactErrors = compactDiscoveryErrors(errors)
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

export function SupplierSearchPreview({ search }) {
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

function ignoreDiscoveryActionError(result) {
  if (result?.catch) {
    result.catch(() => {})
  }
}
