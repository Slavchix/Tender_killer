import {
  formatMoney,
  formatQuantity,
  profileStatusLabel,
} from './formatters'

export function EconomicsPositionRail({
  profiles = [],
  selectedEconomicsProfileIndex = 0,
  onSelectedEconomicsProfileChange,
}) {
  return (
    <aside className="economics-position-rail" role="listbox" aria-label="Позиции для экономики">
      {profiles.length ? profiles.map((profile, index) => (
        <EconomicsPositionRailRow
          index={index}
          key={`${profile.position_index}-${profile.product_name}-${index}`}
          onSelect={onSelectedEconomicsProfileChange}
          profile={profile}
          selected={index === selectedEconomicsProfileIndex}
        />
      )) : (
        <p className="muted-text">Товарные позиции пока не сформированы.</p>
      )}
    </aside>
  )
}

function EconomicsPositionRailRow({ profile, index, selected = false, onSelect }) {
  const supplierOptions = Array.isArray(profile.raw_payload?.supplier_options)
    ? profile.raw_payload.supplier_options
    : []
  const profileEconomics = profile.raw_payload?.economics || {}
  const costValue = profileEconomics.total_cost ?? profileEconomics.unit_cost

  return (
    <button
      className={selected ? 'profile-row economics-profile-row selected' : 'profile-row economics-profile-row'}
      onClick={() => onSelect?.(index)}
      type="button"
    >
      <span className="profile-position">#{profile.position_index || index + 1}</span>
      <span className="profile-name">{profile.product_name || 'Без названия'}</span>
      <span className="profile-meta quantity">{formatQuantity(profile.quantity, profile.unit)}</span>
      <span className="profile-meta classifier">
        {costValue ? `себестоимость ${formatMoney(costValue)}` : `${supplierOptions.length} поставщиков`}
      </span>
      <span className={`profile-status ${profile.profile_status || 'draft'}`}>{profileStatusLabel(profile.profile_status)}</span>
    </button>
  )
}
