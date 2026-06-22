import { useEffect, useRef, useState } from 'react'
import { BookOpenCheck, CalendarDays, HelpCircle, Save, UserRound } from 'lucide-react'
import { AnalysisDecisionBrief } from './TenderAnalysisDecisionBrief'
import { AnalysisDocumentsPanel } from './TenderAnalysisDocumentsPanel'
import { AnalysisPassport } from './TenderAnalysisPassport'
import {
  AnalysisSectionBody,
  analysisSectionItems,
} from './TenderAnalysisSections'
import { AnalysisSummary } from './TenderAnalysisSummary'

export function TenderAnalysisTab({
  analysis,
  analyzing,
  preparingAnalysis,
  downloading,
  extracting,
  onPrepareAnalysis,
  onDownload,
  onExtract,
  onAnalysisFeedback,
  onAnalysisWorkflow,
  savingAnalysisFeedbackId,
  savingAnalysisWorkflow,
  reportHref,
  documents = [],
}) {
  const [selectedAnalysisSection, setSelectedAnalysisSection] = useState('decision_risks')
  const [analysisViewMode, setAnalysisViewMode] = useState('compact')
  const userSelectedAnalysisSectionRef = useRef(false)
  const analysisSections = analysisSectionItems(analysis, documents)
  const analysisSectionKey = analysisSections.map((section) => section.id).join('|')
  const analysisActionDisabled = preparingAnalysis || downloading || extracting || analyzing
  const primarySection = analysis?.operator_view?.decision_brief?.primary_section
  const tzWorkflow = analysis?.operator_view?.tz_workflow || {}
  const aiQuestions = analysis?.operator_view?.ai_questions || {}
  const playbooks = analysis?.operator_view?.playbooks || {}
  const analysisHistory = analysis?.analysis_history || []
  const [workflowDraft, setWorkflowDraft] = useState(workflowDraftFromContract(tzWorkflow))

  useEffect(() => {
    const sectionIds = new Set(analysisSections.map((section) => section.id))
    setSelectedAnalysisSection((currentSection) => {
      if (!userSelectedAnalysisSectionRef.current && primarySection && sectionIds.has(primarySection)) {
        return primarySection
      }
      if (!sectionIds.has(currentSection)) {
        userSelectedAnalysisSectionRef.current = false
        return analysisSections[0]?.id || 'decision_risks'
      }
      return currentSection
    })
  }, [analysisSectionKey, primarySection])

  useEffect(() => {
    setWorkflowDraft(workflowDraftFromContract(tzWorkflow))
  }, [tzWorkflow.status, tzWorkflow.responsible, tzWorkflow.deadline, tzWorkflow.comment])

  function selectAnalysisSection(sectionId) {
    userSelectedAnalysisSectionRef.current = true
    setSelectedAnalysisSection(sectionId)
  }

  function updateWorkflowDraft(field, value) {
    setWorkflowDraft((current) => ({ ...current, [field]: value }))
  }

  function saveWorkflowDraft(event) {
    event.preventDefault()
    onAnalysisWorkflow?.(workflowDraft)
  }

  return (
    <section className="detail-section active analysis-section">
      <div className="section-heading-row analysis-action-row">
        <div>
          <h3>Анализ ТЗ</h3>
          <p className="muted-text">Риски, требования и доказательства из документов.</p>
        </div>
        <div className="analysis-actions">
          <button className="primary-button compact" disabled={analysisActionDisabled} onClick={onPrepareAnalysis} type="button">
            {preparingAnalysis ? 'Готовлю...' : 'Подготовить анализ'}
          </button>
          <a className="secondary-link-button compact" href={reportHref}>
            Скачать Word
          </a>
        </div>
      </div>

      <AnalysisDocumentsPanel
        documents={documents}
        preparing={preparingAnalysis}
        downloading={downloading}
        extracting={extracting}
        onDownload={onDownload}
        onExtract={onExtract}
      />
      <AnalysisHistory history={analysisHistory} />
      <AnalysisSummary analysis={analysis} documents={documents} />
      <AnalysisDecisionBrief
        analysis={analysis}
        documents={documents}
        onOpenSection={selectAnalysisSection}
      />
      {analysis ? (
        <div className="analysis-saas-grid">
          <AnalysisWorkflowPanel
            disabled={!onAnalysisWorkflow || savingAnalysisWorkflow}
            draft={workflowDraft}
            onChange={updateWorkflowDraft}
            onSubmit={saveWorkflowDraft}
            saving={savingAnalysisWorkflow}
            workflow={tzWorkflow}
          />
          <AnalysisQuestionsPanel questions={aiQuestions} />
          <AnalysisPlaybooksPanel playbooks={playbooks} />
        </div>
      ) : null}
      <AnalysisPassport
        analysis={analysis}
        sections={analysisSections}
        selectedSection={selectedAnalysisSection}
        onSelectSection={selectAnalysisSection}
      />

      <div className="analysis-workspace">
        <div className="analysis-main-panel">
          {analysis ? (
            <AnalysisSectionBody
              sectionId={selectedAnalysisSection}
              analysis={analysis}
              documents={documents}
              viewMode={analysisViewMode}
              onViewModeChange={setAnalysisViewMode}
              onFeedback={onAnalysisFeedback}
              savingFeedbackId={savingAnalysisFeedbackId}
            />
          ) : (
            <p className="muted-text">Сначала извлеки текст документов, затем запусти анализ ТЗ.</p>
          )}
        </div>

      </div>
    </section>
  )
}

