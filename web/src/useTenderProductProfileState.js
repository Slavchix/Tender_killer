import { useState } from 'react'

export function useTenderProductProfileState(tender) {
  const [productProfiles, setProductProfiles] = useState(tender.product_profiles || [])
  const [productProfileSummary, setProductProfileSummary] = useState(tender.product_profile_summary || null)
  const [economics, setEconomics] = useState(tender.economics || null)
  const [selectedProfileIndex, setSelectedProfileIndex] = useState(0)
  const [profilesLoading, setProfilesLoading] = useState(false)

  function applyProductTenderState(nextTender, options = {}) {
    setProductProfiles(nextTender.product_profiles || [])
    setProductProfileSummary(nextTender.product_profile_summary || null)
    setEconomics(nextTender.economics || null)
    if (options.resetSelection !== false) setSelectedProfileIndex(0)
  }

  return {
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
  }
}
