from __future__ import annotations

from pathlib import Path

from tender_killer.encoding_guard import find_mojibake


APP_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "App.jsx"
STYLES_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "styles.css"
API_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "api.js"
CONSTANTS_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "constants.js"
DASHBOARD_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "Dashboard.jsx"
DATABASE_VIEW_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "DatabaseView.jsx"
FILTERS_PANEL_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "FiltersPanel.jsx"
FORMATTERS_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "formatters.js"
PAGINATION_BAR_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "PaginationBar.jsx"
TENDER_DETAILS_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "TenderDetails.jsx"
TENDER_LIST_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "TenderList.jsx"


def _css_rule(source: str, selector: str) -> str:
    start = source.index(selector)
    end = source.index("}", start)
    return source[start:end]


def test_tender_cockpit_exposes_normalized_metadata_filters():
    source = APP_SOURCE.read_text(encoding="utf-8")
    constants_source = CONSTANTS_SOURCE.read_text(encoding="utf-8")
    filters_source = FILTERS_PANEL_SOURCE.read_text(encoding="utf-8")

    for key in ("source_family", "procedure_type", "customer_inn"):
        assert f"{key}: ''" in constants_source
        assert f"onUpdateFilter('{key}'" in filters_source

    assert "procedureTypeOptions" in filters_source
    assert "sourceFamilyOptions" in filters_source


def test_frontend_uses_dedicated_api_client():
    app_source = APP_SOURCE.read_text(encoding="utf-8")
    api_source = API_SOURCE.read_text(encoding="utf-8") if API_SOURCE.exists() else ""

    assert "from './api'" in app_source
    assert "function apiJson" in api_source
    assert "export function fetchTenderDetail" in api_source
    assert "export function saveProfileEconomics" in api_source
    assert "export function autoSelectProfileSupplierOption" in api_source
    assert "fetch(" not in app_source
    assert "fetch(" in api_source
    assert find_mojibake(app_source, APP_SOURCE) == []
    assert find_mojibake(api_source, API_SOURCE) == []


def test_frontend_uses_dedicated_formatters_module():
    app_source = APP_SOURCE.read_text(encoding="utf-8")
    tender_details_source = (
        TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
        if TENDER_DETAILS_SOURCE.exists()
        else ""
    )
    formatter_source = (
        FORMATTERS_SOURCE.read_text(encoding="utf-8")
        if FORMATTERS_SOURCE.exists()
        else ""
    )

    assert "from './formatters'" in tender_details_source
    assert "export function formatMoney" in formatter_source
    assert "export function formatDateTime" in formatter_source
    assert "export function documentRecordsForTender" in formatter_source
    assert "export function economicsStatusLabel" in formatter_source
    assert "function formatMoney" not in app_source
    assert "function documentStatusCounts" not in app_source
    assert find_mojibake(app_source, APP_SOURCE) == []
    assert find_mojibake(tender_details_source, TENDER_DETAILS_SOURCE) == []
    assert find_mojibake(formatter_source, FORMATTERS_SOURCE) == []


def test_frontend_uses_dedicated_constants_module():
    app_source = APP_SOURCE.read_text(encoding="utf-8")
    constants_source = (
        CONSTANTS_SOURCE.read_text(encoding="utf-8")
        if CONSTANTS_SOURCE.exists()
        else ""
    )

    assert "from './constants'" in app_source
    assert "export const sourceLabels" in constants_source
    assert "export const workflowLabels" in constants_source
    assert "export const viewLabels" in constants_source
    assert "export const navItems" in constants_source
    assert "export const initialFilters" in constants_source
    assert "export const initialTenderPage" in constants_source
    assert "const sourceLabels" not in app_source
    assert "const initialFilters" not in app_source
    assert find_mojibake(app_source, APP_SOURCE) == []
    assert find_mojibake(constants_source, CONSTANTS_SOURCE) == []


