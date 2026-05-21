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
