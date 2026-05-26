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
TENDER_DETAILS_HEADER_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "TenderDetailsHeader.jsx"
TENDER_DETAILS_STATUS_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "TenderDetailsStatusStack.jsx"
TENDER_ANALYSIS_TAB_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "TenderAnalysisTab.jsx"
TENDER_DECISION_SUMMARY_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "TenderDecisionSummary.jsx"
TENDER_DOCUMENTS_TAB_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "TenderDocumentsTab.jsx"
TENDER_ECONOMICS_TAB_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "TenderEconomicsTab.jsx"
TENDER_OVERVIEW_TAB_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "TenderOverviewTab.jsx"
TENDER_PRODUCTS_TAB_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "TenderProductsTab.jsx"
TENDER_WORKFLOW_TAB_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "TenderWorkflowTab.jsx"
TENDER_LIST_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "TenderList.jsx"
USE_TENDER_DOCUMENT_ANALYSIS_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "useTenderDocumentAnalysis.js"
USE_TENDER_PRODUCT_PROFILES_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "useTenderProductProfiles.js"
USE_TENDER_WORKFLOW_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "useTenderWorkflow.js"
USE_TENDER_NOTIFICATION_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "useTenderNotification.js"
USE_TENDER_REFRESH_DETAILS_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "useTenderRefreshDetails.js"


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
    assert "from './TenderDetailActions'" in tender_details_source
    assert "from './TenderDetailsHeader'" in tender_details_source
    assert "from './TenderDetailsStatusStack'" in tender_details_source
    assert "from './TenderDecisionSummary'" in tender_details_source
    assert "from './TenderEconomicsTab'" in tender_details_source
    assert "from './TenderProductsTab'" in tender_details_source
    assert "from './TenderWorkflowTab'" in tender_details_source
    assert "from './useTenderDocumentAnalysis'" in tender_details_source
    assert "from './useTenderProductProfiles'" in tender_details_source
    assert "from './useTenderWorkflow'" in tender_details_source
    assert "from './useTenderNotification'" in tender_details_source
    assert "from './useTenderRefreshDetails'" in tender_details_source
    assert "details-panel" in app_source
    assert "<TenderDetails tender={details}" in app_source
    assert "function TenderDetails" not in app_source
    assert find_mojibake(app_source, APP_SOURCE) == []
    assert find_mojibake(tender_details_source, TENDER_DETAILS_SOURCE) == []


def test_frontend_uses_dedicated_tender_overview_tab_module():
    tender_details_source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
    overview_source = (
        TENDER_OVERVIEW_TAB_SOURCE.read_text(encoding="utf-8")
        if TENDER_OVERVIEW_TAB_SOURCE.exists()
        else ""
    )

    assert "from './TenderOverviewTab'" in tender_details_source
    assert "export function TenderOverviewTab" in overview_source
    assert "overview-brief-grid" in overview_source
    assert "Паспорт закупки" in overview_source
    assert "<TenderOverviewTab tender={tender} raw={raw} />" in tender_details_source
    assert "function TenderOverviewTab" not in tender_details_source
    assert find_mojibake(tender_details_source, TENDER_DETAILS_SOURCE) == []
    assert find_mojibake(overview_source, TENDER_OVERVIEW_TAB_SOURCE) == []


def test_frontend_uses_dedicated_tender_documents_tab_module():
    tender_details_source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
    documents_source = (
        TENDER_DOCUMENTS_TAB_SOURCE.read_text(encoding="utf-8")
        if TENDER_DOCUMENTS_TAB_SOURCE.exists()
        else ""
    )

    assert "from './TenderDocumentsTab'" in tender_details_source
    assert "export function TenderDocumentsTab" in documents_source
    assert "function DocumentStatusSummary" in documents_source
    assert "document-table" in documents_source
    assert "document-status ${document.text_status || 'pending'}" in documents_source
    assert "<TenderDocumentsTab" in tender_details_source
    assert "function DocumentStatusSummary" not in tender_details_source
    assert "document-table" not in tender_details_source
    assert find_mojibake(tender_details_source, TENDER_DETAILS_SOURCE) == []
    assert find_mojibake(documents_source, TENDER_DOCUMENTS_TAB_SOURCE) == []