def test_frontend_uses_dedicated_dashboard_module():
    app_source = APP_SOURCE.read_text(encoding="utf-8")
    dashboard_source = (
        DASHBOARD_SOURCE.read_text(encoding="utf-8")
        if DASHBOARD_SOURCE.exists()
        else ""
    )

    assert "from './Dashboard'" in app_source
    assert "export function DashboardView" in dashboard_source
    assert "function DashboardAttentionPanel" in dashboard_source
    assert "function DashboardTenderPreview" in dashboard_source
    assert "function SourceStatusPanel" in dashboard_source
    assert "function DashboardView" not in app_source
    assert "function DashboardAttentionPanel" not in app_source
    assert find_mojibake(app_source, APP_SOURCE) == []
    assert find_mojibake(dashboard_source, DASHBOARD_SOURCE) == []


def test_frontend_uses_dedicated_database_view_module():
    app_source = APP_SOURCE.read_text(encoding="utf-8")
    database_view_source = (
        DATABASE_VIEW_SOURCE.read_text(encoding="utf-8")
        if DATABASE_VIEW_SOURCE.exists()
        else ""
    )

    assert "from './DatabaseView'" in app_source
    assert "export function DatabaseView" in database_view_source
    assert "fetchDatabaseTables" in database_view_source
    assert "fetchDatabaseTable" in database_view_source
    assert "formatDbCell" in database_view_source
    assert "function DatabaseView" not in app_source
    assert find_mojibake(app_source, APP_SOURCE) == []
    assert find_mojibake(database_view_source, DATABASE_VIEW_SOURCE) == []


def test_frontend_uses_dedicated_pagination_bar_module():
    app_source = APP_SOURCE.read_text(encoding="utf-8")
    tender_list_source = (
        TENDER_LIST_SOURCE.read_text(encoding="utf-8")
        if TENDER_LIST_SOURCE.exists()
        else ""
    )
    pagination_source = (
        PAGINATION_BAR_SOURCE.read_text(encoding="utf-8")
        if PAGINATION_BAR_SOURCE.exists()
        else ""
    )

    assert "from './PaginationBar'" in tender_list_source
    assert "export function PaginationBar" in pagination_source
    assert "page-size-control" in pagination_source
    assert "onPageLimitChange" in pagination_source
    assert "function PaginationBar" not in app_source
    assert find_mojibake(app_source, APP_SOURCE) == []
    assert find_mojibake(tender_list_source, TENDER_LIST_SOURCE) == []
    assert find_mojibake(pagination_source, PAGINATION_BAR_SOURCE) == []


def test_frontend_uses_dedicated_filters_panel_module():
    app_source = APP_SOURCE.read_text(encoding="utf-8")
    filters_source = (
        FILTERS_PANEL_SOURCE.read_text(encoding="utf-8")
        if FILTERS_PANEL_SOURCE.exists()
        else ""
    )

    assert "from './FiltersPanel'" in app_source
    assert "export function FiltersPanel" in filters_source
    assert "filters-panel" in filters_source
    assert "sourceOptions.map" in filters_source
    assert "procedureTypeOptions.map" in filters_source
    assert "onToggleMultiFilter('source'" in filters_source
    assert "function FiltersPanel" not in app_source
    assert find_mojibake(app_source, APP_SOURCE) == []
    assert find_mojibake(filters_source, FILTERS_PANEL_SOURCE) == []


def test_frontend_uses_dedicated_tender_list_module():
    app_source = APP_SOURCE.read_text(encoding="utf-8")
    tender_list_source = (
        TENDER_LIST_SOURCE.read_text(encoding="utf-8")
        if TENDER_LIST_SOURCE.exists()
        else ""
    )

    assert "from './TenderList'" in app_source
    assert "export function TenderList" in tender_list_source
    assert "function TenderListItem" in tender_list_source
    assert "tender-list" in tender_list_source
    assert "PaginationBar" in tender_list_source
    assert "onTenderSelect(tender)" in tender_list_source
    assert "function TenderList" not in app_source
    assert "className=\"tender-list\"" not in app_source
    assert find_mojibake(app_source, APP_SOURCE) == []
    assert find_mojibake(tender_list_source, TENDER_LIST_SOURCE) == []


