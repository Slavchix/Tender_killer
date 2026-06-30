import { BookOpenCheck, CalendarDays, HelpCircle, ListChecks, Save, UserRound } from 'lucide-react'
import { resolveEvidenceDrilldown } from './TenderAnalysisEvidenceModel'

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

function AnalysisConditionGroupsPanel({ conditionGroups = {}, evidenceIndex = {}, onEvidenceSelect }) {
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

function AnalysisWorkflowPanel({ workflow = {}, draft, disabled = false, saving = false, onChange, onSubmit }) {
  const statuses = Array.isArray(workflow.statuses) ? workflow.statuses : []
  const journal = Array.isArray(workflow.journal) ? workflow.journal.slice(-4).reverse() : []
  const safeDraft = draft || {
    status: workflow.status || 'analysis_ready',
    responsible: '',
    deadline: '',
    comment: '',
  }
  return (
    <form className="analysis-workflow-panel" onSubmit={onSubmit}>
      <div className="analysis-saas-panel-head">
        <span><CalendarDays size={15} /> Рабочий процесс ТЗ</span>
        <strong>{workflow.status_label || workflowStatusLabel(workflow.status)}</strong>
      </div>
      <div className="analysis-workflow-steps">
        {statuses.map((status) => (
          <span className={status.current ? 'current' : status.done ? 'done' : ''} key={status.id}>
            {status.label || status.id}
          </span>
        ))}
      </div>
      <div className="analysis-workflow-form">
        <label>
          <span>Статус</span>
          <select disabled={disabled} onChange={(event) => onChange?.('status', event.target.value)} value={safeDraft.status}>
            {statuses.map((status) => (
              <option key={status.id} value={status.id}>{status.label || status.id}</option>
            ))}
          </select>
        </label>
        <label>
          <span><UserRound size={13} /> Ответственный</span>
          <input disabled={disabled} onChange={(event) => onChange?.('responsible', event.target.value)} value={safeDraft.responsible} />
        </label>
        <label>
          <span>Дедлайн</span>
          <input disabled={disabled} onChange={(event) => onChange?.('deadline', event.target.value)} type="date" value={safeDraft.deadline} />
        </label>
        <label className="wide">
          <span>Комментарий</span>
          <textarea disabled={disabled} onChange={(event) => onChange?.('comment', event.target.value)} rows={2} value={safeDraft.comment} />
        </label>
      </div>
      <button className="secondary-button compact" disabled={disabled} type="submit">
        <Save size={15} /> {saving ? 'Сохраняю...' : 'Сохранить'}
      </button>
      {journal.length ? (
        <div className="analysis-workflow-journal">
          {journal.map((entry, index) => (
            <span key={`${entry.changed_at || index}-${entry.action || index}`}>
              {entry.actor || 'оператор'} · {entry.comment || entry.action}
            </span>
          ))}
        </div>
      ) : null}
    </form>
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

function workflowStatusLabel(status) {
  const labels = {
    documents_not_downloaded: 'документы не скачаны',
    text_extracted: 'текст извлечен',
    analysis_ready: 'анализ готов',
    operator_checked: 'оператор проверил',
    has_blockers: 'есть блокеры',
  }
  return labels[status] || 'анализ готов'
}

function questionCount(questions = {}) {
  return Array.isArray(questions.items) ? questions.items.length : 0
}

function playbookCount(playbooks = {}) {
  return Array.isArray(playbooks.items) ? playbooks.items.length : 0
}

function conditionGroupCount(conditionGroups = {}) {
  return Array.isArray(conditionGroups.items) ? conditionGroups.items.length : 0
}

function conditionGroupSummaryLabel(conditionGroups = {}) {
  const metrics = conditionGroups.metrics || {}
  const conflicts = Number(metrics.conflicts || 0)
  const missing = Number(metrics.expected_missing || 0)
  if (conflicts) return `противоречий: ${conflicts}`
  if (missing) return `не найдено: ${missing}`
  return 'по смысловым группам'
}
