import { AnalysisDecisionBrief } from './TenderAnalysisDecisionBrief'
import { AnalysisDocumentsPanel } from './TenderAnalysisDocumentsPanel'
import { AnalysisEvidenceDrilldownPanel } from './TenderAnalysisEvidenceDrilldown'
import { AnalysisHistory } from './TenderAnalysisHistory'
import { AnalysisPassport } from './TenderAnalysisPassport'
import { AnalysisSecondaryDrawers } from './TenderAnalysisSecondaryDrawers'
import { AnalysisSectionBody } from './TenderAnalysisSections'
import { AnalysisSummary } from './TenderAnalysisSummary'
import { useTenderAnalysisWorkflowDraft } from './useTenderAnalysisWorkflowDraft'
import { useTenderAnalysisWorkspace } from './useTenderAnalysisWorkspace'

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
  const analysisActionDisabled = preparingAnalysis || downloading || extracting || analyzing
  const tzWorkflow = analysis?.operator_view?.tz_workflow || {}
  const conditionGroups = analysis?.operator_view?.condition_groups || {}
  const aiQuestions = analysis?.operator_view?.ai_questions || {}
  const playbooks = analysis?.operator_view?.playbooks || {}
  const analysisHistory = analysis?.analysis_history || []
  const {
    analysisSections,
    analysisViewMode,
    evidenceDrilldowns,
    selectAnalysisSection,
    selectEvidenceDrilldown,
    selectedAnalysisSection,
    selectedEvidence,
    setAnalysisViewMode,
  } = useTenderAnalysisWorkspace(analysis, documents)
  const {
    saveWorkflowDraft,
    updateWorkflowDraft,
    workflowDraft,
  } = useTenderAnalysisWorkflowDraft(tzWorkflow, onAnalysisWorkflow)

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