def test_frontend_uses_dedicated_tender_details_module():
    app_source = APP_SOURCE.read_text(encoding="utf-8")
    tender_details_source = (
        TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
        if TENDER_DETAILS_SOURCE.exists()
        else ""
    )

    assert "from './TenderDetails'" in app_source
    assert "export function TenderDetails" in tender_details_source
    assert "function TenderOverviewTab" in tender_details_source
    assert "function EconomicsTabPanel" in tender_details_source
    assert "function WorkflowTabPanel" in tender_details_source
    assert "details-panel" in app_source
    assert "<TenderDetails tender={details}" in app_source
    assert "function TenderDetails" not in app_source
    assert "function TenderOverviewTab" not in app_source
    assert find_mojibake(app_source, APP_SOURCE) == []
    assert find_mojibake(tender_details_source, TENDER_DETAILS_SOURCE) == []


def test_tender_cockpit_exposes_page_size_selector():
    source = APP_SOURCE.read_text(encoding="utf-8")
    pagination_source = PAGINATION_BAR_SOURCE.read_text(encoding="utf-8")

    assert "tenderPageLimitOptions" in source
    assert "const [pageLimit, setPageLimit]" in source
    assert "params.set('limit', String(pageLimit))" in source
    assert "function changePageLimit" in source
    assert "setPageOffset(0)" in source
    assert "onPageLimitChange={changePageLimit}" in source
    assert "На странице" in pagination_source
    assert "Закупок на странице" in pagination_source
    assert find_mojibake(source, APP_SOURCE) == []


def test_tender_analysis_renders_actionable_checklist():
    source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")

    assert "<AnalysisChecklist items={analysis.checklist} />" in source
    assert "function AnalysisChecklist" in source
    assert "Проверочный список" in source
    assert "analysis-checklist" in source
    assert "analysisCategoryLabel" in source
    assert "analysisSeverityLabel" in source
    assert find_mojibake(source, TENDER_DETAILS_SOURCE) == []


def test_product_profile_renders_fulfillment_requirements():
    source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
    formatter_source = FORMATTERS_SOURCE.read_text(encoding="utf-8")

    assert "profile.fulfillment_requirements" in source
    assert "formatFulfillmentRequirements" in source
    assert "fulfillmentRequirementTypeLabel" in formatter_source
    assert "Поставка и исполнение" in source
    assert find_mojibake(source, TENDER_DETAILS_SOURCE) == []


def test_tender_details_render_economics_summary():
    source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")

    assert "{ id: 'economics', label: 'Экономика' }" in source
    assert "<EconomicsSummary economics={economics} tender={tender} />" in source
    assert "function EconomicsSummary" in source
    assert "economicsStatusLabel" in source
    assert "Маржа" in source
    assert find_mojibake(source, TENDER_DETAILS_SOURCE) == []


def test_product_profile_renders_economics_input_form():
    source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
    api_source = API_SOURCE.read_text(encoding="utf-8")

    assert "function ProductEconomicsForm" in source
    assert "onEconomicsSave" in source
    assert "product-profiles/${profile.position_index}" in api_source
    assert "${productProfilePath(tender, profile)}/economics" in api_source
    assert "unit_cost" in source
    assert "logistics_cost" in source
    assert "documents_cost" in source
    assert "other_costs" in source
    assert "Себестоимость" in source
    assert find_mojibake(source, TENDER_DETAILS_SOURCE) == []


def test_product_profile_renders_supplier_option_form():
    source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
    api_source = API_SOURCE.read_text(encoding="utf-8")
    formatter_source = FORMATTERS_SOURCE.read_text(encoding="utf-8")

    assert "function ProductSupplierOptionsForm" in source
    assert "onSupplierOptionSave" in source
    assert "selectSupplierOption" in source
    assert "autoSelectSupplierOption" in source
    assert "onSupplierOptionSelect" in source
    assert "onSupplierOptionAutoSelect" in source
    assert "product-profiles/${profile.position_index}" in api_source
    assert "${productProfilePath(tender, profile)}/supplier-options" in api_source
    assert "${productProfilePath(tender, profile)}/supplier-options/${optionIndex}/select" in api_source
    assert "supplier-options/best/select" in api_source
    assert "supplier_options" in source
    assert "economics_price_source" in source
    assert "EconomicsPriceSource" in source
    assert "unit_price" in source
    assert "availability" in source
    assert "Лучший в расчет" in source
    assert "Источник цены" in source
    assert "В расчет" in source
    assert "selected: 'в расчете'" in formatter_source
    assert "Поставщики" in source
    assert find_mojibake(source, TENDER_DETAILS_SOURCE) == []