def test_frontend_uses_dedicated_tender_analysis_tab_module():
    tender_details_source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
    analysis_source = (
        TENDER_ANALYSIS_TAB_SOURCE.read_text(encoding="utf-8")
        if TENDER_ANALYSIS_TAB_SOURCE.exists()
        else ""
    )

    assert "from './TenderAnalysisTab'" in tender_details_source
    assert "export function TenderAnalysisTab" in analysis_source
    assert "export function AnalysisList" in analysis_source
    assert "function AnalysisChecklist" in analysis_source
    assert "analysis-tab-summary" in analysis_source
    assert "analysis-checklist" in analysis_source
    assert "<TenderAnalysisTab" in tender_details_source
    assert "function AnalysisTabPanel" not in tender_details_source
    assert "function AnalysisChecklist" not in tender_details_source
    assert find_mojibake(tender_details_source, TENDER_DETAILS_SOURCE) == []
    assert find_mojibake(analysis_source, TENDER_ANALYSIS_TAB_SOURCE) == []


def test_frontend_uses_dedicated_tender_economics_tab_module():
    tender_details_source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
    economics_source = (
        TENDER_ECONOMICS_TAB_SOURCE.read_text(encoding="utf-8")
        if TENDER_ECONOMICS_TAB_SOURCE.exists()
        else ""
    )

    assert "from './TenderEconomicsTab'" in tender_details_source
    assert "export function TenderEconomicsTab" in economics_source
    assert "function EconomicsSummary" in economics_source
    assert "function ProductEconomicsForm" in economics_source
    assert "function ProductSupplierOptionsForm" in economics_source
    assert "economics-workbench" in economics_source
    assert "<TenderEconomicsTab" in tender_details_source
    assert "function EconomicsTabPanel" not in tender_details_source
    assert "function ProductEconomicsForm" not in tender_details_source
    assert find_mojibake(tender_details_source, TENDER_DETAILS_SOURCE) == []
    assert find_mojibake(economics_source, TENDER_ECONOMICS_TAB_SOURCE) == []


def test_frontend_uses_dedicated_tender_workflow_tab_module():
    tender_details_source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
    workflow_source = (
        TENDER_WORKFLOW_TAB_SOURCE.read_text(encoding="utf-8")
        if TENDER_WORKFLOW_TAB_SOURCE.exists()
        else ""
    )

    assert "from './TenderWorkflowTab'" in tender_details_source
    assert "export function WorkflowTabPanel" in workflow_source
    assert "workflow-status-summary" in workflow_source
    assert "workflow-note-panel" in workflow_source
    assert "<WorkflowTabPanel" in tender_details_source
    assert "function WorkflowTabPanel" not in tender_details_source
    assert "workflow-status-summary" not in tender_details_source
    assert "workflow-note-panel" not in tender_details_source
    assert find_mojibake(tender_details_source, TENDER_DETAILS_SOURCE) == []
    assert find_mojibake(workflow_source, TENDER_WORKFLOW_TAB_SOURCE) == []


def test_frontend_uses_dedicated_tender_products_tab_module():
    tender_details_source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
    products_source = (
        TENDER_PRODUCTS_TAB_SOURCE.read_text(encoding="utf-8")
        if TENDER_PRODUCTS_TAB_SOURCE.exists()
        else ""
    )

    assert "from './TenderProductsTab'" in tender_details_source
    assert "export function TenderProductsTab" in products_source
    assert "function ProductTabSummary" in products_source
    assert "function ProductProfileDetail" in products_source
    assert "function TenderItems" in products_source
    assert "product-profile-section" in products_source
    assert "product-tab-summary" in products_source
    assert "profile-detail" in products_source
    assert "source-items" in products_source
    assert "<TenderProductsTab" in tender_details_source
    assert "function ProductTabSummary" not in tender_details_source
    assert "function ProductProfileDetail" not in tender_details_source
    assert "function TenderItems" not in tender_details_source
    assert "function ProfileSummary" not in tender_details_source
    assert "product-tab-summary" not in tender_details_source
    assert "profile-detail" not in tender_details_source
    assert "source-items" not in tender_details_source
    assert find_mojibake(tender_details_source, TENDER_DETAILS_SOURCE) == []
    assert find_mojibake(products_source, TENDER_PRODUCTS_TAB_SOURCE) == []


