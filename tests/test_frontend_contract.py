from __future__ import annotations

from pathlib import Path

from tender_killer.encoding_guard import find_mojibake


GITIGNORE_SOURCE = Path(__file__).resolve().parents[1] / ".gitignore"
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
TENDER_DETAILS_SHARED_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "TenderDetailsShared.jsx"
TENDER_DETAIL_ACTIONS_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "TenderDetailActions.jsx"
TENDER_MARKET_STATE_IMPORT_SOURCE = (
    Path(__file__).resolve().parents[1] / "web" / "src" / "TenderMarketStateImport.jsx"
)
TENDER_DETAILS_HEADER_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "TenderDetailsHeader.jsx"
TENDER_DETAILS_STATUS_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "TenderDetailsStatusStack.jsx"
TENDER_DETAILS_TABS_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "TenderDetailsTabs.jsx"
TENDER_DETAILS_NAVIGATION_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "TenderDetailsNavigation.jsx"
TENDER_TAB_PANELS_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "TenderTabPanels.jsx"
TENDER_FULLSCREEN_WORKSPACE_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "TenderFullscreenWorkspace.jsx"
TENDER_WORKSPACES_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "TenderWorkspaces.jsx"
TENDER_ANALYSIS_TAB_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "TenderAnalysisTab.jsx"
TENDER_ANALYSIS_SUMMARY_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "TenderAnalysisSummary.jsx"
TENDER_ANALYSIS_SECTIONS_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "TenderAnalysisSections.jsx"
TENDER_ANALYSIS_EVIDENCE_SOURCE = (
    Path(__file__).resolve().parents[1] / "web" / "src" / "TenderAnalysisEvidencePanel.jsx"
)
TENDER_ANALYSIS_EVIDENCE_MODEL_SOURCE = (
    Path(__file__).resolve().parents[1] / "web" / "src" / "TenderAnalysisEvidenceModel.js"
)
TENDER_ANALYSIS_DECISION_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "TenderAnalysisDecisionBrief.jsx"
TENDER_ANALYSIS_DOCUMENTS_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "TenderAnalysisDocumentsPanel.jsx"
TENDER_ANALYSIS_PASSPORT_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "TenderAnalysisPassport.jsx"
TENDER_DECISION_STRIP_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "TenderDecisionStrip.jsx"
TENDER_DECISION_SUMMARY_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "TenderDecisionSummary.jsx"
TENDER_ECONOMICS_TAB_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "TenderEconomicsTab.jsx"
TENDER_ECONOMICS_DECISION_SCENARIOS_SOURCE = (
    Path(__file__).resolve().parents[1] / "web" / "src" / "TenderEconomicsDecisionScenarios.jsx"
)
TENDER_ECONOMICS_PRICE_BOOK_FEED_SOURCE = (
    Path(__file__).resolve().parents[1] / "web" / "src" / "TenderEconomicsPriceBookFeed.jsx"
)
TENDER_ECONOMICS_FORMS_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "TenderEconomicsForms.jsx"
TENDER_ECONOMICS_COST_FORM_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "TenderEconomicsCostForm.jsx"
TENDER_ECONOMICS_SUMMARY_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "TenderEconomicsSummary.jsx"
TENDER_ECONOMICS_SUPPLIERS_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "TenderEconomicsSuppliers.jsx"
TENDER_ECONOMICS_SUPPLIER_DISCOVERY_SOURCE = (
    Path(__file__).resolve().parents[1] / "web" / "src" / "TenderEconomicsSupplierDiscovery.jsx"
)
TENDER_ECONOMICS_SUPPLIER_OPTIONS_SOURCE = (
    Path(__file__).resolve().parents[1] / "web" / "src" / "TenderEconomicsSupplierOptions.jsx"
)
TENDER_ECONOMICS_AUTO_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "TenderEconomicsAuto.jsx"
TENDER_ECONOMICS_POSITION_RAIL_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "TenderEconomicsPositionRail.jsx"
TENDER_ECONOMICS_WORKBENCH_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "TenderEconomicsWorkbench.jsx"
TENDER_ECONOMICS_PROFILE_WORKSPACE_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "TenderEconomicsProfileWorkspace.jsx"
TENDER_ECONOMICS_METRICS_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "TenderEconomicsMetrics.jsx"
TENDER_OVERVIEW_TAB_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "TenderOverviewTab.jsx"
TENDER_PRODUCTS_TAB_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "TenderProductsTab.jsx"
TENDER_SUMMARY_TAB_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "TenderSummaryTab.jsx"
TENDER_WORKFLOW_TAB_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "TenderWorkflowTab.jsx"
TENDER_LIST_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "TenderList.jsx"
USE_TENDER_DOCUMENT_ANALYSIS_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "useTenderDocumentAnalysis.js"
USE_TENDER_PRODUCT_PROFILES_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "useTenderProductProfiles.js"
USE_TENDER_WORKFLOW_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "useTenderWorkflow.js"
USE_TENDER_NOTIFICATION_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "useTenderNotification.js"
USE_TENDER_REFRESH_DETAILS_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "useTenderRefreshDetails.js"
USE_TENDER_DETAILS_UI_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "useTenderDetailsUi.js"
USE_TENDER_MARKET_STATE_IMPORT_SOURCE = (
    Path(__file__).resolve().parents[1] / "web" / "src" / "useTenderMarketStateImport.js"
)


def _css_rule(source: str, selector: str) -> str:
    start = source.index(selector)
    end = source.index("}", start)
    return source[start:end]


def test_tender_cockpit_exposes_normalized_metadata_filters():
    source = APP_SOURCE.read_text(encoding="utf-8")
    constants_source = CONSTANTS_SOURCE.read_text(encoding="utf-8")
    filters_source = FILTERS_PANEL_SOURCE.read_text(encoding="utf-8")

    for key in ("source_family", "procedure_type", "customer_inn", "deadline_hours"):
        assert f"{key}: ''" in constants_source

    assert "export const regionOptions" in constants_source
    assert "export const deadlineOptions" in constants_source
    assert "value: '12'" in constants_source
    assert "value: 'Краснодарский край'" in constants_source
    assert "value: 'Республика Татарстан'" in constants_source
    assert "deadlineOptions.map" in filters_source
    assert "onUpdateFilter('deadline_hours'" in filters_source
    assert "regionOptions.map" in filters_source
    assert "name=\"region\"" in filters_source
    assert "onUpdateFilter('region'" in filters_source
    assert "onUpdateFilter('customer_inn'" in filters_source
    assert "onUpdateFilter('source_family'" not in filters_source
    assert "onUpdateFilter('procedure_type'" not in filters_source
    assert "procedureTypeOptions" not in filters_source
    assert "sourceFamilyOptions" not in filters_source
    assert "quickRegionOptions" not in filters_source


def test_frontend_uses_dedicated_api_client():
    app_source = APP_SOURCE.read_text(encoding="utf-8")
    api_source = API_SOURCE.read_text(encoding="utf-8") if API_SOURCE.exists() else ""

    assert "from './api'" in app_source
    assert "function apiJson" in api_source
    assert "payload.error" in api_source
    assert "error.payload = payload" in api_source
    assert "error.status = response.status" in api_source
    assert "response.json().catch" in api_source
    assert "export function fetchTenderDetail" in api_source
    assert "export function fetchDashboardQueues" in api_source
    assert "/api/dashboard/queues" in api_source
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
    header_source = (
        TENDER_DETAILS_HEADER_SOURCE.read_text(encoding="utf-8")
        if TENDER_DETAILS_HEADER_SOURCE.exists()
        else ""
    )
    formatter_source = (
        FORMATTERS_SOURCE.read_text(encoding="utf-8")
        if FORMATTERS_SOURCE.exists()
        else ""
    )

    assert "from './formatters'" in header_source
    assert "export function formatMoney" in formatter_source
    assert "export function formatDateTime" in formatter_source
    assert "export function documentRecordsForTender" in formatter_source
    assert "export function economicsStatusLabel" in formatter_source
    assert "function formatMoney" not in app_source
    assert "function documentStatusCounts" not in app_source
    assert find_mojibake(app_source, APP_SOURCE) == []
    assert find_mojibake(tender_details_source, TENDER_DETAILS_SOURCE) == []
    assert find_mojibake(header_source, TENDER_DETAILS_HEADER_SOURCE) == []
    assert find_mojibake(formatter_source, FORMATTERS_SOURCE) == []


def test_economics_workspace_exposes_compact_operator_flow():
    tab_source = TENDER_ECONOMICS_TAB_SOURCE.read_text(encoding="utf-8")
    suppliers_source = TENDER_ECONOMICS_SUPPLIERS_SOURCE.read_text(encoding="utf-8")
    profile_workspace_source = TENDER_ECONOMICS_PROFILE_WORKSPACE_SOURCE.read_text(encoding="utf-8")
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "EconomicsProgressStepper" in tab_source
    assert "economics-stepper" in tab_source
    assert "nextEconomicsAction" in tab_source
    assert "primaryEconomicsAction" in tab_source
    assert "PriceCandidateQueue" in suppliers_source
    assert "best-price-candidate" in suppliers_source
    assert "candidate-queue-tabs" in suppliers_source
    assert "candidateQueueBuckets" in suppliers_source
    assert "candidateNeedsManualPrice" in suppliers_source
    assert "product_family_mismatch" in suppliers_source
    assert "manual_price_required" in profile_workspace_source
    assert "Локальный browser-fetch не запустился" in profile_workspace_source
    assert "spawn eperm" in profile_workspace_source.lower()
    assert ".economics-stepper" in styles_source
    assert ".best-price-candidate" in styles_source
    assert ".candidate-queue-tabs" in styles_source
    assert find_mojibake(tab_source, TENDER_ECONOMICS_TAB_SOURCE) == []
    assert find_mojibake(suppliers_source, TENDER_ECONOMICS_SUPPLIERS_SOURCE) == []
    assert find_mojibake(profile_workspace_source, TENDER_ECONOMICS_PROFILE_WORKSPACE_SOURCE) == []
    assert find_mojibake(styles_source, STYLES_SOURCE) == []


def test_economics_command_center_keeps_secondary_actions_collapsed():
    tab_source = TENDER_ECONOMICS_TAB_SOURCE.read_text(encoding="utf-8")
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "economics-secondary-menu" in tab_source
    assert "economics-secondary-summary" in tab_source
    assert "secondaryEconomicsActions.map" in tab_source
    assert "primaryEconomicsAction &&" in tab_source
    assert ".economics-secondary-menu" in styles_source
    assert ".economics-secondary-summary" in styles_source
    assert "Готовые цены в расчет" not in tab_source
    assert "Лучшие цены в расчет" not in tab_source
    assert find_mojibake(tab_source, TENDER_ECONOMICS_TAB_SOURCE) == []
    assert find_mojibake(styles_source, STYLES_SOURCE) == []


def test_economics_workspace_surfaces_provider_run_and_candidate_explanations():
    suppliers_source = TENDER_ECONOMICS_SUPPLIERS_SOURCE.read_text(encoding="utf-8")
    discovery_source = TENDER_ECONOMICS_SUPPLIER_DISCOVERY_SOURCE.read_text(encoding="utf-8")
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "ProviderRunSummary" in discovery_source
    assert "provider-run-summary" in discovery_source
    assert "supplierDiscoveryRunBuckets" in discovery_source
    assert "supplier-discovery-next-action" in discovery_source
    assert "CandidateDecisionTrace" in suppliers_source
    assert "CandidatePricePassport" in suppliers_source
    assert "candidate-decision-trace" in suppliers_source
    assert "price-candidate-passport" in suppliers_source
    assert "CandidatePricePassportFacts" in suppliers_source
    assert "candidatePassportFacts(passport)" in suppliers_source
    assert "price-candidate-passport-facts" in suppliers_source
    assert "source_label" in suppliers_source
    assert "freshness_label" in suppliers_source
    assert "match_confidence" in suppliers_source
    assert "unit_pack_label" in suppliers_source
    assert "vat_label" in suppliers_source
    assert "delivery_label" in suppliers_source
    assert "evidence_url" in suppliers_source
    assert "candidateBestReasonItems" in suppliers_source
    assert "candidatePricingPassport" in suppliers_source
    assert "candidate.pricing_passport" in suppliers_source
    assert "score_reasons" in suppliers_source
    assert ".provider-run-summary" in styles_source
    assert ".candidate-decision-trace" in styles_source
    assert ".price-candidate-passport" in styles_source
    assert ".price-candidate-passport-facts" in styles_source
    assert ".supplier-discovery-next-action" in styles_source
    assert find_mojibake(suppliers_source, TENDER_ECONOMICS_SUPPLIERS_SOURCE) == []
    assert find_mojibake(discovery_source, TENDER_ECONOMICS_SUPPLIER_DISCOVERY_SOURCE) == []
    assert find_mojibake(styles_source, STYLES_SOURCE) == []


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


def test_dashboard_api_errors_retry_after_backend_recovers():
    app_source = APP_SOURCE.read_text(encoding="utf-8")

    assert "const DASHBOARD_RETRY_MS = 5000" in app_source
    assert "if (view !== 'dashboard') return undefined" in app_source
    assert "if (!error && !dashboardQueueError) return undefined" in app_source
    assert "const retry = window.setInterval(() => {" in app_source
    assert "loadTenders(appliedFilters, pageOffset)" in app_source
    assert "loadDashboardQueues(appliedFilters)" in app_source
    assert "return () => window.clearInterval(retry)" in app_source
    assert "}, [view, error, dashboardQueueError, appliedFilters, pageOffset, pageLimit])" in app_source


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
    assert "top-filters-panel" in filters_source
    assert "top-filter-form" in filters_source
    assert "is-collapsed" in filters_source
    assert "aria-expanded={!collapsed}" in filters_source
    assert "onToggleCollapsed" in filters_source
    assert "sourceOptions.map" in filters_source
    assert "deadlineOptions.map" in filters_source
    assert "regionOptions.map" in filters_source
    assert "procedureTypeOptions.map" not in filters_source
    assert "sourceSelectValue(filters.source)" in filters_source
    assert "filters.deadline_hours" in filters_source
    assert "onUpdateFilter('source'" in filters_source
    assert "onUpdateFilter('deadline_hours'" in filters_source
    assert "function FiltersPanel" not in app_source
    assert find_mojibake(app_source, APP_SOURCE) == []
    assert find_mojibake(filters_source, FILTERS_PANEL_SOURCE) == []


def test_tender_workbench_is_list_first_with_fullscreen_detail_view():
    app_source = APP_SOURCE.read_text(encoding="utf-8")
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")
    back_button_rule = _css_rule(styles_source, ".detail-screen-toolbar .detail-back-button")
    heading_title_rule = _css_rule(styles_source, ".detail-screen-heading strong")

    assert "tender-list-screen" in app_source
    assert "tender-detail-screen" in app_source
    assert "detail-screen-toolbar" in app_source
    assert "detail-back-button" in app_source
    assert "openTenderDetails" in app_source
    assert "closeTenderDetails" in app_source
    assert "collapsed={filtersCollapsed}" in app_source
    assert "variant=\"top\"" in app_source
    assert "className=\"details-panel\"" not in app_source
    assert "<TenderDetails tender={details}" in app_source
    assert ".tender-list-screen" in styles_source
    assert ".tender-detail-screen" in styles_source
    assert ".tender-detail-card" in styles_source
    assert ".detail-screen-toolbar" in styles_source
    assert ".detail-screen-toolbar .detail-back-button" in styles_source
    assert "width: auto" in back_button_rule
    assert "flex: 0 0 auto" in back_button_rule
    assert "font-size: 22px" in heading_title_rule
    assert "white-space: normal" in heading_title_rule
    assert find_mojibake(app_source, APP_SOURCE) == []
    assert find_mojibake(styles_source, STYLES_SOURCE) == []


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
    assert "TenderListDecisionCues" in tender_list_source
    assert "row-insights" in tender_list_source
    assert "decisionPrimaryInsight" in tender_list_source
    assert "decisionSecondaryInsight" in tender_list_source
    assert "tender.decision?.next_step" in tender_list_source
    assert "tender.decision?.blockers?.[0] || tender.decision?.reasons?.[0]" in tender_list_source
    assert "economicsStatusLabel" not in tender_list_source
    assert "analysisStatusLabel" not in tender_list_source
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
    assert "from './TenderDetailActions'" in tender_details_source
    assert "from './TenderDetailsHeader'" in tender_details_source
    assert "from './TenderDetailsStatusStack'" in tender_details_source
    assert "from './TenderDetailsTabs'" in tender_details_source
    assert "from './TenderDecisionStrip'" in tender_details_source
    assert "from './TenderDecisionSummary'" in tender_details_source
    assert "from './useTenderDocumentAnalysis'" in tender_details_source
    assert "from './useTenderProductProfiles'" in tender_details_source
    assert "from './useTenderWorkflow'" in tender_details_source
    assert "from './useTenderNotification'" in tender_details_source
    assert "from './useTenderRefreshDetails'" in tender_details_source
    assert "from './useTenderDetailsUi'" in tender_details_source
    assert "tender-detail-card" in app_source
    assert "<TenderDetails tender={details}" in app_source
    assert "function TenderDetails" not in app_source
    assert find_mojibake(app_source, APP_SOURCE) == []
    assert find_mojibake(tender_details_source, TENDER_DETAILS_SOURCE) == []


def test_frontend_uses_dedicated_tender_summary_tab_module():
    tender_details_source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
    panels_source = TENDER_TAB_PANELS_SOURCE.read_text(encoding="utf-8")
    summary_source = (
        TENDER_SUMMARY_TAB_SOURCE.read_text(encoding="utf-8")
        if TENDER_SUMMARY_TAB_SOURCE.exists()
        else ""
    )

    assert "from './TenderSummaryTab'" in panels_source
    assert "export function TenderSummaryTab" in summary_source
    assert "summary-decision-grid" not in summary_source
    assert "SummaryMetric" not in summary_source
    assert "summary-next-action" in summary_source
    assert "<TenderSummaryTab" in panels_source
    assert "function TenderSummaryTab" not in tender_details_source
    assert find_mojibake(tender_details_source, TENDER_DETAILS_SOURCE) == []
    assert find_mojibake(panels_source, TENDER_TAB_PANELS_SOURCE) == []
    assert find_mojibake(summary_source, TENDER_SUMMARY_TAB_SOURCE) == []


def test_frontend_embeds_document_preparation_in_analysis_workspace():
    tender_details_source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
    panels_source = TENDER_TAB_PANELS_SOURCE.read_text(encoding="utf-8")
    workspaces_source = TENDER_WORKSPACES_SOURCE.read_text(encoding="utf-8")
    analysis_source = TENDER_ANALYSIS_TAB_SOURCE.read_text(encoding="utf-8")
    analysis_documents_source = (
        TENDER_ANALYSIS_DOCUMENTS_SOURCE.read_text(encoding="utf-8")
        if TENDER_ANALYSIS_DOCUMENTS_SOURCE.exists()
        else ""
    )

    assert "from './TenderDocumentsTab'" not in workspaces_source
    assert "mode === 'documents'" not in workspaces_source
    assert "from './TenderAnalysisDocumentsPanel'" in analysis_source
    assert "export function AnalysisDocumentsPanel" in analysis_documents_source
    assert "function DocumentStatusSummary" in analysis_documents_source
    assert "<section className=\"analysis-documents-panel\"" not in analysis_documents_source
    assert "<h4>Документы для анализа</h4>" not in analysis_documents_source
    assert "document-table" in analysis_documents_source
    assert "<details className=\"document-table-toggle analysis-documents-toggle\">" in analysis_documents_source
    assert "Показать документы" in analysis_documents_source
    assert "<DocumentStatusSummary" in analysis_documents_source
    assert analysis_documents_source.index("<details className=\"document-table-toggle analysis-documents-toggle\">") < analysis_documents_source.index("<DocumentStatusSummary")
    assert "document-status ${document.text_status || 'pending'}" in analysis_documents_source
    assert "<AnalysisDocumentsPanel" in analysis_source
    assert "onDownload={onDownload}" in analysis_source
    assert "onExtract={onExtract}" in analysis_source
    assert "from './TenderDocumentsTab'" not in panels_source
    assert "function DocumentStatusSummary" not in tender_details_source
    assert "document-table" not in tender_details_source
    assert find_mojibake(tender_details_source, TENDER_DETAILS_SOURCE) == []
    assert find_mojibake(panels_source, TENDER_TAB_PANELS_SOURCE) == []
    assert find_mojibake(workspaces_source, TENDER_WORKSPACES_SOURCE) == []
    assert find_mojibake(analysis_source, TENDER_ANALYSIS_TAB_SOURCE) == []
    assert find_mojibake(analysis_documents_source, TENDER_ANALYSIS_DOCUMENTS_SOURCE) == []


def test_analysis_tab_renders_collapsed_analysis_history():
    analysis_source = TENDER_ANALYSIS_TAB_SOURCE.read_text(encoding="utf-8")
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "analysis?.analysis_history" in analysis_source
    assert "analysis-history" in analysis_source
    assert "История анализа" in analysis_source
    assert "entry.changes" in analysis_source
    assert ".analysis-history" in styles_source
    assert ".analysis-history-row" in styles_source
    assert find_mojibake(analysis_source, TENDER_ANALYSIS_TAB_SOURCE) == []