def test_economics_tab_renders_auto_estimate_panel():
    source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
    api_source = API_SOURCE.read_text(encoding="utf-8")
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "runProfileAutoEconomics" in source
    assert "acceptProfileAutoEconomics" in source
    assert "ProductAutoEconomicsPanel" in source
    assert "economics/auto-estimate" in api_source
    assert "economics/auto-estimate/accept" in api_source
    assert "economics_auto" in source
    assert "Авторасчет" in source
    assert "Рассчитать" in source
    assert "Принять в расчет" in source
    assert "заполнит пустые допущения" in source
    assert "Уверенность" in source
    assert ".auto-economics-panel" in styles_source
    assert find_mojibake(source, TENDER_DETAILS_SOURCE) == []
    assert find_mojibake(styles_source, STYLES_SOURCE) == []


def test_economics_tab_renders_assumptions_form():
    source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
    api_source = API_SOURCE.read_text(encoding="utf-8")
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "saveProfileEconomicsAssumptions" in source
    assert "ProductEconomicsAssumptionsForm" in source
    assert "economics/assumptions" in api_source
    assert "economics_assumptions" in source
    assert "vat_mode" in source
    assert "risk_reserve_percent" in source
    assert "target_margin_percent" in source
    assert "Допущения" in source
    assert "НДС" in source
    assert "Целевая маржа" in source
    assert ".economics-assumptions-form" in styles_source
    assert find_mojibake(source, TENDER_DETAILS_SOURCE) == []
    assert find_mojibake(styles_source, STYLES_SOURCE) == []


def test_economics_tab_renders_bid_scenarios():
    source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "BidScenarioStrip" in source
    assert "economics.bid_scenarios" in source
    assert "Сценарии цены" in source
    assert "bid-scenario-grid" in source
    assert ".bid-scenario-grid" in styles_source
    assert find_mojibake(source, TENDER_DETAILS_SOURCE) == []
    assert find_mojibake(styles_source, STYLES_SOURCE) == []


def test_economics_tab_renders_participation_decision():
    source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "ParticipationDecisionCard" in source
    assert "economics.participation_decision" in source
    assert "Решение по участию" in source
    assert "Лимит" in source
    assert "participation-decision" in source
    assert ".participation-decision" in styles_source
    assert find_mojibake(source, TENDER_DETAILS_SOURCE) == []
    assert find_mojibake(styles_source, STYLES_SOURCE) == []


def test_economics_tab_owns_product_costs_and_suppliers():
    app_source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "function EconomicsTabPanel({" in app_source
    assert "productProfiles" in app_source
    assert "selectedEconomicsProfileIndex" in app_source
    assert "<ProductEconomicsForm profile={selectedEconomicsProfile}" in app_source
    assert "<ProductSupplierOptionsForm" in app_source
    assert "profile={selectedEconomicsProfile}" in app_source
    assert "economics-workbench" in app_source
    assert ".economics-workbench" in styles_source
    assert find_mojibake(app_source, TENDER_DETAILS_SOURCE) == []
    assert find_mojibake(styles_source, STYLES_SOURCE) == []


def test_product_detail_keeps_passport_and_requirements_only():
    app_source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
    constants_source = CONSTANTS_SOURCE.read_text(encoding="utf-8")

    assert "export const productDetailModes = [" in constants_source
    assert "{ id: 'pricing'" not in app_source
    assert "{ id: 'suppliers'" not in app_source
    assert "activeProfileMode === 'pricing'" not in app_source
    assert "activeProfileMode === 'suppliers'" not in app_source
    assert find_mojibake(app_source, TENDER_DETAILS_SOURCE) == []


