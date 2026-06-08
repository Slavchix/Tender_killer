import { useEffect, useState } from 'react'
import { productDetailModes } from './constants'
import {
  formatAmount,
  formatFulfillmentRequirements,
  formatMoney,
  formatQuantity,
  profileStatusLabel,
} from './formatters'
import { tenderReferenceTotalPrice, tenderReferenceUnitPrice } from './TenderEconomicsPriceComparison'
import { AnalysisList } from './TenderAnalysisSections'
import { Info, SummaryMetric } from './TenderDetailsShared'

export function TenderProductsTab({
  tender,
  productProfiles,
  productProfileSummary,
  selectedProfileIndex,
  onSelectedProfileIndexChange,
  profilesLoading,
  onRebuildProductProfiles,
}) {
  return (
    <section className="detail-section active product-profile-section">
      <div className="section-heading-row">
        <h3>Товары</h3>
        <button className="secondary-button compact" disabled={profilesLoading} onClick={onRebuildProductProfiles} type="button">
          {profilesLoading ? 'Обновление...' : 'Обновить профили'}
        </button>
      </div>
      <ProductTabSummary
        summary={productProfileSummary}
        total={productProfiles.length}
        itemsCount={(tender.items || []).length}
      />
      {productProfiles.length ? (
        <div className="profile-layout">
          <div className="profile-list" role="listbox" aria-label="Товарные профили">
            {productProfiles.map((profile, index) => (
              <button
                className={index === selectedProfileIndex ? 'profile-row selected' : 'profile-row'}
                key={`${profile.position_index}-${profile.product_name}-${index}`}
                onClick={() => onSelectedProfileIndexChange(index)}
                type="button"
              >
                <span className="profile-position">#{profile.position_index || index + 1}</span>
                <span className="profile-name">{profile.product_name || 'Без названия'}</span>
                <span className="profile-meta quantity">
                  {formatQuantity(profile.quantity, profile.unit)}
                  {formatProfileTenderPrice(profile) ? ` · ${formatProfileTenderPrice(profile)}` : ''}
                </span>
                <span className="profile-meta classifier">{profile.classifier_type || 'код'} {profile.classifier_code || profile.okpd2 || 'не найден'}</span>
                <span className={`profile-status ${profile.profile_status || 'draft'}`}>{profileStatusLabel(profile.profile_status)}</span>
              </button>
            ))}
          </div>
          <ProductProfileDetail profile={productProfiles[selectedProfileIndex]} />
        </div>
      ) : (
        <p className="muted-text">Товарные профили пока не сформированы.</p>
      )}
      <TenderItems items={tender.items || []} profiles={productProfiles} />
    </section>
  )
}

function ProductTabSummary({ summary, total, itemsCount }) {
  const data = summary || {}
  const positionTotal = data.total ?? total ?? itemsCount ?? 0
  const ready = data.ready ?? 0
  const needsReview = data.needs_review ?? 0
  const matched = data.matched ?? 0

  return (
    <div className="product-tab-summary tab-summary-grid" aria-label="Сводка товарных профилей">
      <SummaryMetric value={positionTotal} label="позиций" />
      <SummaryMetric value={ready} label="готовы" />
      <SummaryMetric value={needsReview} label="проверить" />
      <SummaryMetric value={matched} label="найдены" />
    </div>
  )
}

