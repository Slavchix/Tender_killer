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

export const deadlineOptions = [
  { value: '', label: 'Бессрочно' },
  { value: '1', label: '1 час' },
  { value: '2', label: '2 часа' },
  { value: '3', label: '3 часа' },
  { value: '5', label: '5 часов' },
  { value: '12', label: '12 часов' },
]

export const regionOptions = [
  { value: '', label: 'Все регионы' },
  { value: 'Москва', label: 'Москва' },
  { value: 'Московская область', label: 'Московская область' },
  { value: 'Санкт-Петербург', label: 'Санкт-Петербург' },
  { value: 'Севастополь', label: 'Севастополь' },
  { value: 'Республика Адыгея', label: 'Республика Адыгея' },
  { value: 'Республика Алтай', label: 'Республика Алтай' },
  { value: 'Республика Башкортостан', label: 'Республика Башкортостан' },
  { value: 'Республика Бурятия', label: 'Республика Бурятия' },
  { value: 'Республика Дагестан', label: 'Республика Дагестан' },
  { value: 'Республика Ингушетия', label: 'Республика Ингушетия' },
  { value: 'Кабардино-Балкарская Республика', label: 'Кабардино-Балкарская Республика' },
  { value: 'Республика Калмыкия', label: 'Республика Калмыкия' },
  { value: 'Карачаево-Черкесская Республика', label: 'Карачаево-Черкесская Республика' },
  { value: 'Республика Карелия', label: 'Республика Карелия' },
  { value: 'Республика Коми', label: 'Республика Коми' },
  { value: 'Республика Крым', label: 'Республика Крым' },
  { value: 'Республика Марий Эл', label: 'Республика Марий Эл' },
  { value: 'Республика Мордовия', label: 'Республика Мордовия' },
  { value: 'Республика Саха (Якутия)', label: 'Республика Саха (Якутия)' },
  { value: 'Республика Северная Осетия - Алания', label: 'Республика Северная Осетия - Алания' },
  { value: 'Республика Татарстан', label: 'Республика Татарстан' },
  { value: 'Республика Тыва', label: 'Республика Тыва' },
  { value: 'Удмуртская Республика', label: 'Удмуртская Республика' },
  { value: 'Республика Хакасия', label: 'Республика Хакасия' },
  { value: 'Чеченская Республика', label: 'Чеченская Республика' },
  { value: 'Чувашская Республика', label: 'Чувашская Республика' },
  { value: 'Алтайский край', label: 'Алтайский край' },
  { value: 'Забайкальский край', label: 'Забайкальский край' },
  { value: 'Камчатский край', label: 'Камчатский край' },
  { value: 'Краснодарский край', label: 'Краснодарский край' },
  { value: 'Красноярский край', label: 'Красноярский край' },
  { value: 'Пермский край', label: 'Пермский край' },
  { value: 'Приморский край', label: 'Приморский край' },
  { value: 'Ставропольский край', label: 'Ставропольский край' },
  { value: 'Хабаровский край', label: 'Хабаровский край' },
  { value: 'Амурская область', label: 'Амурская область' },
  { value: 'Архангельская область', label: 'Архангельская область' },
  { value: 'Астраханская область', label: 'Астраханская область' },
  { value: 'Белгородская область', label: 'Белгородская область' },
  { value: 'Брянская область', label: 'Брянская область' },
  { value: 'Владимирская область', label: 'Владимирская область' },
  { value: 'Волгоградская область', label: 'Волгоградская область' },
  { value: 'Вологодская область', label: 'Вологодская область' },
  { value: 'Воронежская область', label: 'Воронежская область' },
  { value: 'Ивановская область', label: 'Ивановская область' },
  { value: 'Иркутская область', label: 'Иркутская область' },
  { value: 'Калининградская область', label: 'Калининградская область' },
  { value: 'Калужская область', label: 'Калужская область' },
  { value: 'Кемеровская область', label: 'Кемеровская область' },
  { value: 'Кировская область', label: 'Кировская область' },
  { value: 'Костромская область', label: 'Костромская область' },
  { value: 'Курганская область', label: 'Курганская область' },
  { value: 'Курская область', label: 'Курская область' },
  { value: 'Ленинградская область', label: 'Ленинградская область' },
  { value: 'Липецкая область', label: 'Липецкая область' },
  { value: 'Магаданская область', label: 'Магаданская область' },
  { value: 'Мурманская область', label: 'Мурманская область' },
  { value: 'Нижегородская область', label: 'Нижегородская область' },
  { value: 'Новгородская область', label: 'Новгородская область' },
  { value: 'Новосибирская область', label: 'Новосибирская область' },
  { value: 'Омская область', label: 'Омская область' },
  { value: 'Оренбургская область', label: 'Оренбургская область' },
  { value: 'Орловская область', label: 'Орловская область' },
  { value: 'Пензенская область', label: 'Пензенская область' },
  { value: 'Псковская область', label: 'Псковская область' },
  { value: 'Ростовская область', label: 'Ростовская область' },
  { value: 'Рязанская область', label: 'Рязанская область' },
  { value: 'Самарская область', label: 'Самарская область' },
  { value: 'Саратовская область', label: 'Саратовская область' },
  { value: 'Сахалинская область', label: 'Сахалинская область' },
  { value: 'Свердловская область', label: 'Свердловская область' },
  { value: 'Смоленская область', label: 'Смоленская область' },
  { value: 'Тамбовская область', label: 'Тамбовская область' },
  { value: 'Тверская область', label: 'Тверская область' },
  { value: 'Томская область', label: 'Томская область' },
  { value: 'Тульская область', label: 'Тульская область' },
  { value: 'Тюменская область', label: 'Тюменская область' },
  { value: 'Ульяновская область', label: 'Ульяновская область' },
  { value: 'Челябинская область', label: 'Челябинская область' },
  { value: 'Ярославская область', label: 'Ярославская область' },
  { value: 'Еврейская автономная область', label: 'Еврейская автономная область' },
  { value: 'Ненецкий автономный округ', label: 'Ненецкий автономный округ' },
  { value: 'Ханты-Мансийский автономный округ - Югра', label: 'Ханты-Мансийский автономный округ - Югра' },
  { value: 'Чукотский автономный округ', label: 'Чукотский автономный округ' },
  { value: 'Ямало-Ненецкий автономный округ', label: 'Ямало-Ненецкий автономный округ' },
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
  deadline_hours: '',
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
