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
