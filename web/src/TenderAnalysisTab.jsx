import { useEffect, useRef, useState } from 'react'
import { AnalysisDecisionBrief } from './TenderAnalysisDecisionBrief'
import { AnalysisDocumentsPanel } from './TenderAnalysisDocumentsPanel'
import { AnalysisEvidenceDrilldownPanel } from './TenderAnalysisEvidenceDrilldown'
import { resolveEvidenceDrilldown } from './TenderAnalysisEvidenceModel'
import { AnalysisHistory } from './TenderAnalysisHistory'
import { AnalysisPassport } from './TenderAnalysisPassport'
import { AnalysisSecondaryDrawers } from './TenderAnalysisSecondaryDrawers'
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
  const conditionGroups = analysis?.operator_view?.condition_groups || {}
  const aiQuestions = analysis?.operator_view?.ai_questions || {}
  const playbooks = analysis?.operator_view?.playbooks || {}
  const evidenceDrilldowns = analysis?.operator_view?.evidence_drilldowns || {}
  const analysisHistory = analysis?.analysis_history || []
  const [workflowDraft, setWorkflowDraft] = useState(workflowDraftFromContract(tzWorkflow))
  const [selectedEvidence, setSelectedEvidence] = useState(null)

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

  useEffect(() => {
    setSelectedEvidence(null)
  }, [analysis?.analyzed_at, analysis?.status])

  function selectAnalysisSection(sectionId) {
    userSelectedAnalysisSectionRef.current = true
    setSelectedAnalysisSection(sectionId)
  }

  function selectEvidenceDrilldown(value) {
    setSelectedEvidence(resolveEvidenceDrilldown(value, evidenceDrilldowns))
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
            Скачать отчет
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
        <AnalysisSecondaryDrawers
          conditionGroups={conditionGroups}
          evidenceIndex={evidenceDrilldowns}
          onEvidenceSelect={selectEvidenceDrilldown}
          onWorkflowDraftChange={updateWorkflowDraft}
          onWorkflowSubmit={saveWorkflowDraft}
          playbooks={playbooks}
          questions={aiQuestions}
          workflow={tzWorkflow}
          workflowDisabled={!onAnalysisWorkflow || savingAnalysisWorkflow}
          workflowDraft={workflowDraft}
          workflowSaving={savingAnalysisWorkflow}
        />
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
              onEvidenceSelect={selectEvidenceDrilldown}
              viewMode={analysisViewMode}
              onViewModeChange={setAnalysisViewMode}
              onFeedback={onAnalysisFeedback}
              savingFeedbackId={savingAnalysisFeedbackId}
            />
          ) : (
            <p className="muted-text">Сначала извлеки текст документов, затем запусти анализ ТЗ.</p>
          )}
        </div>
        {analysis ? (
          <AnalysisEvidenceDrilldownPanel
            evidenceIndex={evidenceDrilldowns}
            selectedEvidence={selectedEvidence}
          />
        ) : null}
      </div>
    </section>
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
