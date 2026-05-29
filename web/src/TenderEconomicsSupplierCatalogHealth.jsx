export function SupplierCatalogHealthPanel({ supplierCatalogHealth, loading = false, error = '', onRefresh }) {
  const catalogs = Array.isArray(supplierCatalogHealth?.catalogs) ? supplierCatalogHealth.catalogs : []
  if (!loading && !error && !catalogs.length) return null

  return (
    <div className="supplier-catalog-health">
      <div className="supplier-catalog-health-heading">
        <span>Статус каталогов</span>
        <button
          className="secondary-button compact"
          disabled={loading || !onRefresh}
          onClick={() => ignoreCatalogActionError(onRefresh?.(true))}
          type="button"
        >
          {loading ? 'Проверяю...' : 'Проверить'}
        </button>
      </div>
      {error && <p>{error}</p>}
      {catalogs.length > 0 && (
        <div className="supplier-catalog-health-grid">
          {catalogs.map((catalog) => (
            <a
              className={`supplier-catalog-health-item ${catalog.status || 'unknown'}`}
              href={catalog.sample_url}
              key={catalog.preset_id || catalog.provider}
              target="_blank"
              rel="noreferrer"
            >
              <strong>{catalog.label || catalog.provider}</strong>
              <span>{catalog.provider}</span>
              <em>{supplierCatalogHealthStatusLabel(catalog.status, catalog.http_status, catalog.error_kind)}</em>
              {(catalog.error || catalog.body_preview) && (
                <small>{[catalog.error, catalog.body_preview].filter(Boolean).join(' · ')}</small>
              )}
            </a>
          ))}
        </div>
      )}
    </div>
  )
}

function supplierCatalogHealthStatusLabel(status, httpStatus, errorKind = '') {
  if (status === 'ok') return httpStatus ? `HTTP ${httpStatus}` : 'доступен'
  if (status === 'error' && errorKind === 'access_blocked') return httpStatus ? `блокировка ${httpStatus}` : 'блокировка'
  if (status === 'error' && errorKind === 'network_error') return 'сеть недоступна'
  if (status === 'error') return httpStatus ? `ошибка ${httpStatus}` : 'ошибка'
  return 'настроен'
}

function ignoreCatalogActionError(result) {
  if (result?.catch) {
    result.catch(() => {})
  }
}
