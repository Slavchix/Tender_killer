import {
  SupplierDiscoveryPreview,
  SupplierSearchPreview,
} from './TenderEconomicsSupplierDiscovery'
import { SupplierInputForm } from './TenderEconomicsSupplierInputForm'
import { SupplierOptionsList } from './TenderEconomicsSupplierOptions'

export function ProductSupplierOptionsForm({
  profile,
  onSave,
  onSelect,
  onAutoSelect,
  onDiscoveryImport,
  onSearchPrepare,
  onPresetSave,
  onDiscoveryRun,
  onDiscoveryUrlRun,
  supplierCatalogHealth,
  supplierCatalogHealthLoading = false,
  supplierCatalogHealthError = '',
  onSupplierCatalogHealthRefresh,
  saving = false,
  importingDiscovery = false,
  preparingSearch = false,
  savingPresets = false,
  discoveringDiscovery = false,
  autoSelecting = false,
}) {
  const supplierOptions = Array.isArray(profile?.raw_payload?.supplier_options)
    ? profile.raw_payload.supplier_options
    : []
  const supplierSearch = profile?.raw_payload?.supplier_search || null
  const supplierDiscovery = profile?.raw_payload?.supplier_discovery || null
  const supplierSearchQueries = Array.isArray(supplierSearch?.queries) ? supplierSearch.queries : []

  return (
    <section className="profile-block supplier-options-block">
      <SupplierInputForm
        profile={profile}
        supplierOptions={supplierOptions}
        supplierSearchQueries={supplierSearchQueries}
        onSave={onSave}
        onAutoSelect={onAutoSelect}
        onSearchPrepare={onSearchPrepare}
        onPresetSave={onPresetSave}
        onDiscoveryRun={onDiscoveryRun}
        onDiscoveryUrlRun={onDiscoveryUrlRun}
        supplierCatalogHealth={supplierCatalogHealth}
        supplierCatalogHealthLoading={supplierCatalogHealthLoading}
        supplierCatalogHealthError={supplierCatalogHealthError}
        onSupplierCatalogHealthRefresh={onSupplierCatalogHealthRefresh}
        saving={saving}
        preparingSearch={preparingSearch}
        savingPresets={savingPresets}
        discoveringDiscovery={discoveringDiscovery}
        autoSelecting={autoSelecting}
      />
      <SupplierSearchPreview search={supplierSearch} />
      <SupplierDiscoveryPreview
        discovery={supplierDiscovery}
        importing={importingDiscovery}
        onImport={(candidateIndex) => onDiscoveryImport?.(profile, candidateIndex)}
      />
      <SupplierOptionsList
        supplierOptions={supplierOptions}
        saving={saving}
        onSelect={(optionIndex) => onSelect?.(profile, optionIndex)}
      />
    </section>
  )
}
