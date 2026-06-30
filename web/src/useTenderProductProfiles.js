import { useEffect, useState } from 'react'
import {
  fetchPriceDiscoveryJob,
  rebuildTenderProductProfiles,
} from './api'
import { useTenderEconomicsProfileActions } from './useTenderEconomicsProfileActions'
import {
  isPriceDiscoveryJobActive,
  priceDiscoveryStatusMessage,
  useTenderPriceCandidateActions,
} from './useTenderPriceCandidateActions'
import { useTenderProductProfileState } from './useTenderProductProfileState'
import { useTenderSupplierProfileActions } from './useTenderSupplierProfileActions'

export function useTenderProductProfiles(tender, onTenderRefresh, setDetailStatus) {
  const [reviewingPriceCandidateId, setReviewingPriceCandidateId] = useState(null)
  const [priceDiscoveryJob, setPriceDiscoveryJob] = useState(null)

  const {
    productProfiles,
    productProfileSummary,
    economics,
    selectedProfileIndex,
    setSelectedProfileIndex,
    profilesLoading,
    setProfilesLoading,
    setProductProfiles,
    setProductProfileSummary,
    applyProductTenderState,
  } = useTenderProductProfileState(tender)

  function updateFromNextTender(nextTender, message) {
    onTenderRefresh(nextTender)
    applyProductTenderState(nextTender, { resetSelection: false })
    setDetailStatus(message)
    return nextTender
  }

  const economicsActions = useTenderEconomicsProfileActions({
    tender,
    updateFromNextTender,
    setDetailStatus,
  })
  const supplierActions = useTenderSupplierProfileActions({
    tender,
    updateFromNextTender,
    applyProductTenderState,
    onTenderRefresh,
    setDetailStatus,
  })

  useEffect(() => {
    applyProductTenderState(tender)
    economicsActions.resetEconomicsActionState()
    supplierActions.resetSupplierActionState()
    setReviewingPriceCandidateId(null)
    setPriceDiscoveryJob(null)
  }, [tender.source, tender.external_id, tender.product_profiles, tender.product_profile_summary, tender.economics])

  useEffect(() => {
    if (!isPriceDiscoveryJobActive(priceDiscoveryJob) || !priceDiscoveryJob?.job_id) return undefined

    let cancelled = false
    const timer = window.setTimeout(() => {
      fetchPriceDiscoveryJob(priceDiscoveryJob.job_id)
        .then((payload) => {
          if (cancelled) return

          const job = payload.price_discovery_job || {}
          const active = isPriceDiscoveryJobActive(job)
          if (!active && payload.tender) {
            onTenderRefresh(payload.tender)
            applyProductTenderState(payload.tender, { resetSelection: false })
          }
          setPriceDiscoveryJob(job)
          setDetailStatus(priceDiscoveryStatusMessage(job))
          if (!active) {
            setReviewingPriceCandidateId(null)
          }
        })
        .catch((err) => {
          if (cancelled) return
          setPriceDiscoveryJob(null)
          setReviewingPriceCandidateId(null)
          setDetailStatus(err.message)
        })
    }, 1500)

    return () => {
      cancelled = true
      window.clearTimeout(timer)
    }
  }, [priceDiscoveryJob, onTenderRefresh, setDetailStatus])

  function rebuildProductProfiles() {
    setProfilesLoading(true)
    rebuildTenderProductProfiles(tender)
      .then((payload) => {
        setProductProfiles(payload.product_profiles || [])
        setProductProfileSummary(payload.summary || null)
        setSelectedProfileIndex(0)
      })
      .catch((err) => {
        setProductProfileSummary((current) => current || { total: productProfiles.length })
        window.alert(err.message)
      })
      .finally(() => setProfilesLoading(false))
  }

  const priceCandidateActions = useTenderPriceCandidateActions({
    tender,
    updateFromNextTender,
    setDetailStatus,
    reviewingPriceCandidateId,
    setReviewingPriceCandidateId,
    priceDiscoveryJob,
    setPriceDiscoveryJob,
  })

  return {
    productProfiles,
    productProfileSummary,
    economics,
    selectedProfileIndex,
    setSelectedProfileIndex,
    profilesLoading,
    savingEconomicsPosition: economicsActions.savingEconomicsPosition,
    savingAssumptionsPosition: economicsActions.savingAssumptionsPosition,
    savingSupplierOptionPosition: supplierActions.savingSupplierOptionPosition,
    importingSupplierCandidatePosition: supplierActions.importingSupplierCandidatePosition,
    reviewingPriceCandidateId,
    preparingSupplierSearchPosition: supplierActions.preparingSupplierSearchPosition,
    discoveringSupplierPosition: supplierActions.discoveringSupplierPosition,
    autoSelectingSupplierPosition: supplierActions.autoSelectingSupplierPosition,
    autoSelectingAllSuppliers: supplierActions.autoSelectingAllSuppliers,
    confirmingReadyPriceCandidates: priceCandidateActions.confirmingReadyPriceCandidates,
    stagingPriceCandidates: priceCandidateActions.stagingPriceCandidates,
    stagingPriceBookFeed: priceCandidateActions.stagingPriceBookFeed,
    runningPriceDiscovery: priceCandidateActions.runningPriceDiscovery,
    applyingAutoPrices: priceCandidateActions.applyingAutoPrices,
    autoEstimatingPosition: economicsActions.autoEstimatingPosition,
    acceptingAutoEconomicsPosition: economicsActions.acceptingAutoEconomicsPosition,
    priceDiscoveryJob,
    applyProductTenderState,
    rebuildProductProfiles,
    saveProfileEconomics: economicsActions.saveProfileEconomics,
    saveProfileEconomicsAssumptions: economicsActions.saveProfileEconomicsAssumptions,
    saveSupplierOption: supplierActions.saveSupplierOption,
    selectSupplierOption: supplierActions.selectSupplierOption,
    autoSelectSupplierOption: supplierActions.autoSelectSupplierOption,
    autoSelectAllSupplierOptions: supplierActions.autoSelectAllSupplierOptions,
    confirmReadyPriceCandidates: priceCandidateActions.confirmReadyPriceCandidates,
    stagePriceCandidates: priceCandidateActions.stagePriceCandidates,
    stagePriceBookFeed: priceCandidateActions.stagePriceBookFeed,
    stagePriceBookFeedFile: priceCandidateActions.stagePriceBookFeedFile,
    applyAutoPrices: priceCandidateActions.applyAutoPrices,
    runPriceDiscovery: priceCandidateActions.runPriceDiscovery,
    importSupplierDiscoveryCandidate: supplierActions.importSupplierDiscoveryCandidate,
    confirmPriceCandidate: priceCandidateActions.confirmPriceCandidate,
    rejectPriceCandidate: priceCandidateActions.rejectPriceCandidate,
    prepareSupplierSearch: supplierActions.prepareSupplierSearch,
    runSupplierDiscovery: supplierActions.runSupplierDiscovery,
    runSupplierUrlDiscovery: supplierActions.runSupplierUrlDiscovery,
    stageSupplierManualPriceCandidate: supplierActions.stageSupplierManualPriceCandidate,
    runProfileAutoEconomics: economicsActions.runProfileAutoEconomics,
    acceptProfileAutoEconomics: economicsActions.acceptProfileAutoEconomics,
  }
}
