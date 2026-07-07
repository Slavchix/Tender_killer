import { resolveEvidenceDrilldown } from './TenderAnalysisEvidenceModel'

export function AnalysisConditionGroupsPanel({ conditionGroups = {}, evidenceIndex = {}, onEvidenceSelect }) {
  const items = Array.isArray(conditionGroups.items) ? conditionGroups.items : []
  if (!items.length) return null
  return (
    <section className="analysis-condition-groups">
      <div className="analysis-condition-list">
        {items.slice(0, 8).map((item) => (
          <article className={`analysis-condition-card status-${item.status || 'confirmed'}`} key={item.family || item.label}>
            <div>
              <strong>{item.label || item.family}</strong>
              <span>{conditionGroupStatusLabel(item.status)} · {conditionGroupSourceLabel(item.source_status)}</span>
            </div>
            <p>{item.summary || item.resolution}</p>
            <small>{item.resolution}</small>
            <ConditionGroupSources
              evidenceIndex={evidenceIndex}
              factIds={item.related_fact_ids}
              onEvidenceSelect={onEvidenceSelect}
              sources={item.sources}
            />
          </article>
        ))}
      </div>
    </section>
  )
}

export function conditionGroupCount(conditionGroups = {}) {
  return Array.isArray(conditionGroups.items) ? conditionGroups.items.length : 0
}

export function conditionGroupSummaryLabel(conditionGroups = {}) {
  const metrics = conditionGroups.metrics || {}
  const conflicts = Number(metrics.conflicts || 0)
  const missing = Number(metrics.expected_missing || 0)
  if (conflicts) return `противоречий: ${conflicts}`
  if (missing) return `не найдено: ${missing}`
  return 'по смысловым группам'
}

function ConditionGroupSources({ factIds, sources, evidenceIndex = {}, onEvidenceSelect }) {
  const ids = Array.isArray(factIds) ? factIds.filter(Boolean).slice(0, 3) : []
  const sourceLabels = Array.isArray(sources) ? sources.filter(Boolean).slice(0, 3) : []
  if (!ids.length && !sourceLabels.length) return null
  return (
    <div className="analysis-condition-sources">
      {ids.length ? ids.map((factId) => {
        const evidence = resolveEvidenceDrilldown(factId, evidenceIndex)
        return (
          <button
            disabled={!evidence || !onEvidenceSelect}
            key={factId}
            onClick={() => evidence && onEvidenceSelect?.(evidence)}
            type="button"
          >
            {evidence?.source_label || evidence?.title || factId}
          </button>
        )
      }) : sourceLabels.map((source) => (
        <span key={source}>{source}</span>
      ))}
    </div>
  )
}

function conditionGroupStatusLabel(status) {
  if (status === 'conflict') return 'противоречие'
  if (status === 'expected_missing') return 'не найдено'
  if (status === 'manual_review') return 'нужна проверка'
  return 'подтверждено'
}

function conditionGroupSourceLabel(status) {
  if (status === 'primary_source') return 'главный источник'
  if (status === 'explicit_source') return 'точный источник'
  if (status === 'conflicting_sources') return 'источники спорят'
  if (status === 'missing') return 'нет источника'
  if (status === 'needs_source_review') return 'сверить источник'
  return 'контекст источника'
}