function AnalysisWorkflowPanel({ workflow = {}, draft, disabled = false, saving = false, onChange, onSubmit }) {
  const statuses = Array.isArray(workflow.statuses) ? workflow.statuses : []
  const journal = Array.isArray(workflow.journal) ? workflow.journal.slice(-4).reverse() : []
  return (
    <form className="analysis-workflow-panel" onSubmit={onSubmit}>
      <div className="analysis-saas-panel-head">
        <span><CalendarDays size={15} /> Workflow ТЗ</span>
        <strong>{workflow.status_label || workflow.status || 'analysis_ready'}</strong>
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
          <select disabled={disabled} onChange={(event) => onChange?.('status', event.target.value)} value={draft.status}>
            {statuses.map((status) => (
              <option key={status.id} value={status.id}>{status.label || status.id}</option>
            ))}
          </select>
        </label>
        <label>
          <span><UserRound size={13} /> Ответственный</span>
          <input disabled={disabled} onChange={(event) => onChange?.('responsible', event.target.value)} value={draft.responsible} />
        </label>
        <label>
          <span>Дедлайн</span>
          <input disabled={disabled} onChange={(event) => onChange?.('deadline', event.target.value)} type="date" value={draft.deadline} />
        </label>
        <label className="wide">
          <span>Комментарий</span>
          <textarea disabled={disabled} onChange={(event) => onChange?.('comment', event.target.value)} rows={2} value={draft.comment} />
        </label>
      </div>
      <button className="secondary-button compact" disabled={disabled} type="submit">
        <Save size={15} /> {saving ? 'Сохраняю...' : 'Сохранить'}
      </button>
      {journal.length ? (
        <div className="analysis-workflow-journal">
          {journal.map((entry, index) => (
            <span key={`${entry.changed_at || index}-${entry.action || index}`}>
              {entry.actor || 'operator'} · {entry.comment || entry.action}
            </span>
          ))}
        </div>
      ) : null}
    </form>
  )
}

function AnalysisQuestionsPanel({ questions = {} }) {
  const items = Array.isArray(questions.items) ? questions.items : []
  if (!items.length) return null
  return (
    <section className="analysis-questions-panel">
      <div className="analysis-saas-panel-head">
        <span><HelpCircle size={15} /> AI-вопросы</span>
        <strong>{items.length}</strong>
      </div>
      <div className="analysis-questions-grid">
        {items.map((item) => (
          <article className={`analysis-question-card ${item.answer_status || 'not_found'}`} key={item.id || item.question}>
            <strong>{item.question}</strong>
            <p>{item.answer}</p>
            <QuestionSources sources={item.sources} />
          </article>
        ))}
      </div>
    </section>
  )
}

