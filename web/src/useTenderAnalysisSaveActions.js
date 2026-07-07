import { useState } from 'react'
import { saveAnalysisFeedback, saveAnalysisWorkflow } from './api'

export function useTenderAnalysisSaveActions(tender, setAnalysis) {
  const [savingAnalysisFeedbackId, setSavingAnalysisFeedbackId] = useState('')
  const [savingAnalysisWorkflow, setSavingAnalysisWorkflow] = useState(false)

  function resetAnalysisSaveState() {
    setSavingAnalysisFeedbackId('')
    setSavingAnalysisWorkflow(false)
  }

  function saveFactFeedback(factId, state, comment = '') {
    if (!factId) return Promise.resolve()
    setSavingAnalysisFeedbackId(factId)
    return saveAnalysisFeedback(tender, { fact_id: factId, state, comment })
      .then((payload) => {
        setAnalysis(payload.analysis || null)
      })
      .catch((err) => {
        setAnalysis((currentAnalysis) => ({
          ...(currentAnalysis || {}),
          feedback_error: err.message,
        }))
      })
      .finally(() => {
        setSavingAnalysisFeedbackId('')
      })
  }

  function saveTzWorkflow(payload) {
    setSavingAnalysisWorkflow(true)
    return saveAnalysisWorkflow(tender, payload)
      .then((responsePayload) => {
        setAnalysis(responsePayload.analysis || null)
      })
      .catch((err) => {
        setAnalysis((currentAnalysis) => ({
          ...(currentAnalysis || {}),
          workflow_error: err.message,
        }))
      })
      .finally(() => {
        setSavingAnalysisWorkflow(false)
      })
  }

  return {
    savingAnalysisFeedbackId,
    savingAnalysisWorkflow,
    resetAnalysisSaveState,
    saveFactFeedback,
    saveTzWorkflow,
  }
}
