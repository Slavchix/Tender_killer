import { ExternalLink, ShieldAlert } from 'lucide-react'
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
      <CustomerEisPanel tender={tender} />
    </section>
  )
}

function CustomerEisPanel({ tender }) {
  const riskProfile = tender.customer_risk_profile || {}
  const eis_reference = tender.eis_reference || {}
  const identifiers = eis_reference.identifiers || {}
  const customer = riskProfile.customer || {}
  const factors = (riskProfile.factors || [])
    .filter((factor) => factor?.evidence)
    .slice(0, 2)
  const links = (eis_reference.links || [])
    .filter((link) => link?.url)
    .slice(0, 3)
  const customerInn = customer.inn || identifiers.customer_inn || tender.customer_inn || ''
  const historyTotal = Number(riskProfile.history?.total || 0)

  if (!riskProfile.status && !links.length && !customerInn) return null

  return (
    <section className={`customer-eis-panel ${riskProfile.level || 'unknown'}`} aria-label="Заказчик и ЕИС">
      <div className="customer-eis-head">
        <div>
          <span><ShieldAlert size={15} /> Заказчик / ЕИС</span>
          <strong>{customerRiskLabel(riskProfile.level)}</strong>
        </div>
        <p>{customer.name || tender.customer || 'заказчик не указан'}{customerInn ? ` · ИНН ${customerInn}` : ''}</p>
      </div>
      <div className="customer-eis-facts">
        <Info label="История" value={historyTotal ? `${historyTotal} закупок` : 'нет истории'} />
        <Info label="ЕИС" value={identifiers.purchase_number || identifiers.customer_inn || 'ручной поиск'} />
        <Info label="Доступ" value={eis_reference.network_fetch_enabled ? 'авто' : 'ссылки'} />
      </div>
      {!!factors.length && (
        <div className="customer-eis-reasons">
          {factors.map((factor) => (
            <p key={`${factor.id || factor.evidence}`}>{factor.evidence}</p>
          ))}
        </div>
      )}
      {!!links.length && (
        <div className="customer-eis-links">
          {links.map((link) => (
            <a className="customer-eis-link" href={link.url} key={link.id || link.url} rel="noreferrer" target="_blank">
              {linkLabel(link)}
              <ExternalLink size={13} />
            </a>
          ))}
        </div>
      )}
    </section>
  )
}

function customerRiskLabel(level) {
  return {
    high: 'высокий риск',
    medium: 'нужна сверка',
    low: 'низкий риск',
  }[level] || 'риск не рассчитан'
}

function linkLabel(link) {
  return {
    eis_purchase_search: 'закупка',
    eis_contracts_by_customer: 'контракты',
    eis_complaints_by_customer: 'жалобы',
    eis_rnp_by_customer: 'РНП',
    eis_home: 'ЕИС',
  }[link.id] || link.label || 'ЕИС'
}