function QuestionSources({ sources }) {
  const visibleSources = Array.isArray(sources) ? sources.slice(0, 2) : []
  if (!visibleSources.length) return <small>Источник не найден</small>
  return (
    <ul>
      {visibleSources.map((source, index) => (
        <li key={`${source.fact_id || index}-${source.source_label || index}`}>
          <span>{source.source_label || source.document_name}</span>
          <em>{source.fragment}</em>
        </li>
      ))}
    </ul>
  )
}

function AnalysisPlaybooksPanel({ playbooks = {} }) {
  const items = Array.isArray(playbooks.items) ? playbooks.items : []
  if (!items.length) return null
  return (
    <section className="analysis-playbooks-panel">
      <div className="analysis-saas-panel-head">
        <span><BookOpenCheck size={15} /> Playbooks</span>
        <strong>{items.length}</strong>
      </div>
      <div className="analysis-playbook-list">
        {items.map((item) => (
          <article className={`analysis-playbook-card severity-${item.severity || 'medium'}`} key={item.id || item.title}>
            <strong>{item.title}</strong>
            <p>{item.summary}</p>
            <PlaybookList values={item.what_to_do} />
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

function workflowDraftFromContract(workflow = {}) {
  return {
    status: workflow.status || 'analysis_ready',
    responsible: workflow.responsible || '',
    deadline: workflow.deadline || '',
    comment: workflow.comment || '',
  }
}

function AnalysisHistory({ history = [] }) {
  const visibleHistory = Array.isArray(history) ? history.slice(0, 5) : []
  if (!visibleHistory.length) {
    return null
  }
  return (
    <details className="analysis-history">
      <summary>История анализа ({visibleHistory.length})</summary>
      <div className="analysis-history-list">
        {visibleHistory.map((entry) => {
          const changes = entry.changes || {}
          return (
            <article className="analysis-history-row" key={entry.id || entry.run_number || entry.analyzed_at}>
              <div>
                <strong>Версия {entry.run_number || '1'}</strong>
                <span>{formatAnalysisHistoryDate(entry.analyzed_at)}</span>
              </div>
              <p>{changes.summary || 'Изменения не зафиксированы.'}</p>
              <small>
                +{changes.added_count || 0} / -{changes.removed_count || 0} / Δ{changes.changed_count || 0}
                {changes.feedback_count ? ` · меток: ${changes.feedback_count}` : ''}
              </small>
              <AnalysisHistoryDetails changes={changes} />
            </article>
          )
        })}
      </div>
    </details>
  )
}

function AnalysisHistoryDetails({ changes = {} }) {
  const documents = changes.documents || {}
  const conditionChanges = Array.isArray(changes.condition_changes)
    ? changes.condition_changes.map(formatConditionChange).filter(Boolean)
    : []
  const groups = [
    ['Добавлено', changes.added],
    ['Изменено', changes.changed],
    ['Удалено', changes.removed],
    ['Метки оператора', changes.feedback],
    ['Документы добавлены', documents.added],
    ['Документы изменены', documents.changed],
    ['Документы удалены', documents.removed],
    ['Изменившиеся условия', conditionChanges],
  ]
    .map(([label, values]) => [label, Array.isArray(values) ? values.filter(Boolean).slice(0, 5) : []])
    .filter(([, values]) => values.length)

  if (!groups.length) {
    return null
  }
  return (
    <details className="analysis-history-details">
      <summary>Показать изменения</summary>
      <div>
        {groups.map(([label, values]) => (
          <section key={label}>
            <strong>{label}</strong>
            <ul>
              {values.map((value) => (
                <li key={value}>{value}</li>
              ))}
            </ul>
          </section>
        ))}
      </div>
    </details>
  )
}

function formatConditionChange(item = {}) {
  const label = item.label || item.family || 'условие'
  const type = item.change_type === 'added'
    ? 'добавлено'
    : item.change_type === 'removed'
      ? 'удалено'
      : 'изменено'
  return `${label}: ${type}`
}

function formatAnalysisHistoryDate(value) {
  if (!value) {
    return 'дата не указана'
  }
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) {
    return String(value)
  }
  return parsed.toLocaleString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}
