import { useState } from 'react'
import {
  acceptProfileAutoEconomics as acceptProfileAutoEconomicsRequest,
  runProfileAutoEconomics as runProfileAutoEconomicsRequest,
  saveProfileEconomics as saveProfileEconomicsRequest,
  saveProfileEconomicsAssumptions as saveProfileEconomicsAssumptionsRequest,
} from './api'

export function useTenderEconomicsProfileActions({ tender, updateFromNextTender, setDetailStatus }) {
  const [savingEconomicsPosition, setSavingEconomicsPosition] = useState(null)
  const [savingAssumptionsPosition, setSavingAssumptionsPosition] = useState(null)
  const [autoEstimatingPosition, setAutoEstimatingPosition] = useState(null)
  const [acceptingAutoEconomicsPosition, setAcceptingAutoEconomicsPosition] = useState(null)

  function resetEconomicsActionState() {
    setSavingEconomicsPosition(null)
    setSavingAssumptionsPosition(null)
    setAutoEstimatingPosition(null)
    setAcceptingAutoEconomicsPosition(null)
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
    savingEconomicsPosition,
    savingAssumptionsPosition,
    autoEstimatingPosition,
    acceptingAutoEconomicsPosition,
    resetEconomicsActionState,
    saveProfileEconomics,
    saveProfileEconomicsAssumptions,
    runProfileAutoEconomics,
    acceptProfileAutoEconomics,
  }
}
