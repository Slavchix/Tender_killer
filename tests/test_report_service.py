from __future__ import annotations

from tender_killer.report_service import build_tender_report_response


def test_build_tender_report_response_returns_docx_download_payload():
    response = build_tender_report_response(
        {
            "source": "mosreg_market",
            "external_id": "3668200",
            "url": "https://example.test/3668200",
            "title": "Paper tender",
        }
    )

    assert response["filename"] == "tender-killer-3668200.docx"
    assert response["content_type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    assert response["body"].startswith(b"PK")
