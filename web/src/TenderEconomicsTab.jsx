import { useEffect, useState } from 'react'
import { AnalysisList } from './TenderAnalysisTab'
import {
  economicsStatusLabel,
  formatConfidence,
  formatCostDriver,
  formatMoney,
  formatPercent,
  formatQuantity,
  profileStatusLabel,
  supplierAvailabilityLabel,
  supplierConfidenceLabel,
  supplierStatusLabel,
  taxModeLabel,
} from './formatters'
import { Info, SummaryMetric } from './TenderDetailsShared'

const SUPPLIER_CATALOG_PRESETS = [
  { preset_id: 'officemag_office_supplies', label: 'OfficeMag', provider: 'officemag' },
  { preset_id: 'komus_office_supplies', label: 'Komus', provider: 'komus' },
  { preset_id: 'petrovich_building_materials', label: 'Petrovich', provider: 'petrovich' },
  { preset_id: 'vseinstrumenti_building_materials', label: 'Vseinstrumenti', provider: 'vseinstrumenti' },
]

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
  const missingInputs = economics?.missing_cost_inputs?.length || 0
  const displayedRevenue = economics?.revenue ?? tender?.price
  const profiles = productProfiles || []
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
    <section className="detail-section active economics-section">
      <div className="section-heading-row">
        <h3>Экономика</h3>
      </div>
      <div className="economics-tab-summary tab-summary-grid" aria-label="Сводка экономики">
        <SummaryMetric value={economics ? economicsStatusLabel(economics.status) : 'не рассчитана'} label="статус" />
        <SummaryMetric value={formatMoney(displayedRevenue)} label="НМЦК" />
        <SummaryMetric value={formatMoney(economics?.estimated_total_cost)} label="затраты" />
        <SummaryMetric value={formatMoney(economics?.break_even_price)} label="безубыток" />
        <SummaryMetric value={economics ? formatPercent(economics.margin_percent) : 'нет'} label="маржа" />
        <SummaryMetric value={missingInputs} label="цен добавить" />
      </div>
      <EconomicsSummary economics={economics} tender={tender} />
      <div className="economics-workbench">
        <div className="economics-position-list" role="listbox" aria-label="Позиции для экономики">
          {profiles.length ? profiles.map((profile, index) => {
            const supplierOptions = Array.isArray(profile.raw_payload?.supplier_options)
              ? profile.raw_payload.supplier_options
              : []
            const profileEconomics = profile.raw_payload?.economics || {}
            const costValue = profileEconomics.total_cost ?? profileEconomics.unit_cost
            return (
              <button
                className={index === selectedEconomicsProfileIndex ? 'profile-row selected' : 'profile-row'}
                key={`${profile.position_index}-${profile.product_name}-${index}`}
                onClick={() => onSelectedEconomicsProfileChange?.(index)}
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
          }) : (
            <p className="muted-text">Товарные позиции пока не сформированы.</p>
          )}
        </div>
        <div className="economics-position-panel">
          {selectedEconomicsProfile ? (
            <>
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
              <ProductSupplierOptionsForm
                profile={selectedEconomicsProfile}
                onSave={onSupplierOptionSave}
                onSelect={onSupplierOptionSelect}
                onAutoSelect={onSupplierOptionAutoSelect}
                onDiscoveryImport={onSupplierDiscoveryImport}
                onSearchPrepare={onSupplierSearchPrepare}
                onPresetSave={onSupplierCatalogPresetsSave}
                onDiscoveryRun={onSupplierDiscoveryRun}
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
            </>
          ) : (
            <p className="muted-text">Сначала обнови детали закупки, чтобы появились товарные позиции.</p>
          )}
        </div>
      </div>
    </section>
  )
}

