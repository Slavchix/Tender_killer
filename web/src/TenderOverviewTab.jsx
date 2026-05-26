import { sourceLabels } from './constants'
import { Info } from './TenderDetailsShared'

export function TenderOverviewTab({ tender, raw }) {
  const law = tender.law || raw.federalLawName || raw.SourcePlatformName || 'не найден'
  const category = tender.category || raw.CategoryName || 'не найдена'

  return (
    <section className="detail-section active overview-tab">
      <div className="tab-lead">
        <div>
          <span>Паспорт закупки</span>
          <strong>{tender.external_id}</strong>
          <p>{tender.customer || 'заказчик не указан'}</p>
        </div>
        <div className="tab-lead-facts">
          <span>{tender.region || 'регион не указан'}</span>
          <span>{law}</span>
        </div>
      </div>
      <div className="overview-brief-grid">
        <Info label="Площадка" value={sourceLabels[tender.source] || tender.source} />
        <Info label="Статус площадки" value={tender.status || 'не указан'} />
        <Info label="Категория" value={category} />
        <Info label="ОКПД2" value={tender.okpd2 || raw.Koz2Value || 'не найден'} />
      </div>
    </section>
  )
}
