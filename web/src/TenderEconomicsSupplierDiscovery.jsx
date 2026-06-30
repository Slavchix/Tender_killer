import { formatMoney, supplierConfidenceLabel } from './formatters'
import { ProviderRunSummary, SupplierDiscoveryDiagnostics, supplierDiscoveryNextAction, supplierDiscoveryNoCandidateHint } from './TenderEconomicsSupplierDiscoveryDiagnostics'

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

export { SupplierSearchPreview } from './TenderEconomicsSupplierSearchPreview'

function ignoreDiscoveryActionError(result) {
  if (result?.catch) {
    result.catch(() => {})
  }
}