function ProductProfileDetail({ profile }) {
  const [activeProfileMode, setActiveProfileMode] = useState('overview')

  useEffect(() => {
    setActiveProfileMode('overview')
  }, [profile?.position_index])

  if (!profile) {
    return <div className="profile-detail muted-text">Выбери позицию из списка</div>
  }

  const documentEvidence = (profile.evidence || []).filter((item) => item?.field === 'document_requirement')
  const classifierLabel = `${profile.classifier_type || 'тип не указан'} ${profile.classifier_code || 'код не найден'}`
  const tenderUnitPrice = tenderReferenceUnitPrice(profile)
  const tenderTotalPrice = tenderReferenceTotalPrice(profile)

  return (
    <div className="profile-detail">
      <div className="profile-detail-header">
        <div>
          <span>Позиция #{profile.position_index || '—'}</span>
          <h4>{profile.product_name || 'Без названия'}</h4>
        </div>
        <strong className={`profile-status ${profile.profile_status || 'draft'}`}>
          {profileStatusLabel(profile.profile_status)}
        </strong>
      </div>

      <nav className="product-detail-tabs" aria-label="Разделы товарного профиля">
        {productDetailModes.map((mode) => (
          <button
            className={activeProfileMode === mode.id ? 'active' : ''}
            key={mode.id}
            onClick={() => setActiveProfileMode(mode.id)}
            type="button"
          >
            {mode.label}
          </button>
        ))}
      </nav>

      {activeProfileMode === 'overview' && (
        <>
          <section className="profile-block">
            <h5>Идентификация позиции</h5>
            <div className="profile-detail-grid">
              <Info label="Детализированное наименование" value={profile.details || 'не найдено'} />
              <Info label="Количество" value={formatQuantity(profile.quantity, profile.unit)} />
              <Info label="Цена за ед." value={formatMoney(tenderUnitPrice)} />
              <Info label="Сумма позиции" value={formatMoney(tenderTotalPrice)} />
              <Info label="ОКПД2" value={profile.okpd2 || 'не найден'} />
              <Info label="Классификатор площадки" value={classifierLabel} />
            </div>
          </section>

          <section className="profile-block">
            <h5>Пакет для поиска товара</h5>
            <AnalysisList title="Поисковые фразы" items={profile.search_phrases || []} empty="Поисковые фразы пока не сформированы" />
            <AnalysisList title="Стоп-слова" items={profile.stop_words || []} empty="Стоп-слова пока не заданы" danger />
          </section>
        </>
      )}

      {activeProfileMode === 'requirements' && (
        <>
          <section className="profile-block">
            <h5>Требования и документы</h5>
            <AnalysisList title="Характеристики из карточки и ТЗ" items={profile.required_characteristics || []} empty="Характеристики пока не найдены" />
            <AnalysisList title="Стандарты" items={profile.standards || []} empty="ГОСТ/ТУ пока не найдены" />
            <AnalysisList title="Сертификаты и документы" items={profile.cert_documents || []} empty="Сертификаты/декларации пока не найдены" />
            <AnalysisList title="Поставка и исполнение" items={formatFulfillmentRequirements(profile.fulfillment_requirements || [])} empty="Требования к поставке и исполнению пока не найдены" />
            <AnalysisList title="Страна происхождения" items={profile.origin_country_requirements || []} empty="Требования по стране пока не найдены" />
          </section>

          <section className="profile-block">
            <h5>Подтверждения из ТЗ</h5>
            {documentEvidence.length ? (
              <div className="evidence-list">
                {documentEvidence.map((item, index) => (
                  <div className="evidence-row" key={`${item.source}-${index}`}>
                    <span>{item.source || 'документ'}</span>
                    <p>{item.value}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="muted-text">Связанные фрагменты ТЗ пока не найдены.</p>
            )}
          </section>
        </>
      )}
    </div>
  )
}

function formatProfileTenderPrice(profile) {
  const unitPrice = tenderReferenceUnitPrice(profile)
  const totalPrice = tenderReferenceTotalPrice(profile)
  const parts = []
  if (unitPrice != null) parts.push(formatMoney(unitPrice))
  if (totalPrice != null) parts.push(formatMoney(totalPrice))
  return parts.join(' · ')
}

function TenderItems({ items, profiles = [] }) {
  if (!items.length) {
    return <p className="muted-text">Позиции из карточки пока не найдены.</p>
  }

  const profileByPosition = profilesByPosition(profiles)

  return (
    <details className="source-items">
      <summary>Позиции из карточки ({items.length})</summary>
      <div className="items-list">
        {items.map((item, index) => {
          const profile = profileByPosition.get(Number(item.position_index)) || profileByPosition.get(index + 1)
          const itemWithProfilePrice = itemWithProfilePricing(item, profile)
          const unitPrice = tenderReferenceUnitPrice(itemWithProfilePrice)
          const totalPrice = tenderReferenceTotalPrice(itemWithProfilePrice)

          return (
            <div className="item-card" key={`${item.position_index}-${item.name}`}>
              <div className="item-title">
                <span>№{item.position_index}</span>
                <strong>{item.name}</strong>
              </div>
              {item.details && <p>{item.details}</p>}
              <div className="item-facts">
                <Info label="Кол-во" value={formatAmount(itemWithProfilePrice.quantity, itemWithProfilePrice.unit)} />
                <Info label="Цена за ед." value={formatMoney(unitPrice)} />
                <Info label="Сумма" value={formatMoney(totalPrice)} />
                <Info label="Классификатор" value={item.classifier_code || item.okpd2 || 'не найден'} />
              </div>
            </div>
          )
        })}
      </div>
    </details>
  )
}

function profilesByPosition(profiles = []) {
  const result = new Map()
  profiles.forEach((profile, index) => {
    const positionIndex = Number(profile?.position_index)
    if (Number.isFinite(positionIndex)) {
      result.set(positionIndex, profile)
    }
    if (!result.has(index + 1)) {
      result.set(index + 1, profile)
    }
  })
  return result
}

function itemWithProfilePricing(item, profile) {
  if (!profile) return item

  return {
    ...profile,
    ...item,
    quantity: positiveValue(item?.quantity, profile?.quantity),
    unit: item?.unit || profile?.unit,
    unit_price: positiveValue(item?.unit_price, profile?.unit_price),
    total_price: positiveValue(item?.total_price, profile?.total_price),
    raw_payload: {
      ...objectPayload(profile?.raw_payload),
      ...objectPayload(item?.raw_payload),
    },
  }
}

function objectPayload(value) {
  return value && typeof value === 'object' ? value : {}
}

function positiveValue(primary, fallback) {
  const number = Number(primary)
  return Number.isFinite(number) && number > 0 ? primary : fallback
}
