import { useState } from 'react'
import {
  addProfileSupplierOption,
  autoSelectTenderSupplierOptions as autoSelectTenderSupplierOptionsRequest,
  autoSelectProfileSupplierOption,
  importProfileSupplierDiscoveryCandidate,
  prepareProfileSupplierSearch as prepareProfileSupplierSearchRequest,
  runProfileSupplierDiscovery as runProfileSupplierDiscoveryRequest,
  runProfileSupplierUrlDiscovery as runProfileSupplierUrlDiscoveryRequest,
  selectProfileSupplierOption,
  stageProfileSupplierDiscoveryCandidates as stageProfileSupplierDiscoveryCandidatesRequest,
} from './api'

export function useTenderSupplierProfileActions({
  tender,
  updateFromNextTender,
  applyProductTenderState,
  onTenderRefresh,
  setDetailStatus,
}) {
  const [savingSupplierOptionPosition, setSavingSupplierOptionPosition] = useState(null)
  const [importingSupplierCandidatePosition, setImportingSupplierCandidatePosition] = useState(null)
  const [preparingSupplierSearchPosition, setPreparingSupplierSearchPosition] = useState(null)
  const [discoveringSupplierPosition, setDiscoveringSupplierPosition] = useState(null)
  const [autoSelectingSupplierPosition, setAutoSelectingSupplierPosition] = useState(null)
  const [autoSelectingAllSuppliers, setAutoSelectingAllSuppliers] = useState(false)

  function resetSupplierActionState() {
    setSavingSupplierOptionPosition(null)
    setImportingSupplierCandidatePosition(null)
    setPreparingSupplierSearchPosition(null)
    setDiscoveringSupplierPosition(null)
    setAutoSelectingSupplierPosition(null)
    setAutoSelectingAllSuppliers(false)
  }

  function refreshFromErrorPayload(err) {
    if (!err.payload?.product_profiles) return
    onTenderRefresh(err.payload)
    applyProductTenderState(err.payload, { resetSelection: false })
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
      .then((nextTender) => updateFromNextTender(nextTender, 'Лучшая цена взята в расчет'))
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

  function runSupplierDiscovery(profile) {
    if (!profile?.position_index) return null
    setDiscoveringSupplierPosition(profile.position_index)
    setDetailStatus('')
    return runProfileSupplierDiscoveryRequest(tender, profile)
      .then((nextTender) => updateFromNextTender(nextTender, 'Кандидаты поставщиков найдены'))
      .catch((err) => {
        refreshFromErrorPayload(err)
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
        refreshFromErrorPayload(err)
        setDetailStatus(err.message)
        throw err
      })
      .finally(() => setDiscoveringSupplierPosition(null))
  }

  function stageSupplierManualPriceCandidate(profile, candidate) {
    if (!profile?.position_index || !candidate) return null
    setDiscoveringSupplierPosition(profile.position_index)
    setDetailStatus('')
    return stageProfileSupplierDiscoveryCandidatesRequest(tender, profile, [candidate])
      .then((nextTender) => updateFromNextTender(nextTender, 'Ручная цена добавлена в кандидаты'))
      .catch((err) => {
        refreshFromErrorPayload(err)
        setDetailStatus(err.message)
        throw err
      })
      .finally(() => setDiscoveringSupplierPosition(null))
  }

  return {
    savingSupplierOptionPosition,
    importingSupplierCandidatePosition,
    preparingSupplierSearchPosition,
    discoveringSupplierPosition,
    autoSelectingSupplierPosition,
    autoSelectingAllSuppliers,
    resetSupplierActionState,
    saveSupplierOption,
    selectSupplierOption,
    autoSelectSupplierOption,
    autoSelectAllSupplierOptions,
    importSupplierDiscoveryCandidate,
    prepareSupplierSearch,
    runSupplierDiscovery,
    runSupplierUrlDiscovery,
    stageSupplierManualPriceCandidate,
  }
}
