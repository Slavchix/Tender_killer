import { useEffect, useState } from 'react'
import {
  acceptProfileAutoEconomics as acceptProfileAutoEconomicsRequest,
  addProfileSupplierOption,
  autoSelectTenderSupplierOptions as autoSelectTenderSupplierOptionsRequest,
  autoSelectProfileSupplierOption,
  confirmReadyTenderPriceCandidates as confirmReadyTenderPriceCandidatesRequest,
  confirmProfilePriceCandidate as confirmProfilePriceCandidateRequest,
  fetchSupplierCatalogHealth,
  importProfileSupplierDiscoveryCandidate,
  prepareProfileSupplierSearch as prepareProfileSupplierSearchRequest,
  rebuildTenderProductProfiles,
  rejectProfilePriceCandidate as rejectProfilePriceCandidateRequest,
  runProfileAutoEconomics as runProfileAutoEconomicsRequest,
  runProfileSupplierDiscovery as runProfileSupplierDiscoveryRequest,
  runProfileSupplierUrlDiscovery as runProfileSupplierUrlDiscoveryRequest,
  saveProfileSupplierCatalogPresets as saveProfileSupplierCatalogPresetsRequest,
  saveProfileEconomics as saveProfileEconomicsRequest,
  saveProfileEconomicsAssumptions as saveProfileEconomicsAssumptionsRequest,
  selectProfileSupplierOption,
} from './api'

const READY_PRICE_CANDIDATES_REVIEW_ID = 'ready-price-candidates-bulk'

