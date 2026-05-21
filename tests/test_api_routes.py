from tender_killer.api_routes import parse_database_table_path, parse_tender_path


def test_parse_tender_path_decodes_source_external_id_and_suffix() -> None:
    route = parse_tender_path(
        "/api/tenders/mosreg_market/3668200%2F2026/documents/download",
        suffix="documents/download",
    )

    assert route is not None
    assert route.source == "mosreg_market"
    assert route.external_id == "3668200/2026"


def test_parse_tender_path_rejects_wrong_suffix_or_shape() -> None:
    assert parse_tender_path("/api/tenders/mosreg_market/3668200/documents/download", suffix="analysis/run") is None
    assert parse_tender_path("/api/tenders/mosreg_market/3668200/extra") is None


def test_parse_database_table_path_decodes_single_table_name() -> None:
    assert parse_database_table_path("/api/db/tables/source_runs") == "source_runs"
    assert parse_database_table_path("/api/db/tables/source_runs/extra") is None