def test_frontend_uses_dedicated_tender_decision_summary_module():
    tender_details_source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
    decision_source = (
        TENDER_DECISION_SUMMARY_SOURCE.read_text(encoding="utf-8")
        if TENDER_DECISION_SUMMARY_SOURCE.exists()
        else ""
    )

    assert "from './TenderDecisionSummary'" in tender_details_source
    assert "export function TenderDecisionSummary" in decision_source
    assert "export function PriceChangeBanner" in decision_source
    assert "decision-summary-grid" in decision_source
    assert "price-change-banner" in decision_source
    assert "formatPriceChangeDirection" in decision_source
    assert "<TenderDecisionSummary tender={tender} economics={economics} />" in tender_details_source
    assert "<PriceChangeBanner change={tender.price_change} />" in tender_details_source
    assert "function TenderDecisionSummary" not in tender_details_source
    assert "function PriceChangeBanner" not in tender_details_source
    assert "decision-summary-grid" not in tender_details_source
    assert "price-change-banner" not in tender_details_source
    assert find_mojibake(tender_details_source, TENDER_DETAILS_SOURCE) == []
    assert find_mojibake(decision_source, TENDER_DECISION_SUMMARY_SOURCE) == []


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
    assert "details-action-group secondary-actions" in actions_source
    assert "onRefreshDetails" in actions_source
    assert "onDownloadDocuments" in actions_source
    assert "onExtractDocumentText" in actions_source
    assert "onAnalyzeTender" in actions_source
    assert "onSendToTelegram" in actions_source
    assert "report.docx" in actions_source
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
    assert "formatMoney" in header_source
    assert "formatDate" in header_source
    assert "sourceLabels" in header_source
    assert "workflowLabels" in header_source
    assert "details-header" in header_source
    assert "<TenderDetailsHeader tender={tender} />" in tender_details_source
    assert "details-header" not in tender_details_source
    assert "Building2" not in tender_details_source
    assert "formatMoney" not in tender_details_source
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
    source = TENDER_ANALYSIS_TAB_SOURCE.read_text(encoding="utf-8")

    assert "<AnalysisChecklist items={analysis.checklist} />" in source
    assert "function AnalysisChecklist" in source
    assert "Проверочный список" in source
    assert "analysis-checklist" in source
    assert "analysisCategoryLabel" in source
    assert "analysisSeverityLabel" in source
    assert find_mojibake(source, TENDER_DETAILS_SOURCE) == []


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
    details_source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
    source = TENDER_ECONOMICS_TAB_SOURCE.read_text(encoding="utf-8")

    assert "{ id: 'economics', label: 'Экономика' }" in details_source
    assert "<EconomicsSummary economics={economics} tender={tender} />" in source
    assert "function EconomicsSummary" in source
    assert "economicsStatusLabel" in source
    assert "Маржа" in source
    assert find_mojibake(details_source, TENDER_DETAILS_SOURCE) == []
    assert find_mojibake(source, TENDER_ECONOMICS_TAB_SOURCE) == []

def test_product_profile_renders_economics_input_form():
    source = TENDER_ECONOMICS_TAB_SOURCE.read_text(encoding="utf-8")
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
    assert find_mojibake(source, TENDER_ECONOMICS_TAB_SOURCE) == []

