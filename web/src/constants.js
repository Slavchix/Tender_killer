import { Building2, Database, FileText } from 'lucide-react'

export const sourceLabels = {
  moscow_supplier_portal: 'Москва',
  mosreg_market: 'МО',
}

export const workflowLabels = {
  new: 'Новая',
  opened: 'Открыта',
  interesting: 'Интересно',
  in_progress: 'В работу',
  skipped: 'Пропустить',
  archive: 'Архив',
}

export const viewLabels = {
  dashboard: 'Дашборд',
  tenders: 'Закупки',
  database: 'SQLite',
}

export const navItems = [
  { id: 'dashboard', label: viewLabels.dashboard, caption: 'Сводка', icon: Building2 },
  { id: 'tenders', label: viewLabels.tenders, caption: 'Работа', icon: FileText },
  { id: 'database', label: viewLabels.database, caption: 'Данные', icon: Database },
]

export const sourceOptions = [
  { value: 'moscow_supplier_portal', label: 'Москва' },
  { value: 'mosreg_market', label: 'МО' },
]

export const lawOptions = [
  { value: '', label: 'Все' },
  { value: '44-ФЗ', label: '44-ФЗ' },
  { value: '223-ФЗ', label: '223-ФЗ' },
]

export const statusOptions = [
  { value: 'active', label: 'Активные' },
  { value: '', label: 'Все' },
  { value: 'Прием', label: 'Прием заявок' },
  { value: 'Заверш', label: 'Завершенные' },
]

export const quickRegionOptions = [
  { value: 'Москва', label: 'Москва' },
  { value: 'Московская область', label: 'МО' },
  { value: 'Москва + МО', label: 'Москва + МО' },
]

export const sourceFamilyOptions = [
  { value: '', label: 'Все' },
  { value: 'moscow', label: 'Москва' },
  { value: 'mosreg', label: 'МО' },
]

export const procedureTypeOptions = [
  { value: '', label: 'Все' },
  { value: 'electronic_shop', label: 'Эл-магазин' },
  { value: 'quotation_session', label: 'Котировка' },
  { value: 'supplier_portal', label: 'Портал' },
  { value: 'need', label: 'Потребность' },
  { value: 'tender', label: 'Тендер' },
]

export const initialFilters = {
  q: '',
  source: '',
  law: '',
  region: '',
  status: 'active',
  source_family: '',
  procedure_type: '',
  customer_inn: '',
  workflow_status: '',
  okpd2: '',
  min_price: '',
  max_price: '',
}

export const defaultTenderPageLimit = 25
export const tenderPageLimitOptions = [10, 25, 50, 100]

export const productDetailModes = [
  { id: 'overview', label: 'Паспорт' },
  { id: 'requirements', label: 'ТЗ' },
]

export const initialTenderPage = {
  total: 0,
  limit: defaultTenderPageLimit,
  offset: 0,
  has_previous: false,
  previous_offset: null,
  has_next: false,
  next_offset: null,
}
