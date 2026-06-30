import { HelpCircle } from 'lucide-react'
import { resolveEvidenceDrilldown } from './TenderAnalysisEvidenceModel'

export function AnalysisQuestionsPanel({ questions = {}, evidenceIndex = {}, onEvidenceSelect, showHeader = true }) {
  const items = Array.isArray(questions.items) ? questions.items : []
  if (!items.length) return null
  return (
    <section className="analysis-questions-panel">
      {showHeader && (
        <div className="analysis-saas-panel-head">
          <span><HelpCircle size={15} /> Контрольные вопросы</span>
          <strong>{items.length}</strong>
        </div>
      )}
      <div className="analysis-questions-grid">
        {items.map((item) => (
          <article className={`analysis-question-card ${item.answer_status || 'not_found'}`} key={item.id || item.question}>
            <strong>{item.question}</strong>
            <p>{item.answer}</p>
            <QuestionSources
              evidenceIndex={evidenceIndex}
              onEvidenceSelect={onEvidenceSelect}
              sources={item.sources}
            />
          </article>
        ))}
      </div>
    </section>
  )
}

export function questionCount(questions = {}) {
  return Array.isArray(questions.items) ? questions.items.length : 0
}

function QuestionSources({ sources, evidenceIndex = {}, onEvidenceSelect }) {
  const visibleSources = Array.isArray(sources) ? sources.slice(0, 2) : []
  if (!visibleSources.length) return <small>Источник не найден</small>
  return (
    <ul>
      {visibleSources.map((source, index) => (
        <li key={`${source.fact_id || index}-${source.source_label || index}`}>
          <button
            className="analysis-source-button"
            onClick={() => onEvidenceSelect?.(resolveEvidenceDrilldown(source, evidenceIndex))}
            type="button"
          >
            <span>{source.source_label || source.document_name}</span>
            <em>{source.fragment}</em>
          </button>
        </li>
      ))}
    </ul>
  )
}