def test_product_profile_renders_supplier_option_form():
    details_source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
    source = TENDER_ECONOMICS_TAB_SOURCE.read_text(encoding="utf-8")
    api_source = API_SOURCE.read_text(encoding="utf-8")
    formatter_source = FORMATTERS_SOURCE.read_text(encoding="utf-8")

    assert "function ProductSupplierOptionsForm" in source
    assert "onSupplierOptionSave" in source
    assert "selectSupplierOption" in details_source
    assert "autoSelectSupplierOption" in details_source
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
    assert find_mojibake(details_source, TENDER_DETAILS_SOURCE) == []
    assert find_mojibake(source, TENDER_ECONOMICS_TAB_SOURCE) == []

def test_economics_tab_renders_auto_estimate_panel():
    details_source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
    source = TENDER_ECONOMICS_TAB_SOURCE.read_text(encoding="utf-8")
    api_source = API_SOURCE.read_text(encoding="utf-8")
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "runProfileAutoEconomics" in details_source
    assert "acceptProfileAutoEconomics" in details_source
    assert "onAutoEconomicsRun" in source
    assert "onAutoEconomicsAccept" in source
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
    assert find_mojibake(details_source, TENDER_DETAILS_SOURCE) == []
    assert find_mojibake(source, TENDER_ECONOMICS_TAB_SOURCE) == []
    assert find_mojibake(styles_source, STYLES_SOURCE) == []

def test_economics_tab_renders_assumptions_form():
    details_source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
    source = TENDER_ECONOMICS_TAB_SOURCE.read_text(encoding="utf-8")
    api_source = API_SOURCE.read_text(encoding="utf-8")
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "saveProfileEconomicsAssumptions" in details_source
    assert "onEconomicsAssumptionsSave" in source
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
    assert find_mojibake(details_source, TENDER_DETAILS_SOURCE) == []
    assert find_mojibake(source, TENDER_ECONOMICS_TAB_SOURCE) == []
    assert find_mojibake(styles_source, STYLES_SOURCE) == []

def test_economics_tab_renders_bid_scenarios():
    source = TENDER_ECONOMICS_TAB_SOURCE.read_text(encoding="utf-8")
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "BidScenarioStrip" in source
    assert "economics.bid_scenarios" in source
    assert "Сценарии цены" in source
    assert "bid-scenario-grid" in source
    assert ".bid-scenario-grid" in styles_source
    assert find_mojibake(source, TENDER_ECONOMICS_TAB_SOURCE) == []
    assert find_mojibake(styles_source, STYLES_SOURCE) == []

def test_economics_tab_renders_participation_decision():
    source = TENDER_ECONOMICS_TAB_SOURCE.read_text(encoding="utf-8")
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "ParticipationDecisionCard" in source
    assert "economics.participation_decision" in source
    assert "Решение по участию" in source
    assert "Лимит" in source
    assert "participation-decision" in source
    assert ".participation-decision" in styles_source
    assert find_mojibake(source, TENDER_ECONOMICS_TAB_SOURCE) == []
    assert find_mojibake(styles_source, STYLES_SOURCE) == []

def test_economics_tab_owns_product_costs_and_suppliers():
    details_source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
    app_source = TENDER_ECONOMICS_TAB_SOURCE.read_text(encoding="utf-8")
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "export function TenderEconomicsTab({" in app_source
    assert "productProfiles" in app_source
    assert "selectedEconomicsProfileIndex" in app_source
    assert "<ProductEconomicsForm profile={selectedEconomicsProfile}" in app_source
    assert "<ProductSupplierOptionsForm" in app_source
    assert "profile={selectedEconomicsProfile}" in app_source
    assert "<TenderEconomicsTab" in details_source
    assert "economics-workbench" in app_source
    assert ".economics-workbench" in styles_source
    assert find_mojibake(details_source, TENDER_DETAILS_SOURCE) == []
    assert find_mojibake(app_source, TENDER_ECONOMICS_TAB_SOURCE) == []
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


