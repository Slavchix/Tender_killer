from __future__ import annotations

from typing import Any

from tender_killer.reports import build_tender_report_docx
from tender_killer.reports import report_filename

DOCX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def build_tender_report_response(tender: dict[str, Any]) -> dict[str, Any]:
    return {
        "body": build_tender_report_docx(tender),
        "filename": report_filename(tender),
        "content_type": DOCX_CONTENT_TYPE,
    }