function EconomicsSummary({ economics, tender }) {
  if (!economics) {
    return (
      <p className="muted-text">
        {tender?.price ? 'НМЦК подтянута из карточки закупки. Добавь себестоимость по позициям, чтобы посчитать маржу.' : 'Черновик экономики пока не рассчитан.'}
      </p>
    )
  }

  const missingInputs = economics.missing_cost_inputs || []
  const riskTypes = economics.risk_types || []
  const items = economics.items || []
  const bidScenarios = economics.bid_scenarios || []
  const participationDecision = economics.participation_decision || null

  return (
    <div className="economics-card">
      <div className="analysis-status-row">
        <strong>{economicsStatusLabel(economics.status)}</strong>
        <span>Маржа: {formatPercent(economics.margin_percent)}</span>
      </div>
      {economics.recommendation && <p>{economics.recommendation}</p>}
      <ParticipationDecisionCard decision={participationDecision} />
      <BidScenarioStrip scenarios={bidScenarios} />
      <div className="economics-grid">
        <Info label="НМЦК" value={formatMoney(economics.revenue)} />
        <Info label="Себестоимость" value={formatMoney(economics.supplier_cost)} />
        <Info label="Резерв риска" value={`${formatMoney(economics.risk_reserve)} · ${formatPercent(economics.risk_reserve_rate_percent)}`} />
        <Info label="Итого затраты" value={formatMoney(economics.estimated_total_cost)} />
        <Info label="Безубыток" value={formatMoney(economics.break_even_price)} />
        <Info label="Минимальная ставка" value={formatMoney(economics.minimum_margin_price)} />
        <Info label="Интересная ставка" value={formatMoney(economics.interesting_price)} />
        <Info label="Маржа" value={`${formatMoney(economics.gross_margin)} · ${formatPercent(economics.margin_percent)}`} />
        <Info label="Риски исполнения" value={riskTypes.length ? riskTypes.join(', ') : 'нет'} />
      </div>
      {missingInputs.length > 0 && (
        <div className="economics-warning">
          <strong>Нужны цены</strong>
          <p>{missingInputs.join(', ')}</p>
        </div>
      )}
      {items.length > 0 && (
        <div className="economics-items">
          {items.map((item, index) => (
            <div className="economics-item" key={`${item.product_name}-${index}`}>
              <strong>{item.product_name}</strong>
              <span>{formatQuantity(item.quantity, item.unit)}</span>
              <span>{formatMoney(item.total_cost)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function ParticipationDecisionCard({ decision }) {
  if (!decision) return null

  return (
    <section className={`participation-decision ${decision.status || ''}`} aria-label="Решение по участию">
      <div>
        <span>Решение по участию</span>
        <strong>{decision.label || 'проверить'}</strong>
      </div>
      <div>
        <span>Лимит</span>
        <strong>{formatMoney(decision.limit_price)}</strong>
      </div>
      {decision.recommendation && <p>{decision.recommendation}</p>}
    </section>
  )
}

function BidScenarioStrip({ scenarios = [] }) {
  if (!scenarios.length) return null

  return (
    <section className="bid-scenario-strip" aria-label="Сценарии цены участия">
      <div className="profile-block-heading">
        <h5>Сценарии цены</h5>
      </div>
      <div className="bid-scenario-grid">
        {scenarios.map((scenario) => (
          <div className={`bid-scenario ${scenario.id || ''}`} key={scenario.id || scenario.label}>
            <span>{scenario.label}</span>
            <strong>{formatMoney(scenario.price)}</strong>
            <em>{formatMoney(scenario.margin_amount)} · {formatPercent(scenario.margin_percent)}</em>
          </div>
        ))}
      </div>
    </section>
  )
}

function ProductEconomicsForm({ profile, onSave, saving = false }) {
  const economics = profile?.raw_payload?.economics || {}
  const priceSource = profile?.raw_payload?.economics_price_source || null
  const [values, setValues] = useState(() => economicsFormValues(economics))

  useEffect(() => {
    setValues(economicsFormValues(economics))
  }, [profile?.position_index, profile?.raw_payload])

  function updateField(name, value) {
    setValues((current) => ({ ...current, [name]: value }))
  }

  function submitEconomics(event) {
    event.preventDefault()
    if (!onSave) return
    onSave(profile, values)
  }

  return (
    <form className="economics-input-form" onSubmit={submitEconomics}>
      <div className="profile-block-heading">
        <h5>Себестоимость</h5>
        <button className="secondary-button compact" disabled={saving || !onSave} type="submit">
          {saving ? 'Сохраняю...' : 'Сохранить'}
        </button>
      </div>
      <EconomicsPriceSource source={priceSource} />
      <div className="economics-input-grid">
        <label>
          <span>За единицу</span>
          <input
            inputMode="decimal"
            name="unit_cost"
            onChange={(event) => updateField('unit_cost', event.target.value)}
            placeholder="0"
            value={values.unit_cost}
          />
        </label>
        <label>
          <span>Логистика</span>
          <input
            inputMode="decimal"
            name="logistics_cost"
            onChange={(event) => updateField('logistics_cost', event.target.value)}
            placeholder="0"
            value={values.logistics_cost}
          />
        </label>
        <label>
          <span>Документы</span>
          <input
            inputMode="decimal"
            name="documents_cost"
            onChange={(event) => updateField('documents_cost', event.target.value)}
            placeholder="0"
            value={values.documents_cost}
          />
        </label>
        <label>
          <span>Прочее</span>
          <input
            inputMode="decimal"
            name="other_costs"
            onChange={(event) => updateField('other_costs', event.target.value)}
            placeholder="0"
            value={values.other_costs}
          />
        </label>
      </div>
    </form>
  )
}

function EconomicsPriceSource({ source }) {
  if (!source) return null
  const supplier = source.supplier_name || source.supplier_url || 'поставщик'
  const mode = source.selection === 'manual_selected' ? 'выбран вручную' : 'выбран автоматически'

  return (
    <div className={`price-source-note ${source.confidence || 'needs_review'}`}>
      <span>Источник цены</span>
      <strong>{supplier} · {formatMoney(source.unit_price)}</strong>
      <em>{mode} · {supplierConfidenceLabel(source.confidence)}</em>
    </div>
  )
}

function ProductEconomicsAssumptionsForm({ profile, item, onSave, saving = false }) {
  const assumptions = profile?.raw_payload?.economics_assumptions || {}
  const [values, setValues] = useState(() => economicsAssumptionsFormValues(assumptions))

  useEffect(() => {
    setValues(economicsAssumptionsFormValues(assumptions))
  }, [profile?.position_index, profile?.raw_payload])

  function updateField(name, value) {
    setValues((current) => ({ ...current, [name]: value }))
  }

  function submitAssumptions(event) {
    event.preventDefault()
    if (!onSave) return
    onSave(profile, values)
  }

  return (
    <form className="economics-assumptions-form" onSubmit={submitAssumptions}>
      <div className="profile-block-heading">
        <h5>Допущения</h5>
        <button className="secondary-button compact" disabled={saving || !onSave} type="submit">
          {saving ? 'Сохраняю...' : 'Сохранить'}
        </button>
      </div>
      <div className="economics-input-grid">
        <label>
          <span>НДС</span>
          <select name="vat_mode" onChange={(event) => updateField('vat_mode', event.target.value)} value={values.vat_mode}>
            <option value="unknown">проверить</option>
            <option value="vat_included">включен</option>
            <option value="vat_excluded">сверху</option>
            <option value="no_vat">без НДС</option>
          </select>
        </label>
        <label>
          <span>Ставка НДС, %</span>
          <input
            inputMode="decimal"
            name="vat_rate_percent"
            onChange={(event) => updateField('vat_rate_percent', event.target.value)}
            placeholder="20"
            value={values.vat_rate_percent}
          />
        </label>
        <label>
          <span>Резерв, %</span>
          <input
            inputMode="decimal"
            name="risk_reserve_percent"
            onChange={(event) => updateField('risk_reserve_percent', event.target.value)}
            placeholder="0"
            value={values.risk_reserve_percent}
          />
        </label>
        <label>
          <span>Целевая маржа, %</span>
          <input
            inputMode="decimal"
            name="target_margin_percent"
            onChange={(event) => updateField('target_margin_percent', event.target.value)}
            placeholder="15"
            value={values.target_margin_percent}
          />
        </label>
      </div>
      <div className="assumptions-preview">
        <Info label="НДС сверху" value={formatMoney(item?.vat_cost)} />
        <Info label="Резерв позиции" value={formatMoney(item?.position_risk_reserve)} />
        <Info label="Итого позиция" value={formatMoney(item?.estimated_total_cost)} />
        <Info label="Целевая цена" value={formatMoney(item?.target_price)} />
      </div>
    </form>
  )
}

function economicsFormValues(economics = {}) {
  return {
    unit_cost: economics.unit_cost ?? '',
    logistics_cost: economics.logistics_cost ?? '',
    documents_cost: economics.documents_cost ?? '',
    other_costs: economics.other_costs ?? '',
  }
}

function economicsAssumptionsFormValues(assumptions = {}) {
  return {
    vat_mode: assumptions.vat_mode || 'unknown',
    vat_rate_percent: assumptions.vat_rate_percent ?? '',
    risk_reserve_percent: assumptions.risk_reserve_percent ?? '',
    target_margin_percent: assumptions.target_margin_percent ?? '',
  }
}

function ProductAutoEconomicsPanel({ profile, onRun, onAccept, saving = false, accepting = false }) {
  const estimate = profile?.raw_payload?.economics_auto || null
  const costDrivers = Array.isArray(estimate?.cost_drivers) ? estimate.cost_drivers : []
  const needsReview = Array.isArray(estimate?.needs_review) ? estimate.needs_review : []

  return (
    <section className="auto-economics-panel">
      <div className="profile-block-heading">
        <h5>Авторасчет</h5>
        <div className="auto-economics-actions">
          <button className="secondary-button compact" disabled={saving || !onRun} onClick={() => onRun?.(profile)} type="button">
            {saving ? 'Расчет...' : 'Рассчитать'}
          </button>
          <button className="secondary-button compact" disabled={accepting || !estimate || !onAccept} onClick={() => onAccept?.(profile)} type="button">
            {accepting ? 'Применяю...' : 'Принять в расчет'}
          </button>
        </div>
      </div>
      {estimate ? (
        <>
          <div className="auto-economics-metrics">
            <Info label="Итого" value={formatMoney(estimate.estimated_total_cost)} />
            <Info label="Скрытые расходы" value={formatMoney(estimate.hidden_costs_total)} />
            <Info label="Резерв" value={formatMoney(estimate.risk_reserve)} />
            <Info label="НДС" value={taxModeLabel(estimate.tax_mode, estimate.vat_rate_percent)} />
            <Info label="Уверенность" value={formatConfidence(estimate.confidence)} />
          </div>
          {estimate.manual_inputs_present && (
            <p className="auto-economics-note">Ручная экономика уже заполнена, авторасчет сохранен как черновик.</p>
          )}
          <p className="auto-economics-note">Авторасчет заполнит пустые допущения по НДС, резерву и марже.</p>
          <AnalysisList
            title="Факторы расходов"
            items={costDrivers.map(formatCostDriver)}
            empty="Скрытые расходы пока не найдены"
          />
          <AnalysisList
            title="Проверить вручную"
            items={needsReview}
            empty="Критичных проверок пока нет"
            danger={needsReview.length > 0}
          />
        </>
      ) : (
        <p className="muted-text">Черновик авторасчета пока не построен.</p>
      )}
    </section>
  )
}

function ProductSupplierOptionsForm({
  profile,
  onSave,
  onSelect,
  onAutoSelect,
  onDiscoveryImport,
  onSearchPrepare,
  onPresetSave,
  onDiscoveryRun,
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
    <section className="profile-block supplier-options-block">
      <form className="supplier-input-form" onSubmit={submitSupplierOption}>
        <div className="profile-block-heading">
          <h5>Поставщики</h5>
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
              disabled={autoSelecting || !onAutoSelect || !supplierOptions.length}
              onClick={() => ignoreSupplierActionError(onAutoSelect?.(profile))}
              type="button"
            >
              {autoSelecting ? 'Выбираю...' : 'Лучший в расчет'}
            </button>
            <button className="secondary-button compact" disabled={saving || !onSave || !hasSupplierOptionInput(values)} type="submit">
              {saving ? 'Сохраняю...' : 'Добавить'}
            </button>
          </div>
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
        <div className="supplier-input-grid">
          <label>
            <span>Запрос-источник</span>
            <select
              name="source_query"
              onChange={(event) => updateField('source_query', event.target.value)}
              value={values.source_query}
            >
              <option value="">Без привязки</option>
              {supplierSearchQueries.map((item) => (
                <option key={`${item.priority}-${item.query}`} value={item.query}>
                  {item.query}
                </option>
              ))}
            </select>
          </label>
          <label>
            <span>Поставщик</span>
            <input
              name="name"
              onChange={(event) => updateField('name', event.target.value)}
              placeholder="Название"
              value={values.name}
            />
          </label>
          <label>
            <span>Ссылка</span>
            <input
              name="url"
              onChange={(event) => updateField('url', event.target.value)}
              placeholder="https://"
              value={values.url}
            />
          </label>
          <label>
            <span>Цена за ед.</span>
            <input
              inputMode="decimal"
              name="unit_price"
              onChange={(event) => updateField('unit_price', event.target.value)}
              placeholder="0"
              value={values.unit_price}
            />
          </label>
          <label>
            <span>Наличие</span>
            <select
              name="availability"
              onChange={(event) => updateField('availability', event.target.value)}
              value={values.availability}
            >
              <option value="unknown">Неясно</option>
              <option value="in_stock">В наличии</option>
              <option value="on_request">Под заказ</option>
              <option value="not_available">Нет</option>
            </select>
          </label>
          <label>
            <span>Статус</span>
            <select
              name="status"
              onChange={(event) => updateField('status', event.target.value)}
              value={values.status}
            >
              <option value="candidate">Кандидат</option>
              <option value="suitable">Подходит</option>
              <option value="rejected">Не подходит</option>
            </select>
          </label>
        </div>
        <label className="supplier-note-field">
          <span>Заметка</span>
          <textarea
            name="note"
            onChange={(event) => updateField('note', event.target.value)}
            placeholder="Условия, НДС, доставка, ограничения"
            value={values.note}
          />
        </label>
      </form>

      <SupplierSearchPreview search={supplierSearch} />
      <SupplierDiscoveryPreview
        discovery={supplierDiscovery}
        importing={importingDiscovery}
        onImport={(candidateIndex) => onDiscoveryImport?.(profile, candidateIndex)}
      />

      {supplierOptions.length ? (
        <div className="supplier-options-list">
          {supplierOptions.map((option, index) => (
            <div
              className={option.status === 'selected' ? 'supplier-option-row selected' : 'supplier-option-row'}
              key={`${option.url || option.name || 'supplier'}-${index}`}
            >
              <div>
                {option.url ? (
                  <a href={option.url} target="_blank" rel="noreferrer">{option.name || option.url}</a>
                ) : (
                  <strong>{option.name || 'Поставщик'}</strong>
                )}
                {option.note && <p>{option.note}</p>}
                {option.source_query && <p>Запрос: {option.source_query}</p>}
              </div>
              <span>{formatMoney(option.unit_price)}</span>
              <em>{supplierAvailabilityLabel(option.availability)} · {supplierStatusLabel(option.status)}</em>
              <button
                className="supplier-select-button"
                disabled={saving || !onSelect || option.status === 'selected'}
                onClick={() => ignoreSupplierActionError(onSelect?.(profile, index))}
                type="button"
              >
                {option.status === 'selected' ? 'В расчете' : 'В расчет'}
              </button>
            </div>
          ))}
        </div>
      ) : (
        <p className="muted-text">Кандидаты поставщиков пока не добавлены.</p>
      )}
    </section>
  )
}

function SupplierCatalogHealthPanel({ supplierCatalogHealth, loading = false, error = '', onRefresh }) {
  const catalogs = Array.isArray(supplierCatalogHealth?.catalogs) ? supplierCatalogHealth.catalogs : []
  if (!loading && !error && !catalogs.length) return null

  return (
    <div className="supplier-catalog-health">
      <div className="supplier-catalog-health-heading">
        <span>Статус каталогов</span>
        <button
          className="secondary-button compact"
          disabled={loading || !onRefresh}
          onClick={() => ignoreSupplierActionError(onRefresh?.(true))}
          type="button"
        >
          {loading ? 'Проверяю...' : 'Проверить'}
        </button>
      </div>
      {error && <p>{error}</p>}
      {catalogs.length > 0 && (
        <div className="supplier-catalog-health-grid">
          {catalogs.map((catalog) => (
            <a
              className={`supplier-catalog-health-item ${catalog.status || 'unknown'}`}
              href={catalog.sample_url}
              key={catalog.preset_id || catalog.provider}
              target="_blank"
              rel="noreferrer"
            >
              <strong>{catalog.label || catalog.provider}</strong>
              <span>{catalog.provider}</span>
              <em>{supplierCatalogHealthStatusLabel(catalog.status, catalog.http_status)}</em>
            </a>
          ))}
        </div>
      )}
    </div>
  )
}

function supplierCatalogHealthStatusLabel(status, httpStatus) {
  if (status === 'ok') return httpStatus ? `HTTP ${httpStatus}` : 'доступен'
  if (status === 'error') return httpStatus ? `ошибка ${httpStatus}` : 'ошибка'
  return 'настроен'
}

function SupplierCatalogPresetControls({ profile, saving = false, onPresetSave }) {
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
    ignoreSupplierActionError(onPresetSave(profile, nextPresetIds))
  }

  return (
    <div className="supplier-catalog-presets">
      <div className="supplier-catalog-preset-heading">
        <span>Каталоги</span>
        <div>
          <button
            className={autoMode ? 'secondary-button compact active' : 'secondary-button compact'}
            disabled={disabled || autoMode}
            onClick={() => ignoreSupplierActionError(onPresetSave(profile, null))}
            type="button"
          >
            Авто
          </button>
          <button
            className={disabledMode ? 'secondary-button compact active' : 'secondary-button compact'}
            disabled={disabled || disabledMode}
            onClick={() => ignoreSupplierActionError(onPresetSave(profile, []))}
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

function SupplierDiscoveryPreview({ discovery, importing = false, onImport }) {
  const candidates = Array.isArray(discovery?.candidates) ? discovery.candidates : []
  const diagnostics = Array.isArray(discovery?.collector_diagnostics) ? discovery.collector_diagnostics : []
  const noCandidates = discovery?.status === 'no_candidates'
  if (!candidates.length && !diagnostics.length) return null

  return (
    <div className="supplier-discovery-preview">
      <span>{noCandidates && !candidates.length ? 'Кандидаты не найдены' : 'Найденные кандидаты'}</span>
      {noCandidates && !candidates.length && <p>Смотри диагностику ниже: она показывает, какие каталоги и страницы проверялись.</p>}
      <SupplierDiscoveryDiagnostics diagnostics={diagnostics} />
      {candidates.length > 0 && candidates.map((candidate, index) => {
        const imported = candidate.review_status === 'imported'
        const confidenceReasons = Array.isArray(candidate.confidence_reasons) ? candidate.confidence_reasons : []
        return (
          <div className={imported ? 'supplier-discovery-row imported' : 'supplier-discovery-row'} key={`${candidate.url || candidate.name || 'candidate'}-${index}`}>
            <div>
              {candidate.url ? (
                <a href={candidate.url} target="_blank" rel="noreferrer">{candidate.name || candidate.url}</a>
              ) : (
                <strong>{candidate.name || 'Поставщик'}</strong>
              )}
              {candidate.source_query && <p>Запрос: {candidate.source_query}</p>}
              {candidate.provider && <p>{candidate.provider}</p>}
              <p>
                {supplierConfidenceLabel(candidate.confidence)}
                {confidenceReasons.length ? ` · ${confidenceReasons.join(', ')}` : ''}
              </p>
            </div>
            <span>{formatMoney(candidate.unit_price)}</span>
            <button
              className="secondary-button compact"
              disabled={importing || imported || !onImport}
              onClick={() => ignoreSupplierActionError(onImport?.(index))}
              type="button"
            >
              {imported ? 'Добавлен' : 'Добавить'}
            </button>
          </div>
        )
      })}
    </div>
  )
}

function ignoreSupplierActionError(result) {
  if (result?.catch) {
    result.catch(() => {})
  }
}

function SupplierDiscoveryDiagnostics({ diagnostics }) {
  if (!Array.isArray(diagnostics) || !diagnostics.length) return null

  return (
    <div className="supplier-discovery-diagnostics">
      {diagnostics.map((diagnostics, index) => {
        const errors = Array.isArray(diagnostics.errors) ? diagnostics.errors : []
        return (
          <section key={`${diagnostics.provider || 'collector'}-${index}`}>
            <strong>{diagnostics.provider || 'collector'}</strong>
            <div className="supplier-discovery-metrics">
              <span>Запросы: {diagnostics.queries_seen || 0}</span>
              <span>Ссылки: {diagnostics.links_seen || 0}</span>
              <span>Пропущено: {diagnostics.links_skipped || 0}</span>
              <span>Страницы: {diagnostics.pages_fetched || 0}</span>
              <span>Кандидаты: {diagnostics.candidates_found || 0}</span>
            </div>
            {errors.length ? <p>{errors.join(' · ')}</p> : null}
          </section>
        )
      })}
    </div>
  )
}

function SupplierSearchPreview({ search }) {
  const queries = Array.isArray(search?.queries) ? search.queries : []
  if (!queries.length) return null

  return (
    <div className="supplier-search-preview">
      <span>Запросы для поиска</span>
      <div>
        {queries.map((item) => (
          <section key={`${item.kind}-${item.priority}-${item.query}`}>
            <code>{item.query}</code>
            <div className="supplier-search-links">
              {(Array.isArray(item.quick_links) ? item.quick_links : []).map((link) => (
                <a href={link.url} key={`${item.query}-${link.label}`} target="_blank" rel="noreferrer">
                  {link.label}
                </a>
              ))}
            </div>
          </section>
        ))}
      </div>
    </div>
  )
}

function supplierOptionFormValues() {
  return {
    name: '',
    url: '',
    unit_price: '',
    availability: 'unknown',
    status: 'candidate',
    source_query: '',
    note: '',
  }
}

function supplierOptionPayload(values, searchQueries = []) {
  const payload = { ...values }
  const selectedQuery = searchQueries.find((item) => item.query === values.source_query)
  if (selectedQuery) {
    payload.source_kind = selectedQuery.kind || ''
  }
  return payload
}

function hasSupplierOptionInput(values) {
  return Boolean(values.name || values.url || values.unit_price || values.note)
}
