import { Building2 } from 'lucide-react'
import { sourceLabels, workflowLabels } from './constants'
import { formatDate, nmcPriceValue, participantBidValue } from './formatters'

export function TenderDetailsHeader({ tender }) {
  return (
    <div className="details-header">
      <div className="details-title-row">
        <div className="panel-title"><Building2 size={18} /> Карточка</div>
        <span className={`workflow-chip ${tender.workflow_status || 'new'}`}>
          {workflowLabels[tender.workflow_status] || 'Новая'}
        </span>
      </div>
      <h2>{tender.title}</h2>
      <div className="detail-pills">
        <span>{sourceLabels[tender.source] || tender.source}</span>
        <span>{nmcPriceValue(tender)}</span>
        <span>{participantBidValue(tender.market_state)}</span>
        <span>{formatDate(tender.deadline_at)}</span>
      </div>
    </div>
  )
}
