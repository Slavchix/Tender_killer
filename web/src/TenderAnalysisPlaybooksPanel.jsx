import { BookOpenCheck } from 'lucide-react'
import { resolveEvidenceDrilldown } from './TenderAnalysisEvidenceModel'

export function AnalysisPlaybooksPanel({ playbooks = {}, evidenceIndex = {}, onEvidenceSelect, showHeader = true }) {
  const items = Array.isArray(playbooks.items) ? playbooks.items : []
  if (!items.length) return null
  return (
    <section className="analysis-playbooks-panel">
      {showHeader && (
        <div className="analysis-saas-panel-head">
          <span><BookOpenCheck size={15} /> Подсказки оператора</span>
          <strong>{items.length}</strong>
        </div>
      )}
      <div className="analysis-playbook-list">
        {items.map((item) => (
          <article className={`analysis-playbook-card severity-${item.severity || 'medium'}`} key={item.id || item.title}>
            <strong>{item.title}</strong>
            <p>{item.summary}</p>
            <PlaybookList values={item.what_to_do} />
            <PlaybookEvidenceButtons
              evidenceIndex={evidenceIndex}
              factIds={item.source_fact_ids}
              onEvidenceSelect={onEvidenceSelect}
            />
          </article>
        ))}
      </div>
    </section>
  )
}

export function playbookCount(playbooks = {}) {
  return Array.isArray(playbooks.items) ? playbooks.items.length : 0
}

function PlaybookList({ values }) {
  const items = Array.isArray(values) ? values.filter(Boolean).slice(0, 3) : []
  if (!items.length) return null
  return (
    <ul>
      {items.map((value) => (
        <li key={value}>{value}</li>
      ))}
    </ul>
  )
}

function PlaybookEvidenceButtons({ factIds, evidenceIndex = {}, onEvidenceSelect }) {
  const ids = Array.isArray(factIds) ? factIds.filter(Boolean).slice(0, 3) : []
  if (!ids.length || !onEvidenceSelect) return null
  return (
    <div className="analysis-playbook-sources">
      {ids.map((factId) => {
        const evidence = resolveEvidenceDrilldown(factId, evidenceIndex)
        if (!evidence) return null
        return (
          <button key={factId} onClick={() => onEvidenceSelect(evidence)} type="button">
            {evidence.source_label || evidence.title || factId}
          </button>
        )
      })}
    </div>
  )
}