def test_tender_workbench_v1_reduces_detail_panel_overload():
    app_source = APP_SOURCE.read_text(encoding="utf-8")
    tender_details_source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
    decision_source = (
        TENDER_DECISION_SUMMARY_SOURCE.read_text(encoding="utf-8")
        if TENDER_DECISION_SUMMARY_SOURCE.exists()
        else ""
    )
    economics_source = TENDER_ECONOMICS_TAB_SOURCE.read_text(encoding="utf-8")
    overview_source = TENDER_OVERVIEW_TAB_SOURCE.read_text(encoding="utf-8")
    products_source = (
        TENDER_PRODUCTS_TAB_SOURCE.read_text(encoding="utf-8")
        if TENDER_PRODUCTS_TAB_SOURCE.exists()
        else ""
    )
    constants_source = CONSTANTS_SOURCE.read_text(encoding="utf-8")

    assert "workspace workbench-layout" in app_source
    assert "export function TenderDecisionSummary" in decision_source
    assert "<TenderDecisionSummary tender={tender} economics={economics} />" in tender_details_source
    assert "decision-summary-grid" in decision_source
    assert "product-detail-tabs" in products_source
    assert "export const productDetailModes" in constants_source
    assert "Паспорт" in overview_source
    assert "ТЗ" in constants_source
    assert "economics-workbench" in economics_source
    assert find_mojibake(app_source, APP_SOURCE) == []
    assert find_mojibake(tender_details_source, TENDER_DETAILS_SOURCE) == []
    assert find_mojibake(decision_source, TENDER_DECISION_SUMMARY_SOURCE) == []
    assert find_mojibake(economics_source, TENDER_ECONOMICS_TAB_SOURCE) == []
    assert find_mojibake(overview_source, TENDER_OVERVIEW_TAB_SOURCE) == []
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
    assert "minmax(560px, 1.1fr)" in styles_source
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
    detail_tabs_rule = _css_rule(styles_source, ".detail-tabs")

    assert "details-title-row" in header_source
    assert "<TenderDetailActions" in app_source
    assert "details-action-group primary-actions" in actions_source
    assert "details-action-group secondary-actions" in actions_source
    assert "documentStatusLabel" in documents_source
    assert "document-status ${document.text_status || 'pending'}" in documents_source
    assert "download-status ${document.local_path ? 'downloaded' : 'missing'}" in documents_source
    assert "grid-template-columns: repeat(4" not in detail_actions_rule
    assert ("flex-wrap: wrap" in detail_actions_rule or "auto-fit" in detail_actions_rule)
    assert "flex-wrap: wrap" in detail_tabs_rule
    assert "overflow-x: auto" not in detail_tabs_rule
    assert ".document-status.unsupported" in styles_source
    assert ".document-status.ok" in styles_source
    assert find_mojibake(app_source, TENDER_DETAILS_SOURCE) == []
    assert find_mojibake(header_source, TENDER_DETAILS_HEADER_SOURCE) == []
    assert find_mojibake(actions_source, TENDER_DETAIL_ACTIONS_SOURCE) == []
    assert find_mojibake(documents_source, TENDER_DOCUMENTS_TAB_SOURCE) == []
    assert find_mojibake(styles_source, STYLES_SOURCE) == []


