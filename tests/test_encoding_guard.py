from pathlib import Path

from tender_killer.encoding_guard import default_scan_paths, find_mojibake, scan_paths


def _mojibake(text: str) -> str:
    return text.encode("utf-8").decode("cp1251")


def test_find_mojibake_reports_corrupted_cyrillic() -> None:
    findings = find_mojibake(
        "Панель закупок\n" + _mojibake("На странице") + "\n",
        path=Path("web/src/App.jsx"),
    )

    assert len(findings) == 1
    assert findings[0].path == Path("web/src/App.jsx")
    assert findings[0].line == 2
    assert findings[0].marker


def test_runtime_sources_do_not_contain_cyrillic_mojibake() -> None:
    findings = scan_paths(default_scan_paths(Path(".")))

    assert findings == []
