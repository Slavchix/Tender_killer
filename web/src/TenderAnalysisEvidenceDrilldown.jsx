import { FileSearch } from 'lucide-react'
import { evidenceIndexItems, uniqueEvidenceNotes } from './TenderAnalysisEvidenceModel'

export function AnalysisEvidenceDrilldownPanel({ evidenceIndex = {}, selectedEvidence }) {
  const evidence = selectedEvidence || evidenceIndexItems(evidenceIndex)[0]
  if (!evidence) {
    return (
      <aside className="analysis-evidence-drilldown empty">
        <div className="analysis-saas-panel-head">
          <span><FileSearch size={15} /> Источник</span>
        </div>
        <p>Выберите факт, вопрос или подсказку, чтобы увидеть фрагмент документа.</p>
      </aside>
    )
  }
  const sourceBinding = evidence.source_binding && typeof evidence.source_binding === 'object' ? evidence.source_binding : {}
  const confidence = evidence.confidence_level && typeof evidence.confidence_level === 'object' ? evidence.confidence_level : {}
  const quality = evidence.evidence_quality && typeof evidence.evidence_quality === 'object' ? evidence.evidence_quality : {}
  const relatedFactIds = Array.isArray(evidence.related_fact_ids) ? evidence.related_fact_ids : []
  const evidenceNotes = uniqueEvidenceNotes([sourceBinding.detail, quality.detail])
  return (
    <aside className="analysis-evidence-drilldown">
      <div className="analysis-saas-panel-head">
        <span><FileSearch size={15} /> Источник</span>
        <strong>{quality.label || sourceBinding.label || evidence.source_label || 'фрагмент'}</strong>
      </div>
      <div className="analysis-evidence-drilldown-title">
        <strong>{evidence.title || evidence.label || evidence.question || 'Источник'}</strong>
        <span>{evidence.source_label || evidence.document_name || 'Источник не привязан'}</span>
      </div>
      <div className="analysis-evidence-meta">
        {sourceBinding.label && <span className={`analysis-source-binding-${sourceBinding.level || 'context'}`}>{sourceBinding.label}</span>}
        {confidence.label && <span className={`analysis-confidence-${confidence.level || 'medium'}`}>{confidence.label}</span>}
        {quality.label && <span className={`analysis-evidence-quality-${quality.level || 'context'}`}>{quality.label}</span>}
      </div>
      {evidenceNotes.map((note) => (
        <p key={note}>{note}</p>
      ))}
      {evidence.fragment && (
        <blockquote className="analysis-evidence-fragment">
          {evidence.fragment}
        </blockquote>
      )}
      {evidence.source_context && evidence.source_context !== evidence.fragment && (
        <p className="analysis-evidence-context">{evidence.source_context}</p>
      )}
      {relatedFactIds.length ? (
        <div className="analysis-evidence-related">
          <span>Связанные факты</span>
          <strong>{relatedFactIds.join(', ')}</strong>
        </div>
      ) : null}
    </aside>
  )
}