def test_tender_detail_tabs_have_scannable_work_areas():
    app_source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
    overview_source = TENDER_OVERVIEW_TAB_SOURCE.read_text(encoding="utf-8")
    documents_source = TENDER_DOCUMENTS_TAB_SOURCE.read_text(encoding="utf-8")
    products_source = (
        TENDER_PRODUCTS_TAB_SOURCE.read_text(encoding="utf-8")
        if TENDER_PRODUCTS_TAB_SOURCE.exists()
        else ""
    )
    formatter_source = FORMATTERS_SOURCE.read_text(encoding="utf-8")
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "export function TenderOverviewTab" in overview_source
    assert "function ProductTabSummary" in products_source
    assert "function DocumentStatusSummary" in documents_source
    assert "export function documentStatusCounts" in formatter_source
    assert "<TenderOverviewTab tender={tender} raw={raw} />" in app_source
    assert "<TenderProductsTab" in app_source
    assert "<ProductTabSummary" in products_source
    assert "<TenderDocumentsTab" in app_source
    assert "tab-lead" in overview_source
    assert "overview-brief-grid" in overview_source
    assert "document-status-summary" in documents_source
    assert "product-tab-summary" in products_source
    assert ".tab-lead" in styles_source
    assert ".overview-brief-grid" in styles_source
    assert ".document-status-summary" in styles_source
    assert ".product-tab-summary" in styles_source
    assert find_mojibake(app_source, TENDER_DETAILS_SOURCE) == []
    assert find_mojibake(overview_source, TENDER_OVERVIEW_TAB_SOURCE) == []
    assert find_mojibake(documents_source, TENDER_DOCUMENTS_TAB_SOURCE) == []
    assert find_mojibake(products_source, TENDER_PRODUCTS_TAB_SOURCE) == []
    assert find_mojibake(styles_source, STYLES_SOURCE) == []


def test_decision_tabs_are_extracted_to_consistent_work_panels():
    app_source = TENDER_DETAILS_SOURCE.read_text(encoding="utf-8")
    analysis_source = TENDER_ANALYSIS_TAB_SOURCE.read_text(encoding="utf-8")
    economics_source = TENDER_ECONOMICS_TAB_SOURCE.read_text(encoding="utf-8")
    workflow_source = (
        TENDER_WORKFLOW_TAB_SOURCE.read_text(encoding="utf-8")
        if TENDER_WORKFLOW_TAB_SOURCE.exists()
        else ""
    )
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "export function TenderAnalysisTab" in analysis_source
    assert "export function TenderEconomicsTab" in economics_source
    assert "export function WorkflowTabPanel" in workflow_source
    assert "<TenderAnalysisTab" in app_source
    assert "<TenderEconomicsTab" in app_source
    assert "productProfiles={productProfiles}" in app_source
    assert "<WorkflowTabPanel" in app_source
    assert "analysis-tab-summary" in analysis_source
    assert "economics-tab-summary" in economics_source
    assert "workflow-status-summary" in workflow_source
    assert "workflow-note-panel" in workflow_source
    assert ".analysis-tab-summary," in styles_source
    assert ".economics-tab-summary," in styles_source
    assert ".workflow-status-summary" in styles_source
    assert ".workflow-note-panel" in styles_source
    assert find_mojibake(app_source, TENDER_DETAILS_SOURCE) == []
    assert find_mojibake(analysis_source, TENDER_ANALYSIS_TAB_SOURCE) == []
    assert find_mojibake(economics_source, TENDER_ECONOMICS_TAB_SOURCE) == []
    assert find_mojibake(workflow_source, TENDER_WORKFLOW_TAB_SOURCE) == []
    assert find_mojibake(styles_source, STYLES_SOURCE) == []

def test_economics_tab_uses_tender_price_before_manual_calculation():
    app_source = TENDER_ECONOMICS_TAB_SOURCE.read_text(encoding="utf-8")

    assert "export function TenderEconomicsTab({" in app_source
    assert "const displayedRevenue = economics?.revenue ?? tender?.price" in app_source
    assert "<SummaryMetric value={formatMoney(displayedRevenue)} label=\"НМЦК\" />" in app_source
    assert "НМЦК подтянута из карточки закупки" in app_source
    assert find_mojibake(app_source, TENDER_ECONOMICS_TAB_SOURCE) == []

def test_economics_tab_renders_bid_thresholds():
    app_source = TENDER_ECONOMICS_TAB_SOURCE.read_text(encoding="utf-8")

    assert "economics?.break_even_price" in app_source
    assert "economics.break_even_price" in app_source
    assert "economics.minimum_margin_price" in app_source
    assert "economics.interesting_price" in app_source
    assert "Безубыток" in app_source
    assert "Минимальная ставка" in app_source
    assert "Интересная ставка" in app_source
    assert find_mojibake(app_source, TENDER_ECONOMICS_TAB_SOURCE) == []

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