def test_analysis_workspace_exposes_single_prepare_flow():
    tender_details_source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
    workspaces_source = TENDER_WORKSPACES_SOURCE.read_text(encoding="utf-8")
    analysis_source = TENDER_ANALYSIS_TAB_SOURCE.read_text(encoding="utf-8")
    hook_source = USE_TENDER_DOCUMENT_ANALYSIS_SOURCE.read_text(encoding="utf-8")

    assert "const [preparingAnalysis, setPreparingAnalysis]" in hook_source
    assert "async function prepareTenderAnalysis()" in hook_source
    assert "await downloadDocuments()" in hook_source
    assert "await extractDocumentText()" in hook_source
    assert "await analyzeTender()" in hook_source
    assert "setPreparingAnalysis(false)" in hook_source
    assert "preparingAnalysis," in hook_source
    assert "prepareTenderAnalysis," in hook_source
    assert "preparingAnalysis," in tender_details_source
    assert "onPrepareTenderAnalysis: prepareTenderAnalysis" in tender_details_source
    assert "preparingAnalysis," in workspaces_source
    assert "onPrepareTenderAnalysis," in workspaces_source
    assert "preparingAnalysis={preparingAnalysis}" in workspaces_source
    assert "onPrepareAnalysis={onPrepareTenderAnalysis}" in workspaces_source
    assert "preparingAnalysis" in analysis_source
    assert "onPrepareAnalysis" in analysis_source
    assert "Подготовить анализ" in analysis_source
    assert "preparingAnalysis || downloading || extracting || analyzing" in analysis_source
    assert find_mojibake(tender_details_source, TENDER_DETAILS_SOURCE) == []
    assert find_mojibake(workspaces_source, TENDER_WORKSPACES_SOURCE) == []
    assert find_mojibake(analysis_source, TENDER_ANALYSIS_TAB_SOURCE) == []
    assert find_mojibake(hook_source, USE_TENDER_DOCUMENT_ANALYSIS_SOURCE) == []


def test_local_dev_runtime_logs_are_ignored():
    gitignore_source = GITIGNORE_SOURCE.read_text(encoding="utf-8")

    assert "api-dev.out.log" in gitignore_source
    assert "api-dev.err.log" in gitignore_source


def test_frontend_uses_dedicated_tender_analysis_tab_module():
    tender_details_source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
    workspaces_source = (
        TENDER_WORKSPACES_SOURCE.read_text(encoding="utf-8")
        if TENDER_WORKSPACES_SOURCE.exists()
        else ""
    )
    analysis_source = (
        TENDER_ANALYSIS_TAB_SOURCE.read_text(encoding="utf-8")
        if TENDER_ANALYSIS_TAB_SOURCE.exists()
        else ""
    )
    analysis_summary_source = (
        TENDER_ANALYSIS_SUMMARY_SOURCE.read_text(encoding="utf-8")
        if TENDER_ANALYSIS_SUMMARY_SOURCE.exists()
        else ""
    )
    analysis_sections_source = (
        TENDER_ANALYSIS_SECTIONS_SOURCE.read_text(encoding="utf-8")
        if TENDER_ANALYSIS_SECTIONS_SOURCE.exists()
        else ""
    )
    analysis_evidence_source = (
        TENDER_ANALYSIS_EVIDENCE_SOURCE.read_text(encoding="utf-8")
        if TENDER_ANALYSIS_EVIDENCE_SOURCE.exists()
        else ""
    )
    analysis_decision_source = (
        TENDER_ANALYSIS_DECISION_SOURCE.read_text(encoding="utf-8")
        if TENDER_ANALYSIS_DECISION_SOURCE.exists()
        else ""
    )

    assert "from './TenderAnalysisTab'" in workspaces_source
    assert "export function TenderAnalysisTab" in analysis_source
    assert "from './TenderAnalysisSummary'" in analysis_source
    assert "from './TenderAnalysisSections'" in analysis_source
    assert "from './TenderAnalysisEvidencePanel'" not in analysis_source
    assert "from './TenderAnalysisDecisionBrief'" in analysis_source
    assert "export function AnalysisSummary" in analysis_summary_source
    assert "export function AnalysisSectionRail" in analysis_sections_source
    assert "export function AnalysisSectionBody" in analysis_sections_source
    assert "export function AnalysisList" in analysis_sections_source
    assert "export function AnalysisChecklist" in analysis_sections_source
    assert "export function AnalysisEvidencePanel" in analysis_evidence_source
    assert "export function AnalysisDecisionBrief" in analysis_decision_source
    assert "analysis-tab-summary" in analysis_summary_source
    assert "analysis-checklist" in analysis_sections_source
    assert "<TenderAnalysisTab" in workspaces_source
    assert "function AnalysisTabPanel" not in tender_details_source
    assert "function AnalysisChecklist" not in tender_details_source
    assert "function AnalysisChecklist" not in analysis_source
    assert "renderAnalysisSection" not in analysis_source
    assert find_mojibake(tender_details_source, TENDER_DETAILS_SOURCE) == []
    assert find_mojibake(workspaces_source, TENDER_WORKSPACES_SOURCE) == []
    assert find_mojibake(analysis_source, TENDER_ANALYSIS_TAB_SOURCE) == []
    assert find_mojibake(analysis_summary_source, TENDER_ANALYSIS_SUMMARY_SOURCE) == []
    assert find_mojibake(analysis_sections_source, TENDER_ANALYSIS_SECTIONS_SOURCE) == []
    assert find_mojibake(analysis_evidence_source, TENDER_ANALYSIS_EVIDENCE_SOURCE) == []
    assert find_mojibake(analysis_decision_source, TENDER_ANALYSIS_DECISION_SOURCE) == []


def test_frontend_analysis_reads_backend_operator_view_contract():
    analysis_summary_source = TENDER_ANALYSIS_SUMMARY_SOURCE.read_text(encoding="utf-8")
    analysis_sections_source = TENDER_ANALYSIS_SECTIONS_SOURCE.read_text(encoding="utf-8")
    analysis_decision_source = TENDER_ANALYSIS_DECISION_SOURCE.read_text(encoding="utf-8")

    assert "analysis?.operator_view" in analysis_summary_source
    assert "analysis?.operator_view" in analysis_sections_source
    assert "analysis?.operator_view" in analysis_decision_source
    assert "decision_brief" in analysis_decision_source
    assert "operatorView?.action_plan" in analysis_decision_source
    assert "operatorView?.document_state" not in analysis_decision_source
    assert "analysis-document-state" not in analysis_decision_source
    assert "documentStatusCounts" not in analysis_summary_source
    assert "documents_ready" not in analysis_summary_source
    assert "documents_total" not in analysis_summary_source
    assert "operatorView?.sections" in analysis_sections_source
    assert "operatorView?.metrics" in analysis_summary_source
    assert "buildAnalysisDecision" not in analysis_decision_source
    assert find_mojibake(analysis_summary_source, TENDER_ANALYSIS_SUMMARY_SOURCE) == []
    assert find_mojibake(analysis_sections_source, TENDER_ANALYSIS_SECTIONS_SOURCE) == []
    assert find_mojibake(analysis_decision_source, TENDER_ANALYSIS_DECISION_SOURCE) == []


def test_frontend_uses_dedicated_tender_economics_tab_module():
    tender_details_source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
    workspaces_source = (
        TENDER_WORKSPACES_SOURCE.read_text(encoding="utf-8")
        if TENDER_WORKSPACES_SOURCE.exists()
        else ""
    )
    economics_source = (
        TENDER_ECONOMICS_TAB_SOURCE.read_text(encoding="utf-8")
        if TENDER_ECONOMICS_TAB_SOURCE.exists()
        else ""
    )
    economics_summary_source = (
        TENDER_ECONOMICS_SUMMARY_SOURCE.read_text(encoding="utf-8")
        if TENDER_ECONOMICS_SUMMARY_SOURCE.exists()
        else ""
    )
    economics_decision_scenarios_source = (
        TENDER_ECONOMICS_DECISION_SCENARIOS_SOURCE.read_text(encoding="utf-8")
        if TENDER_ECONOMICS_DECISION_SCENARIOS_SOURCE.exists()
        else ""
    )
    economics_forms_source = (
        TENDER_ECONOMICS_FORMS_SOURCE.read_text(encoding="utf-8")
        if TENDER_ECONOMICS_FORMS_SOURCE.exists()
        else ""
    )
    economics_cost_form_source = (
        TENDER_ECONOMICS_COST_FORM_SOURCE.read_text(encoding="utf-8")
        if TENDER_ECONOMICS_COST_FORM_SOURCE.exists()
        else ""
    )
    economics_suppliers_source = (
        TENDER_ECONOMICS_SUPPLIERS_SOURCE.read_text(encoding="utf-8")
        if TENDER_ECONOMICS_SUPPLIERS_SOURCE.exists()
        else ""
    )
    economics_supplier_discovery_source = (
        TENDER_ECONOMICS_SUPPLIER_DISCOVERY_SOURCE.read_text(encoding="utf-8")
        if TENDER_ECONOMICS_SUPPLIER_DISCOVERY_SOURCE.exists()
        else ""
    )
    economics_supplier_options_source = (
        TENDER_ECONOMICS_SUPPLIER_OPTIONS_SOURCE.read_text(encoding="utf-8")
        if TENDER_ECONOMICS_SUPPLIER_OPTIONS_SOURCE.exists()
        else ""
    )
    economics_auto_source = (
        TENDER_ECONOMICS_AUTO_SOURCE.read_text(encoding="utf-8")
        if TENDER_ECONOMICS_AUTO_SOURCE.exists()
        else ""
    )
    economics_position_rail_source = (
        TENDER_ECONOMICS_POSITION_RAIL_SOURCE.read_text(encoding="utf-8")
        if TENDER_ECONOMICS_POSITION_RAIL_SOURCE.exists()
        else ""
    )
    economics_workbench_source = (
        TENDER_ECONOMICS_WORKBENCH_SOURCE.read_text(encoding="utf-8")
        if TENDER_ECONOMICS_WORKBENCH_SOURCE.exists()
        else ""
    )
    economics_profile_workspace_source = (
        TENDER_ECONOMICS_PROFILE_WORKSPACE_SOURCE.read_text(encoding="utf-8")
        if TENDER_ECONOMICS_PROFILE_WORKSPACE_SOURCE.exists()
        else ""
    )
    economics_metrics_source = (
        TENDER_ECONOMICS_METRICS_SOURCE.read_text(encoding="utf-8")
        if TENDER_ECONOMICS_METRICS_SOURCE.exists()
        else ""
    )

    assert "from './TenderEconomicsTab'" in workspaces_source
    assert "export function TenderEconomicsTab" in economics_source
    assert "from './TenderEconomicsMetrics'" in economics_source
    assert "from './TenderEconomicsSummary'" in economics_source
    assert "from './TenderEconomicsWorkbench'" in economics_source
    assert "from './TenderEconomicsForms'" not in economics_source
    assert "from './TenderEconomicsSuppliers'" not in economics_source
    assert "from './TenderEconomicsAuto'" not in economics_source
    assert "from './TenderEconomicsPositionRail'" not in economics_source
    assert "from './TenderEconomicsProfileWorkspace'" in economics_workbench_source
    assert "from './TenderEconomicsForms'" not in economics_workbench_source
    assert "from './TenderEconomicsForms'" in economics_profile_workspace_source
    assert "from './TenderEconomicsCostForm'" not in economics_workbench_source
    assert "from './TenderEconomicsCostForm'" in economics_profile_workspace_source
    assert "from './TenderEconomicsSuppliers'" not in economics_workbench_source
    assert "from './TenderEconomicsSuppliers'" in economics_profile_workspace_source
    assert "from './TenderEconomicsAuto'" not in economics_workbench_source
    assert "from './TenderEconomicsAuto'" in economics_profile_workspace_source
    assert "from './TenderEconomicsPositionRail'" in economics_workbench_source
    assert "from './TenderEconomicsSupplierOptions'" in economics_suppliers_source
    assert "from './TenderEconomicsSupplierDiscovery'" not in economics_suppliers_source
    assert "from './TenderEconomicsSupplierInputForm'" not in economics_suppliers_source
    assert "function EconomicsSummary" not in economics_source
    assert "export function EconomicsSummary" in economics_summary_source
    assert "from './TenderEconomicsDecisionScenarios'" in economics_summary_source
    assert "function BidScenarioStrip" not in economics_summary_source
    assert "function ParticipationDecisionCard" not in economics_summary_source
    assert "export function BidScenarioStrip" in economics_decision_scenarios_source
    assert "export function ParticipationDecisionCard" in economics_decision_scenarios_source
    assert "function ProductEconomicsForm" not in economics_source
    assert "export function ProductEconomicsForm" not in economics_forms_source
    assert "export function ProductEconomicsForm" in economics_cost_form_source
    assert "export function ProductEconomicsAssumptionsForm" in economics_forms_source
    assert "function ProductSupplierOptionsForm" not in economics_source
    assert "export function ProductSupplierOptionsForm" in economics_suppliers_source
    assert "export function SupplierSearchPreview" in economics_supplier_discovery_source
    assert "export function SupplierDiscoveryPreview" in economics_supplier_discovery_source
    assert "export function SupplierOptionsList" in economics_supplier_options_source
    assert "function ProductAutoEconomicsPanel" not in economics_source
    assert "export function ProductAutoEconomicsPanel" in economics_auto_source
    assert "function EconomicsPositionRail" not in economics_source
    assert "export function EconomicsPositionRail" in economics_position_rail_source
    assert "function TenderEconomicsWorkbench" not in economics_source
    assert "export function TenderEconomicsWorkbench" in economics_workbench_source
    assert "export function TenderEconomicsProfileWorkspace" in economics_profile_workspace_source
    assert "function TenderEconomicsMetrics" not in economics_source
    assert "export function TenderEconomicsMetrics" in economics_metrics_source
    assert "economics-tab-summary" in economics_metrics_source
    assert "economics-workbench" in economics_workbench_source
    assert "<TenderEconomicsTab" in workspaces_source
    assert "function EconomicsTabPanel" not in tender_details_source
    assert "function ProductEconomicsForm" not in tender_details_source
    assert "function ProductSupplierOptionsForm" not in tender_details_source
    assert find_mojibake(tender_details_source, TENDER_DETAILS_SOURCE) == []
    assert find_mojibake(workspaces_source, TENDER_WORKSPACES_SOURCE) == []
    assert find_mojibake(economics_source, TENDER_ECONOMICS_TAB_SOURCE) == []
    assert find_mojibake(economics_summary_source, TENDER_ECONOMICS_SUMMARY_SOURCE) == []
    assert find_mojibake(economics_decision_scenarios_source, TENDER_ECONOMICS_DECISION_SCENARIOS_SOURCE) == []
    assert find_mojibake(economics_forms_source, TENDER_ECONOMICS_FORMS_SOURCE) == []
    assert find_mojibake(economics_cost_form_source, TENDER_ECONOMICS_COST_FORM_SOURCE) == []
    assert find_mojibake(economics_suppliers_source, TENDER_ECONOMICS_SUPPLIERS_SOURCE) == []
    assert find_mojibake(economics_supplier_discovery_source, TENDER_ECONOMICS_SUPPLIER_DISCOVERY_SOURCE) == []
    assert find_mojibake(economics_supplier_options_source, TENDER_ECONOMICS_SUPPLIER_OPTIONS_SOURCE) == []
    assert find_mojibake(economics_auto_source, TENDER_ECONOMICS_AUTO_SOURCE) == []
    assert find_mojibake(economics_position_rail_source, TENDER_ECONOMICS_POSITION_RAIL_SOURCE) == []
    assert find_mojibake(economics_workbench_source, TENDER_ECONOMICS_WORKBENCH_SOURCE) == []
    assert find_mojibake(economics_profile_workspace_source, TENDER_ECONOMICS_PROFILE_WORKSPACE_SOURCE) == []
    assert find_mojibake(economics_metrics_source, TENDER_ECONOMICS_METRICS_SOURCE) == []


def test_frontend_uses_dedicated_tender_workflow_tab_module():
    tender_details_source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
    panels_source = TENDER_TAB_PANELS_SOURCE.read_text(encoding="utf-8")
    workflow_source = (
        TENDER_WORKFLOW_TAB_SOURCE.read_text(encoding="utf-8")
        if TENDER_WORKFLOW_TAB_SOURCE.exists()
        else ""
    )

    assert "from './TenderWorkflowTab'" in panels_source
    assert "export function WorkflowTabPanel" in workflow_source
    assert "workflow-compact-row" in workflow_source
    assert "workflow-status-select" in workflow_source
    assert "workflow-note-panel" in workflow_source
    assert "debug-details" not in workflow_source
    assert "raw-grid" not in workflow_source
    assert "<WorkflowTabPanel" in panels_source
    assert "raw={raw}" not in panels_source
    assert "function WorkflowTabPanel" not in tender_details_source
    assert "workflow-status-summary" not in tender_details_source
    assert "workflow-note-panel" not in tender_details_source
    assert find_mojibake(tender_details_source, TENDER_DETAILS_SOURCE) == []
    assert find_mojibake(panels_source, TENDER_TAB_PANELS_SOURCE) == []
    assert find_mojibake(workflow_source, TENDER_WORKFLOW_TAB_SOURCE) == []


def test_frontend_uses_dedicated_tender_products_tab_module():
    tender_details_source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
    panels_source = TENDER_TAB_PANELS_SOURCE.read_text(encoding="utf-8")
    workspaces_source = TENDER_WORKSPACES_SOURCE.read_text(encoding="utf-8")
    products_source = (
        TENDER_PRODUCTS_TAB_SOURCE.read_text(encoding="utf-8")
        if TENDER_PRODUCTS_TAB_SOURCE.exists()
        else ""
    )

    assert "from './TenderProductsTab'" in workspaces_source
    assert "export function TenderProductsTab" in products_source
    assert "function ProductTabSummary" in products_source
    assert "function ProductProfileDetail" in products_source
    assert "function TenderItems" in products_source
    assert "product-profile-section" in products_source
    assert "product-tab-summary" in products_source
    assert "profile-detail" in products_source
    assert "source-items" in products_source
    assert "<TenderProductsTab" in workspaces_source
    assert "from './TenderProductsTab'" not in panels_source
    assert "function ProductTabSummary" not in tender_details_source
    assert "function ProductProfileDetail" not in tender_details_source
    assert "function TenderItems" not in tender_details_source
    assert "function ProfileSummary" not in tender_details_source
    assert "product-tab-summary" not in tender_details_source
    assert "profile-detail" not in tender_details_source
    assert "source-items" not in tender_details_source
    assert find_mojibake(tender_details_source, TENDER_DETAILS_SOURCE) == []
    assert find_mojibake(panels_source, TENDER_TAB_PANELS_SOURCE) == []
    assert find_mojibake(workspaces_source, TENDER_WORKSPACES_SOURCE) == []
    assert find_mojibake(products_source, TENDER_PRODUCTS_TAB_SOURCE) == []


def test_frontend_uses_dedicated_tender_decision_strip_module():
    tender_details_source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
    strip_source = (
        TENDER_DECISION_STRIP_SOURCE.read_text(encoding="utf-8")
        if TENDER_DECISION_STRIP_SOURCE.exists()
        else ""
    )
    price_change_source = (
        TENDER_DECISION_SUMMARY_SOURCE.read_text(encoding="utf-8")
        if TENDER_DECISION_SUMMARY_SOURCE.exists()
        else ""
    )
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "from './TenderDecisionStrip'" in tender_details_source
    assert "from './TenderDecisionSummary'" in tender_details_source
    assert "export function TenderDecisionStrip" in strip_source
    assert "decision-strip-grid" in strip_source
    assert "documentStatusCounts" in strip_source
    assert "tenderDecisionLabel" in strip_source
    assert "tender.decision?.metrics" in strip_source
    assert "tender.decision?.reasons" in strip_source
    assert "tender.decision?.blockers" in strip_source
    assert "tender.decision?.reason_tree" in strip_source
    assert "decision-tree" in strip_source
    assert "decisionTree.positive" in strip_source
    assert "decisionTree.negative" in strip_source
    assert "decisionTree.actions" in strip_source
    assert "decision-strip-explanation" in strip_source
    assert "decision-strip-blockers" in strip_source
    assert ".decision-tree" in styles_source
    assert ".decision-tree-branch" in styles_source
    assert ".decision-strip-explanation" in styles_source
    assert ".decision-strip-blockers" in styles_source
    assert "function decisionLabel" not in strip_source
    assert "export function PriceChangeBanner" in price_change_source
    assert "price-change-banner" in price_change_source
    assert "formatPriceChangeDirection" in price_change_source
    assert "<TenderDecisionStrip" in tender_details_source
    assert "<PriceChangeBanner change={tender.price_change} />" in tender_details_source
    assert "function TenderDecisionStrip" not in tender_details_source
    assert "function PriceChangeBanner" not in tender_details_source
    assert "decision-strip-grid" not in tender_details_source
    assert "price-change-banner" not in tender_details_source
    assert find_mojibake(tender_details_source, TENDER_DETAILS_SOURCE) == []
    assert find_mojibake(strip_source, TENDER_DECISION_STRIP_SOURCE) == []
    assert find_mojibake(price_change_source, TENDER_DECISION_SUMMARY_SOURCE) == []


