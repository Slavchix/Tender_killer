from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_tz_section_constants_are_imported_from_sections_service():
    for relative_path in [
        "src/tender_killer/analysis_passport_service.py",
        "src/tender_killer/reports.py",
        "src/tender_killer/reports_tz_four_blocks.py",
        "src/tender_killer/reports_tz_sections.py",
    ]:
        source = (ROOT / relative_path).read_text(encoding="utf-8")
        assert "analysis_operator_view_service import MAJOR_SECTION" not in source
        assert "analysis_operator_sections_service import MAJOR_SECTION" in source


def test_operator_view_does_not_reexport_section_constants():
    source = (ROOT / "src/tender_killer/analysis_operator_view_service.py").read_text(encoding="utf-8")

    assert "MAJOR_SECTION_DEFINITIONS" not in source
    assert "MAJOR_SECTION_IDS" not in source


def test_operator_view_service_delegates_final_assembly():
    source = (ROOT / "src/tender_killer/analysis_operator_view_service.py").read_text(encoding="utf-8")

    assert "analysis_operator_view_assembler_service import assemble_operator_view" in source
    for forbidden_import in [
        "analysis_action_plan_service",
        "analysis_condition_groups_service",
        "analysis_evidence_drilldown_service",
        "analysis_operator_summary_service",
        "analysis_playbook_service",
        "analysis_questions_service",
        "analysis_workflow_service",
    ]:
        assert forbidden_import not in source


def test_operator_view_service_delegates_fact_source_selection():
    source = (ROOT / "src/tender_killer/analysis_operator_view_service.py").read_text(encoding="utf-8")

    assert "analysis_operator_fact_source_service import build_operator_fact_source" in source
    for forbidden_import in [
        "analysis_legacy_operator_items_service",
        "analysis_operator_item_service import build_operator_item",
        "AnalysisFactsContract",
    ]:
        assert forbidden_import not in source
