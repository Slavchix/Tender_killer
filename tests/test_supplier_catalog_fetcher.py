from __future__ import annotations

from tender_killer.supplier_catalog_fetcher import fetch_public_text


def test_fetch_public_text_decodes_data_urls_without_network() -> None:
    assert fetch_public_text("data:text/html,%3Cmain%3Eok%3C/main%3E") == "<main>ok</main>"