def test_frontend_uses_dedicated_tender_detail_actions_module():
    tender_details_source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
    actions_source = (
        TENDER_DETAIL_ACTIONS_SOURCE.read_text(encoding="utf-8")
        if TENDER_DETAIL_ACTIONS_SOURCE.exists()
        else ""
    )

    assert "from './TenderDetailActions'" in tender_details_source
    assert "export function TenderDetailActions" in actions_source
    assert "details-action-group primary-actions" in actions_source
    assert "onRefreshDetails" in actions_source
    assert "details-action-group secondary-actions" not in actions_source
    assert "onDownloadDocuments" not in actions_source
    assert "onExtractDocumentText" not in actions_source
    assert "onAnalyzeTender" not in actions_source
    assert "onSendToTelegram" not in actions_source
    assert "report.docx" not in actions_source
    assert "<TenderDetailActions" in tender_details_source
    assert "details-action-group primary-actions" not in tender_details_source
    assert "details-action-group secondary-actions" not in tender_details_source
    assert "className=\"detail-action\"" not in tender_details_source
    assert find_mojibake(tender_details_source, TENDER_DETAILS_SOURCE) == []
    assert find_mojibake(actions_source, TENDER_DETAIL_ACTIONS_SOURCE) == []


def test_tender_details_uses_dedicated_header_module():
    tender_details_source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
    header_source = (
        TENDER_DETAILS_HEADER_SOURCE.read_text(encoding="utf-8")
        if TENDER_DETAILS_HEADER_SOURCE.exists()
        else ""
    )

    assert "from './TenderDetailsHeader'" in tender_details_source
    assert "export function TenderDetailsHeader" in header_source
    assert "Building2" in header_source
    assert "nmcPriceValue" in header_source
    assert "participantBidValue" in header_source
    assert "formatDate" in header_source
    assert "sourceLabels" in header_source
    assert "workflowLabels" in header_source
    assert "details-header" in header_source
    assert "<TenderDetailsHeader tender={tender} />" in tender_details_source
    assert "details-header" not in tender_details_source
    assert "Building2" not in tender_details_source
    assert "nmcPriceValue" not in tender_details_source
    assert "participantBidValue" not in tender_details_source
    assert "formatDate" not in tender_details_source
    assert "sourceLabels" not in tender_details_source
    assert "workflowLabels" not in tender_details_source
    assert find_mojibake(tender_details_source, TENDER_DETAILS_SOURCE) == []
    assert find_mojibake(header_source, TENDER_DETAILS_HEADER_SOURCE) == []


def test_tender_details_uses_dedicated_status_stack_module():
    tender_details_source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
    status_source = (
        TENDER_DETAILS_STATUS_SOURCE.read_text(encoding="utf-8")
        if TENDER_DETAILS_STATUS_SOURCE.exists()
        else ""
    )

    assert "from './TenderDetailsStatusStack'" in tender_details_source
    assert "export function TenderDetailsStatusStack" in status_source
    assert "messages.length" in status_source
    assert "status-stack" in status_source
    assert "inline-status" in status_source
    assert "<TenderDetailsStatusStack messages={statusMessages} />" in tender_details_source
    assert "status-stack" not in tender_details_source
    assert "inline-status" not in tender_details_source
    assert find_mojibake(tender_details_source, TENDER_DETAILS_SOURCE) == []
    assert find_mojibake(status_source, TENDER_DETAILS_STATUS_SOURCE) == []


def test_tender_details_uses_dedicated_tabs_module():
    tender_details_source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
    tabs_source = (
        TENDER_DETAILS_TABS_SOURCE.read_text(encoding="utf-8")
        if TENDER_DETAILS_TABS_SOURCE.exists()
        else ""
    )
    navigation_source = (
        TENDER_DETAILS_NAVIGATION_SOURCE.read_text(encoding="utf-8")
        if TENDER_DETAILS_NAVIGATION_SOURCE.exists()
        else ""
    )
    panels_source = (
        TENDER_TAB_PANELS_SOURCE.read_text(encoding="utf-8")
        if TENDER_TAB_PANELS_SOURCE.exists()
        else ""
    )
    workspaces_source = (
        TENDER_WORKSPACES_SOURCE.read_text(encoding="utf-8")
        if TENDER_WORKSPACES_SOURCE.exists()
        else ""
    )

    assert "from './TenderDetailsTabs'" in tender_details_source
    assert "export function TenderDetailsTabs" in tabs_source
    assert "TenderDetailsNavigation" not in tabs_source
    assert "detail-workspace-launchers" not in tabs_source
    assert "detail-workspace-launchers" not in navigation_source
    assert "detail-tabs" not in navigation_source
    assert "TenderTabPanels" in tabs_source
    assert "detail-tab-panel" in panels_source
    assert "TenderSummaryTab" in panels_source
    assert "TenderProductsTab" in workspaces_source
    assert "TenderDocumentsTab" not in workspaces_source
    assert "TenderWorkspaces" in tabs_source
    assert "WorkflowTabPanel" in panels_source
    assert "<TenderDetailsTabs" in tender_details_source
    assert "const tabs =" not in tender_details_source
    assert "detail-tabs" not in tender_details_source
    assert "detail-tab-panel" not in tender_details_source
    assert "TenderSummaryTab" not in tender_details_source
    assert "TenderProductsTab" not in tender_details_source
    assert "TenderDocumentsTab" not in tender_details_source
    assert "TenderWorkspaces" not in tender_details_source
    assert "TenderAnalysisTab" not in tender_details_source
    assert "TenderEconomicsTab" not in tender_details_source
    assert "WorkflowTabPanel" not in tender_details_source
    assert find_mojibake(tender_details_source, TENDER_DETAILS_SOURCE) == []
    assert find_mojibake(tabs_source, TENDER_DETAILS_TABS_SOURCE) == []
    assert find_mojibake(navigation_source, TENDER_DETAILS_NAVIGATION_SOURCE) == []
    assert find_mojibake(panels_source, TENDER_TAB_PANELS_SOURCE) == []
    assert find_mojibake(workspaces_source, TENDER_WORKSPACES_SOURCE) == []


def test_tender_details_passes_grouped_state_to_tabs_module():
    tender_details_source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
    tabs_source = TENDER_DETAILS_TABS_SOURCE.read_text(encoding="utf-8")

    for group_name in (
        "productState",
        "documentState",
        "analysisState",
        "economicsState",
        "workflowState",
    ):
        assert f"const {group_name} = {{" in tender_details_source
        assert f"{group_name}={{{group_name}}}" in tender_details_source
        assert group_name in tabs_source

    for direct_prop in (
        "raw={raw}",
        "activeTab={activeTab}",
        "onActiveTabChange={setActiveTab}",
        "productProfileSummary={productProfileSummary}",
        "selectedProfileIndex={selectedProfileIndex}",
        "onDownloadDocuments={downloadDocuments}",
        "analyzing={analyzing}",
        "onEconomicsSave={saveProfileEconomics}",
        "onSupplierCatalogHealthRefresh={refreshSupplierCatalogHealth}",
        "note={note}",
        "onSaveWorkflow={saveWorkflow}",
    ):
        assert direct_prop not in tender_details_source

    assert "tabState" not in tabs_source
    assert "productState," in tabs_source
    assert "documentState," in tabs_source
    assert "analysisState," in tabs_source
    assert "economicsState," in tabs_source
    assert "workflowState," in tabs_source
    assert find_mojibake(tender_details_source, TENDER_DETAILS_SOURCE) == []
    assert find_mojibake(tabs_source, TENDER_DETAILS_TABS_SOURCE) == []


def test_tender_details_tabs_keep_grouped_state_for_panels_and_workspaces():
    tabs_source = TENDER_DETAILS_TABS_SOURCE.read_text(encoding="utf-8")
    panels_source = TENDER_TAB_PANELS_SOURCE.read_text(encoding="utf-8")
    workspaces_source = TENDER_WORKSPACES_SOURCE.read_text(encoding="utf-8")

    for child_name in ("TenderTabPanels", "TenderWorkspaces"):
        assert f"<{child_name}" in tabs_source

    for group_name in (
        "productState",
        "documentState",
        "analysisState",
        "economicsState",
        "workflowState",
    ):
        assert f"{group_name}={{{group_name}}}" in tabs_source
        assert group_name in panels_source

    for group_name in (
        "productState",
        "documentState",
        "analysisState",
        "economicsState",
    ):
        assert f"{group_name}={{{group_name}}}" in tabs_source
        assert group_name in workspaces_source

    for direct_prop in (
        "documentRecords={documentRecords}",
        "analysis={analysis}",
        "analyzing={analyzing}",
        "onAnalyzeTender={onAnalyzeTender}",
        "economics={economics}",
        "onEconomicsSave={onEconomicsSave}",
        "onSupplierCatalogHealthRefresh={onSupplierCatalogHealthRefresh}",
        "note={note}",
        "onSaveWorkflow={onSaveWorkflow}",
    ):
        assert direct_prop not in tabs_source

    assert "tabState" not in panels_source
    assert "const { analysis } = analysisState" in panels_source
    assert "const { economics } = economicsState" in panels_source
    assert "documentRecords," in workspaces_source
    assert "onDownloadDocuments," in workspaces_source
    assert "const {" in workspaces_source
    assert find_mojibake(tabs_source, TENDER_DETAILS_TABS_SOURCE) == []
    assert find_mojibake(panels_source, TENDER_TAB_PANELS_SOURCE) == []
    assert find_mojibake(workspaces_source, TENDER_WORKSPACES_SOURCE) == []


def test_tender_details_uses_document_analysis_hook():
    tender_details_source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
    hook_source = (
        USE_TENDER_DOCUMENT_ANALYSIS_SOURCE.read_text(encoding="utf-8")
        if USE_TENDER_DOCUMENT_ANALYSIS_SOURCE.exists()
        else ""
    )

    assert "from './useTenderDocumentAnalysis'" in tender_details_source
    assert "useTenderDocumentAnalysis(tender)" in tender_details_source
    assert "export function useTenderDocumentAnalysis" in hook_source
    assert "downloadTenderDocuments" in hook_source
    assert "payload.skipped" in hook_source
    assert "уже скачано" in hook_source
    assert "extractTenderDocumentText" in hook_source
    assert "runTenderAnalysis" in hook_source
    assert "documentRecordsForTender" in hook_source
    assert "function downloadDocuments" not in tender_details_source
    assert "function extractDocumentText" not in tender_details_source
    assert "function analyzeTender" not in tender_details_source
    assert "const [documentRecords" not in tender_details_source
    assert "const [analysis" not in tender_details_source
    assert "const [downloading" not in tender_details_source
    assert "const [extracting" not in tender_details_source
    assert "const [analyzing" not in tender_details_source
    assert find_mojibake(tender_details_source, TENDER_DETAILS_SOURCE) == []
    assert find_mojibake(hook_source, USE_TENDER_DOCUMENT_ANALYSIS_SOURCE) == []


def test_document_analysis_hook_ignores_stale_async_results_after_tender_switch():
    hook_source = USE_TENDER_DOCUMENT_ANALYSIS_SOURCE.read_text(encoding="utf-8")

    assert "useRef" in hook_source
    assert "function documentTenderKey(tender)" in hook_source
    assert "currentTenderKeyRef" in hook_source
    assert "downloadRequestRef" in hook_source
    assert "extractRequestRef" in hook_source
    assert "analysisRequestRef" in hook_source
    assert "prepareRequestRef" in hook_source
    assert "function isCurrentRequest(requestRef, requestId, requestTenderKey, currentTenderKeyRef)" in hook_source
    assert "downloadRequestRef.current = null" in hook_source
    assert "extractRequestRef.current = null" in hook_source
    assert "analysisRequestRef.current = null" in hook_source
    assert "prepareRequestRef.current = null" in hook_source
    assert "setDownloading(false)" in hook_source
    assert "setExtracting(false)" in hook_source
    assert "setAnalyzing(false)" in hook_source
    assert "setPreparingAnalysis(false)" in hook_source
    assert "if (!isCurrentRequest(downloadRequestRef, requestId, requestTenderKey, currentTenderKeyRef)) return" in hook_source
    assert "if (!isCurrentRequest(extractRequestRef, requestId, requestTenderKey, currentTenderKeyRef)) return" in hook_source
    assert "if (!isCurrentRequest(analysisRequestRef, requestId, requestTenderKey, currentTenderKeyRef)) return" in hook_source
    assert hook_source.count(
        "if (!isCurrentRequest(prepareRequestRef, requestId, requestTenderKey, currentTenderKeyRef)) return"
    ) == 3
    assert find_mojibake(hook_source, USE_TENDER_DOCUMENT_ANALYSIS_SOURCE) == []


def test_tender_details_uses_product_profiles_hook():
    tender_details_source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
    hook_source = (
        USE_TENDER_PRODUCT_PROFILES_SOURCE.read_text(encoding="utf-8")
        if USE_TENDER_PRODUCT_PROFILES_SOURCE.exists()
        else ""
    )

    assert "from './useTenderProductProfiles'" in tender_details_source
    assert "useTenderProductProfiles(tender, onTenderRefresh, setDetailStatus)" in tender_details_source
    assert "export function useTenderProductProfiles" in hook_source
    for api_name in (
        "rebuildTenderProductProfiles",
        "saveProfileEconomics",
        "saveProfileEconomicsAssumptions",
        "addProfileSupplierOption",
        "selectProfileSupplierOption",
        "autoSelectProfileSupplierOption",
        "runProfileAutoEconomics",
        "acceptProfileAutoEconomics",
    ):
        assert api_name in hook_source
    for local_function in (
        "function rebuildProductProfiles",
        "function saveProfileEconomics",
        "function saveProfileEconomicsAssumptions",
        "function saveSupplierOption",
        "function selectSupplierOption",
        "function autoSelectSupplierOption",
        "function runProfileAutoEconomics",
        "function acceptProfileAutoEconomics",
    ):
        assert local_function not in tender_details_source
    for state_name in (
        "productProfiles",
        "productProfileSummary",
        "economics",
        "selectedProfileIndex",
        "profilesLoading",
        "savingEconomicsPosition",
        "savingAssumptionsPosition",
        "savingSupplierOptionPosition",
        "autoSelectingSupplierPosition",
        "autoEstimatingPosition",
        "acceptingAutoEconomicsPosition",
    ):
        assert f"const [{state_name}" not in tender_details_source
    assert "applyProductTenderState" in tender_details_source
    assert "applyProductTenderState" in hook_source
    assert find_mojibake(tender_details_source, TENDER_DETAILS_SOURCE) == []
    assert find_mojibake(hook_source, USE_TENDER_PRODUCT_PROFILES_SOURCE) == []


def test_tender_details_uses_workflow_hook():
    tender_details_source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
    hook_source = (
        USE_TENDER_WORKFLOW_SOURCE.read_text(encoding="utf-8")
        if USE_TENDER_WORKFLOW_SOURCE.exists()
        else ""
    )

    assert "from './useTenderWorkflow'" in tender_details_source
    assert "useTenderWorkflow(tender, onWorkflowUpdate)" in tender_details_source
    assert "export function useTenderWorkflow" in hook_source
    assert "saveTenderWorkflow" in hook_source
    assert "function saveWorkflow" not in tender_details_source
    assert "const [note" not in tender_details_source
    assert "const [saving" not in tender_details_source
    assert find_mojibake(tender_details_source, TENDER_DETAILS_SOURCE) == []
    assert find_mojibake(hook_source, USE_TENDER_WORKFLOW_SOURCE) == []


def test_tender_details_uses_notification_hook():
    tender_details_source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
    hook_source = (
        USE_TENDER_NOTIFICATION_SOURCE.read_text(encoding="utf-8")
        if USE_TENDER_NOTIFICATION_SOURCE.exists()
        else ""
    )

    assert "from './useTenderNotification'" in tender_details_source
    assert "useTenderNotification(tender)" in tender_details_source
    assert "export function useTenderNotification" in hook_source
    assert "sendTenderNotification" in hook_source
    assert "function sendToTelegram" not in tender_details_source
    assert "const [sending" not in tender_details_source
    assert "const [notifyStatus" not in tender_details_source
    assert find_mojibake(tender_details_source, TENDER_DETAILS_SOURCE) == []
    assert find_mojibake(hook_source, USE_TENDER_NOTIFICATION_SOURCE) == []


def test_tender_details_uses_refresh_details_hook():
    tender_details_source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
    hook_source = (
        USE_TENDER_REFRESH_DETAILS_SOURCE.read_text(encoding="utf-8")
        if USE_TENDER_REFRESH_DETAILS_SOURCE.exists()
        else ""
    )

    assert "from './useTenderRefreshDetails'" in tender_details_source
    assert "useTenderRefreshDetails({" in tender_details_source
    assert "export function useTenderRefreshDetails" in hook_source
    assert "refreshTenderDetails" in hook_source
    assert "shouldAutoRefreshDetails" in hook_source
    assert "applyProductTenderState(nextTender)" in hook_source
    assert "function refreshDetails" not in tender_details_source
    assert "const [refreshingDetails" not in tender_details_source
    assert "autoRefreshKey" not in tender_details_source
    assert "refreshTenderDetails" not in tender_details_source
    assert "shouldAutoRefreshDetails" not in tender_details_source
    assert find_mojibake(tender_details_source, TENDER_DETAILS_SOURCE) == []
    assert find_mojibake(hook_source, USE_TENDER_REFRESH_DETAILS_SOURCE) == []


def test_refresh_details_hides_auto_no_change_status():
    hook_source = USE_TENDER_REFRESH_DETAILS_SOURCE.read_text(encoding="utf-8")

    assert "const NO_DETAIL_CHANGE_MESSAGE" in hook_source
    assert "if (!payload.refreshed && options.automatic)" in hook_source
    assert "setDetailStatus('')" in hook_source
    assert "payload.message ||" not in hook_source
    assert "Detail data did not change" not in hook_source
    assert "Источник не вернул новые детали; оставил сохраненные данные." in hook_source


def test_tender_details_uses_ui_state_hook():
    tender_details_source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
    hook_source = (
        USE_TENDER_DETAILS_UI_SOURCE.read_text(encoding="utf-8")
        if USE_TENDER_DETAILS_UI_SOURCE.exists()
        else ""
    )

    assert "from './useTenderDetailsUi'" in tender_details_source
    assert "useTenderDetailsUi({" in tender_details_source
    assert "export function useTenderDetailsUi" in hook_source
    assert "useEffect" in hook_source
    assert "useState" in hook_source
    assert "function safeJson" not in hook_source
    assert "raw_payload_json" not in hook_source
    assert "statusMessages" in hook_source
    assert "useState('summary')" not in hook_source
    assert "setActiveTab('summary')" not in hook_source
    assert "[tender.source, tender.external_id]" in hook_source
    assert "tender.product_profiles" not in hook_source
    assert "tender.product_profile_summary" not in hook_source
    assert "tender.economics" not in hook_source
    assert "setNotifyStatus('')" in hook_source
    assert "setDetailStatus('')" in hook_source
    assert "const [activeTab" not in tender_details_source
    assert "const [detailStatus" not in tender_details_source
    assert "const statusMessages" not in tender_details_source
    assert "useEffect" not in tender_details_source
    assert "useState" not in tender_details_source
    assert find_mojibake(tender_details_source, TENDER_DETAILS_SOURCE) == []
    assert find_mojibake(hook_source, USE_TENDER_DETAILS_UI_SOURCE) == []


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
    source = TENDER_ANALYSIS_SECTIONS_SOURCE.read_text(encoding="utf-8")
    styles = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "MAJOR_ANALYSIS_SECTIONS" in source
    assert "buildMajorAnalysisSections(analysis, documents)" in source
    assert "visibleMajorAnalysisSections" in source
    assert "analysisSectionHasContent" in source
    assert "document_summary" in source
    assert "'decision_risks'" in source
    assert "'product_compliance'" in source
    assert "'fulfillment_terms'" in source
    assert "'acceptance_payment'" in source
    assert "export function AnalysisChecklist" in source
    assert "Проверочный список" in source
    assert "analysis-checklist" in source
    assert "grid-template-columns: 1fr" in styles
    assert ".analysis-card," in styles
    assert "item.source_label || item.source" in source
    assert "item.source_context" in source
    assert "analysis-source-context" in source
    assert ".analysis-source-context" in styles
    assert "Источник" in source
    row_text_rule = styles[
        styles.index(".analysis-checklist-row p"):styles.index("}", styles.index(".analysis-checklist-row p"))
    ]
    assert "overflow-wrap: anywhere" in row_text_rule
    assert "analysisCategoryLabel" in source
    assert "analysisSeverityLabel" in source
    assert find_mojibake(source, TENDER_ANALYSIS_SECTIONS_SOURCE) == []


def test_summary_metrics_have_stable_wrapping_container():
    shared_source = TENDER_DETAILS_SHARED_SOURCE.read_text(encoding="utf-8")
    styles = STYLES_SOURCE.read_text(encoding="utf-8")

    assert 'className="summary-metric"' in shared_source
    assert ".summary-metric {" in styles
    assert ".summary-metric strong" in styles
    assert ".summary-metric .summary-label" in styles
    assert "display: grid" in styles[styles.index(".summary-metric {"):styles.index(".summary-metric strong")]
    assert "min-width: 0" in styles[styles.index(".summary-metric {"):styles.index(".summary-metric strong")]


