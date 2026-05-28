import { useEffect } from 'react'
import { TenderEconomicsMetrics } from './TenderEconomicsMetrics'
import { EconomicsSummary } from './TenderEconomicsSummary'
import { TenderEconomicsWorkbench } from './TenderEconomicsWorkbench'

export function TenderEconomicsTab({
  tender,
  economics,
  productProfiles = [],
  selectedEconomicsProfileIndex = 0,
  onSelectedEconomicsProfileChange,
  onEconomicsSave,
  onEconomicsAssumptionsSave,
  onSupplierOptionSave,
  onSupplierOptionSelect,
  onSupplierOptionAutoSelect,
  onSupplierDiscoveryImport,
  onSupplierSearchPrepare,
  onSupplierCatalogPresetsSave,
  onSupplierDiscoveryRun,
  onSupplierUrlDiscoveryRun,
  onAutoEconomicsRun,
  onAutoEconomicsAccept,
  savingEconomicsPosition = null,
  savingAssumptionsPosition = null,
  savingSupplierOptionPosition = null,
  importingSupplierCandidatePosition = null,
  preparingSupplierSearchPosition = null,
  savingSupplierCatalogPresetPosition = null,
  discoveringSupplierPosition = null,
  autoSelectingSupplierPosition = null,
  autoEstimatingPosition = null,
  acceptingAutoEconomicsPosition = null,
  supplierCatalogHealth = null,
  supplierCatalogHealthLoading = false,
  supplierCatalogHealthError = '',
  onSupplierCatalogHealthRefresh,
}) {
  const profiles = productProfiles || []

  useEffect(() => {
    if (supplierCatalogHealth || supplierCatalogHealthLoading || supplierCatalogHealthError) return
    onSupplierCatalogHealthRefresh?.(false)?.catch?.(() => {})
  }, [
    onSupplierCatalogHealthRefresh,
    supplierCatalogHealth,
    supplierCatalogHealthLoading,
    supplierCatalogHealthError,
  ])

  return (
    <section className="detail-section active economics-section">
      <div className="section-heading-row">
        <h3>Экономика</h3>
      </div>
      <TenderEconomicsMetrics economics={economics} tender={tender} />
      <EconomicsSummary economics={economics} tender={tender} />
      <TenderEconomicsWorkbench
        economics={economics}
        profiles={profiles}
        selectedEconomicsProfileIndex={selectedEconomicsProfileIndex}
        onSelectedEconomicsProfileChange={onSelectedEconomicsProfileChange}
        onEconomicsSave={onEconomicsSave}
        onEconomicsAssumptionsSave={onEconomicsAssumptionsSave}
        onSupplierOptionSave={onSupplierOptionSave}
        onSupplierOptionSelect={onSupplierOptionSelect}
        onSupplierOptionAutoSelect={onSupplierOptionAutoSelect}
        onSupplierDiscoveryImport={onSupplierDiscoveryImport}
        onSupplierSearchPrepare={onSupplierSearchPrepare}
        onSupplierCatalogPresetsSave={onSupplierCatalogPresetsSave}
        onSupplierDiscoveryRun={onSupplierDiscoveryRun}
        onSupplierUrlDiscoveryRun={onSupplierUrlDiscoveryRun}
        onAutoEconomicsRun={onAutoEconomicsRun}
        onAutoEconomicsAccept={onAutoEconomicsAccept}
        savingEconomicsPosition={savingEconomicsPosition}
        savingAssumptionsPosition={savingAssumptionsPosition}
        savingSupplierOptionPosition={savingSupplierOptionPosition}
        importingSupplierCandidatePosition={importingSupplierCandidatePosition}
        preparingSupplierSearchPosition={preparingSupplierSearchPosition}
        savingSupplierCatalogPresetPosition={savingSupplierCatalogPresetPosition}
        discoveringSupplierPosition={discoveringSupplierPosition}
        autoSelectingSupplierPosition={autoSelectingSupplierPosition}
        autoEstimatingPosition={autoEstimatingPosition}
        acceptingAutoEconomicsPosition={acceptingAutoEconomicsPosition}
        supplierCatalogHealth={supplierCatalogHealth}
        supplierCatalogHealthLoading={supplierCatalogHealthLoading}
        supplierCatalogHealthError={supplierCatalogHealthError}
        onSupplierCatalogHealthRefresh={onSupplierCatalogHealthRefresh}
      />
    </section>
  )
}
