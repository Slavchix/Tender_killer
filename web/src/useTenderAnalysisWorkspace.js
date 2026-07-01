import { useEffect, useRef, useState } from 'react'
import { analysisSectionItems } from './analysisSectionsModel'
import { resolveEvidenceDrilldown } from './TenderAnalysisEvidenceModel'

export function useTenderAnalysisWorkspace(analysis, documents = []) {
  const [selectedAnalysisSection, setSelectedAnalysisSection] = useState('decision_risks')
  const [analysisViewMode, setAnalysisViewMode] = useState('compact')
  const [selectedEvidence, setSelectedEvidence] = useState(null)
  const userSelectedAnalysisSectionRef = useRef(false)
  const analysisSections = analysisSectionItems(analysis, documents)
  const analysisSectionKey = analysisSections.map((section) => section.id).join('|')
  const primarySection = analysis?.operator_view?.decision_brief?.primary_section
  const evidenceDrilldowns = analysis?.operator_view?.evidence_drilldowns || {}

  useEffect(() => {
    const sectionIds = new Set(analysisSections.map((section) => section.id))
    setSelectedAnalysisSection((currentSection) => {
      if (!userSelectedAnalysisSectionRef.current && primarySection && sectionIds.has(primarySection)) {
        return primarySection
      }
      if (!sectionIds.has(currentSection)) {
        userSelectedAnalysisSectionRef.current = false
        return analysisSections[0]?.id || 'decision_risks'
      }
      return currentSection
    })
  }, [analysisSectionKey, primarySection])

  useEffect(() => {
    setSelectedEvidence(null)
  }, [analysis?.analyzed_at, analysis?.status])

  function selectAnalysisSection(sectionId) {
    userSelectedAnalysisSectionRef.current = true
    setSelectedAnalysisSection(sectionId)
  }

  function selectEvidenceDrilldown(value) {
    setSelectedEvidence(resolveEvidenceDrilldown(value, evidenceDrilldowns))
  }

  return {
    analysisSections,
    analysisViewMode,
    evidenceDrilldowns,
    selectAnalysisSection,
    selectEvidenceDrilldown,
    selectedAnalysisSection,
    selectedEvidence,
    setAnalysisViewMode,
  }
}
