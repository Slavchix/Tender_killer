import { useEffect, useState } from 'react'
import {
  SupplierCatalogHealthPanel,
  SupplierCatalogPresetControls,
} from './TenderEconomicsSupplierCatalogs'
import { SupplierActionBar } from './TenderEconomicsSupplierActions'
import {
  SupplierInputFields,
  hasSupplierOptionInput,
  supplierOptionFormValues,
  supplierOptionPayload,
} from './TenderEconomicsSupplierFields'

export function SupplierInputForm({
  profile,
  supplierOptions = [],
  supplierSearchQueries = [],
  onSave,
  onAutoSelect,
  onSearchPrepare,
  onPresetSave,
  onDiscoveryRun,
  onDiscoveryUrlRun,
  supplierCatalogHealth,
  supplierCatalogHealthLoading = false,
  supplierCatalogHealthError = '',
  onSupplierCatalogHealthRefresh,
  saving = false,
  preparingSearch = false,
  savingPresets = false,
  discoveringDiscovery = false,
  autoSelecting = false,
}) {
  const [values, setValues] = useState(() => supplierOptionFormValues())

  useEffect(() => {
    setValues(supplierOptionFormValues())
  }, [profile?.position_index])

  function updateField(name, value) {
    setValues((current) => ({ ...current, [name]: value }))
  }

  function submitSupplierOption(event) {
    event.preventDefault()
    if (!onSave) return
    const result = onSave(profile, supplierOptionPayload(values, supplierSearchQueries))
    if (result?.then) {
      result.then(() => setValues(supplierOptionFormValues())).catch(() => {})
      return
    }
    setValues(supplierOptionFormValues())
  }

  return (
    <form className="supplier-input-form" onSubmit={submitSupplierOption}>
      <div className="profile-block-heading">
        <h5>Поставщики</h5>
        <SupplierActionBar
          profile={profile}
          values={values}
          supplierOptions={supplierOptions}
          supplierSearchQueries={supplierSearchQueries}
          onSave={onSave}
          onAutoSelect={onAutoSelect}
          onSearchPrepare={onSearchPrepare}
          onDiscoveryRun={onDiscoveryRun}
          onDiscoveryUrlRun={onDiscoveryUrlRun}
          saving={saving}
          preparingSearch={preparingSearch}
          discoveringDiscovery={discoveringDiscovery}
          autoSelecting={autoSelecting}
          canSubmit={hasSupplierOptionInput(values)}
        />
      </div>
      <SupplierCatalogPresetControls
        profile={profile}
        saving={savingPresets}
        onPresetSave={onPresetSave}
      />
      <SupplierCatalogHealthPanel
        supplierCatalogHealth={supplierCatalogHealth}
        loading={supplierCatalogHealthLoading}
        error={supplierCatalogHealthError}
        onRefresh={onSupplierCatalogHealthRefresh}
      />
      <SupplierInputFields
        values={values}
        supplierSearchQueries={supplierSearchQueries}
        onFieldChange={updateField}
      />
    </form>
  )
}