def test_tender_workbench_v1_reduces_detail_panel_overload():
    app_source = APP_SOURCE.read_text(encoding="utf-8")
    tender_details_source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
    constants_source = CONSTANTS_SOURCE.read_text(encoding="utf-8")

    assert "workspace workbench-layout" in app_source
    assert "function TenderDecisionSummary" in tender_details_source
    assert "<TenderDecisionSummary tender={tender} economics={economics} />" in tender_details_source
    assert "decision-summary-grid" in tender_details_source
    assert "product-detail-tabs" in tender_details_source
    assert "export const productDetailModes" in constants_source
    assert "Паспорт" in tender_details_source
    assert "ТЗ" in tender_details_source
    assert "economics-workbench" in tender_details_source
    assert find_mojibake(app_source, APP_SOURCE) == []
    assert find_mojibake(tender_details_source, TENDER_DETAILS_SOURCE) == []


def test_tender_workbench_has_collapsible_filters_and_wider_list():
    app_source = APP_SOURCE.read_text(encoding="utf-8")
    filters_source = FILTERS_PANEL_SOURCE.read_text(encoding="utf-8")
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "const [filtersCollapsed, setFiltersCollapsed]" in app_source
    assert "filtersCollapsed ? 'workspace workbench-layout filters-collapsed' : 'workspace workbench-layout'" in app_source
    assert "filter-collapse-button" in filters_source
    assert "Свернуть фильтры" in filters_source
    assert "Развернуть фильтры" in filters_source
    assert ".workbench-layout.filters-collapsed" in styles_source
    assert "minmax(560px, 1.1fr)" in styles_source
    assert ".filters-panel.collapsed" in styles_source
    assert find_mojibake(app_source, APP_SOURCE) == []
    assert find_mojibake(styles_source, STYLES_SOURCE) == []


def test_tender_details_v2_keeps_actions_and_document_statuses_scannable():
    app_source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")
    detail_actions_rule = _css_rule(styles_source, ".detail-actions")
    detail_tabs_rule = _css_rule(styles_source, ".detail-tabs")

    assert "details-title-row" in app_source
    assert "details-action-group primary-actions" in app_source
    assert "details-action-group secondary-actions" in app_source
    assert "documentStatusLabel" in app_source
    assert "document-status ${document.text_status || 'pending'}" in app_source
    assert "download-status ${document.local_path ? 'downloaded' : 'missing'}" in app_source
    assert "grid-template-columns: repeat(4" not in detail_actions_rule
    assert ("flex-wrap: wrap" in detail_actions_rule or "auto-fit" in detail_actions_rule)
    assert "flex-wrap: wrap" in detail_tabs_rule
    assert "overflow-x: auto" not in detail_tabs_rule
    assert ".document-status.unsupported" in styles_source
    assert ".document-status.ok" in styles_source
    assert find_mojibake(app_source, TENDER_DETAILS_SOURCE) == []
    assert find_mojibake(styles_source, STYLES_SOURCE) == []


def test_tender_detail_tabs_have_scannable_work_areas():
    app_source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
    formatter_source = FORMATTERS_SOURCE.read_text(encoding="utf-8")
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "function TenderOverviewTab" in app_source
    assert "function ProductTabSummary" in app_source
    assert "function DocumentStatusSummary" in app_source
    assert "export function documentStatusCounts" in formatter_source
    assert "<TenderOverviewTab tender={tender} raw={raw} />" in app_source
    assert "<ProductTabSummary" in app_source
    assert "<DocumentStatusSummary" in app_source
    assert "tab-lead" in app_source
    assert "overview-brief-grid" in app_source
    assert "document-status-summary" in app_source
    assert "product-tab-summary" in app_source
    assert ".tab-lead" in styles_source
    assert ".overview-brief-grid" in styles_source
    assert ".document-status-summary" in styles_source
    assert ".product-tab-summary" in styles_source
    assert find_mojibake(app_source, TENDER_DETAILS_SOURCE) == []
    assert find_mojibake(styles_source, STYLES_SOURCE) == []