def test_product_profile_renders_fulfillment_requirements():
    source = (
        TENDER_PRODUCTS_TAB_SOURCE.read_text(encoding="utf-8")
        if TENDER_PRODUCTS_TAB_SOURCE.exists()
        else ""
    )
    formatter_source = FORMATTERS_SOURCE.read_text(encoding="utf-8")

    assert "profile.fulfillment_requirements" in source
    assert "formatFulfillmentRequirements" in source
    assert "formatProfileTenderPrice(profile)" in source
    assert "tenderReferenceUnitPrice(profile)" in source
    assert "tenderReferenceTotalPrice(profile)" in source
    assert "<TenderItems items={tender.items || []} profiles={productProfiles} />" in source
    assert "const profileByPosition = profilesByPosition(profiles)" in source
    assert "tenderReferenceUnitPrice(itemWithProfilePrice)" in source
    assert "tenderReferenceTotalPrice(itemWithProfilePrice)" in source
    assert "fulfillmentRequirementTypeLabel" in formatter_source
    assert "Поставка и исполнение" in source
    assert find_mojibake(source, TENDER_PRODUCTS_TAB_SOURCE) == []


def test_tender_overview_surfaces_compact_customer_eis_panel():
    source = TENDER_OVERVIEW_TAB_SOURCE.read_text(encoding="utf-8")
    styles = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "CustomerEisPanel" in source
    assert "tender.customer_risk_profile" in source
    assert "tender.eis_reference" in source
    assert "customer-eis-panel" in source
    assert "customer-eis-link" in source
    assert "eis_reference.links" in source
    assert ".customer-eis-panel" in styles
    assert ".customer-eis-links" in styles
    assert find_mojibake(source, TENDER_OVERVIEW_TAB_SOURCE) == []


def test_dashboard_surfaces_customer_review_queue_in_right_rail():
    source = DASHBOARD_SOURCE.read_text(encoding="utf-8")

    assert "customerReviewQueue = queueById(dashboardQueues, 'customer_review')" in source
    assert "DashboardCustomerReviewPanel" in source
    assert "item.customer_risk_profile" in source
    assert "Заказчик / ЕИС" in source
    assert "customerRiskDashboardLine" in source
    assert find_mojibake(source, DASHBOARD_SOURCE) == []


def test_tender_details_render_economics_summary():
    tabs_source = TENDER_DETAILS_TABS_SOURCE.read_text(encoding="utf-8")
    summary_source = TENDER_SUMMARY_TAB_SOURCE.read_text(encoding="utf-8")
    source = TENDER_ECONOMICS_TAB_SOURCE.read_text(encoding="utf-8")
    economics_summary_source = (
        TENDER_ECONOMICS_SUMMARY_SOURCE.read_text(encoding="utf-8")
        if TENDER_ECONOMICS_SUMMARY_SOURCE.exists()
        else ""
    )
    economics_decision_scenarios_source = (
        TENDER_ECONOMICS_DECISION_SCENARIOS_SOURCE.read_text(encoding="utf-8")
        if TENDER_ECONOMICS_DECISION_SCENARIOS_SOURCE.exists()
        else ""
    )

    assert "const workspaceModes = new Set([" in tabs_source
    assert "'economics'" in tabs_source
    assert "const workspaceActions = [" not in tabs_source
    assert "onClick={() => onOpenTab?.('economics')}" in summary_source
    assert "from './TenderEconomicsSummary'" in source
    assert "<EconomicsSummary economics={economics} tender={tender} profiles={profiles} />" in source
    assert "function EconomicsSummary" not in source
    assert "export function EconomicsSummary" in economics_summary_source
    assert "export function EconomicsSummary({ economics, tender, profiles = [] })" in economics_summary_source
    assert "const itemProfiles = profilesByEconomicsItem(profiles)" in economics_summary_source
    assert "tenderReferenceUnitPrice(profile)" in economics_summary_source
    assert "tenderReferenceTotalPrice(profile)" in economics_summary_source
    assert "from './TenderEconomicsDecisionScenarios'" in economics_summary_source
    assert "function ParticipationDecisionCard" not in economics_summary_source
    assert "function BidScenarioStrip" not in economics_summary_source
    assert "export function ParticipationDecisionCard" in economics_decision_scenarios_source
    assert "export function BidScenarioStrip" in economics_decision_scenarios_source
    assert "economicsStatusLabel" in economics_summary_source
    assert "Маржа" in economics_summary_source
    assert find_mojibake(tabs_source, TENDER_DETAILS_TABS_SOURCE) == []
    assert find_mojibake(summary_source, TENDER_SUMMARY_TAB_SOURCE) == []
    assert find_mojibake(source, TENDER_ECONOMICS_TAB_SOURCE) == []
    assert find_mojibake(economics_summary_source, TENDER_ECONOMICS_SUMMARY_SOURCE) == []
    assert find_mojibake(economics_decision_scenarios_source, TENDER_ECONOMICS_DECISION_SCENARIOS_SOURCE) == []

def test_economics_summary_surfaces_analysis_cost_drivers():
    economics_summary_source = TENDER_ECONOMICS_SUMMARY_SOURCE.read_text(encoding="utf-8")
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "analysis_cost_drivers" in economics_summary_source
    assert "analysis_reserve_hint" in economics_summary_source
    assert "analysis-cost-drivers" in economics_summary_source
    assert "Факторы из ТЗ" in economics_summary_source
    assert ".analysis-cost-drivers" in styles_source
    assert find_mojibake(economics_summary_source, TENDER_ECONOMICS_SUMMARY_SOURCE) == []

def test_product_profile_renders_economics_input_form():
    tab_source = TENDER_ECONOMICS_TAB_SOURCE.read_text(encoding="utf-8")
    workbench_source = (
        TENDER_ECONOMICS_WORKBENCH_SOURCE.read_text(encoding="utf-8")
        if TENDER_ECONOMICS_WORKBENCH_SOURCE.exists()
        else ""
    )
    profile_workspace_source = (
        TENDER_ECONOMICS_PROFILE_WORKSPACE_SOURCE.read_text(encoding="utf-8")
        if TENDER_ECONOMICS_PROFILE_WORKSPACE_SOURCE.exists()
        else ""
    )
    forms_source = TENDER_ECONOMICS_FORMS_SOURCE.read_text(encoding="utf-8") if TENDER_ECONOMICS_FORMS_SOURCE.exists() else ""
    cost_form_source = TENDER_ECONOMICS_COST_FORM_SOURCE.read_text(encoding="utf-8") if TENDER_ECONOMICS_COST_FORM_SOURCE.exists() else ""
    api_source = API_SOURCE.read_text(encoding="utf-8")

    assert "from './TenderEconomicsForms'" not in tab_source
    assert "from './TenderEconomicsForms'" not in workbench_source
    assert "from './TenderEconomicsForms'" in profile_workspace_source
    assert "from './TenderEconomicsCostForm'" not in workbench_source
    assert "from './TenderEconomicsCostForm'" in profile_workspace_source
    assert "export function ProductEconomicsForm" not in forms_source
    assert "export function ProductEconomicsForm" in cost_form_source
    assert "function ProductEconomicsForm" not in tab_source
    assert "<ProductEconomicsForm" in profile_workspace_source
    assert "onEconomicsSave" in tab_source
    assert "product-profiles/${profile.position_index}" in api_source
    assert "${productProfilePath(tender, profile)}/economics" in api_source
    assert "unit_cost" in cost_form_source
    assert "unit_cost_basis" in cost_form_source
    assert "supplier_pack" in cost_form_source
    assert "pack_quantity" in cost_form_source
    assert "logistics_cost" in cost_form_source
    assert "documents_cost" in cost_form_source
    assert "packaging_cost" in cost_form_source
    assert "other_costs" in cost_form_source
    assert "economics-landed-preview" in cost_form_source
    assert "buildLandedCostPreview" in cost_form_source
    assert "Себестоимость" in cost_form_source
    assert "Итого себестоимость" in cost_form_source
    assert "landed cost" not in cost_form_source.lower()
    assert find_mojibake(tab_source, TENDER_ECONOMICS_TAB_SOURCE) == []
    assert find_mojibake(workbench_source, TENDER_ECONOMICS_WORKBENCH_SOURCE) == []
    assert find_mojibake(forms_source, TENDER_ECONOMICS_FORMS_SOURCE) == []
    assert find_mojibake(cost_form_source, TENDER_ECONOMICS_COST_FORM_SOURCE) == []

def test_product_profile_renders_supplier_option_form():
    details_source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
    tabs_source = TENDER_DETAILS_TABS_SOURCE.read_text(encoding="utf-8")
    workspaces_source = TENDER_WORKSPACES_SOURCE.read_text(encoding="utf-8")
    hook_source = USE_TENDER_PRODUCT_PROFILES_SOURCE.read_text(encoding="utf-8")
    tab_source = TENDER_ECONOMICS_TAB_SOURCE.read_text(encoding="utf-8")
    workbench_source = (
        TENDER_ECONOMICS_WORKBENCH_SOURCE.read_text(encoding="utf-8")
        if TENDER_ECONOMICS_WORKBENCH_SOURCE.exists()
        else ""
    )
    profile_workspace_source = (
        TENDER_ECONOMICS_PROFILE_WORKSPACE_SOURCE.read_text(encoding="utf-8")
        if TENDER_ECONOMICS_PROFILE_WORKSPACE_SOURCE.exists()
        else ""
    )
    source = (
        TENDER_ECONOMICS_SUPPLIERS_SOURCE.read_text(encoding="utf-8")
        if TENDER_ECONOMICS_SUPPLIERS_SOURCE.exists()
        else ""
    )
    discovery_source = (
        TENDER_ECONOMICS_SUPPLIER_DISCOVERY_SOURCE.read_text(encoding="utf-8")
        if TENDER_ECONOMICS_SUPPLIER_DISCOVERY_SOURCE.exists()
        else ""
    )
    options_source = (
        TENDER_ECONOMICS_SUPPLIER_OPTIONS_SOURCE.read_text(encoding="utf-8")
        if TENDER_ECONOMICS_SUPPLIER_OPTIONS_SOURCE.exists()
        else ""
    )
    forms_source = TENDER_ECONOMICS_FORMS_SOURCE.read_text(encoding="utf-8") if TENDER_ECONOMICS_FORMS_SOURCE.exists() else ""
    cost_form_source = TENDER_ECONOMICS_COST_FORM_SOURCE.read_text(encoding="utf-8") if TENDER_ECONOMICS_COST_FORM_SOURCE.exists() else ""
    api_source = API_SOURCE.read_text(encoding="utf-8")
    formatter_source = FORMATTERS_SOURCE.read_text(encoding="utf-8")
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "from './TenderEconomicsSuppliers'" not in tab_source
    assert "from './TenderEconomicsSuppliers'" not in workbench_source
    assert "from './TenderEconomicsSuppliers'" in profile_workspace_source
    assert "from './TenderEconomicsSupplierOptions'" in source
    assert "from './TenderEconomicsSupplierDiscovery'" in profile_workspace_source
    assert "from './TenderEconomicsSupplierDiscovery'" not in source
    assert "from './TenderEconomicsSupplierInputForm'" not in source
    assert "export function ProductSupplierOptionsForm" in source
    assert "function ProductSupplierOptionsForm" not in tab_source
    assert "<ProductSupplierOptionsForm" in profile_workspace_source
    assert "selectSupplierOption" in details_source
    assert "autoSelectSupplierOption" in details_source
    assert "err.payload?.product_profiles" in hook_source
    assert "applyProductTenderState(err.payload, { resetSelection: false })" in hook_source
    assert "onSupplierOptionSelect" in tab_source
    assert "onSupplierOptionAutoSelect" in tab_source
    assert "product-profiles/${profile.position_index}" in api_source
    assert "${productProfilePath(tender, profile)}/supplier-options" in api_source
    assert "${productProfilePath(tender, profile)}/supplier-options/${optionIndex}/select" in api_source
    assert "supplier-options/best/select" in api_source
    assert "supplier-search/prepare" in api_source
    assert "supplier-discovery/run" in api_source
    assert "supplier-discovery/url" in api_source
    assert "runProfileSupplierUrlDiscovery" in api_source
    assert "export function stageProfileSupplierDiscoveryCandidates" in api_source
    assert "stageProfileSupplierDiscoveryCandidates as stageProfileSupplierDiscoveryCandidatesRequest" in hook_source
    assert "stageSupplierManualPriceCandidate" in hook_source
    assert "onSupplierManualPriceStage: stageSupplierManualPriceCandidate" in details_source
    assert "supplier-discovery/candidates/${candidateIndex}/import" in api_source
    assert "price-candidates/${candidateId}/confirm" in api_source
    assert "price-candidates/${candidateId}/reject" in api_source
    assert "confirmProfilePriceCandidate" in hook_source
    assert "rejectProfilePriceCandidate" in hook_source
    assert "onPriceCandidateConfirm" in profile_workspace_source
    assert "onPriceCandidateReject" in profile_workspace_source
    assert "onSupplierSearchPrepare" in tab_source
    assert "onSupplierDiscoveryRun" in tab_source
    assert "onSupplierUrlDiscoveryRun" in tab_source
    assert "onSupplierDiscoveryImport" in tab_source
    assert "onSupplierManualPriceStage" in tab_source
    assert "onSupplierSearchPrepare" in workbench_source
    assert "onSupplierDiscoveryRun" in workbench_source
    assert "onSupplierUrlDiscoveryRun" in workbench_source
    assert "onSupplierDiscoveryImport" in workbench_source
    assert "onSupplierManualPriceStage" in workbench_source
    assert "ManualSupplierPricePanel" in profile_workspace_source
    assert "manualPriceMode" in profile_workspace_source
    assert "supplier-manual-mode-tabs" in profile_workspace_source
    assert "manual-url-result" in profile_workspace_source
    assert "manualUrlResultFromTender" in profile_workspace_source
    assert "manualUrlResultFromTender(error?.payload" in profile_workspace_source
    assert "SupplierSearchPreview" in profile_workspace_source
    assert "SupplierDiscoveryPreview" in profile_workspace_source
    assert "compact={manualPriceMode === 'links'}" in profile_workspace_source
    assert "diagnosticsOpen={false}" in profile_workspace_source
    assert "manual-product-url-input" in profile_workspace_source
    assert "manual-price-source-select" in profile_workspace_source
    assert "manual-price-unit-input" in profile_workspace_source
    assert "onSupplierUrlDiscoveryRun?.(selectedEconomicsProfile, {" in profile_workspace_source
    assert "onSupplierManualPriceStage?.(selectedEconomicsProfile, candidate)" in profile_workspace_source
    assert "onSupplierDiscoveryImport?.(selectedEconomicsProfile, candidateIndex)" in profile_workspace_source
    assert "Ссылка, КП/прайс или быстрые ссылки" in profile_workspace_source
    assert "supplier-manual-price-panel" in styles_source
    assert "supplier-manual-mode-tabs" in styles_source
    assert "supplier-manual-result" in styles_source
    assert "price_candidates" in source
    assert "PriceCandidateQueue" in source
    assert "tenderReferenceUnitPrice(profile)" in source
    assert "priceComparisonForUnitPrice(candidateUnitPrice, tenderUnitPrice)" in source
    assert "price-candidate-reference-price" in source
    assert "price-candidate-price-delta" in source
    assert "candidateQueueBuckets" in source
    assert "queuedCandidateCount" in source
    assert "reviewStatus !== 'pending'" in source
    assert "showSupplierOptions" in source
    assert "PriceCandidatesEmptyState" in source
    assert "ссылку на товар" in source
    assert "прайса/КП" in source
    assert "formatSupplierStock(candidate)" in source
    assert "formatSupplierStock(option)" in options_source
    assert "candidate.score" in source
    assert "` · оценка ${candidate.score}`" in source
    assert "` · score ${candidate.score}`" not in source
    assert "formatSourceKindLabel" in source
    assert "Цена за единицу" in source
    assert "Прайс" in source
    assert "candidate match reasons" not in source
    assert "candidate.quality_status" in source
    assert "candidate.quality_flags" in source
    assert "candidate.match_reasons" in source
    assert "candidate.raw_payload?.match_reasons" in source
    assert "priceCandidateReasonLabel" in source
    assert "price-candidate-reasons" in source
    assert "priceCandidateQualityLabel" in source
    assert "готова к расчету" in source
    assert "не брать автоматически" in source
    assert "Принять цену" in source
    assert "Отклонить" in source
    assert "supplier_options" in source
    assert "SupplierOptionsList" in source
    assert "searching: 'Поиск'" in formatter_source
    assert "supplier_search" not in source
    assert "supplier_discovery" not in source
    assert "SupplierSearchPreview" not in source
    assert "SupplierInputForm" not in source
    assert "SupplierDiscoveryPreview" not in source
    assert "export function SupplierSearchPreview" in discovery_source
    assert "export function SupplierDiscoveryPreview" in discovery_source
    assert "function SupplierDiscoveryDiagnostics" in discovery_source
    assert "supplierDiscoveryNoCandidateHint" in discovery_source
    assert "technical-discovery-details" in discovery_source
    assert "diagnosticsOpen" in discovery_source
    assert "discovery?.status === 'no_candidates'" in discovery_source
    assert "Кандидаты не найдены" in discovery_source
    assert "Цена не прочиталась автоматически" in discovery_source
    assert "Сайт поставщика заблокировал автоматическую проверку" in discovery_source
    assert "Страница прочиталась, но товар не совпал с позицией" in discovery_source
    assert "candidates.length > 0" in discovery_source
    assert "collector_diagnostics" in discovery_source
    assert "diagnostics.pages_fetched" in discovery_source
    assert "diagnostics.candidates_found" in discovery_source
    assert "diagnostics.links_skipped" in discovery_source
    assert "diagnostics.errors" in discovery_source
    assert "diagnostics.intent_rejection_reasons" in discovery_source
    assert "formatIntentRejectionReason" in discovery_source
    assert "supplier-discovery-rejection-reasons" in discovery_source
    assert "compactDiscoveryErrors(errors)" in discovery_source
    assert "formatDiscoveryError(error)" in discovery_source
    assert "Сайт требует браузерную проверку" in discovery_source
    assert "Добавь ссылку на товар вручную" in discovery_source
    assert "errors.join(' · ')" not in discovery_source
    assert "supplierConfidenceLabel(candidate.confidence)" in discovery_source
    assert "candidate.provider" in discovery_source
    assert "confidence_reasons" in discovery_source
    assert "quick_links" in discovery_source
    assert "supplier-search-links" in discovery_source
    assert "uniqueCatalogSearchLinks(queries)" in discovery_source
    assert "Ручная проверка по каталогам" in discovery_source
    assert "catalogSearchLinks.map" in discovery_source
    assert "href={link.url}" in discovery_source
    assert "review_status" in discovery_source
    assert "economics_price_source" in cost_form_source
    assert "EconomicsPriceSource" in cost_form_source
    assert "unit_price" in cost_form_source
    assert 'name="unit_price"' not in cost_form_source
    assert "updateField('unit_price'" not in cost_form_source
    assert "values.unit_price" not in cost_form_source
    assert "export function SupplierOptionsList" in options_source
    assert "supplier-options-list" in options_source
    assert "supplier-option-row" in options_source
    assert "supplier-select-button" in options_source
    assert "formatMoney(option.unit_price)" in options_source
    assert "supplierAvailabilityLabel(option.availability)" in options_source
    assert "supplierStatusLabel(option.status)" in options_source
    assert "option.status === 'selected'" in options_source
    assert "onSelect?.(index)" in options_source
    assert "Источник цены" in cost_form_source
    assert "В расчет" in options_source
    assert "selected: 'в расчете'" in formatter_source
    assert ".supplier-search-preview" in styles_source
    assert ".supplier-search-links" in styles_source
    assert ".supplier-discovery-preview" in styles_source
    assert ".price-candidates-list" in styles_source
    assert ".price-candidate-row" in styles_source
    assert ".price-candidate-reference-price" in styles_source
    assert ".price-candidate-price-delta" in styles_source
    assert ".price-candidate-reasons" in styles_source
    assert ".supplier-search-catalog-links" in styles_source
    assert ".supplier-discovery-diagnostics" in styles_source
    assert ".supplier-discovery-metrics" in styles_source
    assert ".supplier-discovery-rejection-reasons" in styles_source
    assert find_mojibake(details_source, TENDER_DETAILS_SOURCE) == []
    assert find_mojibake(tabs_source, TENDER_DETAILS_TABS_SOURCE) == []
    assert find_mojibake(workspaces_source, TENDER_WORKSPACES_SOURCE) == []
    assert find_mojibake(hook_source, USE_TENDER_PRODUCT_PROFILES_SOURCE) == []
    assert find_mojibake(tab_source, TENDER_ECONOMICS_TAB_SOURCE) == []
    assert find_mojibake(workbench_source, TENDER_ECONOMICS_WORKBENCH_SOURCE) == []
    assert find_mojibake(source, TENDER_ECONOMICS_SUPPLIERS_SOURCE) == []
    assert find_mojibake(discovery_source, TENDER_ECONOMICS_SUPPLIER_DISCOVERY_SOURCE) == []
    assert find_mojibake(options_source, TENDER_ECONOMICS_SUPPLIER_OPTIONS_SOURCE) == []
    assert find_mojibake(forms_source, TENDER_ECONOMICS_FORMS_SOURCE) == []
    assert find_mojibake(cost_form_source, TENDER_ECONOMICS_COST_FORM_SOURCE) == []
    assert find_mojibake(styles_source, STYLES_SOURCE) == []


