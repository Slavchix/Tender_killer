import { TenderProductsTab } from './TenderProductsTab'
import { TenderDocumentsTab } from './TenderDocumentsTab'
import { TenderSummaryTab } from './TenderSummaryTab'
import { WorkflowTabPanel } from './TenderWorkflowTab'

export function TenderTabPanels({
  activeTab,
  tender,
  raw,
  productProfiles,
  productProfileSummary,
  selectedProfileIndex,
  onSelectedProfileIndexChange,
  profilesLoading,
  onRebuildProductProfiles,
  documentRecords,
  downloading,
  extracting,
  onDownloadDocuments,
  onExtractDocumentText,
  analysis,
  economics,
  onOpenTab,
  note,
  saving,
  onNoteChange,
  onSaveWorkflow,
}) {
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

      {activeTab === 'products' && (
        <TenderProductsTab
          tender={tender}
          productProfiles={productProfiles}
          productProfileSummary={productProfileSummary}
          selectedProfileIndex={selectedProfileIndex}
          onSelectedProfileIndexChange={onSelectedProfileIndexChange}
          profilesLoading={profilesLoading}
          onRebuildProductProfiles={onRebuildProductProfiles}
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
