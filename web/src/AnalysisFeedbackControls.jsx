import { useState } from 'react'
import { Ban, CheckCircle2, ClipboardCheck, XCircle } from 'lucide-react'
import { cleanAnalysisText } from './analysisTextUtils'

export const ANALYSIS_FEEDBACK_ACTIONS = [
  { state: 'correct', label: 'верно', icon: CheckCircle2 },
  { state: 'incorrect', label: 'неверно', icon: XCircle },
  { state: 'not_applicable', label: 'не относится к заявке', icon: Ban },
  { state: 'needs_manual_review', label: 'требует ручной проверки', icon: ClipboardCheck },
]

export function AnalysisFeedbackControls({ item, onFeedback, disabled = false }) {
  const [comment, setComment] = useState(item.feedback_comment || '')
  if (!onFeedback || !item?.id) return null
  return (
    <div className="analysis-feedback-panel">
      <div className="analysis-feedback-actions" aria-label="Метки анализа">
        {ANALYSIS_FEEDBACK_ACTIONS.map((action) => {
          const Icon = action.icon
          const active = item.feedback_state === action.state
          return (
            <button
              aria-label={action.label}
              className={active ? 'active' : ''}
              disabled={disabled}
              key={action.state}
              onClick={() => onFeedback(item.id, active ? 'clear' : action.state, comment)}
              title={action.label}
              type="button"
            >
              <Icon aria-hidden="true" size={15} strokeWidth={2.4} />
            </button>
          )
        })}
      </div>
      <input
        className="analysis-feedback-comment"
        disabled={disabled}
        onChange={(event) => setComment(event.target.value)}
        placeholder="Комментарий оператора"
        type="text"
        value={comment}
      />
    </div>
  )
}

export function feedbackHistoryText(entry = {}) {
  const toState = feedbackStateLabel(entry.to_state)
  const fromState = feedbackStateLabel(entry.from_state)
  const comment = cleanAnalysisText(entry.comment)
  const changedAt = cleanAnalysisText(entry.changed_at)
  const transition = fromState ? `${fromState} → ${toState}` : toState
  return [transition, comment, changedAt].filter(Boolean).join(' · ')
}

export function feedbackStateLabel(state) {
  if (state === 'correct') return 'верно'
  if (state === 'incorrect') return 'неверно'
  if (state === 'not_applicable') return 'не относится к заявке'
  if (state === 'needs_manual_review') return 'требует ручной проверки'
  return cleanAnalysisText(state)
}
