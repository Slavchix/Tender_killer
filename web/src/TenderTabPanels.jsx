import { TenderSummaryTab } from './TenderSummaryTab'
import { WorkflowTabPanel } from './TenderWorkflowTab'

export function TenderTabPanels({
  tender,
  productState,
  documentState,
  analysisState,
  economicsState,
  workflowState,
  onOpenTab,
}) {
  const {
    productProfiles,
  } = productState
  const {
    documentRecords,
  } = documentState
  const { analysis } = analysisState
  const { economics } = economicsState
  const {
    note,
    saving,
    onNoteChange,
    onSaveWorkflow,
  } = workflowState

  return (
    <div className="detail-tab-panel">
      <TenderSummaryTab
        tender={tender}
        economics={economics}
        analysis={analysis}
        productProfiles={productProfiles}
        documents={documentRecords}
        onOpenTab={onOpenTab}
      />

      <WorkflowTabPanel
        tender={tender}
        note={note}
        saving={saving}
        onNoteChange={onNoteChange}
        onSaveWorkflow={onSaveWorkflow}
      />
    </div>
  )
}
