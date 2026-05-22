from __future__ import annotations

from pathlib import Path

from tender_killer.encoding_guard import find_mojibake


APP_SOURCE = Path(__file__).resolve().parents[1] / "web" / "src" / "App.jsx"


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