def test_decision_tabs_are_extracted_to_consistent_work_panels():
    app_source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "function AnalysisTabPanel" in app_source
    assert "function EconomicsTabPanel" in app_source
    assert "function WorkflowTabPanel" in app_source
    assert "<AnalysisTabPanel" in app_source
    assert "<EconomicsTabPanel" in app_source
    assert "productProfiles={productProfiles}" in app_source
    assert "<WorkflowTabPanel" in app_source
    assert "analysis-tab-summary" in app_source
    assert "economics-tab-summary" in app_source
    assert "workflow-status-summary" in app_source
    assert "workflow-note-panel" in app_source
    assert ".analysis-tab-summary," in styles_source
    assert ".economics-tab-summary," in styles_source
    assert ".workflow-status-summary" in styles_source
    assert ".workflow-note-panel" in styles_source
    assert find_mojibake(app_source, TENDER_DETAILS_SOURCE) == []
    assert find_mojibake(styles_source, STYLES_SOURCE) == []


def test_economics_tab_uses_tender_price_before_manual_calculation():
    app_source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")

    assert "function EconomicsTabPanel({" in app_source
    assert "const displayedRevenue = economics?.revenue ?? tender?.price" in app_source
    assert "<SummaryMetric value={formatMoney(displayedRevenue)} label=\"НМЦК\" />" in app_source
    assert "НМЦК подтянута из карточки закупки" in app_source
    assert find_mojibake(app_source, TENDER_DETAILS_SOURCE) == []


def test_economics_tab_renders_bid_thresholds():
    app_source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")

    assert "economics?.break_even_price" in app_source
    assert "economics.break_even_price" in app_source
    assert "economics.minimum_margin_price" in app_source
    assert "economics.interesting_price" in app_source
    assert "Безубыток" in app_source
    assert "Минимальная ставка" in app_source
    assert "Интересная ставка" in app_source
    assert find_mojibake(app_source, TENDER_DETAILS_SOURCE) == []


def test_tender_detail_renders_price_change_banner():
    app_source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "<PriceChangeBanner change={tender.price_change} />" in app_source
    assert "function PriceChangeBanner({ change })" in app_source
    assert "formatPriceChangeDirection" in app_source
    assert "price-change-banner" in app_source
    assert ".price-change-banner" in styles_source
    assert find_mojibake(app_source, TENDER_DETAILS_SOURCE) == []
    assert find_mojibake(styles_source, STYLES_SOURCE) == []


def test_tender_detail_visual_density_has_stable_grids_and_no_negative_offsets():
    app_source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")
    tab_lead_rule = _css_rule(styles_source, ".tab-lead")
    document_row_rule = _css_rule(styles_source, ".document-row")
    compact_button_rule = _css_rule(styles_source, ".secondary-button.compact")

    assert "tab-summary-grid" in app_source
    assert "summary-label" in app_source
    assert ".tab-summary-grid" in styles_source
    assert ".summary-label" in styles_source
    assert "grid-template-columns: minmax(0, 1fr) auto" not in tab_lead_rule
    assert "grid-template-columns: minmax(0, 1fr) minmax(132px, auto)" in document_row_rule
    assert "margin-top: -" not in compact_button_rule
    assert "grid-template-columns: 42px minmax(150px, 1fr) minmax(76px, 0.45fr) 92px" not in styles_source
    assert find_mojibake(app_source, TENDER_DETAILS_SOURCE) == []
    assert find_mojibake(styles_source, STYLES_SOURCE) == []


def test_tender_workflow_tabs_wrap_without_horizontal_scrollbar():
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")
    workflow_tabs_rule = _css_rule(styles_source, ".workflow-tabs")

    assert "flex-wrap: wrap" in workflow_tabs_rule
    assert "overflow-x: auto" not in workflow_tabs_rule
    assert find_mojibake(styles_source, STYLES_SOURCE) == []


