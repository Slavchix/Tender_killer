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
