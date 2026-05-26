import { useEffect, useState } from 'react'
import {
  acceptProfileAutoEconomics as acceptProfileAutoEconomicsRequest,
  addProfileSupplierOption,
  autoSelectProfileSupplierOption,
  importProfileSupplierDiscoveryCandidate,
  prepareProfileSupplierSearch as prepareProfileSupplierSearchRequest,
  rebuildTenderProductProfiles,
  runProfileAutoEconomics as runProfileAutoEconomicsRequest,
  saveProfileEconomics as saveProfileEconomicsRequest,
  saveProfileEconomicsAssumptions as saveProfileEconomicsAssumptionsRequest,
  selectProfileSupplierOption,
} from './api'

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
  const [preparingSupplierSearchPosition, setPreparingSupplierSearchPosition] = useState(null)
  const [autoSelectingSupplierPosition, setAutoSelectingSupplierPosition] = useState(null)
  const [autoEstimatingPosition, setAutoEstimatingPosition] = useState(null)
  const [acceptingAutoEconomicsPosition, setAcceptingAutoEconomicsPosition] = useState(null)

  useEffect(() => {
    applyProductTenderState(tender)
    setSavingEconomicsPosition(null)
    setSavingAssumptionsPosition(null)
    setSavingSupplierOptionPosition(null)
    setImportingSupplierCandidatePosition(null)
    setPreparingSupplierSearchPosition(null)
    setAutoSelectingSupplierPosition(null)
    setAutoEstimatingPosition(null)
    setAcceptingAutoEconomicsPosition(null)
  }, [tender.source, tender.external_id, tender.product_profiles, tender.product_profile_summary, tender.economics])

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
    preparingSupplierSearchPosition,
    autoSelectingSupplierPosition,
    autoEstimatingPosition,
    acceptingAutoEconomicsPosition,
    applyProductTenderState,
    rebuildProductProfiles,
    saveProfileEconomics,
    saveProfileEconomicsAssumptions,
    saveSupplierOption,
    selectSupplierOption,
    autoSelectSupplierOption,
    importSupplierDiscoveryCandidate,
    prepareSupplierSearch,
    runProfileAutoEconomics,
    acceptProfileAutoEconomics,
  }
}
