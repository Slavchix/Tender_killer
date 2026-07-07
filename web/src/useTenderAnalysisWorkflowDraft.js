import { useEffect, useState } from 'react'

export function useTenderAnalysisWorkflowDraft(workflow = {}, onAnalysisWorkflow) {
  const [workflowDraft, setWorkflowDraft] = useState(workflowDraftFromContract(workflow))

  useEffect(() => {
    setWorkflowDraft(workflowDraftFromContract(workflow))
  }, [workflow.status, workflow.responsible, workflow.deadline, workflow.comment])

  function updateWorkflowDraft(field, value) {
    setWorkflowDraft((current) => ({ ...current, [field]: value }))
  }

  function saveWorkflowDraft(event) {
    event.preventDefault()
    onAnalysisWorkflow?.(workflowDraft)
  }

  return {
    saveWorkflowDraft,
    updateWorkflowDraft,
    workflowDraft,
  }
}

function workflowDraftFromContract(workflow = {}) {
  return {
    status: workflow.status || 'analysis_ready',
    responsible: workflow.responsible || '',
    deadline: workflow.deadline || '',
    comment: workflow.comment || '',
  }
}
