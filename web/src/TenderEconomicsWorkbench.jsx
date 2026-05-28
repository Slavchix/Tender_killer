import { ProductAutoEconomicsPanel } from './TenderEconomicsAuto'
import {
  ProductEconomicsAssumptionsForm,
  ProductEconomicsForm,
} from './TenderEconomicsForms'
import { EconomicsPositionRail } from './TenderEconomicsPositionRail'
import { ProductSupplierOptionsForm } from './TenderEconomicsSuppliers'

export function TenderEconomicsWorkbench({
  economics,
  profiles = [],
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
  const selectedEconomicsProfile = profiles[selectedEconomicsProfileIndex] || profiles[0] || null
  const selectedPosition = selectedEconomicsProfile?.position_index
  const savingEconomics = savingEconomicsPosition === selectedPosition
  const savingAssumptions = savingAssumptionsPosition === selectedPosition
  const savingSupplierOption = savingSupplierOptionPosition === selectedPosition
  const importingSupplierCandidate = importingSupplierCandidatePosition === selectedPosition
  const preparingSupplierSearch = preparingSupplierSearchPosition === selectedPosition
  const savingSupplierCatalogPresets = savingSupplierCatalogPresetPosition === selectedPosition
  const discoveringDiscovery = discoveringSupplierPosition === selectedPosition
  const autoSelectingSupplier = autoSelectingSupplierPosition === selectedPosition
  const autoEstimating = autoEstimatingPosition === selectedPosition
  const acceptingAutoEconomics = acceptingAutoEconomicsPosition === selectedPosition

  return (
    <div className="economics-workbench economics-workspace-grid">
      <EconomicsPositionRail
        profiles={profiles}
        selectedEconomicsProfileIndex={selectedEconomicsProfileIndex}
        onSelectedEconomicsProfileChange={onSelectedEconomicsProfileChange}
      />
      <>
        {selectedEconomicsProfile ? (
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
        ) : (
          <section className="economics-calculation-panel economics-empty-panel">
            <p className="muted-text">Сначала обнови детали закупки, чтобы появились товарные позиции.</p>
          </section>
        )}
      </>
    </div>
  )
}