def test_supplier_catalog_health_stays_on_dashboard_not_economics():
    app_source = APP_SOURCE.read_text(encoding="utf-8")
    details_source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
    workspaces_source = TENDER_WORKSPACES_SOURCE.read_text(encoding="utf-8")
    hook_source = USE_TENDER_PRODUCT_PROFILES_SOURCE.read_text(encoding="utf-8")
    tab_source = TENDER_ECONOMICS_TAB_SOURCE.read_text(encoding="utf-8")
    source = TENDER_ECONOMICS_SUPPLIERS_SOURCE.read_text(encoding="utf-8")
    dashboard_source = DASHBOARD_SOURCE.read_text(encoding="utf-8")
    api_source = API_SOURCE.read_text(encoding="utf-8")
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "export function fetchSupplierCatalogHealth" in api_source
    assert "function loadSupplierCatalogHealth" in app_source
    assert "supplierCatalogHealth={supplierCatalogHealth}" in app_source
    assert "function SupplierCatalogStatusPanel" in dashboard_source
    assert "supplier-catalog-dashboard" in dashboard_source
    assert "catalog.connection_state" in dashboard_source
    assert "supplierCatalogHealth" not in hook_source
    assert "refreshSupplierCatalogHealth" not in hook_source
    assert "onSupplierCatalogHealthRefresh" not in details_source
    assert "onSupplierCatalogHealthRefresh" not in workspaces_source
    assert "supplierCatalogHealth" not in workspaces_source
    assert "supplierCatalogHealth" not in tab_source
    assert "supplierCatalogHealth" not in source
    assert "supplier-catalog-health" not in styles_source
    assert "supplier-catalog-presets" not in styles_source
    assert find_mojibake(app_source, APP_SOURCE) == []
    assert find_mojibake(details_source, TENDER_DETAILS_SOURCE) == []
    assert find_mojibake(workspaces_source, TENDER_WORKSPACES_SOURCE) == []
    assert find_mojibake(hook_source, USE_TENDER_PRODUCT_PROFILES_SOURCE) == []
    assert find_mojibake(tab_source, TENDER_ECONOMICS_TAB_SOURCE) == []
    assert find_mojibake(source, TENDER_ECONOMICS_SUPPLIERS_SOURCE) == []
    assert find_mojibake(dashboard_source, DASHBOARD_SOURCE) == []
    assert find_mojibake(api_source, API_SOURCE) == []
    assert find_mojibake(styles_source, STYLES_SOURCE) == []


def test_economics_tab_renders_auto_estimate_panel():
    details_source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
    tab_source = TENDER_ECONOMICS_TAB_SOURCE.read_text(encoding="utf-8")
    workbench_source = (
        TENDER_ECONOMICS_WORKBENCH_SOURCE.read_text(encoding="utf-8")
        if TENDER_ECONOMICS_WORKBENCH_SOURCE.exists()
        else ""
    )
    profile_workspace_source = (
        TENDER_ECONOMICS_PROFILE_WORKSPACE_SOURCE.read_text(encoding="utf-8")
        if TENDER_ECONOMICS_PROFILE_WORKSPACE_SOURCE.exists()
        else ""
    )
    source = (
        TENDER_ECONOMICS_AUTO_SOURCE.read_text(encoding="utf-8")
        if TENDER_ECONOMICS_AUTO_SOURCE.exists()
        else ""
    )
    api_source = API_SOURCE.read_text(encoding="utf-8")
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "runProfileAutoEconomics" in details_source
    assert "acceptProfileAutoEconomics" in details_source
    assert "from './TenderEconomicsAuto'" not in tab_source
    assert "from './TenderEconomicsAuto'" not in workbench_source
    assert "from './TenderEconomicsAuto'" in profile_workspace_source
    assert "onAutoEconomicsRun" in tab_source
    assert "onAutoEconomicsAccept" in tab_source
    assert "ProductAutoEconomicsPanel" in profile_workspace_source
    assert "function ProductAutoEconomicsPanel" not in tab_source
    assert "export function ProductAutoEconomicsPanel" in source
    assert "economics/auto-estimate" in api_source
    assert "economics/auto-estimate/accept" in api_source
    assert "economics_auto" in source
    assert "Авторасчет" in source
    assert "Рассчитать" in source
    assert "Принять в расчет" in source
    assert "заполнит пустые допущения" in source
    assert "Уверенность" in source
    assert "normalizeAutoEconomicsEstimate" in source
    assert "source_position" in source
    assert "Цена поставщика не выбрана" in source
    assert "Открыть товар" in source
    assert ".auto-economics-panel" in styles_source
    assert ".price-source-link" in styles_source
    assert find_mojibake(details_source, TENDER_DETAILS_SOURCE) == []
    assert find_mojibake(tab_source, TENDER_ECONOMICS_TAB_SOURCE) == []
    assert find_mojibake(workbench_source, TENDER_ECONOMICS_WORKBENCH_SOURCE) == []
    assert find_mojibake(profile_workspace_source, TENDER_ECONOMICS_PROFILE_WORKSPACE_SOURCE) == []
    assert find_mojibake(source, TENDER_ECONOMICS_AUTO_SOURCE) == []
    assert find_mojibake(styles_source, STYLES_SOURCE) == []


def test_shared_analysis_list_imports_from_sections_module():
    economics_auto_source = TENDER_ECONOMICS_AUTO_SOURCE.read_text(encoding="utf-8")
    products_source = TENDER_PRODUCTS_TAB_SOURCE.read_text(encoding="utf-8")
    analysis_tab_source = TENDER_ANALYSIS_TAB_SOURCE.read_text(encoding="utf-8")
    analysis_sections_source = TENDER_ANALYSIS_SECTIONS_SOURCE.read_text(encoding="utf-8")

    assert "export function AnalysisList" in analysis_sections_source
    assert "export function AnalysisList" not in analysis_tab_source
    assert "import { AnalysisList } from './TenderAnalysisSections'" in economics_auto_source
    assert "import { AnalysisList } from './TenderAnalysisSections'" in products_source
    assert "import { AnalysisList } from './TenderAnalysisTab'" not in economics_auto_source
    assert "import { AnalysisList } from './TenderAnalysisTab'" not in products_source


def test_economics_tab_renders_assumptions_form():
    details_source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
    tab_source = TENDER_ECONOMICS_TAB_SOURCE.read_text(encoding="utf-8")
    source = TENDER_ECONOMICS_FORMS_SOURCE.read_text(encoding="utf-8") if TENDER_ECONOMICS_FORMS_SOURCE.exists() else ""
    api_source = API_SOURCE.read_text(encoding="utf-8")
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "saveProfileEconomicsAssumptions" in details_source
    assert "onEconomicsAssumptionsSave" in tab_source
    assert "ProductEconomicsAssumptionsForm" in source
    assert "function ProductEconomicsAssumptionsForm" not in tab_source
    assert "economics/assumptions" in api_source
    assert "economics_assumptions" in source
    assert "vat_mode" in source
    assert "risk_reserve_percent" in source
    assert "target_margin_percent" in source
    assert "Допущения" in source
    assert "НДС" in source
    assert "Целевая маржа" in source
    assert ".economics-assumptions-form" in styles_source
    assert find_mojibake(details_source, TENDER_DETAILS_SOURCE) == []
    assert find_mojibake(tab_source, TENDER_ECONOMICS_TAB_SOURCE) == []
    assert find_mojibake(source, TENDER_ECONOMICS_FORMS_SOURCE) == []
    assert find_mojibake(styles_source, STYLES_SOURCE) == []

def test_economics_tab_renders_bid_scenarios():
    source = TENDER_ECONOMICS_SUMMARY_SOURCE.read_text(encoding="utf-8")
    scenarios_source = (
        TENDER_ECONOMICS_DECISION_SCENARIOS_SOURCE.read_text(encoding="utf-8")
        if TENDER_ECONOMICS_DECISION_SCENARIOS_SOURCE.exists()
        else ""
    )
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "from './TenderEconomicsDecisionScenarios'" in source
    assert "BidScenarioStrip" in source
    assert "economics.bid_scenarios" in source
    assert "function BidScenarioStrip" not in source
    assert "export function BidScenarioStrip" in scenarios_source
    assert "Сценарии цены" in scenarios_source
    assert "bid-scenario-grid" in scenarios_source
    assert ".bid-scenario-grid" in styles_source
    assert find_mojibake(source, TENDER_ECONOMICS_SUMMARY_SOURCE) == []
    assert find_mojibake(scenarios_source, TENDER_ECONOMICS_DECISION_SCENARIOS_SOURCE) == []
    assert find_mojibake(styles_source, STYLES_SOURCE) == []


def test_economics_summary_renders_price_passport_and_unit_normalization():
    source = TENDER_ECONOMICS_SUMMARY_SOURCE.read_text(encoding="utf-8")
    scenarios_source = (
        TENDER_ECONOMICS_DECISION_SCENARIOS_SOURCE.read_text(encoding="utf-8")
        if TENDER_ECONOMICS_DECISION_SCENARIOS_SOURCE.exists()
        else ""
    )
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "item.price_passport" in source
    assert "item.unit_normalization" in source
    assert "formatPricePassport" in source
    assert "formatUnitNormalization" in source
    assert "scenario.profit" in scenarios_source
    assert "scenario.role" in scenarios_source
    assert "scenario.is_current" in scenarios_source
    assert ".economics-item-passport" in styles_source
    assert ".bid-scenario.current" in styles_source
    assert find_mojibake(source, TENDER_ECONOMICS_SUMMARY_SOURCE) == []
    assert find_mojibake(scenarios_source, TENDER_ECONOMICS_DECISION_SCENARIOS_SOURCE) == []
    assert find_mojibake(styles_source, STYLES_SOURCE) == []


def test_economics_tab_renders_participation_decision():
    source = TENDER_ECONOMICS_SUMMARY_SOURCE.read_text(encoding="utf-8")
    scenarios_source = (
        TENDER_ECONOMICS_DECISION_SCENARIOS_SOURCE.read_text(encoding="utf-8")
        if TENDER_ECONOMICS_DECISION_SCENARIOS_SOURCE.exists()
        else ""
    )
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "from './TenderEconomicsDecisionScenarios'" in source
    assert "ParticipationDecisionCard" in source
    assert "ParticipationCalculationCard" in source
    assert "economics.participation_decision" in source
    assert "economics.participation_calculation" in source
    assert "function ParticipationDecisionCard" not in source
    assert "function ParticipationCalculationCard" not in source
    assert "export function ParticipationDecisionCard" in scenarios_source
    assert "export function ParticipationCalculationCard" in scenarios_source
    assert "Решение по участию" in scenarios_source
    assert "Расчет участия" in scenarios_source
    assert "Стоп-цена" in scenarios_source
    assert "Лимит" in scenarios_source
    assert "participation-decision" in scenarios_source
    assert "participation-calculation-card" in scenarios_source
    assert ".participation-decision" in styles_source
    assert ".participation-calculation-card" in styles_source
    assert find_mojibake(source, TENDER_ECONOMICS_SUMMARY_SOURCE) == []
    assert find_mojibake(scenarios_source, TENDER_ECONOMICS_DECISION_SCENARIOS_SOURCE) == []
    assert find_mojibake(styles_source, STYLES_SOURCE) == []

def test_economics_tab_owns_product_costs_and_suppliers():
    workspaces_source = TENDER_WORKSPACES_SOURCE.read_text(encoding="utf-8")
    tab_source = TENDER_ECONOMICS_TAB_SOURCE.read_text(encoding="utf-8")
    app_source = (
        TENDER_ECONOMICS_WORKBENCH_SOURCE.read_text(encoding="utf-8")
        if TENDER_ECONOMICS_WORKBENCH_SOURCE.exists()
        else ""
    )
    profile_workspace_source = (
        TENDER_ECONOMICS_PROFILE_WORKSPACE_SOURCE.read_text(encoding="utf-8")
        if TENDER_ECONOMICS_PROFILE_WORKSPACE_SOURCE.exists()
        else ""
    )
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "export function TenderEconomicsTab({" in tab_source
    assert "from './TenderEconomicsWorkbench'" in tab_source
    assert "productProfiles" in tab_source
    assert "selectedEconomicsProfileIndex" in tab_source
    assert "['quantity', 'unit', 'unit_price', 'total_price']" in tab_source
    assert "export function TenderEconomicsWorkbench({" in app_source
    assert "export function TenderEconomicsProfileWorkspace({" in profile_workspace_source
    assert "formatPositionTenderPrice(selectedEconomicsProfile)" in profile_workspace_source
    assert "tenderReferenceUnitPrice" in profile_workspace_source
    assert "tenderReferenceTotalPrice" in profile_workspace_source
    assert "<ProductEconomicsForm profile={selectedEconomicsProfile}" in profile_workspace_source
    assert "<ProductSupplierOptionsForm" in profile_workspace_source
    assert "profile={selectedEconomicsProfile}" in profile_workspace_source
    assert "<TenderEconomicsTab" in workspaces_source
    assert "economics-workbench" in app_source
    assert ".economics-workbench" in styles_source
    assert find_mojibake(workspaces_source, TENDER_WORKSPACES_SOURCE) == []
    assert find_mojibake(tab_source, TENDER_ECONOMICS_TAB_SOURCE) == []
    assert find_mojibake(app_source, TENDER_ECONOMICS_WORKBENCH_SOURCE) == []
    assert find_mojibake(profile_workspace_source, TENDER_ECONOMICS_PROFILE_WORKSPACE_SOURCE) == []
    assert find_mojibake(styles_source, STYLES_SOURCE) == []

def test_economics_tab_is_a_focused_workbench():
    tab_source = TENDER_ECONOMICS_TAB_SOURCE.read_text(encoding="utf-8")
    metrics_source = TENDER_ECONOMICS_METRICS_SOURCE.read_text(encoding="utf-8")
    summary_source = TENDER_ECONOMICS_SUMMARY_SOURCE.read_text(encoding="utf-8")
    workbench_source = TENDER_ECONOMICS_WORKBENCH_SOURCE.read_text(encoding="utf-8")
    profile_workspace_source = TENDER_ECONOMICS_PROFILE_WORKSPACE_SOURCE.read_text(encoding="utf-8")
    suppliers_source = TENDER_ECONOMICS_SUPPLIERS_SOURCE.read_text(encoding="utf-8")
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "economics-command-center" in tab_source
    assert "economics-command-actions" in tab_source
    assert "<TenderEconomicsMetrics tender={tender} economics={economics} profiles={profiles} />" in tab_source
    assert tab_source.index("<TenderEconomicsWorkbench") < tab_source.index("<EconomicsSummary economics={economics} tender={tender} profiles={profiles} />")
    assert "readinessStats(profiles)" in metrics_source
    assert "SummaryMetric value={`${readyPositions}/${totalPositions}`}" in metrics_source
    assert "label=\"цены\"" in metrics_source
    assert "label=\"кандидаты\"" in metrics_source
    assert "economics-analysis-drawer" in summary_source
    assert "<summary>" in summary_source
    assert "analysisCostDrivers.length" in summary_source
    assert "economics-workspace-shell" in workbench_source
    assert "economics-workbench-main" in profile_workspace_source
    assert "economics-center-calculation" in profile_workspace_source
    assert "economics-position-card" in profile_workspace_source
    assert "economics-side-panel" not in profile_workspace_source
    assert "economics-side-section" not in profile_workspace_source
    assert "supplier-tools-drawer" not in suppliers_source
    assert ".economics-command-center" in styles_source
    assert ".economics-workspace-shell" in styles_source
    assert ".economics-workbench-main" in styles_source
    assert ".economics-center-calculation" in styles_source
    assert ".economics-analysis-drawer" in styles_source
    assert ".supplier-tools-drawer" not in styles_source
    assert find_mojibake(tab_source, TENDER_ECONOMICS_TAB_SOURCE) == []
    assert find_mojibake(metrics_source, TENDER_ECONOMICS_METRICS_SOURCE) == []
    assert find_mojibake(summary_source, TENDER_ECONOMICS_SUMMARY_SOURCE) == []
    assert find_mojibake(workbench_source, TENDER_ECONOMICS_WORKBENCH_SOURCE) == []
    assert find_mojibake(profile_workspace_source, TENDER_ECONOMICS_PROFILE_WORKSPACE_SOURCE) == []
    assert find_mojibake(suppliers_source, TENDER_ECONOMICS_SUPPLIERS_SOURCE) == []
    assert find_mojibake(styles_source, STYLES_SOURCE) == []

def test_economics_position_workspace_exposes_unified_position_scenario():
    profile_workspace_source = TENDER_ECONOMICS_PROFILE_WORKSPACE_SOURCE.read_text(encoding="utf-8")
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "const POSITION_SCENARIO_STEPS" in profile_workspace_source
    assert "function PositionEconomicsScenario" in profile_workspace_source
    assert "<PositionEconomicsScenario" in profile_workspace_source
    assert "buildPositionScenarioState(selectedEconomicsProfile" in profile_workspace_source
    assert "pendingPriceCandidatesForProfile(profile)" in profile_workspace_source
    assert "selectedSupplierOptionForProfile(profile)" in profile_workspace_source
    assert "hasPositionEconomicsDraft(profile," in profile_workspace_source
    assert "Нужна цена" in profile_workspace_source
    assert "Проверить кандидата" in profile_workspace_source
    assert "Принять цену" in profile_workspace_source
    assert "Рассчитать" in profile_workspace_source
    assert "Решение" in profile_workspace_source
    assert "Осталось собрать полную себестоимость." in profile_workspace_source
    assert "Нужна проверка цены" in profile_workspace_source
    assert "прайс" in profile_workspace_source
    assert "position-economics-scenario" in profile_workspace_source
    assert "position-scenario-steps" in profile_workspace_source
    assert "position-scenario-cta" in profile_workspace_source
    assert ".position-economics-scenario" in styles_source
    assert ".position-scenario-steps" in styles_source
    assert ".position-scenario-step" in styles_source
    assert ".position-scenario-cta" in styles_source
    assert find_mojibake(profile_workspace_source, TENDER_ECONOMICS_PROFILE_WORKSPACE_SOURCE) == []
    assert find_mojibake(styles_source, STYLES_SOURCE) == []

def test_product_detail_keeps_passport_and_requirements_only():
    app_source = (
        TENDER_PRODUCTS_TAB_SOURCE.read_text(encoding="utf-8")
        if TENDER_PRODUCTS_TAB_SOURCE.exists()
        else ""
    )
    constants_source = CONSTANTS_SOURCE.read_text(encoding="utf-8")

    assert "export const productDetailModes = [" in constants_source
    assert "{ id: 'pricing'" not in app_source
    assert "{ id: 'suppliers'" not in app_source
    assert "activeProfileMode === 'pricing'" not in app_source
    assert "activeProfileMode === 'suppliers'" not in app_source
    assert find_mojibake(app_source, TENDER_PRODUCTS_TAB_SOURCE) == []


def test_tender_workbench_uses_decision_first_summary_shell():
    details_source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
    tabs_source = TENDER_DETAILS_TABS_SOURCE.read_text(encoding="utf-8")
    panels_source = TENDER_TAB_PANELS_SOURCE.read_text(encoding="utf-8")
    ui_source = USE_TENDER_DETAILS_UI_SOURCE.read_text(encoding="utf-8")
    strip_source = (
        TENDER_DECISION_STRIP_SOURCE.read_text(encoding="utf-8")
        if TENDER_DECISION_STRIP_SOURCE.exists()
        else ""
    )
    summary_source = (
        TENDER_SUMMARY_TAB_SOURCE.read_text(encoding="utf-8")
        if TENDER_SUMMARY_TAB_SOURCE.exists()
        else ""
    )
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "from './TenderDecisionStrip'" in details_source
    assert "<TenderDecisionStrip" in details_source
    assert "from './TenderSummaryTab'" in panels_source
    assert "export function TenderSummaryTab" in summary_source
    assert "export function TenderDecisionStrip" in strip_source
    assert "useState('summary')" not in ui_source
    assert "setActiveTab('summary')" not in ui_source
    assert "{ id: 'summary', label: 'Сводка' }" not in tabs_source
    assert "<WorkflowTabPanel" in panels_source
    assert "summary-decision-grid" not in summary_source
    assert "SummaryMetric" not in summary_source
    assert "summary-next-action" in summary_source
    assert "decision-strip-grid" in strip_source
    assert ".decision-strip" in styles_source
    assert ".summary-decision-grid" not in styles_source
    assert find_mojibake(details_source, TENDER_DETAILS_SOURCE) == []
    assert find_mojibake(tabs_source, TENDER_DETAILS_TABS_SOURCE) == []
    assert find_mojibake(strip_source, TENDER_DECISION_STRIP_SOURCE) == []
    assert find_mojibake(summary_source, TENDER_SUMMARY_TAB_SOURCE) == []


