import { ProductAutoEconomicsPanel } from './TenderEconomicsAuto'
import { ProductEconomicsForm } from './TenderEconomicsCostForm'
import { ProductEconomicsAssumptionsForm } from './TenderEconomicsForms'
import { ProductSupplierOptionsForm } from './TenderEconomicsSuppliers'

export function TenderEconomicsProfileWorkspace({
  economics,
  selectedEconomicsProfile,
  selectedEconomicsProfileIndex = 0,
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
  savingEconomics = false,
  savingAssumptions = false,
  savingSupplierOption = false,
  importingSupplierCandidate = false,
  preparingSupplierSearch = false,
  savingSupplierCatalogPresets = false,
  discoveringDiscovery = false,
  autoSelectingSupplier = false,
  autoEstimating = false,
  acceptingAutoEconomics = false,
  supplierCatalogHealth = null,
  supplierCatalogHealthLoading = false,
  supplierCatalogHealthError = '',
  onSupplierCatalogHealthRefresh,
}) {
  return (
    <>
      <section className="economics-calculation-panel">
        <div className="economics-position-heading">
          <span>Позиция #{selectedEconomicsProfile.position_index || selectedEconomicsProfileIndex + 1}</span>
          <strong>{selectedEconomicsProfile.product_name || 'Без названия'}</strong>
        </div>
        <ProductAutoEconomicsPanel
          profile={selectedEconomicsProfile}
          onRun={onAutoEconomicsRun}
          onAccept={onAutoEconomicsAccept}
          saving={autoEstimating}
          accepting={acceptingAutoEconomics}
        />
        <ProductEconomicsForm profile={selectedEconomicsProfile} onSave={onEconomicsSave} saving={savingEconomics} />
        <ProductEconomicsAssumptionsForm
          item={economics?.items?.[selectedEconomicsProfileIndex]}
          profile={selectedEconomicsProfile}
          onSave={onEconomicsAssumptionsSave}
          saving={savingAssumptions}
        />
      </section>
      <aside className="economics-supplier-panel">
        <ProductSupplierOptionsForm
          profile={selectedEconomicsProfile}
          onSave={onSupplierOptionSave}
          onSelect={onSupplierOptionSelect}
          onAutoSelect={onSupplierOptionAutoSelect}
          onDiscoveryImport={onSupplierDiscoveryImport}
          onSearchPrepare={onSupplierSearchPrepare}
          onPresetSave={onSupplierCatalogPresetsSave}
          onDiscoveryRun={onSupplierDiscoveryRun}
          onDiscoveryUrlRun={onSupplierUrlDiscoveryRun}
          supplierCatalogHealth={supplierCatalogHealth}
          supplierCatalogHealthLoading={supplierCatalogHealthLoading}
          supplierCatalogHealthError={supplierCatalogHealthError}
          onSupplierCatalogHealthRefresh={onSupplierCatalogHealthRefresh}
          saving={savingSupplierOption}
          importingDiscovery={importingSupplierCandidate}
          preparingSearch={preparingSupplierSearch}
          savingPresets={savingSupplierCatalogPresets}
          discoveringDiscovery={discoveringDiscovery}
          autoSelecting={autoSelectingSupplier}
        />
      </aside>
    </>
  )
}
