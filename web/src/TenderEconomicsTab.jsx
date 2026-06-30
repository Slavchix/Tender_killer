import {
  SMALL_TENDER_ACTIVE_DISCOVERY_LIMIT,
  TenderEconomicsCommandCenter,
  hasReadyPriceCandidateWithoutCost,
  profileNeedsPriceDiscovery,
} from './TenderEconomicsCommandCenter'
import { TenderEconomicsPriceBookFeed } from './TenderEconomicsPriceBookFeed'
import { TenderEconomicsPriceMemory } from './TenderEconomicsPriceMemory'
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
  onSupplierOptionSelect,
  onSupplierOptionAutoSelectAll,
  onReadyPriceCandidatesConfirmAll,
  onPriceBookFeedStage,
  onPriceBookFeedFileStage,
  onPriceDiscoveryRun,
  onSupplierDiscoveryImport,
  onSupplierSearchPrepare,
  onSupplierDiscoveryRun,
  onSupplierUrlDiscoveryRun,
  onSupplierManualPriceStage,
  onPriceCandidateConfirm,
  onPriceCandidateReject,
  onAutoEconomicsRun,
  onAutoEconomicsAccept,
  savingEconomicsPosition = null,
  savingAssumptionsPosition = null,
  savingSupplierOptionPosition = null,
  importingSupplierCandidatePosition = null,
  reviewingPriceCandidateId = null,
  preparingSupplierSearchPosition = null,
  discoveringSupplierPosition = null,
  autoSelectingAllSuppliers = false,
  confirmingReadyPriceCandidates = false,
  stagingPriceBookFeed = false,
  runningPriceDiscovery = false,
  autoEstimatingPosition = null,
  acceptingAutoEconomicsPosition = null,
  priceDiscoveryJob = null,
}) {
  const profiles = enrichEconomicsProfiles(productProfiles, tender?.items)
  const hasSupplierOptions = profiles.some((profile) => {
    const supplierOptions = profile?.raw_payload?.supplier_options
    return Array.isArray(supplierOptions) && supplierOptions.length > 0
  })
  const readyPriceCandidateCount = profiles.filter(hasReadyPriceCandidateWithoutCost).length
  const priceDiscoveryRunCount = profiles.filter(profileNeedsPriceDiscovery).length
  const canRunActivePriceDiscovery = profiles.length > 0 && profiles.length <= SMALL_TENDER_ACTIVE_DISCOVERY_LIMIT
  const requiresManualPriceFlow = profiles.length > SMALL_TENDER_ACTIVE_DISCOVERY_LIMIT

  return (
    <section className="detail-section active economics-section">
      <TenderEconomicsCommandCenter
        tender={tender}
        economics={economics}
        profiles={profiles}
        readyPriceCandidateCount={readyPriceCandidateCount}
        hasSupplierOptions={hasSupplierOptions}
        canRunActivePriceDiscovery={canRunActivePriceDiscovery}
        requiresManualPriceFlow={requiresManualPriceFlow}
        priceDiscoveryRunCount={priceDiscoveryRunCount}
        runningPriceDiscovery={runningPriceDiscovery}
        confirmingReadyPriceCandidates={confirmingReadyPriceCandidates}
        autoSelectingAllSuppliers={autoSelectingAllSuppliers}
        priceDiscoveryJob={priceDiscoveryJob}
        onPriceDiscoveryRun={onPriceDiscoveryRun}
        onReadyPriceCandidatesConfirmAll={onReadyPriceCandidatesConfirmAll}
        onSupplierOptionAutoSelectAll={onSupplierOptionAutoSelectAll}
      />
      <TenderEconomicsPriceBookFeed
        profiles={profiles}
        onPriceBookFeedStage={onPriceBookFeedStage}
        onPriceBookFeedFileStage={onPriceBookFeedFileStage}
        stagingPriceBookFeed={stagingPriceBookFeed}
      />
      <TenderEconomicsPriceMemory />
      <TenderEconomicsWorkbench
        economics={economics}
        profiles={profiles}
        selectedEconomicsProfileIndex={selectedEconomicsProfileIndex}
        onSelectedEconomicsProfileChange={onSelectedEconomicsProfileChange}
        onEconomicsSave={onEconomicsSave}
        onEconomicsAssumptionsSave={onEconomicsAssumptionsSave}
        onSupplierOptionSelect={onSupplierOptionSelect}
        onSupplierDiscoveryImport={onSupplierDiscoveryImport}
        onSupplierSearchPrepare={onSupplierSearchPrepare}
        onSupplierDiscoveryRun={onSupplierDiscoveryRun}
        onSupplierUrlDiscoveryRun={onSupplierUrlDiscoveryRun}
        onSupplierManualPriceStage={onSupplierManualPriceStage}
        onPriceCandidateConfirm={onPriceCandidateConfirm}
        onPriceCandidateReject={onPriceCandidateReject}
        onAutoEconomicsRun={onAutoEconomicsRun}
        onAutoEconomicsAccept={onAutoEconomicsAccept}
        savingEconomicsPosition={savingEconomicsPosition}
        savingAssumptionsPosition={savingAssumptionsPosition}
        savingSupplierOptionPosition={savingSupplierOptionPosition}
        importingSupplierCandidatePosition={importingSupplierCandidatePosition}
        reviewingPriceCandidateId={reviewingPriceCandidateId}
        preparingSupplierSearchPosition={preparingSupplierSearchPosition}
        discoveringSupplierPosition={discoveringSupplierPosition}
        autoEstimatingPosition={autoEstimatingPosition}
        acceptingAutoEconomicsPosition={acceptingAutoEconomicsPosition}
      />
      <EconomicsSummary economics={economics} tender={tender} profiles={profiles} />
    </section>
  )
}

function enrichEconomicsProfiles(productProfiles = [], tenderItems = []) {
  const itemByPosition = new Map()
  ;(Array.isArray(tenderItems) ? tenderItems : []).forEach((item, index) => {
    if (!item || typeof item !== 'object') return
    const positionIndex = Number(item.position_index || index + 1)
    if (Number.isFinite(positionIndex) && positionIndex > 0) {
      itemByPosition.set(positionIndex, item)
    }
  })

  return (Array.isArray(productProfiles) ? productProfiles : []).map((profile) => {
    if (!profile || typeof profile !== 'object') return profile
    const positionIndex = Number(profile.position_index || 0)
    const item = itemByPosition.get(positionIndex)
    if (!item) return profile
    const enriched = { ...profile }
    ;['quantity', 'unit', 'unit_price', 'total_price'].forEach((key) => {
      if ((enriched[key] == null || enriched[key] === '') && item[key] != null && item[key] !== '') {
        enriched[key] = item[key]
      }
    })
    return enriched
  })
}
