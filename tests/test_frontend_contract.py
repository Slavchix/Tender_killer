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
TENDER_DECISION_STRIP_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "TenderDecisionStrip.jsx"
TENDER_DECISION_SUMMARY_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "TenderDecisionSummary.jsx"
TENDER_DOCUMENTS_TAB_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "TenderDocumentsTab.jsx"
TENDER_ECONOMICS_TAB_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "TenderEconomicsTab.jsx"
TENDER_ECONOMICS_DECISION_SCENARIOS_SOURCE = (
    Path(__file__).resolve().parents[1] / "web" / "src" / "TenderEconomicsDecisionScenarios.jsx"
)
TENDER_ECONOMICS_FORMS_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "TenderEconomicsForms.jsx"
TENDER_ECONOMICS_COST_FORM_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "TenderEconomicsCostForm.jsx"
TENDER_ECONOMICS_SUMMARY_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "TenderEconomicsSummary.jsx"
TENDER_ECONOMICS_SUPPLIERS_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "TenderEconomicsSuppliers.jsx"
TENDER_ECONOMICS_SUPPLIER_CATALOGS_SOURCE = (
    Path(__file__).resolve().parents[1] / "web" / "src" / "TenderEconomicsSupplierCatalogs.jsx"
)
TENDER_ECONOMICS_SUPPLIER_CATALOG_HEALTH_SOURCE = (
    Path(__file__).resolve().parents[1] / "web" / "src" / "TenderEconomicsSupplierCatalogHealth.jsx"
)
TENDER_ECONOMICS_SUPPLIER_DISCOVERY_SOURCE = (
    Path(__file__).resolve().parents[1] / "web" / "src" / "TenderEconomicsSupplierDiscovery.jsx"
)
TENDER_ECONOMICS_SUPPLIER_OPTIONS_SOURCE = (
    Path(__file__).resolve().parents[1] / "web" / "src" / "TenderEconomicsSupplierOptions.jsx"
)
TENDER_ECONOMICS_SUPPLIER_INPUT_SOURCE = (
    Path(__file__).resolve().parents[1] / "web" / "src" / "TenderEconomicsSupplierInputForm.jsx"
)
TENDER_ECONOMICS_SUPPLIER_ACTIONS_SOURCE = (
    Path(__file__).resolve().parents[1] / "web" / "src" / "TenderEconomicsSupplierActions.jsx"
)
TENDER_ECONOMICS_SUPPLIER_FIELDS_SOURCE = (
    Path(__file__).resolve().parents[1] / "web" / "src" / "TenderEconomicsSupplierFields.jsx"
)
TENDER_ECONOMICS_SUPPLIER_PAYLOADS_SOURCE = (
    Path(__file__).resolve().parents[1] / "web" / "src" / "TenderEconomicsSupplierPayloads.js"
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

    for key in ("source_family", "procedure_type", "customer_inn"):
        assert f"{key}: ''" in constants_source

    assert "export const regionOptions" in constants_source
    assert "value: 'Краснодарский край'" in constants_source
    assert "value: 'Республика Татарстан'" in constants_source
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
    assert "regionOptions.map" in filters_source
    assert "procedureTypeOptions.map" not in filters_source
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
    assert "details-panel" in app_source
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


def test_frontend_uses_dedicated_tender_documents_tab_module():
    tender_details_source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
    panels_source = TENDER_TAB_PANELS_SOURCE.read_text(encoding="utf-8")
    workspaces_source = TENDER_WORKSPACES_SOURCE.read_text(encoding="utf-8")
    documents_source = (
        TENDER_DOCUMENTS_TAB_SOURCE.read_text(encoding="utf-8")
        if TENDER_DOCUMENTS_TAB_SOURCE.exists()
        else ""
    )

    assert "from './TenderDocumentsTab'" in workspaces_source
    assert "export function TenderDocumentsTab" in documents_source
    assert "function DocumentStatusSummary" in documents_source
    assert "document-table" in documents_source
    assert "document-status ${document.text_status || 'pending'}" in documents_source
    assert "<TenderDocumentsTab" in workspaces_source
    assert "from './TenderDocumentsTab'" not in panels_source
    assert "function DocumentStatusSummary" not in tender_details_source
    assert "document-table" not in tender_details_source
    assert find_mojibake(tender_details_source, TENDER_DETAILS_SOURCE) == []
    assert find_mojibake(panels_source, TENDER_TAB_PANELS_SOURCE) == []
    assert find_mojibake(workspaces_source, TENDER_WORKSPACES_SOURCE) == []
    assert find_mojibake(documents_source, TENDER_DOCUMENTS_TAB_SOURCE) == []


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
    assert "from './TenderAnalysisEvidencePanel'" in analysis_source
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
    economics_supplier_catalogs_source = (
        TENDER_ECONOMICS_SUPPLIER_CATALOGS_SOURCE.read_text(encoding="utf-8")
        if TENDER_ECONOMICS_SUPPLIER_CATALOGS_SOURCE.exists()
        else ""
    )
    economics_supplier_catalog_health_source = (
        TENDER_ECONOMICS_SUPPLIER_CATALOG_HEALTH_SOURCE.read_text(encoding="utf-8")
        if TENDER_ECONOMICS_SUPPLIER_CATALOG_HEALTH_SOURCE.exists()
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
    economics_supplier_input_source = (
        TENDER_ECONOMICS_SUPPLIER_INPUT_SOURCE.read_text(encoding="utf-8")
        if TENDER_ECONOMICS_SUPPLIER_INPUT_SOURCE.exists()
        else ""
    )
    economics_supplier_actions_source = (
        TENDER_ECONOMICS_SUPPLIER_ACTIONS_SOURCE.read_text(encoding="utf-8")
        if TENDER_ECONOMICS_SUPPLIER_ACTIONS_SOURCE.exists()
        else ""
    )
    economics_supplier_fields_source = (
        TENDER_ECONOMICS_SUPPLIER_FIELDS_SOURCE.read_text(encoding="utf-8")
        if TENDER_ECONOMICS_SUPPLIER_FIELDS_SOURCE.exists()
        else ""
    )
    economics_supplier_payloads_source = (
        TENDER_ECONOMICS_SUPPLIER_PAYLOADS_SOURCE.read_text(encoding="utf-8")
        if TENDER_ECONOMICS_SUPPLIER_PAYLOADS_SOURCE.exists()
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
    assert "from './TenderEconomicsSupplierDiscovery'" in economics_suppliers_source
    assert "from './TenderEconomicsSupplierOptions'" in economics_suppliers_source
    assert "from './TenderEconomicsSupplierInputForm'" in economics_suppliers_source
    assert "from './TenderEconomicsSupplierCatalogs'" in economics_supplier_input_source
    assert "from './TenderEconomicsSupplierCatalogHealth'" in economics_supplier_input_source
    assert "from './TenderEconomicsSupplierActions'" in economics_supplier_input_source
    assert "from './TenderEconomicsSupplierFields'" in economics_supplier_input_source
    assert "from './TenderEconomicsSupplierPayloads'" in economics_supplier_input_source
    assert "from './TenderEconomicsSupplierPayloads'" in economics_supplier_actions_source
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
    assert "export function SupplierCatalogPresetControls" in economics_supplier_catalogs_source
    assert "export function SupplierCatalogHealthPanel" not in economics_supplier_catalogs_source
    assert "export function SupplierCatalogHealthPanel" in economics_supplier_catalog_health_source
    assert "export function SupplierSearchPreview" in economics_supplier_discovery_source
    assert "export function SupplierDiscoveryPreview" in economics_supplier_discovery_source
    assert "export function SupplierOptionsList" in economics_supplier_options_source
    assert "export function SupplierInputForm" in economics_supplier_input_source
    assert "export function SupplierActionBar" in economics_supplier_actions_source
    assert "export function SupplierInputFields" in economics_supplier_fields_source
    assert "export function supplierOptionPayload" not in economics_supplier_fields_source
    assert "export function supplierOptionPayload" in economics_supplier_payloads_source
    assert "export function supplierUrlDiscoveryPayload" in economics_supplier_payloads_source
    assert "export function supplierSourceKind" in economics_supplier_payloads_source
    assert "export function hasSupplierOptionInput" in economics_supplier_payloads_source
    assert "function SupplierActionBar" not in economics_supplier_input_source
    assert "function SupplierInputFields" not in economics_supplier_input_source
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
    assert find_mojibake(economics_supplier_catalogs_source, TENDER_ECONOMICS_SUPPLIER_CATALOGS_SOURCE) == []
    assert find_mojibake(economics_supplier_catalog_health_source, TENDER_ECONOMICS_SUPPLIER_CATALOG_HEALTH_SOURCE) == []
    assert find_mojibake(economics_supplier_discovery_source, TENDER_ECONOMICS_SUPPLIER_DISCOVERY_SOURCE) == []
    assert find_mojibake(economics_supplier_options_source, TENDER_ECONOMICS_SUPPLIER_OPTIONS_SOURCE) == []
    assert find_mojibake(economics_supplier_input_source, TENDER_ECONOMICS_SUPPLIER_INPUT_SOURCE) == []
    assert find_mojibake(economics_supplier_actions_source, TENDER_ECONOMICS_SUPPLIER_ACTIONS_SOURCE) == []
    assert find_mojibake(economics_supplier_fields_source, TENDER_ECONOMICS_SUPPLIER_FIELDS_SOURCE) == []
    assert find_mojibake(economics_supplier_payloads_source, TENDER_ECONOMICS_SUPPLIER_PAYLOADS_SOURCE) == []
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

    assert "from './TenderDecisionStrip'" in tender_details_source
    assert "from './TenderDecisionSummary'" in tender_details_source
    assert "export function TenderDecisionStrip" in strip_source
    assert "decision-strip-grid" in strip_source
    assert "documentStatusCounts" in strip_source
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
    assert "TenderDocumentsTab" in workspaces_source
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
    assert "function isCurrentRequest(requestRef, requestId, requestTenderKey, currentTenderKeyRef)" in hook_source
    assert "downloadRequestRef.current = null" in hook_source
    assert "extractRequestRef.current = null" in hook_source
    assert "analysisRequestRef.current = null" in hook_source
    assert "setDownloading(false)" in hook_source
    assert "setExtracting(false)" in hook_source
    assert "setAnalyzing(false)" in hook_source
    assert "if (!isCurrentRequest(downloadRequestRef, requestId, requestTenderKey, currentTenderKeyRef)) return" in hook_source
    assert "if (!isCurrentRequest(extractRequestRef, requestId, requestTenderKey, currentTenderKeyRef)) return" in hook_source
    assert "if (!isCurrentRequest(analysisRequestRef, requestId, requestTenderKey, currentTenderKeyRef)) return" in hook_source
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

    assert "<AnalysisChecklist items={analysis.checklist} />" in source
    assert "export function AnalysisChecklist" in source
    assert "Проверочный список" in source
    assert "analysis-checklist" in source
    assert "grid-template-columns: minmax(120px, 0.34fr) minmax(0, 1.4fr) minmax(190px, 0.58fr)" in styles
    assert ".analysis-card," in styles
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
    assert "fulfillmentRequirementTypeLabel" in formatter_source
    assert "Поставка и исполнение" in source
    assert find_mojibake(source, TENDER_PRODUCTS_TAB_SOURCE) == []


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
    assert "<EconomicsSummary economics={economics} tender={tender} />" in source
    assert "function EconomicsSummary" not in source
    assert "export function EconomicsSummary" in economics_summary_source
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
    assert "logistics_cost" in cost_form_source
    assert "documents_cost" in cost_form_source
    assert "other_costs" in cost_form_source
    assert "Себестоимость" in cost_form_source
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
    catalogs_source = (
        TENDER_ECONOMICS_SUPPLIER_CATALOGS_SOURCE.read_text(encoding="utf-8")
        if TENDER_ECONOMICS_SUPPLIER_CATALOGS_SOURCE.exists()
        else ""
    )
    catalog_health_source = (
        TENDER_ECONOMICS_SUPPLIER_CATALOG_HEALTH_SOURCE.read_text(encoding="utf-8")
        if TENDER_ECONOMICS_SUPPLIER_CATALOG_HEALTH_SOURCE.exists()
        else ""
    )
    profile_workspace_source = (
        TENDER_ECONOMICS_PROFILE_WORKSPACE_SOURCE.read_text(encoding="utf-8")
        if TENDER_ECONOMICS_PROFILE_WORKSPACE_SOURCE.exists()
        else ""
    )
    input_source = (
        TENDER_ECONOMICS_SUPPLIER_INPUT_SOURCE.read_text(encoding="utf-8")
        if TENDER_ECONOMICS_SUPPLIER_INPUT_SOURCE.exists()
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
    input_source = (
        TENDER_ECONOMICS_SUPPLIER_INPUT_SOURCE.read_text(encoding="utf-8")
        if TENDER_ECONOMICS_SUPPLIER_INPUT_SOURCE.exists()
        else ""
    )
    actions_source = (
        TENDER_ECONOMICS_SUPPLIER_ACTIONS_SOURCE.read_text(encoding="utf-8")
        if TENDER_ECONOMICS_SUPPLIER_ACTIONS_SOURCE.exists()
        else ""
    )
    fields_source = (
        TENDER_ECONOMICS_SUPPLIER_FIELDS_SOURCE.read_text(encoding="utf-8")
        if TENDER_ECONOMICS_SUPPLIER_FIELDS_SOURCE.exists()
        else ""
    )
    payloads_source = (
        TENDER_ECONOMICS_SUPPLIER_PAYLOADS_SOURCE.read_text(encoding="utf-8")
        if TENDER_ECONOMICS_SUPPLIER_PAYLOADS_SOURCE.exists()
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
    assert "from './TenderEconomicsSupplierDiscovery'" in source
    assert "from './TenderEconomicsSupplierOptions'" in source
    assert "from './TenderEconomicsSupplierInputForm'" in source
    assert "from './TenderEconomicsSupplierCatalogs'" in input_source
    assert "from './TenderEconomicsSupplierCatalogHealth'" in input_source
    assert "from './TenderEconomicsSupplierActions'" in input_source
    assert "from './TenderEconomicsSupplierFields'" in input_source
    assert "from './TenderEconomicsSupplierPayloads'" in input_source
    assert "from './TenderEconomicsSupplierPayloads'" in actions_source
    assert "export function ProductSupplierOptionsForm" in source
    assert "function ProductSupplierOptionsForm" not in tab_source
    assert "<ProductSupplierOptionsForm" in profile_workspace_source
    assert "onSupplierOptionSave" in tab_source
    assert "selectSupplierOption" in details_source
    assert "autoSelectSupplierOption" in details_source
    assert "prepareSupplierSearch" in details_source
    assert "prepareProfileSupplierSearch" in hook_source
    assert "runSupplierDiscovery" in details_source
    assert "runProfileSupplierDiscovery" in hook_source
    assert "runSupplierUrlDiscovery" in details_source
    assert "runProfileSupplierUrlDiscovery" in hook_source
    assert "err.payload?.product_profiles" in hook_source
    assert "applyProductTenderState(err.payload, { resetSelection: false })" in hook_source
    assert "importSupplierDiscoveryCandidate" in details_source
    assert "importProfileSupplierDiscoveryCandidate" in hook_source
    assert "onSupplierOptionSelect" in tab_source
    assert "onSupplierOptionAutoSelect" in tab_source
    assert "onSupplierCatalogPresetsSave" in tab_source
    assert "onSupplierSearchPrepare" in tab_source
    assert "onSupplierDiscoveryRun" in tab_source
    assert "onSupplierUrlDiscoveryRun" in tab_source
    assert "onSupplierDiscoveryImport" in tab_source
    assert "preparingSupplierSearchPosition" in details_source
    assert "discoveringSupplierPosition" in details_source
    assert "importingSupplierCandidatePosition" in details_source
    assert "savingSupplierCatalogPresetPosition" in details_source
    assert "preparingSupplierSearchPosition" in workspaces_source
    assert "discoveringSupplierPosition" in workspaces_source
    assert "importingSupplierCandidatePosition" in workspaces_source
    assert "product-profiles/${profile.position_index}" in api_source
    assert "${productProfilePath(tender, profile)}/supplier-options" in api_source
    assert "${productProfilePath(tender, profile)}/supplier-options/${optionIndex}/select" in api_source
    assert "supplier-options/best/select" in api_source
    assert "supplier-catalog-presets" in api_source
    assert "saveProfileSupplierCatalogPresets" in api_source
    assert "supplier-search/prepare" in api_source
    assert "supplier-discovery/run" in api_source
    assert "supplier-discovery/url" in api_source
    assert "runProfileSupplierUrlDiscovery" in api_source
    assert "supplier-discovery/candidates/${candidateIndex}/import" in api_source
    assert "supplier_options" in source
    assert "supplier_search" in source
    assert "supplier_discovery" in source
    assert "SupplierSearchPreview" in source
    assert "SupplierOptionsList" in source
    assert "SupplierInputForm" in source
    assert "SupplierCatalogPresetControls" in input_source
    assert "export function SupplierInputForm" in input_source
    assert "export function SupplierCatalogHealthPanel" in catalog_health_source
    assert "export function SupplierActionBar" in actions_source
    assert "export function SupplierInputFields" in fields_source
    assert "function SupplierActionBar" not in input_source
    assert "function SupplierInputFields" not in input_source
    assert "from './TenderEconomicsSupplierCatalogs'" in input_source
    assert "SupplierCatalogPresetControls" in input_source
    assert "SupplierCatalogHealthPanel" in input_source
    assert "supplierOptionPayload(values, supplierSearchQueries)" in input_source
    assert "supplierUrlDiscoveryPayload(values, supplierSearchQueries)" in actions_source
    assert "export function supplierOptionPayload" not in fields_source
    assert "export function supplierUrlDiscoveryPayload" not in fields_source
    assert "export function supplierSourceKind" not in fields_source
    assert "export function hasSupplierOptionInput" not in fields_source
    assert "export function supplierOptionFormValues" in payloads_source
    assert "export function supplierOptionPayload" in payloads_source
    assert "export function supplierUrlDiscoveryPayload" in payloads_source
    assert "export function supplierSourceKind" in payloads_source
    assert "export function hasSupplierOptionInput" in payloads_source
    assert "source_kind" in payloads_source
    assert "source_query" in fields_source
    assert "availability" in fields_source
    assert "SUPPLIER_CATALOG_PRESETS" in catalogs_source
    assert "supplier_catalog_preset_ids" in catalogs_source
    assert "ignoreSupplierActionError" in actions_source
    assert "onPresetSave(profile, nextPresetIds)" in catalogs_source
    assert "onPresetSave(profile, null)" in catalogs_source
    assert "SupplierDiscoveryPreview" in source
    assert "export function SupplierSearchPreview" in discovery_source
    assert "export function SupplierDiscoveryPreview" in discovery_source
    assert "function SupplierDiscoveryDiagnostics" in discovery_source
    assert "discovery?.status === 'no_candidates'" in discovery_source
    assert "Кандидаты не найдены" in discovery_source
    assert "Смотри диагностику ниже" in discovery_source
    assert "candidates.length > 0" in discovery_source
    assert "collector_diagnostics" in discovery_source
    assert "diagnostics.pages_fetched" in discovery_source
    assert "diagnostics.candidates_found" in discovery_source
    assert "diagnostics.links_skipped" in discovery_source
    assert "diagnostics.errors" in discovery_source
    assert "supplierConfidenceLabel(candidate.confidence)" in discovery_source
    assert "candidate.provider" in discovery_source
    assert "confidence_reasons" in discovery_source
    assert "quick_links" in discovery_source
    assert "supplier-search-links" in discovery_source
    assert "href={link.url}" in discovery_source
    assert "discoveringDiscovery" in actions_source
    assert "Проверить ссылку" in actions_source
    assert "supplierUrlDiscoveryPayload(values, supplierSearchQueries)" in actions_source
    assert "source_query" in fields_source
    assert "source_kind" in payloads_source
    assert "supplierOptionPayload" in payloads_source
    assert "review_status" in discovery_source
    assert "economics_price_source" in cost_form_source
    assert "EconomicsPriceSource" in cost_form_source
    assert "unit_price" in cost_form_source
    assert 'name="unit_price"' not in cost_form_source
    assert "updateField('unit_price'" not in cost_form_source
    assert "values.unit_price" not in cost_form_source
    assert "availability" in fields_source
    assert "export function SupplierOptionsList" in options_source
    assert "supplier-options-list" in options_source
    assert "supplier-option-row" in options_source
    assert "supplier-select-button" in options_source
    assert "formatMoney(option.unit_price)" in options_source
    assert "supplierAvailabilityLabel(option.availability)" in options_source
    assert "supplierStatusLabel(option.status)" in options_source
    assert "option.status === 'selected'" in options_source
    assert "onSelect?.(index)" in options_source
    assert "Лучший в расчет" in actions_source
    assert "Источник цены" in cost_form_source
    assert "В расчет" in options_source
    assert "selected: 'в расчете'" in formatter_source
    assert "Поставщики" in input_source
    assert ".supplier-search-preview" in styles_source
    assert ".supplier-catalog-presets" in styles_source
    assert ".supplier-catalog-preset-grid" in styles_source
    assert ".supplier-search-links" in styles_source
    assert ".supplier-discovery-preview" in styles_source
    assert ".supplier-discovery-diagnostics" in styles_source
    assert ".supplier-discovery-metrics" in styles_source
    assert find_mojibake(details_source, TENDER_DETAILS_SOURCE) == []
    assert find_mojibake(tabs_source, TENDER_DETAILS_TABS_SOURCE) == []
    assert find_mojibake(workspaces_source, TENDER_WORKSPACES_SOURCE) == []
    assert find_mojibake(hook_source, USE_TENDER_PRODUCT_PROFILES_SOURCE) == []
    assert find_mojibake(tab_source, TENDER_ECONOMICS_TAB_SOURCE) == []
    assert find_mojibake(workbench_source, TENDER_ECONOMICS_WORKBENCH_SOURCE) == []
    assert find_mojibake(source, TENDER_ECONOMICS_SUPPLIERS_SOURCE) == []
    assert find_mojibake(catalogs_source, TENDER_ECONOMICS_SUPPLIER_CATALOGS_SOURCE) == []
    assert find_mojibake(discovery_source, TENDER_ECONOMICS_SUPPLIER_DISCOVERY_SOURCE) == []
    assert find_mojibake(options_source, TENDER_ECONOMICS_SUPPLIER_OPTIONS_SOURCE) == []
    assert find_mojibake(input_source, TENDER_ECONOMICS_SUPPLIER_INPUT_SOURCE) == []
    assert find_mojibake(catalog_health_source, TENDER_ECONOMICS_SUPPLIER_CATALOG_HEALTH_SOURCE) == []
    assert find_mojibake(actions_source, TENDER_ECONOMICS_SUPPLIER_ACTIONS_SOURCE) == []
    assert find_mojibake(fields_source, TENDER_ECONOMICS_SUPPLIER_FIELDS_SOURCE) == []
    assert find_mojibake(payloads_source, TENDER_ECONOMICS_SUPPLIER_PAYLOADS_SOURCE) == []
    assert find_mojibake(forms_source, TENDER_ECONOMICS_FORMS_SOURCE) == []
    assert find_mojibake(cost_form_source, TENDER_ECONOMICS_COST_FORM_SOURCE) == []
    assert find_mojibake(styles_source, STYLES_SOURCE) == []


def test_economics_tab_surfaces_supplier_catalog_health():
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
    source = (
        TENDER_ECONOMICS_SUPPLIERS_SOURCE.read_text(encoding="utf-8")
        if TENDER_ECONOMICS_SUPPLIERS_SOURCE.exists()
        else ""
    )
    catalogs_source = (
        TENDER_ECONOMICS_SUPPLIER_CATALOGS_SOURCE.read_text(encoding="utf-8")
        if TENDER_ECONOMICS_SUPPLIER_CATALOGS_SOURCE.exists()
        else ""
    )
    catalog_health_source = (
        TENDER_ECONOMICS_SUPPLIER_CATALOG_HEALTH_SOURCE.read_text(encoding="utf-8")
        if TENDER_ECONOMICS_SUPPLIER_CATALOG_HEALTH_SOURCE.exists()
        else ""
    )
    input_source = (
        TENDER_ECONOMICS_SUPPLIER_INPUT_SOURCE.read_text(encoding="utf-8")
        if TENDER_ECONOMICS_SUPPLIER_INPUT_SOURCE.exists()
        else ""
    )
    profile_workspace_source = (
        TENDER_ECONOMICS_PROFILE_WORKSPACE_SOURCE.read_text(encoding="utf-8")
        if TENDER_ECONOMICS_PROFILE_WORKSPACE_SOURCE.exists()
        else ""
    )
    api_source = API_SOURCE.read_text(encoding="utf-8")
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "export function fetchSupplierCatalogHealth" in api_source
    assert "/api/supplier-catalogs/health" in api_source
    assert "live = false" in api_source
    assert "?live=1" in api_source
    assert "Не удалось проверить каталоги поставщиков" in api_source
    assert "fetchSupplierCatalogHealth" in hook_source
    assert "refreshSupplierCatalogHealth" in hook_source
    assert "fetchSupplierCatalogHealth({ live })" in hook_source
    assert "refreshSupplierCatalogHealth(false).catch" not in hook_source
    assert "supplierCatalogHealth" in hook_source
    assert "supplierCatalogHealthLoading" in hook_source
    assert "supplierCatalogHealthError" in hook_source
    assert "setSupplierCatalogHealth" in hook_source
    assert "setSupplierCatalogHealthLoading" in hook_source
    assert "setSupplierCatalogHealthError" in hook_source
    assert "onSupplierCatalogHealthRefresh: refreshSupplierCatalogHealth" in details_source
    assert "supplierCatalogHealth" in details_source
    assert "onSupplierCatalogHealthRefresh," in workspaces_source
    assert "supplierCatalogHealth," in workspaces_source
    assert "supplierCatalogHealthLoading," in workspaces_source
    assert "supplierCatalogHealthError," in workspaces_source
    assert "economicsState={economicsState}" in tabs_source
    assert "from './TenderEconomicsSuppliers'" not in tab_source
    assert "from './TenderEconomicsSuppliers'" not in workbench_source
    assert "from './TenderEconomicsSuppliers'" in profile_workspace_source
    assert "from './TenderEconomicsSupplierCatalogs'" in input_source
    assert "from './TenderEconomicsSupplierCatalogHealth'" in input_source
    assert "SupplierCatalogHealthPanel" in input_source
    assert "export function SupplierCatalogHealthPanel" not in catalogs_source
    assert "export function SupplierCatalogHealthPanel" in catalog_health_source
    assert "supplierCatalogHealth?.catalogs" in catalog_health_source
    assert "supplier-catalog-health" in catalog_health_source
    assert "supplier-catalog-health-grid" in catalog_health_source
    assert "onSupplierCatalogHealthRefresh?.(false)" in tab_source
    assert "supplierCatalogHealthLoading || supplierCatalogHealthError" in tab_source
    assert "catalog.http_status" in catalog_health_source
    assert "catalog.error_kind" in catalog_health_source
    assert "catalog.body_preview" in catalog_health_source
    assert "catalog.sample_url" in catalog_health_source
    assert "onSupplierCatalogHealthRefresh" in source
    assert "onRefresh?.(true)" in catalog_health_source
    assert "Статус каталогов" in catalog_health_source
    assert "Проверить" in catalog_health_source
    assert "доступен" in catalog_health_source
    assert "блокировка" in catalog_health_source
    assert "сеть недоступна" in catalog_health_source
    assert "ошибка" in catalog_health_source
    assert "настроен" in catalog_health_source
    assert "??????" not in api_source
    assert "??????" not in source
    assert "??????" not in catalogs_source
    assert "??????" not in catalog_health_source
    assert ".supplier-catalog-health" in styles_source
    assert ".supplier-catalog-health-heading" in styles_source
    assert ".supplier-catalog-health-grid" in styles_source
    assert find_mojibake(details_source, TENDER_DETAILS_SOURCE) == []
    assert find_mojibake(tabs_source, TENDER_DETAILS_TABS_SOURCE) == []
    assert find_mojibake(workspaces_source, TENDER_WORKSPACES_SOURCE) == []
    assert find_mojibake(hook_source, USE_TENDER_PRODUCT_PROFILES_SOURCE) == []
    assert find_mojibake(tab_source, TENDER_ECONOMICS_TAB_SOURCE) == []
    assert find_mojibake(workbench_source, TENDER_ECONOMICS_WORKBENCH_SOURCE) == []
    assert find_mojibake(profile_workspace_source, TENDER_ECONOMICS_PROFILE_WORKSPACE_SOURCE) == []
    assert find_mojibake(source, TENDER_ECONOMICS_SUPPLIERS_SOURCE) == []
    assert find_mojibake(catalogs_source, TENDER_ECONOMICS_SUPPLIER_CATALOGS_SOURCE) == []
    assert find_mojibake(catalog_health_source, TENDER_ECONOMICS_SUPPLIER_CATALOG_HEALTH_SOURCE) == []
    assert find_mojibake(input_source, TENDER_ECONOMICS_SUPPLIER_INPUT_SOURCE) == []
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
    assert ".auto-economics-panel" in styles_source
    assert find_mojibake(details_source, TENDER_DETAILS_SOURCE) == []
    assert find_mojibake(tab_source, TENDER_ECONOMICS_TAB_SOURCE) == []
    assert find_mojibake(workbench_source, TENDER_ECONOMICS_WORKBENCH_SOURCE) == []
    assert find_mojibake(profile_workspace_source, TENDER_ECONOMICS_PROFILE_WORKSPACE_SOURCE) == []
    assert find_mojibake(source, TENDER_ECONOMICS_AUTO_SOURCE) == []
    assert find_mojibake(styles_source, STYLES_SOURCE) == []

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
    assert "economics.participation_decision" in source
    assert "function ParticipationDecisionCard" not in source
    assert "export function ParticipationDecisionCard" in scenarios_source
    assert "Решение по участию" in scenarios_source
    assert "Лимит" in scenarios_source
    assert "participation-decision" in scenarios_source
    assert ".participation-decision" in styles_source
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
    assert "export function TenderEconomicsWorkbench({" in app_source
    assert "export function TenderEconomicsProfileWorkspace({" in profile_workspace_source
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

    assert "workspace workbench-layout" in app_source
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
    assert "grid-template-columns: 260px minmax(360px, 1fr) minmax(0, 1.35fr)" in styles_source
    assert "grid-template-columns: 58px minmax(360px, 1.1fr) minmax(0, 1.25fr)" in styles_source
    assert "overflow-x: hidden" in styles_source
    assert ".filters-panel.collapsed" in styles_source
    assert find_mojibake(app_source, APP_SOURCE) == []
    assert find_mojibake(styles_source, STYLES_SOURCE) == []


def test_tender_details_v2_keeps_actions_and_document_statuses_scannable():
    app_source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
    header_source = TENDER_DETAILS_HEADER_SOURCE.read_text(encoding="utf-8")
    actions_source = (
        TENDER_DETAIL_ACTIONS_SOURCE.read_text(encoding="utf-8")
        if TENDER_DETAIL_ACTIONS_SOURCE.exists()
        else ""
    )
    documents_source = TENDER_DOCUMENTS_TAB_SOURCE.read_text(encoding="utf-8")
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")
    detail_actions_rule = _css_rule(styles_source, ".detail-actions")

    assert "details-title-row" in header_source
    assert "<TenderDetailActions" in app_source
    assert "details-action-group primary-actions" in actions_source
    assert "details-action-group secondary-actions" not in actions_source
    assert "documentStatusLabel" in documents_source
    assert "document-status ${document.text_status || 'pending'}" in documents_source
    assert "download-status ${document.local_path ? 'downloaded' : 'missing'}" in documents_source
    assert "grid-template-columns: repeat(4" not in detail_actions_rule
    assert ("flex-wrap: wrap" in detail_actions_rule or "auto-fit" in detail_actions_rule)
    assert ".detail-workspace-launchers" not in styles_source
    assert ".document-status.unsupported" in styles_source
    assert ".document-status.ok" in styles_source
    assert find_mojibake(app_source, TENDER_DETAILS_SOURCE) == []
    assert find_mojibake(header_source, TENDER_DETAILS_HEADER_SOURCE) == []
    assert find_mojibake(actions_source, TENDER_DETAIL_ACTIONS_SOURCE) == []
    assert find_mojibake(documents_source, TENDER_DOCUMENTS_TAB_SOURCE) == []
    assert find_mojibake(styles_source, STYLES_SOURCE) == []


def test_tender_detail_tabs_have_scannable_work_areas():
    panels_source = TENDER_TAB_PANELS_SOURCE.read_text(encoding="utf-8")
    workspaces_source = TENDER_WORKSPACES_SOURCE.read_text(encoding="utf-8")
    summary_source = TENDER_SUMMARY_TAB_SOURCE.read_text(encoding="utf-8")
    documents_source = TENDER_DOCUMENTS_TAB_SOURCE.read_text(encoding="utf-8")
    products_source = (
        TENDER_PRODUCTS_TAB_SOURCE.read_text(encoding="utf-8")
        if TENDER_PRODUCTS_TAB_SOURCE.exists()
        else ""
    )
    formatter_source = FORMATTERS_SOURCE.read_text(encoding="utf-8")
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "export function TenderSummaryTab" in summary_source
    assert "function ProductTabSummary" in products_source
    assert "function DocumentStatusSummary" in documents_source
    assert "export function documentStatusCounts" in formatter_source
    assert "<TenderSummaryTab" in panels_source
    assert "<TenderProductsTab" in workspaces_source
    assert "<ProductTabSummary" in products_source
    assert "<TenderDocumentsTab" in workspaces_source
    assert "summary-decision-grid" not in summary_source
    assert "SummaryMetric" not in summary_source
    assert "summary-work-grid" in summary_source
    assert "document-status-summary" in documents_source
    assert "product-tab-summary" in products_source
    assert ".summary-decision-grid" not in styles_source
    assert ".summary-work-grid" in styles_source
    assert ".document-status-summary" in styles_source
    assert ".product-tab-summary" in styles_source
    assert find_mojibake(panels_source, TENDER_TAB_PANELS_SOURCE) == []
    assert find_mojibake(workspaces_source, TENDER_WORKSPACES_SOURCE) == []
    assert find_mojibake(summary_source, TENDER_SUMMARY_TAB_SOURCE) == []
    assert find_mojibake(documents_source, TENDER_DOCUMENTS_TAB_SOURCE) == []
    assert find_mojibake(products_source, TENDER_PRODUCTS_TAB_SOURCE) == []
    assert find_mojibake(styles_source, STYLES_SOURCE) == []


def test_analysis_tab_exposes_word_report_and_source_evidence_workspace():
    workspaces_source = TENDER_WORKSPACES_SOURCE.read_text(encoding="utf-8")
    analysis_source = TENDER_ANALYSIS_TAB_SOURCE.read_text(encoding="utf-8")
    analysis_sections_source = TENDER_ANALYSIS_SECTIONS_SOURCE.read_text(encoding="utf-8")
    analysis_evidence_source = TENDER_ANALYSIS_EVIDENCE_SOURCE.read_text(encoding="utf-8")
    analysis_evidence_model_source = TENDER_ANALYSIS_EVIDENCE_MODEL_SOURCE.read_text(encoding="utf-8")
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "reportHref" in workspaces_source
    assert "documents={documentRecords}" in workspaces_source
    assert "analysis-action-row" in analysis_source
    assert "Скачать Word" in analysis_source
    assert "analysis-workspace" in analysis_source
    assert "analysis-section-rail" in analysis_sections_source
    assert "const [selectedAnalysisSection, setSelectedAnalysisSection]" in analysis_source
    assert "analysisSectionItems(analysis, documents)" in analysis_source
    assert "<AnalysisSectionRail" in analysis_source
    assert "onSelectSection={setSelectedAnalysisSection}" in analysis_source
    assert "<AnalysisSectionBody" in analysis_source
    assert "<AnalysisEvidencePanel" in analysis_source
    assert "sections.map" in analysis_sections_source
    assert "onClick={() => onSelectSection(section.id)}" in analysis_sections_source
    assert "aria-pressed={active}" in analysis_sections_source
    assert "analysis-evidence-panel" in analysis_evidence_source
    assert "from './TenderAnalysisEvidenceModel'" in analysis_evidence_source
    assert "from './TenderAnalysisEvidenceModel'" in analysis_sections_source
    assert "export function buildDocumentEvidenceItems" in analysis_evidence_model_source
    assert ".analysis-workspace" in styles_source
    assert ".analysis-evidence-panel" in styles_source
    assert ".analysis-section-item:hover" in styles_source
    assert find_mojibake(workspaces_source, TENDER_WORKSPACES_SOURCE) == []
    assert find_mojibake(analysis_source, TENDER_ANALYSIS_TAB_SOURCE) == []
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
    assert "onOpenSection={setSelectedAnalysisSection}" in analysis_source
    assert "export function AnalysisDecisionBrief" in decision_source
    assert "export function buildAnalysisDecision" in decision_source
    assert "analysis-decision-brief" in decision_source
    assert "Короткое решение" in decision_source
    assert "Ключевые причины" in decision_source
    assert "reasons.slice(0, 3)" in decision_source
    assert "onOpenSection?.('risks')" in decision_source
    assert "onOpenSection?.('requirements')" in decision_source
    assert ".analysis-decision-brief" in styles_source
    assert ".analysis-reason-list" in styles_source
    assert find_mojibake(analysis_source, TENDER_ANALYSIS_TAB_SOURCE) == []
    assert find_mojibake(decision_source, TENDER_ANALYSIS_DECISION_SOURCE) == []
    assert find_mojibake(styles_source, STYLES_SOURCE) == []


def test_analysis_documents_render_structured_evidence_model():
    sections_source = TENDER_ANALYSIS_SECTIONS_SOURCE.read_text(encoding="utf-8")
    evidence_source = TENDER_ANALYSIS_EVIDENCE_SOURCE.read_text(encoding="utf-8")
    model_source = TENDER_ANALYSIS_EVIDENCE_MODEL_SOURCE.read_text(encoding="utf-8")
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "buildDocumentEvidenceItems(analysis, documents)" in sections_source
    assert "buildDocumentEvidenceItems(analysis, documents)" in evidence_source
    assert "analysis-document-evidence-grid" in sections_source
    assert "analysis-evidence-item" in evidence_source
    assert "analysis-evidence-item" in sections_source
    assert "item.typeLabel" in evidence_source
    assert "item.importanceLabel" in evidence_source
    assert "item.documentName" in evidence_source
    assert "item.fragment" in evidence_source
    assert "item.impact" in evidence_source
    assert "category: item.category || 'general'" in model_source
    assert "importanceLabel: evidenceImportanceLabel(item.severity)" in model_source
    assert "typeLabel: evidenceTypeLabel(item.category)" in model_source
    assert "impact: evidenceImpactLabel(item)" in model_source
    assert "documentName: resolveEvidenceDocumentName(item, documents)" in model_source
    assert ".analysis-document-evidence-grid" in styles_source
    assert ".analysis-evidence-meta" in styles_source
    assert ".analysis-evidence-impact" in styles_source
    assert find_mojibake(sections_source, TENDER_ANALYSIS_SECTIONS_SOURCE) == []
    assert find_mojibake(evidence_source, TENDER_ANALYSIS_EVIDENCE_SOURCE) == []
    assert find_mojibake(model_source, TENDER_ANALYSIS_EVIDENCE_MODEL_SOURCE) == []
    assert find_mojibake(styles_source, STYLES_SOURCE) == []


def test_economics_tab_uses_three_column_position_workspace():
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
    assert "economics-calculation-panel" in profile_workspace_source
    assert "economics-supplier-panel" in profile_workspace_source
    assert "<ProductEconomicsForm profile={selectedEconomicsProfile}" in profile_workspace_source
    assert "<ProductSupplierOptionsForm" in profile_workspace_source
    assert ".economics-workspace-grid" in styles_source
    assert ".economics-position-rail" in styles_source
    assert ".economics-calculation-panel" in styles_source
    assert ".economics-supplier-panel" in styles_source
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
    assert 'variant="products"' in summary_source
    assert 'variant="documents"' in summary_source
    assert 'className="summary-next-action summary-card secondary"' in summary_source
    assert summary_source.index('variant="economics"') < summary_source.index('variant="analysis"')
    assert summary_source.index('variant="analysis"') < summary_source.index('summary-next-action')
    assert "grid-template-columns: repeat(6, minmax(0, 1fr))" in summary_grid_rule
    assert "grid-auto-rows: minmax(172px, 1fr)" in summary_grid_rule
    assert "grid-column: span 3" in primary_card_rule
    assert "grid-column: span 2" in secondary_card_rule
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


def test_products_documents_analysis_and_economics_open_in_fullscreen_workspace():
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
    assert "onClick={() => onOpenTab?.('products')}" in summary_source
    assert "onClick={() => onOpenTab?.('documents')}" in summary_source
    assert "onClick={() => onOpenTab?.('analysis')}" in summary_source
    assert "onClick={() => onOpenTab?.('economics')}" in summary_source
    assert "from './TenderFullscreenWorkspace'" in workspaces_source
    assert "from './TenderProductsTab'" in workspaces_source
    assert "from './TenderDocumentsTab'" in workspaces_source
    assert "<TenderFullscreenWorkspace" in workspaces_source
    assert "mode === 'products'" in workspaces_source
    assert "mode === 'documents'" in workspaces_source
    assert "mode === 'analysis'" in workspaces_source
    assert "mode === 'economics'" in workspaces_source
    assert "<TenderProductsTab" in workspaces_source
    assert "<TenderDocumentsTab" in workspaces_source
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


def test_products_documents_analysis_and_economics_are_workspace_launchers_not_inline_tabs():
    tabs_source = TENDER_DETAILS_TABS_SOURCE.read_text(encoding="utf-8")
    summary_source = TENDER_SUMMARY_TAB_SOURCE.read_text(encoding="utf-8")
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "const workspaceActions = [" not in tabs_source
    assert "<TenderDetailsNavigation" not in tabs_source
    assert "onClick={() => onOpenTab?.('products')}" in summary_source
    assert "'products'" in tabs_source
    assert "'documents'" in tabs_source
    assert "activeTab === 'products'" not in tabs_source
    assert "activeTab === 'documents'" not in tabs_source
    assert "activeTab === 'analysis'" not in tabs_source
    assert "activeTab === 'economics'" not in tabs_source
    assert ".detail-workspace-launchers" not in styles_source
    assert find_mojibake(tabs_source, TENDER_DETAILS_TABS_SOURCE) == []
    assert find_mojibake(summary_source, TENDER_SUMMARY_TAB_SOURCE) == []
    assert find_mojibake(styles_source, STYLES_SOURCE) == []


def test_tender_workspaces_module_owns_fullscreen_products_documents_analysis_and_economics():
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
    assert "from './TenderDocumentsTab'" in workspaces_source
    assert "from './TenderAnalysisTab'" in workspaces_source
    assert "from './TenderEconomicsTab'" in workspaces_source
    assert "mode === 'products'" in workspaces_source
    assert "mode === 'documents'" in workspaces_source
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
    assert "onOpenTab?.('products')" in summary_source
    assert "onOpenTab?.('documents')" in summary_source
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
    assert "grid-template-columns: minmax(320px, 0.58fr) minmax(420px, 1fr) minmax(360px, 0.78fr)" in fullscreen_economics_rule
    assert "position: sticky" in rail_rule
    assert "top: 0" in rail_rule
    assert "max-height: calc(100vh - 220px)" in rail_rule
    assert "position: sticky" in supplier_rule
    assert "top: 0" in supplier_rule
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

    assert "economics?.break_even_price" in metrics_source
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
    assert "нет расчета" in formatter_source


def test_tender_list_surfaces_market_state_and_economics_decision():
    source = TENDER_LIST_SOURCE.read_text(encoding="utf-8")
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "nmcPriceValue" in source
    assert "marketStateValue(tender.market_state)" in source
    assert "economicsDecisionLabel(tender.economics)" in source
    assert "economics-chip" in source
    assert ".economics-chip" in styles_source
    assert find_mojibake(source, TENDER_LIST_SOURCE) == []


def test_dashboard_surfaces_current_offers_and_saved_economics():
    dashboard_source = DASHBOARD_SOURCE.read_text(encoding="utf-8")
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "currentOfferCount" in dashboard_source
    assert "hasParticipantBid(tender.market_state)" in dashboard_source
    assert "marketMetric" in dashboard_source
    assert "economicsReadyCount" in dashboard_source
    assert "economicsDecisionLabel(tender.economics)" in dashboard_source
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
    assert '<SummaryMetric value={participantBidValue(economics?.market_state || tender?.market_state)} label="ставка участника" />' in metrics_source
    assert "marketStateValue(economics?.market_state || tender?.market_state)" in metrics_source
    assert "marketStateCaption(economics?.market_state || tender?.market_state)" in summary_source
    assert find_mojibake(source, TENDER_ECONOMICS_TAB_SOURCE) == []
    assert find_mojibake(metrics_source, TENDER_ECONOMICS_METRICS_SOURCE) == []
    assert find_mojibake(summary_source, TENDER_ECONOMICS_SUMMARY_SOURCE) == []


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
