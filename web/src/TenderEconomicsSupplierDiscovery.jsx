import { formatMoney, supplierConfidenceLabel } from './formatters'

export function SupplierDiscoveryPreview({ discovery, importing = false, diagnosticsOpen = false, onImport }) {
  const candidates = Array.isArray(discovery?.candidates) ? discovery.candidates : []
  const diagnostics = Array.isArray(discovery?.collector_diagnostics) ? discovery.collector_diagnostics : []
  const noCandidates = discovery?.status === 'no_candidates'
  const noCandidateHint = noCandidates && !candidates.length ? supplierDiscoveryNoCandidateHint(diagnostics) : ''
  const nextAction = supplierDiscoveryNextAction(diagnostics, { noCandidates, candidateCount: candidates.length })
  if (!candidates.length && !diagnostics.length) return null

  return (
    <div className="supplier-discovery-preview">
      <span>{noCandidates && !candidates.length ? 'Кандидаты не найдены' : 'Найденные кандидаты'}</span>
      {noCandidates && !candidates.length && <p>{noCandidateHint}</p>}
      <ProviderRunSummary diagnostics={diagnostics} />
      {nextAction && <p className="supplier-discovery-next-action">{nextAction}</p>}
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

function ProviderRunSummary({ diagnostics }) {
  const buckets = supplierDiscoveryRunBuckets(diagnostics)
  if (!buckets.total) return null
  const blockedTone = buckets.blocked > 0 ? 'warning' : 'ok'

  return (
    <div className="provider-run-summary" aria-label="Сводка проверки поставщиков">
      <span className={blockedTone}>Провайдеры: {buckets.checked}/{buckets.total}</span>
      <span>Кандидаты: {buckets.candidates}</span>
      <span>Страницы: {buckets.pages}</span>
      {buckets.blocked > 0 && <span className="warning">Блок: {buckets.blocked}</span>}
      {buckets.skipped > 0 && <span>Пропущено: {buckets.skipped}</span>}
    </div>
  )
}

function supplierDiscoveryRunBuckets(diagnostics) {
  const buckets = {
    total: 0,
    checked: 0,
    blocked: 0,
    skipped: 0,
    pages: 0,
    links: 0,
    candidates: 0,
  }
  ;(Array.isArray(diagnostics) ? diagnostics : []).forEach((item) => {
    if (!item || typeof item !== 'object') return
    buckets.total += 1
    buckets.pages += Number(item.pages_fetched || 0)
    buckets.links += Number(item.links_seen || 0)
    buckets.candidates += Number(item.candidates_found || 0)
    if (item.run_state === 'blocked' || item.error_kind === 'access_blocked' || item.skip_reason === 'access_blocked') {
      buckets.blocked += 1
    } else if (item.run_state === 'skipped') {
      buckets.skipped += 1
    } else {
      buckets.checked += 1
    }
  })
  return buckets
}

function supplierDiscoveryNextAction(diagnostics, { noCandidates = false, candidateCount = 0 } = {}) {
  const buckets = supplierDiscoveryRunBuckets(diagnostics)
  if (!buckets.total) return ''
  const items = Array.isArray(diagnostics) ? diagnostics : []
  const rejectedByIntent = items.reduce((total, item) => total + (Number(item?.candidates_rejected_by_intent) || 0), 0)
  if (buckets.blocked > 0) {
    return 'Следующий шаг: открыть карточку товара вручную или внести цену из КП/прайса.'
  }
  if (rejectedByIntent > 0) {
    return 'Следующий шаг: проверить соответствие товара позиции или вставить более точную ссылку.'
  }
  if (noCandidates && candidateCount === 0 && buckets.pages > 0) {
    return 'Следующий шаг: цена не распознана автоматически, внеси цену из карточки вручную.'
  }
  return ''
}

function supplierDiscoveryNoCandidateHint(diagnostics) {
  const items = Array.isArray(diagnostics) ? diagnostics : []
  const errors = items.flatMap((item) => (Array.isArray(item?.errors) ? item.errors : []))
  const diagnosticText = errors.join(' ').toLowerCase()
  const accessBlocked = items.some((item) => item?.error_kind === 'access_blocked' || item?.skip_reason === 'access_blocked')
    || diagnosticText.includes('access_blocked')
    || diagnosticText.includes('browser_fetch_error')
    || diagnosticText.includes('captcha')
    || diagnosticText.includes('403')
    || diagnosticText.includes('429')
    || diagnosticText.includes('503')
  if (accessBlocked) {
    return 'Сайт поставщика заблокировал автоматическую проверку. Открой ссылку вручную или внеси цену из КП/прайса.'
  }

  const rejectedByIntent = items.reduce((total, item) => total + (Number(item?.candidates_rejected_by_intent) || 0), 0)
  const hasIntentReasons = items.some((item) => item?.intent_rejection_reasons && Object.keys(item.intent_rejection_reasons).length > 0)
  if (rejectedByIntent > 0 || hasIntentReasons) {
    return 'Страница прочиталась, но товар не совпал с позицией. Проверь ссылку или внеси цену вручную.'
  }

  const pagesFetched = items.reduce((total, item) => total + (Number(item?.pages_fetched) || 0), 0)
  const candidatesFound = items.reduce((total, item) => total + (Number(item?.candidates_found) || 0), 0)
  if (pagesFetched > 0 && candidatesFound === 0) {
    return 'Страница открылась, но цена не распознана. Внеси цену из карточки вручную или приложи КП/прайс.'
  }

  return 'Цена не прочиталась автоматически. Открой ссылку вручную или внеси цену из КП/прайса.'
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
  if (diagnostics.run_state === 'blocked' || diagnostics.error_kind === 'access_blocked') {
    return 'Заблокирован: сайт требует браузерную проверку'
  }
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
  const allLinks = allSupplierSearchLinks(queries)
  const catalogSearchLinks = uniqueCatalogSearchLinks(queries)
  const primaryLinks = catalogSearchLinks.length ? catalogSearchLinks : allLinks
  const bestProductLink = bestSupplierProductLink(search, primaryLinks, queries)

  return (
    <div className="supplier-search-preview">
      <span>Запросы для поиска</span>
      <BestSupplierProductLink link={bestProductLink} />
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

function BestSupplierProductLink({ link }) {
  if (!link?.url) return null
  const productLink = link.status === 'product_link'
  return (
    <section className={`supplier-best-product-link ${link.status || 'fallback_search'}`}>
      <div>
        <strong>{productLink ? 'Лучшая ссылка' : 'Поиск в каталоге'}</strong>
        <span>
          {link.label || link.provider || 'Каталог'}
          {link.source_query ? ` · ${link.source_query}` : ''}
        </span>
        <p>{link.title || (productLink ? 'Карточка товара' : 'Открыть поиск')}</p>
        {link.message && <em>{link.message}</em>}
      </div>
      <a href={link.url} target="_blank" rel="noreferrer">
        {productLink ? 'Открыть товар' : 'Открыть поиск'}
      </a>
    </section>
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

function bestSupplierProductLink(search, catalogSearchLinks, queries) {
  if (search?.best_product_link?.url) return search.best_product_link
  const fallback = bestFallbackCatalogSearchLink(queries) || catalogSearchLinks[0]
  if (!fallback?.url) return null
  return {
    status: 'fallback_search',
    provider: fallback.provider,
    label: fallback.label || fallback.provider || 'Каталог',
    title: `Открыть поиск в ${fallback.label || fallback.provider || 'каталоге'}`,
    url: fallback.url,
    search_url: fallback.url,
    source_query: fallback.source_query || queries[0]?.query || '',
    query_score: fallback.query_score,
    query_quality: fallback.query_quality,
    message: 'Открой поиск вручную и выбери подходящую карточку.',
  }
}

function bestFallbackCatalogSearchLink(queries) {
  const candidates = []
  ;(Array.isArray(queries) ? queries : []).forEach((item, queryIndex) => {
    const quickLinks = Array.isArray(item.quick_links) ? item.quick_links : []
    quickLinks.forEach((link, linkIndex) => {
      if (link?.link_kind !== 'catalog_search' || !link.url) return
      candidates.push({
        ...link,
        label: link.label || link.provider || 'Каталог',
        source_query: item.query || '',
        query_score: Number(item.query_score || 0),
        query_quality: item.query_quality || '',
        queryIndex,
        linkIndex,
      })
    })
  })
  candidates.sort((left, right) => {
    if (right.query_score !== left.query_score) return right.query_score - left.query_score
    if (left.queryIndex !== right.queryIndex) return left.queryIndex - right.queryIndex
    return left.linkIndex - right.linkIndex
  })
  return candidates[0] || null
}

function uniqueCatalogSearchLinks(queries) {
  const links = []
  const seen = new Set()
  allSupplierSearchLinks(queries).forEach((link) => {
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
  return links
}

function allSupplierSearchLinks(queries) {
  const links = []
  const seen = new Set()
  queries.forEach((item) => {
    const quickLinks = Array.isArray(item.quick_links) ? item.quick_links : []
    quickLinks.forEach((link) => {
      if (!link?.url) return
      const key = String(link.provider || link.preset_id || link.label || link.url).toLowerCase()
      if (seen.has(key)) return
      seen.add(key)
      links.push({
        ...link,
        key,
        label: link.label || link.provider || 'Поиск',
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
