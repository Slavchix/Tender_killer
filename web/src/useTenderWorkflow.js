import { useEffect, useState } from 'react'
import { saveTenderWorkflow } from './api'

export function useTenderWorkflow(tender, onWorkflowUpdate) {
  const [note, setNote] = useState(tender.workflow_note || '')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    setNote(tender.workflow_note || '')
  }, [tender.source, tender.external_id, tender.workflow_note])

  function saveWorkflow(workflowStatus = tender.workflow_status || 'new', workflowNote = note) {
    setSaving(true)
    saveTenderWorkflow(tender, {
      workflow_status: workflowStatus,
      workflow_note: workflowNote,
    })
      .then(onWorkflowUpdate)
      .finally(() => setSaving(false))
  }

  return {
    note,
    setNote,
    saving,
    saveWorkflow,
  }
}
