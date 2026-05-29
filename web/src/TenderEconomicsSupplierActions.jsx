import { supplierUrlDiscoveryPayload } from './TenderEconomicsSupplierPayloads'

export function SupplierActionBar({
  profile,
  values,
  supplierOptions = [],
  supplierSearchQueries = [],
  onSave,
  onAutoSelect,
  onSearchPrepare,
  onDiscoveryRun,
  onDiscoveryUrlRun,
  saving = false,
  preparingSearch = false,
  discoveringDiscovery = false,
  autoSelecting = false,
  canSubmit = false,
}) {
  return (
    <div className="profile-block-actions">
      <button
        className="secondary-button compact"
        disabled={preparingSearch || !onSearchPrepare}
        onClick={() => ignoreSupplierActionError(onSearchPrepare?.(profile))}
        type="button"
      >
        {preparingSearch ? 'Готовлю...' : 'Подготовить поиск'}
      </button>
      <button
        className="secondary-button compact"
        disabled={discoveringDiscovery || !onDiscoveryRun || !supplierSearchQueries.length}
        onClick={() => ignoreSupplierActionError(onDiscoveryRun?.(profile))}
        type="button"
      >
        {discoveringDiscovery ? 'Ищу...' : 'Найти кандидатов'}
      </button>
      <button
        className="secondary-button compact"
        disabled={discoveringDiscovery || !onDiscoveryUrlRun || !values.url}
        onClick={() => ignoreSupplierActionError(onDiscoveryUrlRun?.(profile, supplierUrlDiscoveryPayload(values, supplierSearchQueries)))}
        type="button"
      >
        {discoveringDiscovery ? 'Проверяю...' : 'Проверить ссылку'}
      </button>
      <button
        className="secondary-button compact"
        disabled={autoSelecting || !onAutoSelect || !supplierOptions.length}
        onClick={() => ignoreSupplierActionError(onAutoSelect?.(profile))}
        type="button"
      >
        {autoSelecting ? 'Выбираю...' : 'Лучший в расчет'}
      </button>
      <button className="secondary-button compact" disabled={saving || !onSave || !canSubmit} type="submit">
        {saving ? 'Сохраняю...' : 'Добавить'}
      </button>
    </div>
  )
}

function ignoreSupplierActionError(result) {
  if (result?.catch) {
    result.catch(() => {})
  }
}
