const SUPPLIER_CATALOG_PRESETS = [
  { preset_id: 'officemag_office_supplies', label: 'OfficeMag', provider: 'officemag' },
  { preset_id: 'komus_office_supplies', label: 'Komus', provider: 'komus' },
  { preset_id: 'petrovich_building_materials', label: 'Petrovich', provider: 'petrovich' },
  { preset_id: 'lemanapro_building_materials', label: 'Lemana Pro', provider: 'lemanapro' },
  { preset_id: 'vseinstrumenti_building_materials', label: 'ВсеИнструменты', provider: 'vseinstrumenti' },
]

export function SupplierCatalogPresetControls({ profile, saving = false, onPresetSave }) {
  const rawPayload = profile?.raw_payload || {}
  const explicitPresetIds = Array.isArray(rawPayload.supplier_catalog_preset_ids)
    ? rawPayload.supplier_catalog_preset_ids
    : null
  const selectedPresetIds = explicitPresetIds || []
  const autoMode = explicitPresetIds === null
  const disabledMode = Array.isArray(explicitPresetIds) && explicitPresetIds.length === 0
  const disabled = saving || !onPresetSave

  function togglePreset(presetId) {
    const selected = new Set(selectedPresetIds)
    if (selected.has(presetId)) {
      selected.delete(presetId)
    } else {
      selected.add(presetId)
    }
    const nextPresetIds = Array.from(selected)
    ignoreCatalogActionError(onPresetSave(profile, nextPresetIds))
  }

  return (
    <div className="supplier-catalog-presets">
      <div className="supplier-catalog-preset-heading">
        <span>Каталоги</span>
        <div>
          <button
            className={autoMode ? 'secondary-button compact active' : 'secondary-button compact'}
            disabled={disabled || autoMode}
            onClick={() => ignoreCatalogActionError(onPresetSave(profile, null))}
            type="button"
          >
            Авто
          </button>
          <button
            className={disabledMode ? 'secondary-button compact active' : 'secondary-button compact'}
            disabled={disabled || disabledMode}
            onClick={() => ignoreCatalogActionError(onPresetSave(profile, []))}
            type="button"
          >
            Выкл
          </button>
        </div>
      </div>
      <div className="supplier-catalog-preset-grid">
        {SUPPLIER_CATALOG_PRESETS.map((preset) => (
          <label key={preset.preset_id}>
            <input
              checked={selectedPresetIds.includes(preset.preset_id)}
              disabled={disabled}
              onChange={() => togglePreset(preset.preset_id)}
              type="checkbox"
            />
            <span>{preset.label}</span>
            <em>{preset.provider}</em>
          </label>
        ))}
      </div>
      {autoMode && <p className="muted-text">Автоподбор включен по названию и ОКПД2.</p>}
      {disabledMode && <p className="muted-text">Каталоги отключены для этой позиции.</p>}
      {saving && <p className="muted-text">Сохраняю каталоги...</p>}
    </div>
  )
}

function ignoreCatalogActionError(result) {
  if (result?.catch) {
    result.catch(() => {})
  }
}
