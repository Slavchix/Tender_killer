import { BookOpenCheck, CalendarDays, HelpCircle, ListChecks } from 'lucide-react'
import {
  AnalysisConditionGroupsPanel,
  conditionGroupCount,
  conditionGroupSummaryLabel,
} from './TenderAnalysisConditionGroups'
import { resolveEvidenceDrilldown } from './TenderAnalysisEvidenceModel'
import { AnalysisWorkflowPanel, workflowStatusLabel } from './TenderAnalysisWorkflowPanel'

export function AnalysisSecondaryDrawers({
  conditionGroups = {},
  evidenceIndex = {},
  onEvidenceSelect,
  onWorkflowDraftChange,
  onWorkflowSubmit,
  playbooks = {},
  questions = {},
  workflow = {},
  workflowDisabled = false,
  workflowDraft,
  workflowSaving = false,
}) {
  return (
    <div className="analysis-secondary-panel-stack">
      <details className="analysis-secondary-drawer">
        <summary>
          <span><ListChecks size={15} /> Сводка условий</span>
          <strong>{conditionGroupCount(conditionGroups)}</strong>
          <em>{conditionGroupSummaryLabel(conditionGroups)}</em>
        </summary>
        <AnalysisConditionGroupsPanel
          conditionGroups={conditionGroups}
          evidenceIndex={evidenceIndex}
          onEvidenceSelect={onEvidenceSelect}
        />
      </details>
      <details className="analysis-secondary-drawer">
        <summary>
          <span><CalendarDays size={15} /> Проверка ТЗ и подсказки</span>
          <strong>{workflow.status_label || workflowStatusLabel(workflow.status)}</strong>
          <em>подсказок: {playbookCount(playbooks)}</em>
        </summary>
        <div className="analysis-secondary-drawer-body">
          <AnalysisWorkflowPanel
            disabled={workflowDisabled}
            draft={workflowDraft}
            onChange={onWorkflowDraftChange}
            onSubmit={onWorkflowSubmit}
            saving={workflowSaving}
            workflow={workflow}
          />
          <AnalysisPlaybooksPanel
            evidenceIndex={evidenceIndex}
            onEvidenceSelect={onEvidenceSelect}
            playbooks={playbooks}
          />
        </div>
      </details>
      <details className="analysis-secondary-drawer">
        <summary>
          <span><HelpCircle size={15} /> Контрольные вопросы</span>
          <strong>{questionCount(questions)}</strong>
          <em>быстрая сверка по источникам</em>
        </summary>
        <AnalysisQuestionsPanel
          evidenceIndex={evidenceIndex}
          onEvidenceSelect={onEvidenceSelect}
          questions={questions}
          showHeader={false}
        />
      </details>
    </div>
  )
}

function AnalysisQuestionsPanel({ questions = {}, evidenceIndex = {}, onEvidenceSelect, showHeader = true }) {
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

function AnalysisPlaybooksPanel({ playbooks = {}, evidenceIndex = {}, onEvidenceSelect, showHeader = true }) {
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

function questionCount(questions = {}) {
  return Array.isArray(questions.items) ? questions.items.length : 0
}

function playbookCount(playbooks = {}) {
  return Array.isArray(playbooks.items) ? playbooks.items.length : 0
}