def test_tender_workbench_v1_reduces_detail_panel_overload():
    app_source = APP_SOURCE.read_text(encoding="utf-8")
    tender_details_source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
    strip_source = (
        TENDER_DECISION_STRIP_SOURCE.read_text(encoding="utf-8")
        if TENDER_DECISION_STRIP_SOURCE.exists()
        else ""
    )
    summary_source = (
        TENDER_SUMMARY_TAB_SOURCE.read_text(encoding="utf-8")
        if TENDER_SUMMARY_TAB_SOURCE.exists()
        else ""
    )
    economics_source = TENDER_ECONOMICS_TAB_SOURCE.read_text(encoding="utf-8")
    products_source = (
        TENDER_PRODUCTS_TAB_SOURCE.read_text(encoding="utf-8")
        if TENDER_PRODUCTS_TAB_SOURCE.exists()
        else ""
    )
    constants_source = CONSTANTS_SOURCE.read_text(encoding="utf-8")

    assert "workspace tender-list-screen" in app_source
    assert "workspace tender-detail-screen" in app_source
    assert "export function TenderDecisionStrip" in strip_source
    assert "<TenderDecisionStrip" in tender_details_source
    assert "decision-strip-grid" in strip_source
    assert "export function TenderSummaryTab" in summary_source
    assert "summary-decision-grid" not in summary_source
    assert "SummaryMetric" not in summary_source
    assert "product-detail-tabs" in products_source
    assert "export const productDetailModes" in constants_source
    assert "ТЗ" in constants_source
    economics_workbench_source = (
        TENDER_ECONOMICS_WORKBENCH_SOURCE.read_text(encoding="utf-8")
        if TENDER_ECONOMICS_WORKBENCH_SOURCE.exists()
        else ""
    )

    assert "economics-workbench" in economics_workbench_source
    assert find_mojibake(app_source, APP_SOURCE) == []
    assert find_mojibake(tender_details_source, TENDER_DETAILS_SOURCE) == []
    assert find_mojibake(strip_source, TENDER_DECISION_STRIP_SOURCE) == []
    assert find_mojibake(summary_source, TENDER_SUMMARY_TAB_SOURCE) == []
    assert find_mojibake(economics_source, TENDER_ECONOMICS_TAB_SOURCE) == []
    assert find_mojibake(economics_workbench_source, TENDER_ECONOMICS_WORKBENCH_SOURCE) == []
    assert find_mojibake(products_source, TENDER_PRODUCTS_TAB_SOURCE) == []

def test_tender_workbench_has_top_filters_and_list_first_layout():
    app_source = APP_SOURCE.read_text(encoding="utf-8")
    filters_source = FILTERS_PANEL_SOURCE.read_text(encoding="utf-8")
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "const [filtersCollapsed, setFiltersCollapsed]" in app_source
    assert "onToggleCollapsed={() => setFiltersCollapsed" in app_source
    assert "onToggleMultiFilter" not in app_source
    assert "variant=\"top\"" in app_source
    assert "top-filters-panel" in filters_source
    assert "top-filter-form" in filters_source
    assert "is-collapsed" in filters_source
    assert "aria-expanded={!collapsed}" in filters_source
    assert "filter-collapse-button" not in filters_source
    assert ".tender-list-screen" in styles_source
    assert ".tender-detail-screen" in styles_source
    assert ".top-filters-panel" in styles_source
    assert ".top-filters-panel.is-collapsed" in styles_source
    assert "grid-template-columns: minmax(220px, 1.2fr) repeat(6, minmax(112px, 0.62fr)) minmax(200px, 0.8fr) auto" in styles_source
    assert "overflow-x: hidden" in styles_source
    assert find_mojibake(app_source, APP_SOURCE) == []
    assert find_mojibake(filters_source, FILTERS_PANEL_SOURCE) == []
    assert find_mojibake(styles_source, STYLES_SOURCE) == []


def test_tender_details_v2_keeps_actions_and_document_statuses_scannable():
    app_source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
    header_source = TENDER_DETAILS_HEADER_SOURCE.read_text(encoding="utf-8")
    actions_source = (
        TENDER_DETAIL_ACTIONS_SOURCE.read_text(encoding="utf-8")
        if TENDER_DETAIL_ACTIONS_SOURCE.exists()
        else ""
    )
    analysis_documents_source = TENDER_ANALYSIS_DOCUMENTS_SOURCE.read_text(encoding="utf-8")
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")
    detail_actions_rule = _css_rule(styles_source, ".detail-actions")

    assert "details-title-row" in header_source
    assert "<TenderDetailActions" in app_source
    assert "details-action-group primary-actions" in actions_source
    assert "details-action-group secondary-actions" not in actions_source
    assert "documentStatusLabel" in analysis_documents_source
    assert "document-status ${document.text_status || 'pending'}" in analysis_documents_source
    assert "download-status ${document.local_path ? 'downloaded' : 'missing'}" in analysis_documents_source
    assert "grid-template-columns: repeat(4" not in detail_actions_rule
    assert ("flex-wrap: wrap" in detail_actions_rule or "auto-fit" in detail_actions_rule)
    assert ".detail-workspace-launchers" not in styles_source
    assert ".document-status.unsupported" in styles_source
    assert ".document-status.ok" in styles_source
    assert find_mojibake(app_source, TENDER_DETAILS_SOURCE) == []
    assert find_mojibake(header_source, TENDER_DETAILS_HEADER_SOURCE) == []
    assert find_mojibake(actions_source, TENDER_DETAIL_ACTIONS_SOURCE) == []
    assert find_mojibake(analysis_documents_source, TENDER_ANALYSIS_DOCUMENTS_SOURCE) == []
    assert find_mojibake(styles_source, STYLES_SOURCE) == []


def test_tender_detail_tabs_have_scannable_work_areas():
    panels_source = TENDER_TAB_PANELS_SOURCE.read_text(encoding="utf-8")
    workspaces_source = TENDER_WORKSPACES_SOURCE.read_text(encoding="utf-8")
    summary_source = TENDER_SUMMARY_TAB_SOURCE.read_text(encoding="utf-8")
    analysis_source = TENDER_ANALYSIS_TAB_SOURCE.read_text(encoding="utf-8")
    analysis_documents_source = TENDER_ANALYSIS_DOCUMENTS_SOURCE.read_text(encoding="utf-8")
    products_source = (
        TENDER_PRODUCTS_TAB_SOURCE.read_text(encoding="utf-8")
        if TENDER_PRODUCTS_TAB_SOURCE.exists()
        else ""
    )
    formatter_source = FORMATTERS_SOURCE.read_text(encoding="utf-8")
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "export function TenderSummaryTab" in summary_source
    assert "function ProductTabSummary" in products_source
    assert "function DocumentStatusSummary" in analysis_documents_source
    assert "export function documentStatusCounts" in formatter_source
    assert "<TenderSummaryTab" in panels_source
    assert "<TenderProductsTab" in workspaces_source
    assert "<ProductTabSummary" in products_source
    assert "<AnalysisDocumentsPanel" in analysis_source
    assert "<TenderDocumentsTab" not in workspaces_source
    assert "summary-decision-grid" not in summary_source
    assert "SummaryMetric" not in summary_source
    assert "summary-work-grid" in summary_source
    assert "document-status-summary" in analysis_documents_source
    assert "product-tab-summary" in products_source
    assert ".summary-decision-grid" not in styles_source
    assert ".summary-work-grid" in styles_source
    assert ".document-status-summary" in styles_source
    assert ".product-tab-summary" in styles_source
    assert find_mojibake(panels_source, TENDER_TAB_PANELS_SOURCE) == []
    assert find_mojibake(workspaces_source, TENDER_WORKSPACES_SOURCE) == []
    assert find_mojibake(summary_source, TENDER_SUMMARY_TAB_SOURCE) == []
    assert find_mojibake(analysis_source, TENDER_ANALYSIS_TAB_SOURCE) == []
    assert find_mojibake(analysis_documents_source, TENDER_ANALYSIS_DOCUMENTS_SOURCE) == []
    assert find_mojibake(products_source, TENDER_PRODUCTS_TAB_SOURCE) == []
    assert find_mojibake(styles_source, STYLES_SOURCE) == []


def test_analysis_tab_exposes_word_report_and_source_evidence_workspace():
    workspaces_source = TENDER_WORKSPACES_SOURCE.read_text(encoding="utf-8")
    analysis_source = TENDER_ANALYSIS_TAB_SOURCE.read_text(encoding="utf-8")
    analysis_documents_source = TENDER_ANALYSIS_DOCUMENTS_SOURCE.read_text(encoding="utf-8")
    analysis_sections_source = TENDER_ANALYSIS_SECTIONS_SOURCE.read_text(encoding="utf-8")
    analysis_evidence_source = TENDER_ANALYSIS_EVIDENCE_SOURCE.read_text(encoding="utf-8")
    analysis_evidence_model_source = TENDER_ANALYSIS_EVIDENCE_MODEL_SOURCE.read_text(encoding="utf-8")
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "reportHref" in workspaces_source
    assert "documents={documentRecords}" in workspaces_source
    assert "analysis-action-row" in analysis_source
    assert "Скачать отчет" in analysis_source
    assert "Проанализировать" not in analysis_source
    assert "onClick={onAnalyze}" not in analysis_source
    assert "onDownload={onDownload}" in analysis_source
    assert "onExtract={onExtract}" in analysis_source
    assert "downloadStatusLabel" not in analysis_source
    assert "Скачать документы" in analysis_documents_source
    assert "Извлечь текст" in analysis_documents_source
    assert "analysis-workspace" in analysis_source
    assert "analysis-section-rail" in analysis_sections_source
    assert "const [selectedAnalysisSection, setSelectedAnalysisSection]" in analysis_source
    assert "analysisSectionItems(analysis, documents)" in analysis_source
    assert "<AnalysisSectionRail" not in analysis_source
    assert "sections={analysisSections}" in analysis_source
    assert "onSelectSection={selectAnalysisSection}" in analysis_source
    assert "<AnalysisSectionBody" in analysis_source
    assert "TenderAnalysisEvidencePanel" not in analysis_source
    assert "<AnalysisEvidencePanel" not in analysis_source
    assert "sections.map" in analysis_sections_source
    assert "onClick={() => onSelectSection(section.id)}" in analysis_sections_source
    assert "aria-pressed={active}" in analysis_sections_source
    assert "analysis-evidence-panel" not in analysis_source
    assert "from './TenderAnalysisEvidenceModel'" in analysis_evidence_source
    assert "from './TenderAnalysisEvidenceModel'" not in analysis_sections_source
    assert "MAJOR_ANALYSIS_SECTIONS" in analysis_sections_source
    assert "export function buildDocumentEvidenceItems" in analysis_evidence_model_source
    assert ".analysis-workspace" in styles_source
    assert "grid-template-columns: 1fr" in styles_source
    assert ".analysis-section-item:hover" in styles_source
    assert find_mojibake(workspaces_source, TENDER_WORKSPACES_SOURCE) == []
    assert find_mojibake(analysis_source, TENDER_ANALYSIS_TAB_SOURCE) == []
    assert find_mojibake(analysis_documents_source, TENDER_ANALYSIS_DOCUMENTS_SOURCE) == []
    assert find_mojibake(analysis_sections_source, TENDER_ANALYSIS_SECTIONS_SOURCE) == []
    assert find_mojibake(analysis_evidence_source, TENDER_ANALYSIS_EVIDENCE_SOURCE) == []
    assert find_mojibake(analysis_evidence_model_source, TENDER_ANALYSIS_EVIDENCE_MODEL_SOURCE) == []
    assert find_mojibake(styles_source, STYLES_SOURCE) == []


def test_analysis_tab_renders_decision_first_brief():
    analysis_source = TENDER_ANALYSIS_TAB_SOURCE.read_text(encoding="utf-8")
    decision_source = TENDER_ANALYSIS_DECISION_SOURCE.read_text(encoding="utf-8")
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "from './TenderAnalysisDecisionBrief'" in analysis_source
    assert "<AnalysisDecisionBrief" in analysis_source
    assert "onOpenSection={selectAnalysisSection}" in analysis_source
    assert "export function AnalysisDecisionBrief" in decision_source
    assert "analysis?.operator_view" in decision_source
    assert "operatorView?.decision_brief" in decision_source
    assert "fallbackAnalysisDecision" in decision_source
    assert "analysis-decision-brief" in decision_source
    assert "Короткое решение" in decision_source
    assert "Ключевые причины" in decision_source
    assert "reasons.slice(0, 3)" in decision_source
    assert '<details className="analysis-action-plan">' in decision_source
    assert "<summary>" in decision_source
    assert "analysis-action-plan-list" in decision_source
    assert "analysis-document-state" not in decision_source
    assert "documentState" not in decision_source
    assert "onOpenSection?.(primarySection)" in decision_source
    assert "onOpenSection?.('evidence')" not in decision_source
    assert "'decision_risks'" in decision_source
    assert "'product_compliance'" in decision_source
    assert ".analysis-decision-brief" in styles_source
    assert ".analysis-reason-list" in styles_source
    assert ".analysis-action-plan summary" in styles_source
    assert ".analysis-action-plan-list" in styles_source
    assert ".analysis-document-state" not in styles_source
    assert find_mojibake(analysis_source, TENDER_ANALYSIS_TAB_SOURCE) == []
    assert find_mojibake(decision_source, TENDER_ANALYSIS_DECISION_SOURCE) == []
    assert find_mojibake(styles_source, STYLES_SOURCE) == []


def test_analysis_tab_renders_compact_tz_passport_navigation():
    analysis_source = TENDER_ANALYSIS_TAB_SOURCE.read_text(encoding="utf-8")
    passport_source = TENDER_ANALYSIS_PASSPORT_SOURCE.read_text(encoding="utf-8")
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "from './TenderAnalysisPassport'" in analysis_source
    assert "selectedSection={selectedAnalysisSection}" in analysis_source
    assert "onSelectSection={selectAnalysisSection}" in analysis_source
    assert "sections={analysisSections}" in analysis_source
    assert "<AnalysisSectionRail" not in analysis_source
    decision_index = analysis_source.index("<AnalysisDecisionBrief")
    passport_index = analysis_source.index("<AnalysisPassport")
    workspace_index = analysis_source.index('className="analysis-workspace"')
    assert decision_index < passport_index < workspace_index
    assert "export function AnalysisPassport" in passport_source
    assert "analysis?.tz_passport" in passport_source
    assert "navSections.map(passportSectionNavItem)" in passport_source
    assert "PASSPORT_SECTION_TARGETS" not in passport_source
    assert "onSelectSection?.(item.target)" in passport_source
    assert "analysis-passport" in passport_source
    assert "analysis-passport-nav" in passport_source
    assert "analysis-passport-item" not in passport_source
    assert ".analysis-passport" in styles_source
    assert ".analysis-passport-nav" in styles_source
    assert ".analysis-passport-grid" not in styles_source
    assert find_mojibake(passport_source, TENDER_ANALYSIS_PASSPORT_SOURCE) == []


def test_analysis_tab_keeps_manual_section_selection_after_passport_click():
    analysis_source = TENDER_ANALYSIS_TAB_SOURCE.read_text(encoding="utf-8")

    effect_start = analysis_source.index("useEffect(() => {")
    effect_end = analysis_source.index("}, [analysisSectionKey, primarySection])", effect_start)
    effect_body = analysis_source[effect_start:effect_end]

    assert "const analysisSectionKey = analysisSections.map((section) => section.id).join('|')" in analysis_source
    assert "setSelectedAnalysisSection((currentSection)" in effect_body
    assert "setSelectedAnalysisSection(primarySection)" not in effect_body
    assert "selectedAnalysisSection" not in effect_body


def test_analysis_documents_render_structured_evidence_model():
    sections_source = TENDER_ANALYSIS_SECTIONS_SOURCE.read_text(encoding="utf-8")
    evidence_source = TENDER_ANALYSIS_EVIDENCE_SOURCE.read_text(encoding="utf-8")
    model_source = TENDER_ANALYSIS_EVIDENCE_MODEL_SOURCE.read_text(encoding="utf-8")
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "buildDocumentEvidenceItems(analysis, documents)" not in sections_source
    assert "buildDocumentEvidenceItems(analysis, documents)" in evidence_source
    assert "TenderAnalysisEvidenceModel" not in sections_source
    assert "analysis-source-context" in sections_source
    assert "analysis-source-meta" in sections_source
    assert "analysisSourceBinding(item)" in sections_source
    assert "analysisConfidenceLevel(item)" in sections_source
    assert "analysisEvidenceQuality(item)" in sections_source
    assert "source_binding" in sections_source
    assert "confidence_level" in sections_source
    assert "evidence_quality" in sections_source
    assert "analysis-evidence-quality-" in sections_source
    assert "analysis-evidence-item" in evidence_source
    assert "item.fragment" in sections_source
    assert "item.typeLabel" in evidence_source
    assert "item.importanceLabel" in evidence_source
    assert "item.documentName" in evidence_source
    assert "item.fragment" in evidence_source
    assert "item.impact" in evidence_source
    assert "analysis?.evidence_items" in model_source
    assert "item.type_label" in model_source
    assert "item.importance_label" in model_source
    assert "item.document_name" in model_source
    assert "function evidenceTypeLabel" not in model_source
    assert "function evidenceImportanceLabel" not in model_source
    assert "function evidenceImpactLabel" not in model_source
    assert "function resolveEvidenceDocumentName" not in model_source
    assert ".analysis-document-evidence-grid" in styles_source
    assert ".analysis-evidence-meta" in styles_source
    assert ".analysis-evidence-impact" in styles_source
    assert ".analysis-source-meta" in styles_source
    assert ".analysis-confidence-low" in styles_source
    assert ".analysis-evidence-quality-conflict" in styles_source
    assert ".analysis-evidence-quality-missing" in styles_source
    assert find_mojibake(sections_source, TENDER_ANALYSIS_SECTIONS_SOURCE) == []
    assert find_mojibake(evidence_source, TENDER_ANALYSIS_EVIDENCE_SOURCE) == []
    assert find_mojibake(model_source, TENDER_ANALYSIS_EVIDENCE_MODEL_SOURCE) == []
    assert find_mojibake(styles_source, STYLES_SOURCE) == []


def test_economics_tab_uses_two_column_position_workspace():
    economics_source = TENDER_ECONOMICS_TAB_SOURCE.read_text(encoding="utf-8")
    workbench_source = (
        TENDER_ECONOMICS_WORKBENCH_SOURCE.read_text(encoding="utf-8")
        if TENDER_ECONOMICS_WORKBENCH_SOURCE.exists()
        else ""
    )
    rail_source = (
        TENDER_ECONOMICS_POSITION_RAIL_SOURCE.read_text(encoding="utf-8")
        if TENDER_ECONOMICS_POSITION_RAIL_SOURCE.exists()
        else ""
    )
    profile_workspace_source = (
        TENDER_ECONOMICS_PROFILE_WORKSPACE_SOURCE.read_text(encoding="utf-8")
        if TENDER_ECONOMICS_PROFILE_WORKSPACE_SOURCE.exists()
        else ""
    )
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "from './TenderEconomicsWorkbench'" in economics_source
    assert "economics-workspace-grid" in workbench_source
    assert "from './TenderEconomicsPositionRail'" in workbench_source
    assert "from './TenderEconomicsProfileWorkspace'" in workbench_source
    assert "economics-position-rail" in rail_source
    assert "economics-workbench-main" in profile_workspace_source
    assert "economics-position-card" in profile_workspace_source
    assert "economics-center-calculation" in profile_workspace_source
    assert "economics-side-panel" not in profile_workspace_source
    assert "economics-side-section" not in profile_workspace_source
    assert "<ProductAutoEconomicsPanel" in profile_workspace_source
    assert "<ProductEconomicsForm profile={selectedEconomicsProfile}" in profile_workspace_source
    assert "<ProductEconomicsAssumptionsForm" in profile_workspace_source
    assert "<ProductSupplierOptionsForm" in profile_workspace_source
    assert ".economics-workspace-grid" in styles_source
    assert ".economics-position-rail" in styles_source
    assert ".economics-workbench-main" in styles_source
    assert ".economics-position-card" in styles_source
    assert ".economics-center-calculation" in styles_source
    assert ".economics-workspace-grid {\n  grid-template-columns: minmax(260px, 0.42fr) minmax(0, 1fr)" in styles_source
    assert "minmax(230px, 0.58fr) minmax(360px, 1.18fr) minmax(280px, 0.84fr)" not in styles_source
    assert find_mojibake(economics_source, TENDER_ECONOMICS_TAB_SOURCE) == []
    assert find_mojibake(workbench_source, TENDER_ECONOMICS_WORKBENCH_SOURCE) == []
    assert find_mojibake(rail_source, TENDER_ECONOMICS_POSITION_RAIL_SOURCE) == []
    assert find_mojibake(profile_workspace_source, TENDER_ECONOMICS_PROFILE_WORKSPACE_SOURCE) == []
    assert find_mojibake(styles_source, STYLES_SOURCE) == []


def test_tender_summary_cards_wrap_without_clipping_actions():
    summary_source = TENDER_SUMMARY_TAB_SOURCE.read_text(encoding="utf-8")
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")
    summary_grid_rule = _css_rule(styles_source, ".summary-work-grid")
    primary_card_rule = _css_rule(styles_source, ".summary-card.primary")
    secondary_card_rule = _css_rule(styles_source, ".summary-card.secondary")
    compact_button_rule = _css_rule(styles_source, ".secondary-button.compact")
    summary_button_rule = _css_rule(styles_source, ".summary-card .secondary-button")

    assert 'variant="economics"' in summary_source
    assert 'variant="analysis"' in summary_source
    assert 'variant="products"' not in summary_source
    assert 'variant="documents"' not in summary_source
    assert "action=\"Открыть анализ\"" in summary_source
    assert "action=\"Открыть товары\"" not in summary_source
    assert "onClick={() => onOpenTab?.('documents')}" not in summary_source
    assert "onClick={() => onOpenTab?.('products')}" not in summary_source
    assert 'className="summary-next-action summary-card"' in summary_source
    assert summary_source.index('variant="economics"') < summary_source.index('variant="analysis"')
    assert summary_source.index('variant="analysis"') < summary_source.index('summary-next-action')
    assert "grid-template-columns: repeat(2, minmax(0, 1fr))" in summary_grid_rule
    assert "grid-auto-rows: auto" in summary_grid_rule
    assert "min-height: 172px" in primary_card_rule
    assert "grid-column: span 2" in secondary_card_rule
    assert ".summary-next-action.summary-card {\n  grid-column: 1 / -1" in styles_source
    assert "grid-template-columns: minmax(120px, 0.6fr) minmax(190px, 0.9fr) minmax(0, 1.5fr)" in styles_source
    assert "height: auto" in compact_button_rule
    assert "min-height: 38px" in compact_button_rule
    assert "white-space: normal" in compact_button_rule
    assert "line-height: 1.15" in compact_button_rule
    assert "height: auto" in summary_button_rule
    assert "overflow-wrap: break-word" in summary_button_rule
    assert find_mojibake(styles_source, STYLES_SOURCE) == []


