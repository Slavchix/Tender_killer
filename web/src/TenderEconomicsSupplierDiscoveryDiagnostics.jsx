import {
  compactDiscoveryErrors,
  compactIntentRejectionReasons,
  formatDiscoveryRunState,
  supplierDiscoveryRunBuckets,
} from './TenderEconomicsSupplierDiscoveryDiagnosticsModel'

export {
  supplierDiscoveryNextAction,
  supplierDiscoveryNoCandidateHint,
} from './TenderEconomicsSupplierDiscoveryDiagnosticsModel'

export function ProviderRunSummary({ diagnostics }) {
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

export function SupplierDiscoveryDiagnostics({ diagnostics }) {
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