export function useTenderProductProfiles(tender, onTenderRefresh, setDetailStatus) {
  const [productProfiles, setProductProfiles] = useState(tender.product_profiles || [])
  const [productProfileSummary, setProductProfileSummary] = useState(tender.product_profile_summary || null)
  const [economics, setEconomics] = useState(tender.economics || null)
  const [selectedProfileIndex, setSelectedProfileIndex] = useState(0)
  const [profilesLoading, setProfilesLoading] = useState(false)
  const [savingEconomicsPosition, setSavingEconomicsPosition] = useState(null)
  const [savingAssumptionsPosition, setSavingAssumptionsPosition] = useState(null)
  const [savingSupplierOptionPosition, setSavingSupplierOptionPosition] = useState(null)
  const [importingSupplierCandidatePosition, setImportingSupplierCandidatePosition] = useState(null)
  const [reviewingPriceCandidateId, setReviewingPriceCandidateId] = useState(null)
  const [preparingSupplierSearchPosition, setPreparingSupplierSearchPosition] = useState(null)
  const [savingSupplierCatalogPresetPosition, setSavingSupplierCatalogPresetPosition] = useState(null)
  const [discoveringSupplierPosition, setDiscoveringSupplierPosition] = useState(null)
  const [autoSelectingSupplierPosition, setAutoSelectingSupplierPosition] = useState(null)
  const [autoSelectingAllSuppliers, setAutoSelectingAllSuppliers] = useState(false)
  const [autoEstimatingPosition, setAutoEstimatingPosition] = useState(null)
  const [acceptingAutoEconomicsPosition, setAcceptingAutoEconomicsPosition] = useState(null)
  const [supplierCatalogHealth, setSupplierCatalogHealth] = useState(null)
  const [supplierCatalogHealthLoading, setSupplierCatalogHealthLoading] = useState(false)
  const [supplierCatalogHealthError, setSupplierCatalogHealthError] = useState('')

  useEffect(() => {
    applyProductTenderState(tender)
    setSavingEconomicsPosition(null)
    setSavingAssumptionsPosition(null)
    setSavingSupplierOptionPosition(null)
    setImportingSupplierCandidatePosition(null)
    setReviewingPriceCandidateId(null)
    setPreparingSupplierSearchPosition(null)
    setSavingSupplierCatalogPresetPosition(null)
    setDiscoveringSupplierPosition(null)
    setAutoSelectingSupplierPosition(null)
    setAutoSelectingAllSuppliers(false)
    setAutoEstimatingPosition(null)
    setAcceptingAutoEconomicsPosition(null)
  }, [tender.source, tender.external_id, tender.product_profiles, tender.product_profile_summary, tender.economics])

  function refreshSupplierCatalogHealth(live = false) {
    setSupplierCatalogHealthLoading(true)
    setSupplierCatalogHealthError('')
    return fetchSupplierCatalogHealth({ live })
      .then((payload) => {
        setSupplierCatalogHealth(payload)
        return payload
      })
      .catch((err) => {
        setSupplierCatalogHealthError(err.message)
        throw err
      })
      .finally(() => setSupplierCatalogHealthLoading(false))
  }

  function applyProductTenderState(nextTender, options = {}) {
    setProductProfiles(nextTender.product_profiles || [])
    setProductProfileSummary(nextTender.product_profile_summary || null)
    setEconomics(nextTender.economics || null)
    if (options.resetSelection !== false) setSelectedProfileIndex(0)
  }

  function updateFromNextTender(nextTender, message) {
    onTenderRefresh(nextTender)
    applyProductTenderState(nextTender, { resetSelection: false })
    setDetailStatus(message)
    return nextTender
  }

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

  function saveProfileEconomics(profile, economicsInputs) {
    if (!profile?.position_index) return
    setSavingEconomicsPosition(profile.position_index)
    setDetailStatus('')
    saveProfileEconomicsRequest(tender, profile, economicsInputs)
      .then((nextTender) => updateFromNextTender(nextTender, 'Экономика обновлена'))
      .catch((err) => setDetailStatus(err.message))
      .finally(() => setSavingEconomicsPosition(null))
  }

  function saveProfileEconomicsAssumptions(profile, assumptionsInputs) {
    if (!profile?.position_index) return null
    setSavingAssumptionsPosition(profile.position_index)
    setDetailStatus('')
    return saveProfileEconomicsAssumptionsRequest(tender, profile, assumptionsInputs)
      .then((nextTender) => updateFromNextTender(nextTender, 'Допущения экономики обновлены'))
      .catch((err) => {
        setDetailStatus(err.message)
        throw err
      })
      .finally(() => setSavingAssumptionsPosition(null))
  }

  function saveSupplierOption(profile, supplierOption) {
    if (!profile?.position_index) return null
    setSavingSupplierOptionPosition(profile.position_index)
    setDetailStatus('')
    return addProfileSupplierOption(tender, profile, supplierOption)
      .then((nextTender) => updateFromNextTender(nextTender, 'Поставщик добавлен'))
      .catch((err) => {
        setDetailStatus(err.message)
        throw err
      })
      .finally(() => setSavingSupplierOptionPosition(null))
  }

  function selectSupplierOption(profile, optionIndex) {
    if (!profile?.position_index) return null
    setSavingSupplierOptionPosition(profile.position_index)
    setDetailStatus('')
    return selectProfileSupplierOption(tender, profile, optionIndex)
      .then((nextTender) => updateFromNextTender(nextTender, 'Поставщик взят в расчет'))
      .catch((err) => {
        setDetailStatus(err.message)
        throw err
      })
      .finally(() => setSavingSupplierOptionPosition(null))
  }

  function autoSelectSupplierOption(profile) {
    if (!profile?.position_index) return null
    setAutoSelectingSupplierPosition(profile.position_index)
    setDetailStatus('')
    return autoSelectProfileSupplierOption(tender, profile)
      .then((nextTender) => updateFromNextTender(nextTender, 'Лучший поставщик взят в расчет'))
      .catch((err) => {
        setDetailStatus(err.message)
        throw err
      })
      .finally(() => setAutoSelectingSupplierPosition(null))
  }

  function autoSelectAllSupplierOptions() {
    setAutoSelectingAllSuppliers(true)
    setDetailStatus('')
    return autoSelectTenderSupplierOptionsRequest(tender)
      .then((nextTender) => {
        const selection = nextTender.supplier_selection || {}
        const selected = Number(selection.selected_count || 0)
        const skipped = Number(selection.skipped_count || 0)
        return updateFromNextTender(nextTender, `Лучшие цены в расчете: ${selected}, пропущено: ${skipped}`)
      })
      .catch((err) => {
        setDetailStatus(err.message)
        throw err
      })
      .finally(() => setAutoSelectingAllSuppliers(false))
  }

  function confirmReadyPriceCandidates() {
    setReviewingPriceCandidateId(READY_PRICE_CANDIDATES_REVIEW_ID)
    setDetailStatus('')
    return confirmReadyTenderPriceCandidatesRequest(tender)
      .then((nextTender) => {
        const review = nextTender.price_candidate_bulk_review || {}
        const confirmed = Number(review.confirmed_count || 0)
        const skipped = Number(review.skipped_count || 0)
        return updateFromNextTender(nextTender, `Готовые цены приняты: ${confirmed}, пропущено: ${skipped}`)
      })
      .catch((err) => {
        setDetailStatus(err.message)
        throw err
      })
      .finally(() => setReviewingPriceCandidateId(null))
  }

  function importSupplierDiscoveryCandidate(profile, candidateIndex) {
    if (!profile?.position_index) return null
    setImportingSupplierCandidatePosition(profile.position_index)
    setDetailStatus('')
    return importProfileSupplierDiscoveryCandidate(tender, profile, candidateIndex)
      .then((nextTender) => updateFromNextTender(nextTender, 'Найденный поставщик добавлен'))
      .catch((err) => {
        setDetailStatus(err.message)
        throw err
      })
      .finally(() => setImportingSupplierCandidatePosition(null))
  }

  function confirmPriceCandidate(profile, candidate) {
    return reviewPriceCandidate(profile, candidate, confirmProfilePriceCandidateRequest, 'Цена кандидата принята в экономику')
  }

  function rejectPriceCandidate(profile, candidate) {
    return reviewPriceCandidate(profile, candidate, rejectProfilePriceCandidateRequest, 'Цена кандидата отклонена')
  }

  function reviewPriceCandidate(profile, candidate, request, message) {
    if (!profile?.position_index || !candidate?.id) return null
    setReviewingPriceCandidateId(candidate.id)
    setDetailStatus('')
    return request(tender, profile, candidate.id)
      .then((nextTender) => updateFromNextTender(nextTender, message))
      .catch((err) => {
        setDetailStatus(err.message)
        throw err
      })
      .finally(() => setReviewingPriceCandidateId(null))
  }

  function prepareSupplierSearch(profile) {
    if (!profile?.position_index) return null
    setPreparingSupplierSearchPosition(profile.position_index)
    setDetailStatus('')
    return prepareProfileSupplierSearchRequest(tender, profile)
      .then((nextTender) => updateFromNextTender(nextTender, 'Поиск поставщиков подготовлен'))
      .catch((err) => {
        setDetailStatus(err.message)
        throw err
      })
      .finally(() => setPreparingSupplierSearchPosition(null))
  }

  function saveSupplierCatalogPresets(profile, presetIds) {
    if (!profile?.position_index) return null
    setSavingSupplierCatalogPresetPosition(profile.position_index)
    setDetailStatus('')
    return saveProfileSupplierCatalogPresetsRequest(tender, profile, presetIds)
      .then((nextTender) => updateFromNextTender(nextTender, 'Каталоги поставщиков обновлены'))
      .catch((err) => {
        setDetailStatus(err.message)
        throw err
      })
      .finally(() => setSavingSupplierCatalogPresetPosition(null))
  }

  function runSupplierDiscovery(profile) {
    if (!profile?.position_index) return null
    setDiscoveringSupplierPosition(profile.position_index)
    setDetailStatus('')
    return runProfileSupplierDiscoveryRequest(tender, profile)
      .then((nextTender) => updateFromNextTender(nextTender, 'Кандидаты поставщиков найдены'))
      .catch((err) => {
        if (err.payload?.product_profiles) {
          onTenderRefresh(err.payload)
          applyProductTenderState(err.payload, { resetSelection: false })
        }
        setDetailStatus(err.message)
        throw err
      })
      .finally(() => setDiscoveringSupplierPosition(null))
  }

  function runSupplierUrlDiscovery(profile, payload) {
    if (!profile?.position_index) return null
    setDiscoveringSupplierPosition(profile.position_index)
    setDetailStatus('')
    return runProfileSupplierUrlDiscoveryRequest(tender, profile, payload)
      .then((nextTender) => updateFromNextTender(nextTender, 'Кандидат по ссылке найден'))
      .catch((err) => {
        if (err.payload?.product_profiles) {
          onTenderRefresh(err.payload)
          applyProductTenderState(err.payload, { resetSelection: false })
        }
        setDetailStatus(err.message)
        throw err
      })
      .finally(() => setDiscoveringSupplierPosition(null))
  }

  function runProfileAutoEconomics(profile) {
    if (!profile?.position_index) return null
    setAutoEstimatingPosition(profile.position_index)
    setDetailStatus('')
    return runProfileAutoEconomicsRequest(tender, profile)
      .then((nextTender) => updateFromNextTender(nextTender, 'Авторасчет обновлен'))
      .catch((err) => {
        setDetailStatus(err.message)
        throw err
      })
      .finally(() => setAutoEstimatingPosition(null))
  }

  function acceptProfileAutoEconomics(profile) {
    if (!profile?.position_index) return null
    setAcceptingAutoEconomicsPosition(profile.position_index)
    setDetailStatus('')
    return acceptProfileAutoEconomicsRequest(tender, profile)
      .then((nextTender) => updateFromNextTender(nextTender, 'Авторасчет принят в экономику'))
      .catch((err) => {
        setDetailStatus(err.message)
        throw err
      })
      .finally(() => setAcceptingAutoEconomicsPosition(null))
  }

  const confirmingReadyPriceCandidates = reviewingPriceCandidateId === READY_PRICE_CANDIDATES_REVIEW_ID

  return {
    productProfiles,
    productProfileSummary,
    economics,
    selectedProfileIndex,
    setSelectedProfileIndex,
    profilesLoading,
    savingEconomicsPosition,
    savingAssumptionsPosition,
    savingSupplierOptionPosition,
    importingSupplierCandidatePosition,
    reviewingPriceCandidateId,
    preparingSupplierSearchPosition,
    savingSupplierCatalogPresetPosition,
    discoveringSupplierPosition,
    autoSelectingSupplierPosition,
    autoSelectingAllSuppliers,
    confirmingReadyPriceCandidates,
    autoEstimatingPosition,
    acceptingAutoEconomicsPosition,
    supplierCatalogHealth,
    supplierCatalogHealthLoading,
    supplierCatalogHealthError,
    refreshSupplierCatalogHealth,
    applyProductTenderState,
    rebuildProductProfiles,
    saveProfileEconomics,
    saveProfileEconomicsAssumptions,
    saveSupplierOption,
    selectSupplierOption,
    autoSelectSupplierOption,
    autoSelectAllSupplierOptions,
    confirmReadyPriceCandidates,
    importSupplierDiscoveryCandidate,
    confirmPriceCandidate,
    rejectPriceCandidate,
    prepareSupplierSearch,
    saveSupplierCatalogPresets,
    runSupplierDiscovery,
    runSupplierUrlDiscovery,
    runProfileAutoEconomics,
    acceptProfileAutoEconomics,
  }
}
