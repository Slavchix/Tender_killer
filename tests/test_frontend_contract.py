from __future__ import annotations

from pathlib import Path

from tender_killer.encoding_guard import find_mojibake


APP_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "App.jsx"
STYLES_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "styles.css"


def _css_rule(source: str, selector: str) -> str:
    start = source.index(selector)
    end = source.index("}", start)
    return source[start:end]


def test_tender_cockpit_exposes_normalized_metadata_filters():
    source = APP_SOURCE.read_text(encoding="utf-8")

    for key in ("source_family", "procedure_type", "customer_inn"):
        assert f"{key}: ''" in source
        assert f"updateFilter('{key}'" in source

    assert "procedureTypeOptions" in source
    assert "sourceFamilyOptions" in source


def test_tender_cockpit_exposes_page_size_selector():
    source = APP_SOURCE.read_text(encoding="utf-8")

    assert "tenderPageLimitOptions" in source
    assert "const [pageLimit, setPageLimit]" in source
    assert "params.set('limit', String(pageLimit))" in source
    assert "function changePageLimit" in source
    assert "setPageOffset(0)" in source
    assert "onPageLimitChange={changePageLimit}" in source
    assert "На странице" in source
    assert "Закупок на странице" in source
    assert find_mojibake(source, APP_SOURCE) == []


def test_tender_analysis_renders_actionable_checklist():
    source = APP_SOURCE.read_text(encoding="utf-8")

    assert "<AnalysisChecklist items={analysis.checklist} />" in source
    assert "function AnalysisChecklist" in source
    assert "Проверочный список" in source
    assert "analysis-checklist" in source
    assert "analysisCategoryLabel" in source
    assert "analysisSeverityLabel" in source
    assert find_mojibake(source, APP_SOURCE) == []


def test_product_profile_renders_fulfillment_requirements():
    source = APP_SOURCE.read_text(encoding="utf-8")

    assert "profile.fulfillment_requirements" in source
    assert "formatFulfillmentRequirements" in source
    assert "fulfillmentRequirementTypeLabel" in source
    assert "Поставка и исполнение" in source
    assert find_mojibake(source, APP_SOURCE) == []


def test_tender_details_render_economics_summary():
    source = APP_SOURCE.read_text(encoding="utf-8")

    assert "{ id: 'economics', label: 'Экономика' }" in source
    assert "<EconomicsSummary economics={economics} />" in source
    assert "function EconomicsSummary" in source
    assert "economicsStatusLabel" in source
    assert "Маржа" in source
    assert find_mojibake(source, APP_SOURCE) == []


def test_product_profile_renders_economics_input_form():
    source = APP_SOURCE.read_text(encoding="utf-8")

    assert "function ProductEconomicsForm" in source
    assert "onEconomicsSave" in source
    assert "product-profiles/${profile.position_index}/economics" in source
    assert "unit_cost" in source
    assert "logistics_cost" in source
    assert "documents_cost" in source
    assert "other_costs" in source
    assert "Себестоимость" in source
    assert find_mojibake(source, APP_SOURCE) == []


def test_product_profile_renders_supplier_option_form():
    source = APP_SOURCE.read_text(encoding="utf-8")

    assert "function ProductSupplierOptionsForm" in source
    assert "onSupplierOptionSave" in source
    assert "product-profiles/${profile.position_index}/supplier-options" in source
    assert "supplier_options" in source
    assert "unit_price" in source
    assert "availability" in source
    assert "Поставщики" in source
    assert find_mojibake(source, APP_SOURCE) == []


def test_tender_workbench_v1_reduces_detail_panel_overload():
    source = APP_SOURCE.read_text(encoding="utf-8")

    assert "workspace workbench-layout" in source
    assert "function TenderDecisionSummary" in source
    assert "<TenderDecisionSummary tender={tender} economics={economics} />" in source
    assert "decision-summary-grid" in source
    assert "product-detail-tabs" in source
    assert "const productDetailModes" in source
    assert "Паспорт" in source
    assert "Цены" in source
    assert "Поставщики" in source
    assert "ТЗ" in source
    assert find_mojibake(source, APP_SOURCE) == []


def test_tender_workbench_has_collapsible_filters_and_wider_list():
    app_source = APP_SOURCE.read_text(encoding="utf-8")
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "const [filtersCollapsed, setFiltersCollapsed]" in app_source
    assert "filtersCollapsed ? 'workspace workbench-layout filters-collapsed' : 'workspace workbench-layout'" in app_source
    assert "filter-collapse-button" in app_source
    assert "Свернуть фильтры" in app_source
    assert "Развернуть фильтры" in app_source
    assert ".workbench-layout.filters-collapsed" in styles_source
    assert "minmax(560px, 1.1fr)" in styles_source
    assert ".filters-panel.collapsed" in styles_source
    assert find_mojibake(app_source, APP_SOURCE) == []
    assert find_mojibake(styles_source, STYLES_SOURCE) == []


def test_tender_workflow_tabs_wrap_without_horizontal_scrollbar():
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")
    workflow_tabs_rule = _css_rule(styles_source, ".workflow-tabs")

    assert "flex-wrap: wrap" in workflow_tabs_rule
    assert "overflow-x: auto" not in workflow_tabs_rule
    assert find_mojibake(styles_source, STYLES_SOURCE) == []


def test_global_shell_exposes_dashboard_and_side_navigation():
    app_source = APP_SOURCE.read_text(encoding="utf-8")
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "const viewLabels = {" in app_source
    assert "dashboard: 'Дашборд'" in app_source
    assert "tenders: 'Закупки'" in app_source
    assert "const navItems = [" in app_source
    assert "app-frame" in app_source
    assert "app-sidebar" in app_source
    assert "className=\"side-nav\"" in app_source
    assert "setView(item.id)" in app_source
    assert "function DashboardView" in app_source
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
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "function DashboardAttentionPanel" in app_source
    assert "function DashboardTenderPreview" in app_source
    assert "<DashboardAttentionPanel" in app_source
    assert "<DashboardTenderPreview" in app_source
    assert "Требует внимания" in app_source
    assert "Последние закупки" in app_source
    assert "dashboard-attention-list" in app_source
    assert "dashboard-tender-list" in app_source
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