def test_economics_position_rail_keeps_long_product_names_readable():
    economics_source = (
        TENDER_ECONOMICS_POSITION_RAIL_SOURCE.read_text(encoding="utf-8")
        if TENDER_ECONOMICS_POSITION_RAIL_SOURCE.exists()
        else ""
    )
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")
    details_rule = _css_rule(styles_source, ".workbench-layout .details-panel")
    rail_row_rule = _css_rule(styles_source, ".economics-position-rail .profile-row")
    rail_name_rule = _css_rule(styles_source, ".economics-position-rail .profile-name")

    assert "economics-profile-row" in economics_source
    assert "formatPositionTenderPrice(profile)" in economics_source
    assert "tenderReferenceUnitPrice(profile)" in economics_source
    assert "tenderReferenceTotalPrice(profile)" in economics_source
    assert "container-type: inline-size" in details_rule
    assert '"pos status"' in rail_row_rule
    assert '"name name"' in rail_row_rule
    assert "grid-template-columns: minmax(0, 1fr) auto" in rail_row_rule
    assert "overflow-wrap: break-word" in rail_name_rule
    assert "word-break: normal" in rail_name_rule
    assert "hyphens: auto" in rail_name_rule
    assert "@container (max-width: 860px)" in styles_source
    assert "@container (max-width: 620px)" in styles_source
    assert find_mojibake(economics_source, TENDER_ECONOMICS_POSITION_RAIL_SOURCE) == []
    assert find_mojibake(styles_source, STYLES_SOURCE) == []


def test_products_analysis_and_economics_open_in_fullscreen_workspace():
    tabs_source = TENDER_DETAILS_TABS_SOURCE.read_text(encoding="utf-8")
    summary_source = TENDER_SUMMARY_TAB_SOURCE.read_text(encoding="utf-8")
    fullscreen_source = (
        TENDER_FULLSCREEN_WORKSPACE_SOURCE.read_text(encoding="utf-8")
        if TENDER_FULLSCREEN_WORKSPACE_SOURCE.exists()
        else ""
    )
    workspaces_source = TENDER_WORKSPACES_SOURCE.read_text(encoding="utf-8")
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "from './TenderWorkspaces'" in tabs_source
    assert "const [workspaceMode, setWorkspaceMode]" in tabs_source
    assert "function openTab(tabId)" not in tabs_source
    assert "function openWorkspace(mode)" in tabs_source
    assert "workspaceModes.has(tabId)" in tabs_source
    assert "<TenderWorkspaces" in tabs_source
    assert "const workspaceModes = new Set([" in tabs_source
    assert "workspaceActions" not in tabs_source
    assert "onClick={() => onOpenTab?.('products')}" not in summary_source
    assert "onClick={() => onOpenTab?.('analysis')}" in summary_source
    assert "onClick={() => onOpenTab?.('economics')}" in summary_source
    assert "onOpenTab?.('documents')" not in summary_source
    assert "from './TenderFullscreenWorkspace'" in workspaces_source
    assert "from './TenderProductsTab'" in workspaces_source
    assert "from './TenderDocumentsTab'" not in workspaces_source
    assert "<TenderFullscreenWorkspace" in workspaces_source
    assert "mode === 'products'" in workspaces_source
    assert "mode === 'documents'" not in workspaces_source
    assert "mode === 'analysis'" in workspaces_source
    assert "mode === 'economics'" in workspaces_source
    assert "<TenderProductsTab" in workspaces_source
    assert "<TenderDocumentsTab" not in workspaces_source
    assert "export function TenderFullscreenWorkspace" in fullscreen_source
    assert "fullscreen-workspace-backdrop" in fullscreen_source
    assert "fullscreen-workspace-body" in fullscreen_source
    assert "Escape" in fullscreen_source
    assert ".fullscreen-workspace-backdrop" in styles_source
    assert ".fullscreen-workspace-body .analysis-workspace" in styles_source
    assert ".fullscreen-workspace-body .economics-workspace-grid" in styles_source
    assert find_mojibake(tabs_source, TENDER_DETAILS_TABS_SOURCE) == []
    assert find_mojibake(summary_source, TENDER_SUMMARY_TAB_SOURCE) == []
    assert find_mojibake(workspaces_source, TENDER_WORKSPACES_SOURCE) == []
    assert find_mojibake(fullscreen_source, TENDER_FULLSCREEN_WORKSPACE_SOURCE) == []
    assert find_mojibake(styles_source, STYLES_SOURCE) == []


def test_products_analysis_and_economics_are_workspace_launchers_not_inline_tabs():
    tabs_source = TENDER_DETAILS_TABS_SOURCE.read_text(encoding="utf-8")
    summary_source = TENDER_SUMMARY_TAB_SOURCE.read_text(encoding="utf-8")
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "const workspaceActions = [" not in tabs_source
    assert "<TenderDetailsNavigation" not in tabs_source
    assert "onClick={() => onOpenTab?.('products')}" not in summary_source
    assert "'products'" in tabs_source
    assert "'documents'" not in tabs_source
    assert "activeTab === 'products'" not in tabs_source
    assert "activeTab === 'documents'" not in tabs_source
    assert "activeTab === 'analysis'" not in tabs_source
    assert "activeTab === 'economics'" not in tabs_source
    assert ".detail-workspace-launchers" not in styles_source
    assert find_mojibake(tabs_source, TENDER_DETAILS_TABS_SOURCE) == []
    assert find_mojibake(summary_source, TENDER_SUMMARY_TAB_SOURCE) == []
    assert find_mojibake(styles_source, STYLES_SOURCE) == []


def test_tender_workspaces_module_owns_fullscreen_products_analysis_and_economics():
    tabs_source = TENDER_DETAILS_TABS_SOURCE.read_text(encoding="utf-8")
    workspaces_source = (
        TENDER_WORKSPACES_SOURCE.read_text(encoding="utf-8")
        if TENDER_WORKSPACES_SOURCE.exists()
        else ""
    )

    assert "from './TenderWorkspaces'" in tabs_source
    assert "<TenderWorkspaces" in tabs_source
    assert "from './TenderFullscreenWorkspace'" not in tabs_source
    assert "from './TenderAnalysisTab'" not in tabs_source
    assert "from './TenderEconomicsTab'" not in tabs_source
    assert "export function TenderWorkspaces" in workspaces_source
    assert "from './TenderFullscreenWorkspace'" in workspaces_source
    assert "from './TenderProductsTab'" in workspaces_source
    assert "from './TenderDocumentsTab'" not in workspaces_source
    assert "from './TenderAnalysisTab'" in workspaces_source
    assert "from './TenderEconomicsTab'" in workspaces_source
    assert "mode === 'products'" in workspaces_source
    assert "mode === 'documents'" not in workspaces_source
    assert "mode === 'analysis'" in workspaces_source
    assert "mode === 'economics'" in workspaces_source
    assert "report.docx" in workspaces_source
    assert find_mojibake(tabs_source, TENDER_DETAILS_TABS_SOURCE) == []
    assert find_mojibake(workspaces_source, TENDER_WORKSPACES_SOURCE) == []


def test_tender_details_tabs_groups_fullscreen_workspace_props():
    tabs_source = TENDER_DETAILS_TABS_SOURCE.read_text(encoding="utf-8")
    workspaces_source = TENDER_WORKSPACES_SOURCE.read_text(encoding="utf-8")

    assert "productState={productState}" in tabs_source
    assert "documentState={documentState}" in tabs_source
    assert "analysisState={analysisState}" in tabs_source
    assert "economicsState={economicsState}" in tabs_source
    assert "onSupplierCatalogHealthRefresh={onSupplierCatalogHealthRefresh}" not in tabs_source
    assert "supplierCatalogHealth={supplierCatalogHealth}" not in tabs_source
    assert "const {" in workspaces_source
    assert "economicsState" in workspaces_source
    assert find_mojibake(tabs_source, TENDER_DETAILS_TABS_SOURCE) == []
    assert find_mojibake(workspaces_source, TENDER_WORKSPACES_SOURCE) == []


def test_tender_details_tabs_groups_inline_tab_panel_props():
    tabs_source = TENDER_DETAILS_TABS_SOURCE.read_text(encoding="utf-8")
    panels_source = TENDER_TAB_PANELS_SOURCE.read_text(encoding="utf-8")

    assert "tabState={tabState}" not in tabs_source
    assert "productState={productState}" in tabs_source
    assert "documentState={documentState}" in tabs_source
    assert "analysisState={analysisState}" in tabs_source
    assert "economicsState={economicsState}" in tabs_source
    assert "workflowState={workflowState}" in tabs_source
    assert "onExtractDocumentText={onExtractDocumentText}" not in tabs_source
    assert "onRebuildProductProfiles={onRebuildProductProfiles}" not in tabs_source
    assert "tabState" not in panels_source
    assert "workflowState" in panels_source
    assert find_mojibake(tabs_source, TENDER_DETAILS_TABS_SOURCE) == []
    assert find_mojibake(panels_source, TENDER_TAB_PANELS_SOURCE) == []


def test_tender_details_uses_summary_cards_as_workspace_launchers():
    tabs_source = TENDER_DETAILS_TABS_SOURCE.read_text(encoding="utf-8")
    summary_source = TENDER_SUMMARY_TAB_SOURCE.read_text(encoding="utf-8")
    navigation_source = (
        TENDER_DETAILS_NAVIGATION_SOURCE.read_text(encoding="utf-8")
        if TENDER_DETAILS_NAVIGATION_SOURCE.exists()
        else ""
    )

    assert "from './TenderDetailsNavigation'" not in tabs_source
    assert "<TenderDetailsNavigation" not in tabs_source
    assert "detail-navigation" not in tabs_source
    assert "detail-workspace-launchers" not in tabs_source
    assert "export function TenderDetailsNavigation" not in navigation_source
    assert "detail-navigation" not in navigation_source
    assert "detail-tabs" not in navigation_source
    assert "detail-workspace-launchers" not in navigation_source
    assert "workspaceActions.map" not in navigation_source
    assert "tabs.map" not in navigation_source
    assert "onTabOpen(tab.id)" not in navigation_source
    assert "onWorkspaceOpen(action.id)" not in navigation_source
    assert "onOpenTab?.('economics')" in summary_source
    assert "onOpenTab?.('analysis')" in summary_source
    assert "onOpenTab?.('products')" not in summary_source
    assert "onOpenTab?.('documents')" not in summary_source
    assert find_mojibake(tabs_source, TENDER_DETAILS_TABS_SOURCE) == []
    assert find_mojibake(navigation_source, TENDER_DETAILS_NAVIGATION_SOURCE) == []
    assert find_mojibake(summary_source, TENDER_SUMMARY_TAB_SOURCE) == []


def test_tender_tab_panels_module_owns_inline_summary_and_workflow():
    tabs_source = TENDER_DETAILS_TABS_SOURCE.read_text(encoding="utf-8")
    panels_source = (
        TENDER_TAB_PANELS_SOURCE.read_text(encoding="utf-8")
        if TENDER_TAB_PANELS_SOURCE.exists()
        else ""
    )

    assert "from './TenderTabPanels'" in tabs_source
    assert "<TenderTabPanels" in tabs_source
    assert "detail-tab-panel" not in tabs_source
    assert "export function TenderTabPanels" in panels_source
    assert "detail-tab-panel" in panels_source
    assert "from './TenderSummaryTab'" in panels_source
    assert "from './TenderProductsTab'" not in panels_source
    assert "from './TenderDocumentsTab'" not in panels_source
    assert "from './TenderWorkflowTab'" in panels_source
    assert "activeTab" not in panels_source
    assert "activeTab === 'products'" not in panels_source
    assert "activeTab === 'documents'" not in panels_source
    assert "activeTab === 'workflow'" not in panels_source
    assert "<TenderSummaryTab" in panels_source
    assert "<WorkflowTabPanel" in panels_source
    assert find_mojibake(tabs_source, TENDER_DETAILS_TABS_SOURCE) == []
    assert find_mojibake(panels_source, TENDER_TAB_PANELS_SOURCE) == []


def test_fullscreen_economics_workspace_is_a_dedicated_workbench():
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")
    fullscreen_rule = _css_rule(styles_source, ".fullscreen-workspace.economics")
    fullscreen_economics_rule = _css_rule(styles_source, ".fullscreen-workspace-body .economics-workspace-grid")
    rail_rule = _css_rule(styles_source, ".fullscreen-workspace-body .economics-position-rail")
    supplier_rule = _css_rule(styles_source, ".fullscreen-workspace-body .economics-supplier-panel")
    supplier_heading_rule = _css_rule(styles_source, ".fullscreen-workspace-body .supplier-options-block .profile-block-heading")
    supplier_actions_rule = _css_rule(styles_source, ".fullscreen-workspace-body .supplier-options-block .profile-block-actions")

    assert "width: min(1680px, calc(100vw - 36px))" in fullscreen_rule
    assert "grid-template-columns: minmax(320px, 0.38fr) minmax(0, 1fr)" in fullscreen_economics_rule
    assert "minmax(320px, 0.58fr) minmax(420px, 1fr) minmax(360px, 0.78fr)" not in fullscreen_economics_rule
    assert "position: sticky" in rail_rule
    assert "top: 0" in rail_rule
    assert "max-height: calc(100vh - 220px)" in rail_rule
    assert "display: grid" in supplier_heading_rule
    assert "align-items: stretch" in supplier_heading_rule
    assert "grid-template-columns: repeat(2, minmax(0, 1fr))" in supplier_actions_rule
    assert "@container (max-width: 1100px)" in styles_source
    assert find_mojibake(styles_source, STYLES_SOURCE) == []


def test_decision_tabs_are_extracted_to_consistent_work_panels():
    app_source = TENDER_DETAILS_TABS_SOURCE.read_text(encoding="utf-8")
    panels_source = TENDER_TAB_PANELS_SOURCE.read_text(encoding="utf-8")
    workspaces_source = TENDER_WORKSPACES_SOURCE.read_text(encoding="utf-8")
    analysis_source = TENDER_ANALYSIS_TAB_SOURCE.read_text(encoding="utf-8")
    analysis_summary_source = TENDER_ANALYSIS_SUMMARY_SOURCE.read_text(encoding="utf-8")
    economics_source = TENDER_ECONOMICS_TAB_SOURCE.read_text(encoding="utf-8")
    economics_metrics_source = (
        TENDER_ECONOMICS_METRICS_SOURCE.read_text(encoding="utf-8")
        if TENDER_ECONOMICS_METRICS_SOURCE.exists()
        else ""
    )
    workflow_source = (
        TENDER_WORKFLOW_TAB_SOURCE.read_text(encoding="utf-8")
        if TENDER_WORKFLOW_TAB_SOURCE.exists()
        else ""
    )
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "export function TenderAnalysisTab" in analysis_source
    assert "export function TenderEconomicsTab" in economics_source
    assert "export function WorkflowTabPanel" in workflow_source
    assert "<TenderAnalysisTab" in workspaces_source
    assert "<TenderEconomicsTab" in workspaces_source
    assert "productProfiles={productProfiles}" in workspaces_source
    assert "<WorkflowTabPanel" in panels_source
    assert "analysis-tab-summary" in analysis_summary_source
    assert "economics-tab-summary" in economics_metrics_source
    assert "workflow-compact-row" in workflow_source
    assert "workflow-status-select" in workflow_source
    assert "workflow-note-panel" in workflow_source
    assert ".analysis-tab-summary," in styles_source
    assert ".economics-tab-summary," in styles_source
    assert ".workflow-compact-row" in styles_source
    assert ".workflow-status-select" in styles_source
    assert ".workflow-note-panel" in styles_source
    assert find_mojibake(app_source, TENDER_DETAILS_TABS_SOURCE) == []
    assert find_mojibake(panels_source, TENDER_TAB_PANELS_SOURCE) == []
    assert find_mojibake(workspaces_source, TENDER_WORKSPACES_SOURCE) == []
    assert find_mojibake(analysis_source, TENDER_ANALYSIS_TAB_SOURCE) == []
    assert find_mojibake(analysis_summary_source, TENDER_ANALYSIS_SUMMARY_SOURCE) == []
    assert find_mojibake(economics_source, TENDER_ECONOMICS_TAB_SOURCE) == []
    assert find_mojibake(economics_metrics_source, TENDER_ECONOMICS_METRICS_SOURCE) == []
    assert find_mojibake(workflow_source, TENDER_WORKFLOW_TAB_SOURCE) == []
    assert find_mojibake(styles_source, STYLES_SOURCE) == []

def test_economics_tab_uses_tender_price_before_manual_calculation():
    app_source = TENDER_ECONOMICS_TAB_SOURCE.read_text(encoding="utf-8")
    metrics_source = (
        TENDER_ECONOMICS_METRICS_SOURCE.read_text(encoding="utf-8")
        if TENDER_ECONOMICS_METRICS_SOURCE.exists()
        else ""
    )
    summary_source = TENDER_ECONOMICS_SUMMARY_SOURCE.read_text(encoding="utf-8")

    assert "export function TenderEconomicsTab({" in app_source
    assert "from './TenderEconomicsMetrics'" in app_source
    assert "const displayedRevenue = economics?.revenue ?? marketState?.nmc_price ?? tender?.price" in metrics_source
    assert "const revenueLabel = economics?.revenue_kind === 'current_offer'" in metrics_source
    assert "<SummaryMetric value={formatMoney(displayedRevenue)} label={revenueLabel} />" in metrics_source
    assert "НМЦК подтянута из карточки закупки" in summary_source
    assert find_mojibake(app_source, TENDER_ECONOMICS_TAB_SOURCE) == []
    assert find_mojibake(metrics_source, TENDER_ECONOMICS_METRICS_SOURCE) == []
    assert find_mojibake(summary_source, TENDER_ECONOMICS_SUMMARY_SOURCE) == []

def test_economics_tab_renders_bid_thresholds():
    app_source = TENDER_ECONOMICS_TAB_SOURCE.read_text(encoding="utf-8")
    metrics_source = (
        TENDER_ECONOMICS_METRICS_SOURCE.read_text(encoding="utf-8")
        if TENDER_ECONOMICS_METRICS_SOURCE.exists()
        else ""
    )
    summary_source = TENDER_ECONOMICS_SUMMARY_SOURCE.read_text(encoding="utf-8")

    assert "economics?.break_even_price" not in metrics_source
    assert "economics.break_even_price" in summary_source
    assert "economics.minimum_margin_price" in summary_source
    assert "economics.interesting_price" in summary_source
    assert "Безубыток" in summary_source
    assert "Минимальная ставка" in summary_source
    assert "Интересная ставка" in summary_source
    assert find_mojibake(app_source, TENDER_ECONOMICS_TAB_SOURCE) == []
    assert find_mojibake(metrics_source, TENDER_ECONOMICS_METRICS_SOURCE) == []
    assert find_mojibake(summary_source, TENDER_ECONOMICS_SUMMARY_SOURCE) == []

def test_tender_detail_renders_price_change_banner():
    app_source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
    decision_source = (
        TENDER_DECISION_SUMMARY_SOURCE.read_text(encoding="utf-8")
        if TENDER_DECISION_SUMMARY_SOURCE.exists()
        else ""
    )
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "<PriceChangeBanner change={tender.price_change} />" in app_source
    assert "export function PriceChangeBanner({ change })" in decision_source
    assert "formatPriceChangeDirection" in decision_source
    assert "price-change-banner" in decision_source
    assert ".price-change-banner" in styles_source
    assert find_mojibake(app_source, TENDER_DETAILS_SOURCE) == []
    assert find_mojibake(decision_source, TENDER_DECISION_SUMMARY_SOURCE) == []
    assert find_mojibake(styles_source, STYLES_SOURCE) == []


def test_frontend_formats_market_state_for_tender_surfaces():
    formatter_source = FORMATTERS_SOURCE.read_text(encoding="utf-8")

    assert "export function marketStateValue" in formatter_source
    assert "export function participantBidValue" in formatter_source
    assert "export function nmcPriceValue" in formatter_source
    assert "export function hasParticipantBid" in formatter_source
    assert "function positiveNumber" in formatter_source
    assert "if (value === null || value === undefined || value === '') return 'не указана'" in formatter_source
    assert "const currentOffer = positiveNumber(marketState?.current_offer_price)" in formatter_source
    assert "marketState?.bid_count" in formatter_source
    assert "function formatBidCount" in formatter_source
    assert "минимальная из ${formatBidCount(bidCount)}" in formatter_source
    assert "участников нет" in formatter_source
    assert "цена скрыта" in formatter_source
    assert "export function economicsDecisionLabel" in formatter_source
    assert "export function tenderDecisionLabel" in formatter_source
    assert "export function tenderDecisionStatus" in formatter_source
    assert "tender?.decision?.label" in formatter_source
    assert "tender?.decision?.next_step" in formatter_source
    assert "нет расчета" in formatter_source


