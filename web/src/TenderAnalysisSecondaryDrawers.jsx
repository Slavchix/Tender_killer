import { CalendarDays, HelpCircle, ListChecks } from 'lucide-react'
import {
  AnalysisConditionGroupsPanel,
  conditionGroupCount,
  conditionGroupSummaryLabel,
} from './TenderAnalysisConditionGroups'
import { AnalysisPlaybooksPanel, playbookCount } from './TenderAnalysisPlaybooksPanel'
import { AnalysisQuestionsPanel, questionCount } from './TenderAnalysisQuestionsPanel'
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