def test_global_shell_exposes_dashboard_and_side_navigation():
    app_source = APP_SOURCE.read_text(encoding="utf-8")
    constants_source = CONSTANTS_SOURCE.read_text(encoding="utf-8")
    dashboard_source = DASHBOARD_SOURCE.read_text(encoding="utf-8")
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "export const viewLabels = {" in constants_source
    assert "dashboard: 'Дашборд'" in constants_source
    assert "tenders: 'Закупки'" in constants_source
    assert "export const navItems = [" in constants_source
    assert "app-frame" in app_source
    assert "app-sidebar" in app_source
    assert "className=\"side-nav\"" in app_source
    assert "setView(item.id)" in app_source
    assert "export function DashboardView" in dashboard_source
    assert "<DashboardView" in app_source
    assert "view === 'dashboard'" in app_source
    assert ".app-frame" in styles_source
    assert ".app-sidebar" in styles_source
    assert ".side-nav" in styles_source
    assert ".dashboard-grid" in styles_source
    assert find_mojibake(app_source, APP_SOURCE) == []
    assert find_mojibake(styles_source, STYLES_SOURCE) == []


def test_sidebar_can_collapse_without_losing_navigation():
    app_source = APP_SOURCE.read_text(encoding="utf-8")
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "const [sidebarCollapsed, setSidebarCollapsed]" in app_source
    assert "sidebarCollapsed ? 'app-frame sidebar-collapsed' : 'app-frame'" in app_source
    assert "sidebarCollapsed ? 'app-sidebar collapsed' : 'app-sidebar'" in app_source
    assert "sidebar-toggle-button" in app_source
    assert "sidebarCollapsed ? 'Развернуть меню' : 'Свернуть меню'" in app_source
    assert "title={item.label}" in app_source
    assert ".app-frame.sidebar-collapsed" in styles_source
    assert ".app-sidebar.collapsed" in styles_source
    assert ".sidebar-text" in styles_source
    assert ".sidebar-caption" in styles_source
    assert find_mojibake(app_source, APP_SOURCE) == []
    assert find_mojibake(styles_source, STYLES_SOURCE) == []


def test_dashboard_surfaces_attention_and_recent_tenders():
    app_source = APP_SOURCE.read_text(encoding="utf-8")
    dashboard_source = DASHBOARD_SOURCE.read_text(encoding="utf-8")
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "function DashboardAttentionPanel" in dashboard_source
    assert "function DashboardTenderPreview" in dashboard_source
    assert "<DashboardAttentionPanel" in dashboard_source
    assert "<DashboardTenderPreview" in dashboard_source
    assert "Требует внимания" in dashboard_source
    assert "Последние закупки" in dashboard_source
    assert "dashboard-attention-list" in dashboard_source
    assert "dashboard-tender-list" in dashboard_source
    assert ".dashboard-secondary-grid" in styles_source
    assert ".dashboard-attention-list" in styles_source
    assert ".dashboard-tender-list" in styles_source
    assert find_mojibake(app_source, APP_SOURCE) == []
    assert find_mojibake(styles_source, STYLES_SOURCE) == []


def test_dashboard_layout_uses_aligned_full_width_grid():
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")
    shell_width_rule = _css_rule(styles_source, ".topbar,")
    dashboard_view_rule = _css_rule(styles_source, ".dashboard-view {")
    metrics_rule = _css_rule(styles_source, ".dashboard-view .metrics")
    dashboard_grid_rule = _css_rule(styles_source, ".dashboard-grid")
    dashboard_secondary_rule = _css_rule(styles_source, ".dashboard-secondary-grid")
    dashboard_children_rule = _css_rule(styles_source, ".dashboard-grid > *,")

    assert "width: 100%" in shell_width_rule
    assert "align-items: stretch" in dashboard_view_rule
    assert "margin-bottom: 0" in metrics_rule
    assert "minmax(360px, 0.9fr) minmax(0, 1.1fr)" in dashboard_grid_rule
    assert "minmax(360px, 0.9fr) minmax(0, 1.1fr)" in dashboard_secondary_rule
    assert "height: 100%" in dashboard_children_rule
    assert find_mojibake(styles_source, STYLES_SOURCE) == []


def test_tender_notify_uses_backend_message_for_configuration_errors():
    app_source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")

    assert "payload.message || (payload.sent ? 'Отправлено в Telegram' : 'Telegram не настроен')" in app_source
    assert find_mojibake(app_source, TENDER_DETAILS_SOURCE) == []
