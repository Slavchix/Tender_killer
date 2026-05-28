import { TenderDocumentsTab } from './TenderDocumentsTab'
import { TenderSummaryTab } from './TenderSummaryTab'
import { WorkflowTabPanel } from './TenderWorkflowTab'

export function TenderTabPanels({
  tender,
  tabState,
  productState,
  documentState,
  analysisState,
  economicsState,
  workflowState,
  onOpenTab,
}) {
  const { activeTab } = tabState
  const {
    productProfiles,
  } = productState
  const {
    documentRecords,
    downloading,
    extracting,
    onDownloadDocuments,
    onExtractDocumentText,
  } = documentState
  const { analysis } = analysisState
  const { economics } = economicsState
  const {
    raw,
    note,
    saving,
    onNoteChange,
    onSaveWorkflow,
  } = workflowState

  return (
    <div className="detail-tab-panel">
      {activeTab === 'summary' && (
        <TenderSummaryTab
          tender={tender}
          economics={economics}
          analysis={analysis}
          productProfiles={productProfiles}
          documents={documentRecords}
          onOpenTab={onOpenTab}
        />
      )}

      {activeTab === 'documents' && (
        <TenderDocumentsTab
          documents={documentRecords}
          downloading={downloading}
          extracting={extracting}
          onDownload={onDownloadDocuments}
          onExtract={onExtractDocumentText}
        />
      )}

      {activeTab === 'workflow' && (
        <WorkflowTabPanel
          tender={tender}
          raw={raw}
          note={note}
          saving={saving}
          onNoteChange={onNoteChange}
          onSaveWorkflow={onSaveWorkflow}
        />
      )}
    </div>
  )
}
