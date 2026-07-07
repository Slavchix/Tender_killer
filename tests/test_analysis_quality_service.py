from pathlib import Path

from tender_killer.analysis_quality_service import find_unused_direct_imports


ROOT = Path(__file__).resolve().parents[1]


def test_find_unused_direct_imports_reports_unused_import_names(tmp_path):
    source = tmp_path / "analysis_sample.py"
    source.write_text(
        "\n".join(
            [
                "from __future__ import annotations",
                "import json",
                "import re as regex",
                "from typing import Any, TypedDict",
                "",
                "class Payload(TypedDict):",
                "    value: Any",
                "",
                "def compact(value: str) -> str:",
                "    return regex.sub(r'\\s+', ' ', value)",
            ]
        ),
        encoding="utf-8",
    )

    assert find_unused_direct_imports([source]) == [
        {
            "path": str(source),
            "line": 2,
            "name": "json",
        }
    ]


def test_find_unused_direct_imports_treats_all_exports_as_usage(tmp_path):
    source = tmp_path / "analysis_reexport.py"
    source.write_text(
        "\n".join(
            [
                "from sample import exported_name",
                "",
                "__all__ = ['exported_name']",
            ]
        ),
        encoding="utf-8",
    )

    assert find_unused_direct_imports([source]) == []


def test_analysis_modules_do_not_have_unused_direct_imports():
    analysis_sources = sorted((ROOT / "src" / "tender_killer").glob("analysis_*.py"))

    assert find_unused_direct_imports(analysis_sources) == []