def test_tender_list_surfaces_market_state_and_backend_decision():
    source = TENDER_LIST_SOURCE.read_text(encoding="utf-8")
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "nmcPriceValue" in source
    assert "marketStateValue(tender.market_state)" in source
    assert "tenderDecisionLabel(tender)" in source
    assert "tenderDecisionStatus(tender)" in source
    assert "economicsDecisionLabel(tender.economics)" not in source
    assert "economics-chip" in source
    assert ".economics-chip" in styles_source
    assert ".economics-chip.missing_prices" in styles_source
    assert ".economics-chip.with_limit" in styles_source
    assert ".economics-chip.skip" in styles_source
    assert find_mojibake(source, TENDER_LIST_SOURCE) == []


def test_economics_tab_supports_bulk_best_supplier_selection():
    api_source = API_SOURCE.read_text(encoding="utf-8")
    hook_source = USE_TENDER_PRODUCT_PROFILES_SOURCE.read_text(encoding="utf-8")
    details_source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
    economics_source = TENDER_ECONOMICS_TAB_SOURCE.read_text(encoding="utf-8")

    assert "export function autoSelectTenderSupplierOptions" in api_source
    assert "product-profiles/supplier-options/best/select" in api_source
    assert "export function confirmReadyTenderPriceCandidates" in api_source
    assert "price-candidates/ready/confirm" in api_source
    assert "autoSelectTenderSupplierOptions as autoSelectTenderSupplierOptionsRequest" in hook_source
    assert "confirmReadyTenderPriceCandidates as confirmReadyTenderPriceCandidatesRequest" in hook_source
    assert "autoSelectingAllSuppliers" in hook_source
    assert "confirmingReadyPriceCandidates" in hook_source
    assert "READY_PRICE_CANDIDATES_REVIEW_ID" in hook_source
    assert "const confirmingReadyPriceCandidates = reviewingPriceCandidateId === READY_PRICE_CANDIDATES_REVIEW_ID" in hook_source
    assert "const [confirmingReadyPriceCandidates, setConfirmingReadyPriceCandidates]" not in hook_source
    assert "function autoSelectAllSupplierOptions" in hook_source
    assert "function confirmReadyPriceCandidates" in hook_source
    assert "onSupplierOptionAutoSelectAll" in details_source
    assert "onReadyPriceCandidatesConfirmAll" in details_source
    assert "onSupplierOptionAutoSelectAll" in economics_source
    assert "onReadyPriceCandidatesConfirmAll" in economics_source
    assert "autoSelectingAllSuppliers" in economics_source
    assert "confirmingReadyPriceCandidates" in economics_source
    assert "hasReadyPriceCandidateWithoutCost" in economics_source
    assert "economics-secondary-menu" in economics_source
    assert "Готовые цены в расчет" not in economics_source
    assert "Лучшие цены в расчет" not in economics_source
    assert find_mojibake(api_source, API_SOURCE) == []
    assert find_mojibake(hook_source, USE_TENDER_PRODUCT_PROFILES_SOURCE) == []
    assert find_mojibake(economics_source, TENDER_ECONOMICS_TAB_SOURCE) == []


def test_economics_tab_supports_price_candidate_auto_stage():
    api_source = API_SOURCE.read_text(encoding="utf-8")
    hook_source = USE_TENDER_PRODUCT_PROFILES_SOURCE.read_text(encoding="utf-8")
    details_source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
    workspaces_source = TENDER_WORKSPACES_SOURCE.read_text(encoding="utf-8")
    economics_source = TENDER_ECONOMICS_TAB_SOURCE.read_text(encoding="utf-8")

    assert "export function stageTenderPriceCandidates" in api_source
    assert "price-candidates/stage" in api_source
    assert "export function applyTenderAutoPrices" in api_source
    assert "price-candidates/auto-apply" in api_source
    assert "export function stageTenderPriceBookFeed" in api_source
    assert "price-book/feed" in api_source
    assert "export function runTenderPriceDiscovery" in api_source
    assert "price-discovery/run" in api_source
    assert "export function fetchPriceDiscoveryJob" in api_source
    assert "/api/price-discovery/jobs/${encodeURIComponent(jobId)}" in api_source
    assert "stageTenderPriceCandidates as stageTenderPriceCandidatesRequest" in hook_source
    assert "applyTenderAutoPrices as applyTenderAutoPricesRequest" in hook_source
    assert "runTenderPriceDiscovery as runTenderPriceDiscoveryRequest" in hook_source
    assert "fetchPriceDiscoveryJob" in hook_source
    assert "PRICE_CANDIDATE_STAGE_REVIEW_ID" in hook_source
    assert "PRICE_AUTO_APPLY_ID" in hook_source
    assert "PRICE_DISCOVERY_RUN_ID" in hook_source
    assert "function isPriceDiscoveryJobComplete" in hook_source
    assert "const stagingPriceCandidates = reviewingPriceCandidateId === PRICE_CANDIDATE_STAGE_REVIEW_ID" in hook_source
    assert "const applyingAutoPrices = reviewingPriceCandidateId === PRICE_AUTO_APPLY_ID" in hook_source
    assert "!isPriceDiscoveryJobComplete(job)" in hook_source
    assert "isPriceDiscoveryJobActive(priceDiscoveryJob)" in hook_source
    assert "const [priceDiscoveryJob, setPriceDiscoveryJob]" in hook_source
    assert "fetchPriceDiscoveryJob(priceDiscoveryJob.job_id)" in hook_source
    assert "price_discovery_job" in hook_source
    assert "const [stagingPriceCandidates, setStagingPriceCandidates]" not in hook_source
    assert "const [applyingAutoPrices, setApplyingAutoPrices]" not in hook_source
    assert "const [runningPriceDiscovery, setRunningPriceDiscovery]" not in hook_source
    assert "function stagePriceCandidates" in hook_source
    assert "function applyAutoPrices" in hook_source
    assert "function runPriceDiscovery" in hook_source
    assert "priceDiscoveryStatusMessage(job)" in hook_source
    assert "onPriceCandidatesStage" in details_source
    assert "onAutoPricesApply" in details_source
    assert "onPriceDiscoveryRun" in details_source
    assert "priceDiscoveryJob" in details_source
    assert "onPriceCandidatesStage" in workspaces_source
    assert "onAutoPricesApply" in workspaces_source
    assert "onPriceDiscoveryRun" in workspaces_source
    assert "priceDiscoveryJob" in workspaces_source
    assert "onPriceDiscoveryRun" in economics_source
    assert "priceDiscoveryJobStatusText" in economics_source
    assert "runningPriceDiscovery" in economics_source
    assert "SMALL_TENDER_ACTIVE_DISCOVERY_LIMIT = 5" in economics_source
    assert "canRunActivePriceDiscovery" in economics_source
    assert "price-discovery-manual-required" in economics_source
    assert "быстрые ссылки/ссылка на товар/прайс" in economics_source
    assert "Найти цены" in economics_source
    assert "Подготовить цены" not in economics_source
    assert "Автоцены в расчет" not in economics_source
    assert find_mojibake(api_source, API_SOURCE) == []
    assert find_mojibake(hook_source, USE_TENDER_PRODUCT_PROFILES_SOURCE) == []
    assert find_mojibake(economics_source, TENDER_ECONOMICS_TAB_SOURCE) == []


def test_economics_tab_exposes_price_book_feed_import_ui():
    hook_source = USE_TENDER_PRODUCT_PROFILES_SOURCE.read_text(encoding="utf-8")
    details_source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
    workspaces_source = TENDER_WORKSPACES_SOURCE.read_text(encoding="utf-8")
    economics_source = TENDER_ECONOMICS_TAB_SOURCE.read_text(encoding="utf-8")
    feed_source = TENDER_ECONOMICS_PRICE_BOOK_FEED_SOURCE.read_text(encoding="utf-8")
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "stageTenderPriceBookFeed as stageTenderPriceBookFeedRequest" in hook_source
    assert "PRICE_BOOK_FEED_STAGE_ID" in hook_source
    assert "function stagePriceBookFeed" in hook_source
    assert "price_book_feed" in hook_source
    assert "stagingPriceBookFeed" in hook_source
    assert "onPriceBookFeedStage" in details_source
    assert "onPriceBookFeedStage" in workspaces_source
    assert "onPriceBookFeedStage" in economics_source
    assert "TenderEconomicsPriceBookFeed" in economics_source
    assert "<TenderEconomicsPriceBookFeed" in economics_source
    assert "export function TenderEconomicsPriceBookFeed" in feed_source
    assert "parsePriceBookFeedText" in feed_source
    assert "normalizeFeedHeader" in feed_source
    assert "splitDelimitedLine" in feed_source
    assert "feedPreviewRows" in feed_source
    assert "rows: parsed.rows" in feed_source
    assert "price-book-feed-panel" in feed_source
    assert ".price-book-feed-panel" in styles_source
    assert ".price-book-feed-preview" in styles_source
    assert find_mojibake(hook_source, USE_TENDER_PRODUCT_PROFILES_SOURCE) == []
    assert find_mojibake(economics_source, TENDER_ECONOMICS_TAB_SOURCE) == []
    assert find_mojibake(feed_source, TENDER_ECONOMICS_PRICE_BOOK_FEED_SOURCE) == []
    assert find_mojibake(styles_source, STYLES_SOURCE) == []


def test_dashboard_surfaces_current_offers_and_backend_decisions():
    dashboard_source = DASHBOARD_SOURCE.read_text(encoding="utf-8")
    app_source = APP_SOURCE.read_text(encoding="utf-8")
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "fetchDashboardQueues" in app_source
    assert "const [dashboardQueues, setDashboardQueues]" in app_source
    assert "loadDashboardQueues()" in app_source
    assert "dashboardQueues={dashboardQueues}" in app_source
    assert "dashboardQueueError={dashboardQueueError}" in app_source
    assert "dashboardQueues" in dashboard_source
    assert "queuePayload" in dashboard_source
    assert "currentOfferCount" in dashboard_source
    assert "marketMetric" in dashboard_source
    assert "decisionReadyCount" in dashboard_source
    assert "tenderDecisionLabel(tender)" in dashboard_source
    assert "economicsDecisionLabel(tender.economics)" not in dashboard_source
    assert "participantBidValue(tender.market_state)" in dashboard_source
    assert "НМЦК ${nmcPriceValue(tender)}" in dashboard_source
    assert "ставка ${participantBidValue(tender.market_state)}" in dashboard_source
    assert "repeat(auto-fit, minmax(180px, 1fr))" in styles_source
    assert find_mojibake(dashboard_source, DASHBOARD_SOURCE) == []


def test_economics_summary_labels_current_offer_revenue():
    source = TENDER_ECONOMICS_TAB_SOURCE.read_text(encoding="utf-8")
    metrics_source = (
        TENDER_ECONOMICS_METRICS_SOURCE.read_text(encoding="utf-8")
        if TENDER_ECONOMICS_METRICS_SOURCE.exists()
        else ""
    )
    summary_source = TENDER_ECONOMICS_SUMMARY_SOURCE.read_text(encoding="utf-8")

    assert "economics?.revenue_kind === 'current_offer' ? 'Цена участника' : 'НМЦК'" in metrics_source
    assert '<SummaryMetric value={nmcPriceValue(tender, marketState)} label="НМЦК" />' in metrics_source
    assert '<Info label="НМЦК" value={nmcPriceValue(tender, marketState)} />' in summary_source
    assert "<SummaryMetric value={participantBidValue(economics?.market_state || tender?.market_state)}" in metrics_source
    assert "marketStateValue(economics?.market_state || tender?.market_state)" in metrics_source
    assert "marketStateCaption(economics?.market_state || tender?.market_state)" in summary_source
    assert find_mojibake(source, TENDER_ECONOMICS_TAB_SOURCE) == []
    assert find_mojibake(metrics_source, TENDER_ECONOMICS_METRICS_SOURCE) == []
    assert find_mojibake(summary_source, TENDER_ECONOMICS_SUMMARY_SOURCE) == []


def test_economics_summary_surfaces_decision_engine_v2():
    summary_source = TENDER_ECONOMICS_SUMMARY_SOURCE.read_text(encoding="utf-8")
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "const economicsDecision = tender?.decision?.economics_decision || null" in summary_source
    assert "<DecisionEngineV2Panel decision={economicsDecision} />" in summary_source
    assert "decision.auto_price_policy" in summary_source
    assert "decision.historical_benchmark" in summary_source
    assert "formatAutoPricePolicy" in summary_source
    assert "formatHistoricalBenchmark" in summary_source
    assert ".economics-decision-v2" in styles_source
    assert find_mojibake(summary_source, TENDER_ECONOMICS_SUMMARY_SOURCE) == []
    assert find_mojibake(styles_source, STYLES_SOURCE) == []


def test_tender_card_surfaces_participant_bid_next_to_nmc():
    summary_source = TENDER_DECISION_SUMMARY_SOURCE.read_text(encoding="utf-8")
    strip_source = TENDER_DECISION_STRIP_SOURCE.read_text(encoding="utf-8")

    assert 'Info label="НМЦК" value={nmcPriceValue(tender, economics?.market_state || tender.market_state)}' in summary_source
    assert 'Info label="Ставка участника" value={participantBidValue(economics?.market_state || tender.market_state)}' in summary_source
    assert 'SummaryMetric value={nmcPriceValue(tender, economics?.market_state || tender.market_state)} label="НМЦК"' in strip_source
    assert 'SummaryMetric value={participantBidValue(economics?.market_state || tender.market_state)} label="ставка участника"' in strip_source
    assert find_mojibake(summary_source, TENDER_DECISION_SUMMARY_SOURCE) == []
    assert find_mojibake(strip_source, TENDER_DECISION_STRIP_SOURCE) == []


def test_tender_detail_visual_density_has_stable_grids_and_no_negative_offsets():
    app_source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
    products_source = TENDER_PRODUCTS_TAB_SOURCE.read_text(encoding="utf-8")
    workflow_source = TENDER_WORKFLOW_TAB_SOURCE.read_text(encoding="utf-8")
    shared_source = TENDER_DETAILS_SHARED_SOURCE.read_text(encoding="utf-8")
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")
    tab_lead_rule = _css_rule(styles_source, ".tab-lead")
    document_row_rule = _css_rule(styles_source, ".document-row")
    compact_button_rule = _css_rule(styles_source, ".secondary-button.compact")

    assert "tab-summary-grid" in app_source + products_source + workflow_source
    assert "summary-label" in shared_source
    assert ".tab-summary-grid" in styles_source
    assert ".summary-label" in styles_source
    assert "grid-template-columns: minmax(0, 1fr) auto" not in tab_lead_rule
    assert "grid-template-columns: minmax(0, 1fr) minmax(132px, auto)" in document_row_rule
    assert "margin-top: -" not in compact_button_rule
    assert "grid-template-columns: 42px minmax(150px, 1fr) minmax(76px, 0.45fr) 92px" not in styles_source
    assert find_mojibake(app_source, TENDER_DETAILS_SOURCE) == []
    assert find_mojibake(products_source, TENDER_PRODUCTS_TAB_SOURCE) == []
    assert find_mojibake(workflow_source, TENDER_WORKFLOW_TAB_SOURCE) == []
    assert find_mojibake(shared_source, TENDER_DETAILS_SHARED_SOURCE) == []
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
    assert "changeView(item.id)" in app_source
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
    assert "tenders={tenders}" in dashboard_source
    assert "dashboardQueues={dashboardQueues}" in dashboard_source
    assert "dashboardQueueItems(dashboardQueues)" in dashboard_source
    assert "queue.items?.[0]" in dashboard_source
    assert "ТЗ/решение" in dashboard_source
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


def test_dashboard_surfaces_supplier_catalog_connectivity():
    app_source = APP_SOURCE.read_text(encoding="utf-8")
    dashboard_source = DASHBOARD_SOURCE.read_text(encoding="utf-8")
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "fetchSupplierCatalogHealth" in app_source
    assert "const [supplierCatalogHealth, setSupplierCatalogHealth]" in app_source
    assert "const [supplierCatalogHealthError, setSupplierCatalogHealthError]" in app_source
    assert "function loadSupplierCatalogHealth" in app_source
    assert "loadSupplierCatalogHealth(false)" in app_source
    assert "supplierCatalogHealth={supplierCatalogHealth}" in app_source
    assert "onRefreshSupplierCatalogs={() => loadSupplierCatalogHealth(true)}" in app_source
    assert "function SupplierCatalogStatusPanel" in dashboard_source
    assert "<SupplierCatalogStatusPanel" in dashboard_source
    assert "catalogHealth?.catalogs" in dashboard_source
    assert "lemanapro_building_materials" in dashboard_source
    assert "Lemana Pro" in dashboard_source
    assert "mergeSupplierCatalogDashboardFallbacks" in dashboard_source
    assert "supplier-catalog-dashboard" in dashboard_source
    assert "collapsible-status-panel" in dashboard_source
    assert "source-status-toggle" in dashboard_source
    assert "aria-expanded={expanded}" in dashboard_source
    assert "setExpanded((value) => !value)" in dashboard_source
    assert "catalogSummaryText(catalogs, error, loading)" in dashboard_source
    assert "function isCatalogActiveSmallSearch" in dashboard_source
    assert "function isCatalogManualOnly" in dashboard_source
    assert "function isCatalogManualRoute" in dashboard_source
    assert "const activeCatalogs = catalogs.filter(isCatalogActiveSmallSearch)" in dashboard_source
    assert "доступны" in dashboard_source
    assert "ручной режим" in dashboard_source
    assert "публичный поиск офиски" in dashboard_source
    assert "сайт блокирует авто" in dashboard_source
    assert "автопоиск до" not in dashboard_source
    assert "активн. проблем" not in dashboard_source
    assert "browser_error" not in dashboard_source
    assert "sourceSummaryText(sources, error)" in dashboard_source
    assert ".supplier-catalog-dashboard" in styles_source
    assert ".collapsible-status-panel" in styles_source
    assert ".source-status-toggle" in styles_source
    assert ".source-status-summary" in styles_source
    catalog_status_rule = _css_rule(styles_source, ".supplier-catalog-dashboard .source-status-main > div:first-child span")
    assert "flex: 1 1 auto" in catalog_status_rule
    assert "overflow-wrap: anywhere" in catalog_status_rule
    assert find_mojibake(app_source, APP_SOURCE) == []
    assert find_mojibake(dashboard_source, DASHBOARD_SOURCE) == []
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
    notification_source = USE_TENDER_NOTIFICATION_SOURCE.read_text(encoding="utf-8")

    assert "payload.message || (payload.sent ? 'Отправлено в Telegram' : 'Telegram не настроен')" in notification_source
    assert find_mojibake(notification_source, USE_TENDER_NOTIFICATION_SOURCE) == []


def test_frontend_exposes_local_market_state_import():
    api_source = API_SOURCE.read_text(encoding="utf-8")
    details_source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
    actions_source = TENDER_DETAIL_ACTIONS_SOURCE.read_text(encoding="utf-8")
    import_source = TENDER_MARKET_STATE_IMPORT_SOURCE.read_text(encoding="utf-8")
    hook_source = USE_TENDER_MARKET_STATE_IMPORT_SOURCE.read_text(encoding="utf-8")
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "export function importTenderMarketState" in api_source
    assert "/market-state/import" in api_source
    assert "function apiJson(path, { method = 'GET', body, errorMessage = 'API не отвечает', signal } = {})" in api_source
    assert "options.signal = signal" in api_source
    assert "if (error.name === 'AbortError')" in api_source
    assert "useTenderMarketStateImport" in details_source
    assert "TenderMarketStateImport" in actions_source
    assert "market-import-panel" in import_source
    assert "market-import-help" in import_source
    assert "JSON-ответ запроса GetBetUpdate" in import_source
    assert "F12 &gt; Network &gt; Fetch/XHR" in import_source
    assert "lastBetCost, nextCost, uniqueSupplierCount" in import_source
    assert ".market-import-help" in styles_source
    assert "aria-busy={importing}" in import_source
    assert "disabled={!value.trim()}" in import_source
    assert "disabled={importing || !value.trim()}" not in import_source
    assert "JSON.parse(marketImportText" in hook_source
    assert "MARKET_IMPORT_TIMEOUT_MS" in hook_source
    assert "AbortController" in hook_source
    assert "activeImportRef.current?.abort()" in hook_source
    assert "importTenderMarketState(tender, payload, { signal: controller.signal })" in hook_source
    assert "applyProductTenderState(nextTender, { resetSelection: false })" in hook_source
    assert ".market-import-panel" in styles_source
    assert ".market-import-form" in styles_source
    assert find_mojibake(api_source, API_SOURCE) == []
    assert find_mojibake(details_source, TENDER_DETAILS_SOURCE) == []
    assert find_mojibake(actions_source, TENDER_DETAIL_ACTIONS_SOURCE) == []
    assert find_mojibake(import_source, TENDER_MARKET_STATE_IMPORT_SOURCE) == []
    assert find_mojibake(hook_source, USE_TENDER_MARKET_STATE_IMPORT_SOURCE) == []
    assert find_mojibake(styles_source, STYLES_SOURCE) == []
