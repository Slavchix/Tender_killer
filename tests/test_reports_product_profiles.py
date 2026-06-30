from tender_killer.reports_product_profiles import report_product_profile_summary


def test_report_product_profile_summary_prefers_tender_summary_and_normalizes_values():
    summary = report_product_profile_summary(
        {
            "product_profile_summary": {
                "total": "7",
                "ready": "3",
                "needs_review": 2,
                "matched": 1,
                "priced": None,
                "rejected": "bad",
                "draft": 99,
            }
        },
        [{"profile_status": "ready"}],
    )

    assert summary == {
        "total": 7,
        "ready": 3,
        "needs_review": 2,
        "matched": 1,
        "priced": 0,
        "rejected": 0,
    }


def test_report_product_profile_summary_reuses_product_profile_counts_for_missing_summary():
    summary = report_product_profile_summary(
        {},
        [
            {"profile_status": "ready"},
            {"profile_status": "needs_review"},
            {"profile_status": "matched"},
            {"profile_status": "priced"},
            {"profile_status": "rejected"},
            {"profile_status": "searching"},
            {"profile_status": "unknown"},
        ],
    )

    assert summary == {
        "total": 7,
        "ready": 1,
        "needs_review": 1,
        "matched": 1,
        "priced": 1,
        "rejected": 1,
    }
