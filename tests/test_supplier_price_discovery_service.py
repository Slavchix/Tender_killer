from __future__ import annotations

import httpx
import pytest

from tender_killer import supplier_price_discovery_service as price_discovery
from tender_killer.models import ProductProfile
from tender_killer.models import Tender
from tender_killer.storage import TenderStore
from tender_killer.supplier_search_service import prepare_profile_supplier_search
from tender_killer.supplier_price_discovery_service import SchemaOrgProductCollector
from tender_killer.supplier_price_discovery_service import run_profile_supplier_url_discovery
from tender_killer.supplier_price_discovery_service import run_profile_supplier_price_discovery
from tender_killer.supplier_price_discovery_service import run_tender_supplier_price_discovery
from tender_killer.tender_detail_service import get_tender_payload


def test_schema_org_product_collector_extracts_public_offer_price() -> None:
    html = """
    <html>
      <head>
        <script type="application/ld+json">
          {
            "@context": "https://schema.org",
            "@type": "Product",
            "name": "Office paper A4 80 gsm",
            "url": "https://supplier.example/paper-a4",
            "offers": {
              "@type": "Offer",
              "priceSpecification": {
                "@type": "UnitPriceSpecification",
                "price": "925,50",
                "priceCurrency": "RUB",
                "valueAddedTaxIncluded": true
              },
              "availability": "https://schema.org/InStock",
              "shippingDetails": {
                "@type": "OfferShippingDetails",
                "description": "Delivery in Moscow"
              }
            }
          }
        </script>
      </head>
    </html>
    """
    collector = SchemaOrgProductCollector(fetch_text=lambda url: html)

    candidates = collector.collect(
        {
            "query": "office paper a4",
            "kind": "normalized_name",
            "quick_links": [
                {"label": "Supplier page", "url": "https://supplier.example/paper-a4"},
            ],
        }
    )

    assert candidates == [
        {
            "name": "Office paper A4 80 gsm",
            "url": "https://supplier.example/paper-a4",
            "unit_price": 925.5,
            "currency": "RUB",
            "vat_mode": "vat_included",
            "delivery_note": "Delivery in Moscow",
            "availability": "in_stock",
            "status": "candidate",
            "source_query": "office paper a4",
            "source_kind": "normalized_name",
            "note": "Schema.org product offer from https://supplier.example/paper-a4.",
            "provider": "schema_org_product",
        }
    ]


def test_schema_org_product_collector_skips_search_engine_links() -> None:
    calls: list[str] = []
    collector = SchemaOrgProductCollector(fetch_text=lambda url: calls.append(url) or "<html></html>")

    candidates = collector.collect(
        {
            "query": "office paper a4",
            "kind": "normalized_name",
            "quick_links": [
                {"label": "Google", "url": "https://www.google.com/search?q=office+paper+a4"},
                {"label": "Yandex", "url": "https://yandex.ru/search/?text=office+paper+a4"},
            ],
        }
    )

    assert candidates == []
    assert calls == []


def test_public_fetch_error_preserves_blocked_catalog_preview(monkeypatch) -> None:
    url = "https://www.vseinstrumenti.ru/search/?q=cement+mix"
    captured: dict[str, object] = {}

    class BlockedResponse:
        status_code = 403
        text = "<html><body><main>Пожалуйста, пройдите проверку</main></body></html>"
        request = httpx.Request("GET", url)

        def raise_for_status(self) -> None:
            raise httpx.HTTPStatusError("raw forbidden", request=self.request, response=self)

    def fake_get(*args: object, **kwargs: object) -> BlockedResponse:
        captured["args"] = args
        captured.update(kwargs)
        return BlockedResponse()

    monkeypatch.setattr(price_discovery.httpx, "get", fake_get)

    with pytest.raises(httpx.HTTPStatusError) as excinfo:
        price_discovery._fetch_public_text(url)

    message = str(excinfo.value)
    assert "access_blocked HTTP 403" in message
    assert "Пожалуйста, пройдите проверку" in message
    assert captured["trust_env"] is False


def test_officemag_search_results_reject_unrelated_product_families() -> None:
    html = """
    <html>
      <body>
        <ul>
          <li class="listItem">
            <a href="/catalog/goods/112464/">Office paper A4, 80 gsm</a>
            <span class="js-productSum" data-price="493"></span>
          </li>
          <li class="listItem">
            <a href="/catalog/goods/700245/">Body sponge with massage effect</a>
            <span class="js-productSum" data-price="86"></span>
          </li>
          <li class="listItem">
            <a href="/catalog/goods/271846/">Sakura W1510X cartridge for HP LaserJet Pro 4003</a>
            <span class="js-productSum" data-price="3480"></span>
          </li>
        </ul>
      </body>
    </html>
    """

    candidates = price_discovery._officemag_visible_candidates(
        html,
        "https://www.officemag.ru/search/?q=cartridge",
        "cartridge for electrophotographic printing devices",
        "catalog_search",
    )

    assert [candidate["name"] for candidate in candidates] == ["Sakura W1510X cartridge for HP LaserJet Pro 4003"]
    assert candidates[0]["unit_price"] == 3480


def test_provider_catalog_collector_follows_matching_catalog_product_links() -> None:
    pages = {
        "https://petrovich.ru/search/?q=cement+mix": """
            <html>
              <body>
                <a href="/catalog/cement-25kg">Cement mix 25 kg</a>
              </body>
            </html>
        """,
        "https://petrovich.ru/catalog/cement-25kg": """
            <script type="application/ld+json">
            {
              "@context": "https://schema.org",
              "@type": "Product",
              "name": "Cement mix 25 kg",
              "url": "https://petrovich.ru/catalog/cement-25kg",
              "offers": {
                "@type": "Offer",
                "price": "418.90",
                "priceCurrency": "RUB",
                "availability": "https://schema.org/InStock"
              }
            }
            </script>
        """,
    }
    calls: list[str] = []
    collector = price_discovery.ProviderCatalogCollector(
        "petrovich",
        fetch_text=lambda url: calls.append(url) or pages.get(url, "<html></html>"),
    )

    result = collector.collect_with_diagnostics(
        {
            "query": "cement mix",
            "kind": "normalized_name",
            "quick_links": [
                {"label": "Google", "url": "https://www.google.com/search?q=cement+mix"},
                {
                    "label": "Petrovich",
                    "url": "https://petrovich.ru/search/?q=cement+mix",
                    "provider": "petrovich",
                    "link_kind": "catalog_search",
                    "preset_id": "petrovich_building_materials",
                },
                {
                    "label": "OfficeMag",
                    "url": "https://www.officemag.ru/search/?q=cement+mix",
                    "provider": "officemag",
                    "link_kind": "catalog_search",
                    "preset_id": "officemag_office_supplies",
                },
            ],
        }
    )

    assert calls == [
        "https://petrovich.ru/search/?q=cement+mix",
        "https://petrovich.ru/catalog/cement-25kg",
    ]
    assert result["diagnostics"] == {
        "provider": "catalog_petrovich",
        "queries_seen": 1,
        "links_seen": 3,
        "links_skipped": 2,
        "pages_fetched": 2,
        "candidates_found": 1,
        "errors": [],
    }
    assert result["candidates"] == [
        {
            "name": "Cement mix 25 kg",
            "url": "https://petrovich.ru/catalog/cement-25kg",
            "unit_price": 418.9,
            "currency": "RUB",
            "availability": "in_stock",
            "status": "candidate",
            "source_query": "cement mix",
            "source_kind": "normalized_name",
            "note": "Petrovich catalog offer from https://petrovich.ru/catalog/cement-25kg.",
            "provider": "petrovich",
        }
    ]


def test_provider_catalog_collector_extracts_officemag_visible_offer_without_schema_org() -> None:
    pages = {
        "https://www.officemag.ru/search/?q=office+paper+a4": """
            <html>
              <body>
                <a href="/catalog/goods/110532/">Office paper A4</a>
              </body>
            </html>
        """,
        "https://www.officemag.ru/catalog/goods/110532/": """
            <html>
              <body>
                <h1>Office paper A4 80 gsm, 500 sheets</h1>
                <p>449,83 руб.</p>
                <p>346,00 руб.</p>
                <p>Наличие на складе в Москве 16891 шт.</p>
              </body>
            </html>
        """,
    }
    calls: list[str] = []
    collector = price_discovery.ProviderCatalogCollector(
        "officemag",
        fetch_text=lambda url: calls.append(url) or pages.get(url, "<html></html>"),
    )

    result = collector.collect_with_diagnostics(
        {
            "query": "office paper a4",
            "kind": "normalized_name",
            "quick_links": [
                {
                    "label": "OfficeMag",
                    "url": "https://www.officemag.ru/search/?q=office+paper+a4",
                    "provider": "officemag",
                    "link_kind": "catalog_search",
                    "preset_id": "officemag_office_supplies",
                }
            ],
        }
    )

    assert calls == [
        "https://www.officemag.ru/search/?q=office+paper+a4",
        "https://www.officemag.ru/catalog/goods/110532/",
    ]
    assert result["diagnostics"]["candidates_found"] == 1
    assert result["candidates"] == [
        {
            "name": "Office paper A4 80 gsm, 500 sheets",
            "url": "https://www.officemag.ru/catalog/goods/110532/",
            "unit_price": 346.0,
            "currency": "RUB",
            "availability": "in_stock",
            "stock_quantity": 16891,
            "delivery_note": "OfficeMag: склад 16891 шт..",
            "status": "candidate",
            "source_query": "office paper a4",
            "source_kind": "normalized_name",
            "note": "OfficeMag catalog visible offer from https://www.officemag.ru/catalog/goods/110532/.",
            "provider": "officemag",
        }
    ]


def test_provider_catalog_collector_extracts_officemag_search_result_cards() -> None:
    html = """
        <html>
          <body>
            <ul class="listItems">
              <li class="listItem js-productListItem" data-list-name="search">
                <a class="listItemPhoto__link" href="/catalog/goods/271846/">
                  <img alt="Папка на 2 кольцах, ПРОЧНАЯ, картон/ПВХ, BRAUBERG &quot;Office&quot;, ЧЕРНАЯ, 75 мм, до 500 листов, 271846">
                </a>
                <a href="/catalog/goods/271846/">
                  Папка на 2 кольцах, ПРОЧНАЯ, картон/<wbr/>ПВХ, BRAUBERG &laquo;Office&raquo;,
                  ЧЕРНАЯ, 75 мм, до 500 листов, 271846
                </a>
                <span class="code">Код 271846</span>
                <div class="ProductSpecial__item js-ProductSpecialRow ProductSpecial__item--active" data-count="1" data-price="482.58">
                  От <span class="ProductSpecial__count">1</span> шт.
                </div>
                <div class="ProductSpecial__item js-ProductSpecialRow" data-count="3" data-price="458.45">
                  От <span class="ProductSpecial__count">3</span> шт.
                </div>
                <div class="listItemBuy__available">
                  <table>
                    <tr>
                      <td>Наличие на складе</td>
                      <td>39 шт.</td>
                    </tr>
                    <tr>
                      <td>Под заказ от 3-4 д.</td>
                      <td>+6634 шт.</td>
                    </tr>
                  </table>
                </div>
                <div class="ProductState ProductState--stepCount">
                  <div class="ProductState">Мин. партия: 1.</div>
                  <div class="ProductState">В упаковке: 12</div>
                </div>
              </li>
            </ul>
          </body>
        </html>
    """
    collector = price_discovery.ProviderCatalogCollector(
        "officemag",
        fetch_text=lambda url: html,
        max_product_pages=0,
    )

    result = collector.collect_with_diagnostics(
        {
            "query": "папка 2 кольца brauberg 75 мм",
            "kind": "normalized_name",
            "quick_links": [
                {
                    "label": "OfficeMag",
                    "url": "https://www.officemag.ru/search/index.php?SECTION=837&q=folder",
                    "provider": "officemag",
                    "link_kind": "catalog_search",
                    "preset_id": "officemag_office_supplies",
                }
            ],
        }
    )

    assert result["diagnostics"]["pages_fetched"] == 1
    assert result["diagnostics"]["candidates_found"] == 1
    assert result["candidates"] == [
        {
            "name": 'Папка на 2 кольцах, ПРОЧНАЯ, картон/ПВХ, BRAUBERG "Office", ЧЕРНАЯ, 75 мм, до 500 листов, 271846',
            "url": "https://www.officemag.ru/catalog/goods/271846/",
            "unit_price": 458.45,
            "currency": "RUB",
            "availability": "in_stock",
            "stock_quantity": 39,
            "preorder_quantity": 6634,
            "minimum_order_quantity": 1,
            "pack_quantity": 12,
            "delivery_note": "OfficeMag: цена от 1 шт. 482.58 RUB; цена от 3 шт. 458.45 RUB; склад 39 шт.; под заказ +6634 шт.; мин. партия 1; в упаковке 12.",
            "status": "candidate",
            "source_query": "папка 2 кольца brauberg 75 мм",
            "source_kind": "normalized_name",
            "note": "OfficeMag catalog search result from https://www.officemag.ru/search/index.php?SECTION=837&q=folder.",
            "provider": "officemag",
        }
    ]


def test_provider_catalog_collector_extracts_real_russian_officemag_search_result_cards() -> None:
    html = """
        <html>
          <body>
            <ul class="listItems">
              <li class="listItem js-productListItem" data-list-name="search">
                <a class="listItemPhoto__link" href="/catalog/goods/111111/">
                  <img alt="Бумага офисная А4, 500 листов, белая, 80 г/м2">
                </a>
                <a href="/catalog/goods/111111/">
                  Бумага офисная А4, 500 листов, белая, 80 г/м2
                </a>
                <div class="ProductSpecial__item js-ProductSpecialRow ProductSpecial__item--active" data-count="1" data-price="520.00">
                  От <span class="ProductSpecial__count">1</span> шт.
                </div>
                <div class="ProductSpecial__item js-ProductSpecialRow" data-count="10" data-price="498.00">
                  От <span class="ProductSpecial__count">10</span> шт.
                </div>
                <div class="listItemBuy__available">
                  <table>
                    <tr>
                      <td>Наличие на складе</td>
                      <td>123 шт.</td>
                    </tr>
                    <tr>
                      <td>Под заказ от 3-4 д.</td>
                      <td>+200 шт.</td>
                    </tr>
                  </table>
                </div>
                <div class="ProductState ProductState--stepCount">
                  <div class="ProductState">Мин. партия: 1.</div>
                  <div class="ProductState">В упаковке: 5</div>
                </div>
              </li>
            </ul>
          </body>
        </html>
    """
    collector = price_discovery.ProviderCatalogCollector(
        "officemag",
        fetch_text=lambda url: html,
        max_product_pages=0,
    )

    result = collector.collect_with_diagnostics(
        {
            "query": "бумага офисная а4",
            "kind": "catalog_hint",
            "quick_links": [
                {
                    "label": "OfficeMag",
                    "url": "https://www.officemag.ru/search/?q=%D0%B1%D1%83%D0%BC%D0%B0%D0%B3%D0%B0+%D0%BE%D1%84%D0%B8%D1%81%D0%BD%D0%B0%D1%8F+%D0%B04",
                    "provider": "officemag",
                    "link_kind": "catalog_search",
                    "preset_id": "officemag_office_supplies",
                }
            ],
        }
    )

    assert result["diagnostics"]["pages_fetched"] == 1
    assert result["diagnostics"]["candidates_found"] == 1
    assert result["candidates"] == [
        {
            "name": "Бумага офисная А4, 500 листов, белая, 80 г/м2",
            "url": "https://www.officemag.ru/catalog/goods/111111/",
            "unit_price": 498.0,
            "currency": "RUB",
            "availability": "in_stock",
            "stock_quantity": 123,
            "preorder_quantity": 200,
            "minimum_order_quantity": 1,
            "pack_quantity": 5,
            "delivery_note": "OfficeMag: цена от 1 шт. 520 RUB; цена от 10 шт. 498 RUB; склад 123 шт.; под заказ +200 шт.; мин. партия 1; в упаковке 5.",
            "status": "candidate",
            "source_query": "бумага офисная а4",
            "source_kind": "catalog_hint",
            "note": "OfficeMag catalog search result from https://www.officemag.ru/search/?q=%D0%B1%D1%83%D0%BC%D0%B0%D0%B3%D0%B0+%D0%BE%D1%84%D0%B8%D1%81%D0%BD%D0%B0%D1%8F+%D0%B04.",
            "provider": "officemag",
        }
    ]


def test_provider_catalog_collector_skips_officemag_cards_without_query_core_token() -> None:
    html = """
        <html>
          <body>
            <ul class="listItems">
              <li class="listItem js-productListItem" data-list-name="search">
                <a class="listItemPhoto__link" href="/catalog/goods/999999/">
                  <img alt="Знак эвакуационный Направляющая стрелка, комплект 10 штук">
                </a>
                <a href="/catalog/goods/999999/">
                  Знак эвакуационный Направляющая стрелка, комплект 10 штук
                </a>
                <div class="ProductSpecial__item js-ProductSpecialRow" data-count="1" data-price="347"></div>
              </li>
            </ul>
          </body>
        </html>
    """
    collector = price_discovery.ProviderCatalogCollector(
        "officemag",
        fetch_text=lambda url: html,
        max_product_pages=0,
    )

    result = collector.collect_with_diagnostics(
        {
            "query": "Бумага для офисной техники 11.05.01.02.05.009",
            "kind": "catalog_hint",
            "quick_links": [
                {
                    "label": "OfficeMag",
                    "url": "https://www.officemag.ru/search/?q=paper",
                    "provider": "officemag",
                    "link_kind": "catalog_search",
                    "preset_id": "officemag_office_supplies",
                }
            ],
        }
    )

    assert result["diagnostics"]["pages_fetched"] == 1
    assert result["diagnostics"]["candidates_found"] == 0
    assert result["candidates"] == []


def test_provider_catalog_collector_extracts_officemag_product_detail_terms() -> None:
    html = """
        <html>
          <body>
            <h1 class="ProductHead__name">Папка на 2 кольцах, ПРОЧНАЯ, картон/<wbr/>ПВХ, BRAUBERG &laquo;Office&raquo;, ЧЕРНАЯ, 75 мм, до 500 листов, 271846</h1>
            <div class="Product__price js-detailCardGoods" itemprop="price" content="458.45">
              <span class="Price__count">458</span>,<span class="Price__penny">45</span>
              <div class="Product__specialCondition">От 3 шт.</div>
            </div>
            <div class="ProductSpecial__item js-ProductSpecialRow ProductSpecial__item--active" data-count="1" data-price="482.58"></div>
            <div class="ProductSpecial__item js-ProductSpecialRow" data-count="3" data-price="458.45"></div>
            <div class="Availability Availability--inline">
              <div class="Availability__item">На складе <span class="Availability__content">в Москве <span class="Availability__quantity">39 шт.</span></span></div>
              <div class="Availability__item">Под заказ <span class="Availability__content">от 3-4 д. <span class="Availability__quantity">+6634 шт.</span></span></div>
            </div>
            <div class="ProductState ProductState--stepCount">
              <div class="ProductState">Мин. партия: 1.</div>
              <div class="ProductState">В упаковке: 12</div>
            </div>
          </body>
        </html>
    """
    collector = price_discovery.ProviderCatalogCollector(
        "officemag",
        fetch_text=lambda url: html,
        max_product_pages=0,
    )

    result = collector.collect_with_diagnostics(
        {
            "query": "папка 2 кольца brauberg 75 мм",
            "kind": "normalized_name",
            "quick_links": [
                {
                    "label": "OfficeMag manual",
                    "url": "https://www.officemag.ru/catalog/goods/271846/",
                    "provider": "officemag",
                    "link_kind": "manual_product_url",
                    "preset_id": "officemag_office_supplies",
                }
            ],
        }
    )

    assert result["diagnostics"]["candidates_found"] == 1
    assert result["candidates"][0]["unit_price"] == 458.45
    assert result["candidates"][0]["delivery_note"] == (
        "OfficeMag: цена от 1 шт. 482.58 RUB; цена от 3 шт. 458.45 RUB; "
        "склад 39 шт.; под заказ +6634 шт.; мин. партия 1; в упаковке 12."
    )


def test_provider_catalog_collector_uses_browser_fallback_for_officemag_access_block(monkeypatch) -> None:
    url = "https://www.officemag.ru/search/?q=folder"
    request = httpx.Request("GET", url)
    response = httpx.Response(
        503,
        request=request,
        text="<html><body>Ваш браузер не смог пройти проверку.</body></html>",
    )
    browser_calls: list[tuple[str, str | None]] = []
    html = """
        <html>
          <body>
            <ul class="listItems">
              <li class="listItem js-productListItem">
                <a href="/catalog/goods/271846/">
                  Папка на 2 кольцах, ПРОЧНАЯ, картон/<wbr/>ПВХ, BRAUBERG &laquo;Office&raquo;,
                  ЧЕРНАЯ, 75 мм, до 500 листов, 271846
                </a>
                <div class="ProductSpecial__item js-ProductSpecialRow" data-count="3" data-price="458.45"></div>
                <div class="ProductState ProductState--stepCount">
                  <div class="ProductState">Мин. партия: 1.</div>
                  <div class="ProductState">В упаковке: 12</div>
                </div>
              </li>
            </ul>
          </body>
        </html>
    """

    def blocked_fetch(fetch_url: str) -> str:
        raise httpx.HTTPStatusError("access_blocked HTTP 503", request=request, response=response)

    def fake_browser_fetch(fetch_url: str, *, provider: str | None = None) -> str:
        browser_calls.append((fetch_url, provider))
        return html

    monkeypatch.setenv("TENDER_KILLER_SUPPLIER_BROWSER_FETCH", "1")
    monkeypatch.setenv("TENDER_KILLER_SUPPLIER_BROWSER_FETCH_PROVIDERS", "officemag")
    monkeypatch.setattr(price_discovery, "_fetch_public_text", blocked_fetch)
    monkeypatch.setattr(price_discovery.supplier_browser_fetcher, "fetch_text", fake_browser_fetch)

    collector = price_discovery.ProviderCatalogCollector("officemag", max_product_pages=0)
    result = collector.collect_with_diagnostics(
        {
            "query": "папка 2 кольца",
            "kind": "normalized_name",
            "quick_links": [
                {
                    "label": "OfficeMag",
                    "url": url,
                    "provider": "officemag",
                    "link_kind": "catalog_search",
                    "preset_id": "officemag_office_supplies",
                }
            ],
        }
    )

    assert browser_calls == [(url, "officemag")]
    assert result["diagnostics"]["pages_fetched"] == 1
    assert result["diagnostics"]["errors"] == []
    assert result["candidates"][0]["unit_price"] == 458.45
    assert result["candidates"][0]["provider"] == "officemag"


def test_provider_catalog_collector_extracts_vseinstrumenti_visible_offer_without_schema_org() -> None:
    pages = {
        "https://www.vseinstrumenti.ru/category/tsement-3432/": """
            <html>
              <body>
                <a href="/product/cement-movatex-5-kg-17134117/">Cement Movatex 5 kg</a>
              </body>
            </html>
        """,
        "https://www.vseinstrumenti.ru/product/cement-movatex-5-kg-17134117/": """
            <html>
              <body>
                <h1>Cement Movatex D0 M500, 5 kg</h1>
                <p>275 ₽</p>
                <p>В корзину</p>
                <p>Самовывоз: сегодня, бесплатно</p>
              </body>
            </html>
        """,
    }
    calls: list[str] = []
    collector = price_discovery.ProviderCatalogCollector(
        "vseinstrumenti",
        fetch_text=lambda url: calls.append(url) or pages.get(url, "<html></html>"),
    )

    result = collector.collect_with_diagnostics(
        {
            "query": "cement",
            "kind": "normalized_name",
            "quick_links": [
                {
                    "label": "Vseinstrumenti",
                    "url": "https://www.vseinstrumenti.ru/category/tsement-3432/",
                    "provider": "vseinstrumenti",
                    "link_kind": "catalog_search",
                    "preset_id": "vseinstrumenti_building_materials",
                }
            ],
        }
    )

    assert calls == [
        "https://www.vseinstrumenti.ru/category/tsement-3432/",
        "https://www.vseinstrumenti.ru/product/cement-movatex-5-kg-17134117/",
    ]
    assert result["diagnostics"]["candidates_found"] == 1
    assert result["candidates"][0]["name"] == "Cement Movatex D0 M500, 5 kg"
    assert result["candidates"][0]["unit_price"] == 275.0
    assert result["candidates"][0]["currency"] == "RUB"
    assert result["candidates"][0]["availability"] == "in_stock"
    assert result["candidates"][0]["provider"] == "vseinstrumenti"


def test_provider_catalog_collector_extracts_komus_visible_offer_without_schema_org() -> None:
    pages = {
        "https://www.komus.ru/search/?text=office+paper+a4": """
            <html>
              <body>
                <a href="/katalog/posuda-i-tekstil/bumaga-dlya-vypechki/pergament-komus/p/1050505/">
                  Paper Komus 500 sheets
                </a>
              </body>
            </html>
        """,
        "https://www.komus.ru/katalog/posuda-i-tekstil/bumaga-dlya-vypechki/pergament-komus/p/1050505/": """
            <html>
              <body>
                <h1>Paper Komus 500 sheets</h1>
                <p>Доставка завтра</p>
                <p>2,76 ₽ /шт.</p>
                <p>138 ₽ от 1 уп.</p>
              </body>
            </html>
        """,
    }
    calls: list[str] = []
    collector = price_discovery.ProviderCatalogCollector(
        "komus",
        fetch_text=lambda url: calls.append(url) or pages.get(url, "<html></html>"),
    )

    result = collector.collect_with_diagnostics(
        {
            "query": "office paper a4",
            "kind": "normalized_name",
            "quick_links": [
                {
                    "label": "Komus",
                    "url": "https://www.komus.ru/search/?text=office+paper+a4",
                    "provider": "komus",
                    "link_kind": "catalog_search",
                    "preset_id": "komus_office_supplies",
                }
            ],
        }
    )

    assert calls == [
        "https://www.komus.ru/search/?text=office+paper+a4",
        "https://www.komus.ru/katalog/posuda-i-tekstil/bumaga-dlya-vypechki/pergament-komus/p/1050505/",
    ]
    assert result["diagnostics"]["candidates_found"] == 1
    assert result["candidates"][0]["name"] == "Paper Komus 500 sheets"
    assert result["candidates"][0]["unit_price"] == 2.76
    assert result["candidates"][0]["currency"] == "RUB"
    assert result["candidates"][0]["availability"] == "in_stock"
    assert result["candidates"][0]["provider"] == "komus"


def test_provider_catalog_collector_extracts_petrovich_visible_offer_without_schema_org() -> None:
    pages = {
        "https://petrovich.ru/search/?q=cement+mix": """
            <html>
              <body>
                <a href="/product/101902/">Cement waterproofing 15 kg</a>
              </body>
            </html>
        """,
        "https://petrovich.ru/product/101902/": """
            <html>
              <body>
                <h1>Cement waterproofing 15 kg</h1>
                <p>Цена за штуку</p>
                <p>По карте</p>
                <p>2\u202f258 ₽</p>
                <p>2\u202f337 ₽</p>
                <p>В корзину</p>
                <p>Доступно сегодня</p>
              </body>
            </html>
        """,
    }
    calls: list[str] = []
    collector = price_discovery.ProviderCatalogCollector(
        "petrovich",
        fetch_text=lambda url: calls.append(url) or pages.get(url, "<html></html>"),
    )

    result = collector.collect_with_diagnostics(
        {
            "query": "cement mix",
            "kind": "normalized_name",
            "quick_links": [
                {
                    "label": "Petrovich",
                    "url": "https://petrovich.ru/search/?q=cement+mix",
                    "provider": "petrovich",
                    "link_kind": "catalog_search",
                    "preset_id": "petrovich_building_materials",
                }
            ],
        }
    )

    assert calls == [
        "https://petrovich.ru/search/?q=cement+mix",
        "https://petrovich.ru/product/101902/",
    ]
    assert result["diagnostics"]["candidates_found"] == 1
    assert result["candidates"][0]["name"] == "Cement waterproofing 15 kg"
    assert result["candidates"][0]["unit_price"] == 2258.0
    assert result["candidates"][0]["currency"] == "RUB"
    assert result["candidates"][0]["availability"] == "in_stock"
    assert result["candidates"][0]["provider"] == "petrovich"


def test_schema_org_product_collector_leaves_builtin_catalog_links_to_provider_collectors() -> None:
    calls: list[str] = []
    collector = SchemaOrgProductCollector(fetch_text=lambda url: calls.append(url) or "<html></html>")

    result = collector.collect_with_diagnostics(
        {
            "query": "cement mix",
            "kind": "normalized_name",
            "quick_links": [
                {
                    "label": "Petrovich",
                    "url": "https://petrovich.ru/search/?q=cement+mix",
                    "provider": "petrovich",
                    "link_kind": "catalog_search",
                    "preset_id": "petrovich_building_materials",
                }
            ],
        }
    )

    assert calls == []
    assert result == {
        "candidates": [],
        "diagnostics": {
            "provider": "schema_org_product",
            "queries_seen": 1,
            "links_seen": 1,
            "links_skipped": 1,
            "pages_fetched": 0,
            "candidates_found": 0,
            "errors": [],
        },
    }


def test_default_price_collectors_try_builtin_catalogs_before_schema_org_fallback() -> None:
    collectors = price_discovery.default_price_collectors(fetch_text=lambda url: "<html></html>")

    assert [collector.provider for collector in collectors] == [
        "catalog_officemag",
        "catalog_komus",
        "catalog_petrovich",
        "catalog_vseinstrumenti",
        "schema_org_product",
    ]


def test_run_profile_supplier_price_discovery_stages_schema_org_product_candidates(tmp_path) -> None:
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="supplier-price-discovery",
            url="https://market.mosreg.ru/Trade/ViewTrade/supplier-price-discovery",
            title="Paper tender",
            price=100000.0,
        )
    )
    store.upsert_product_profiles(
        "mosreg_market",
        "supplier-price-discovery",
        [
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="supplier-price-discovery",
                position_index=1,
                product_name="Office paper A4",
                quantity=10,
                unit="pack",
                raw_payload={
                    "supplier_search": {
                        "status": "ready",
                        "queries": [
                            {
                                "query": "office paper a4",
                                "kind": "normalized_name",
                                "priority": 1,
                                "quick_links": [
                                    {"label": "Google", "url": "https://www.google.com/search?q=office+paper+a4"},
                                    {"label": "Supplier page", "url": "https://supplier.example/paper-a4"},
                                ],
                            }
                        ],
                    },
                    "note": "keep me",
                },
            )
        ],
    )

    payload = run_profile_supplier_price_discovery(
        store.database_path,
        "mosreg_market",
        "supplier-price-discovery",
        1,
        collectors=[
            SchemaOrgProductCollector(
                fetch_text=lambda url: """
                <script type="application/ld+json">
                {
                  "@context": "https://schema.org",
                  "@type": "Product",
                  "name": "Office paper A4 80 gsm",
                  "url": "https://supplier.example/paper-a4",
                  "offers": {
                    "@type": "Offer",
                    "price": "925.50",
                    "availability": "https://schema.org/InStock"
                  }
                }
                </script>
                """
            )
        ],
    )

    assert payload == {
        "ok": True,
        "position_index": 1,
        "staged_count": 1,
        "supplier_discovery": {
            "status": "pending_review",
            "collector_diagnostics": [
                {
                    "provider": "schema_org_product",
                    "queries_seen": 1,
                    "links_seen": 2,
                    "links_skipped": 1,
                    "pages_fetched": 1,
                    "candidates_found": 1,
                    "errors": [],
                }
            ],
            "candidates": [
                {
                    "name": "Office paper A4 80 gsm",
                    "url": "https://supplier.example/paper-a4",
                    "unit_price": 925.5,
                    "availability": "in_stock",
                    "status": "candidate",
                    "source_query": "office paper a4",
                    "source_kind": "normalized_name",
                    "note": "Schema.org product offer from https://supplier.example/paper-a4.",
                    "provider": "schema_org_product",
                    "confidence": "high",
                    "confidence_reasons": ["has_price", "has_url", "has_source_query"],
                    "review_status": "pending",
                }
            ],
        },
    }
    detail = get_tender_payload(store.database_path, "mosreg_market", "supplier-price-discovery")
    profile = detail["product_profiles"][0]
    assert profile["profile_status"] == "matched"
    assert profile["raw_payload"]["note"] == "keep me"
    assert profile["raw_payload"]["supplier_discovery"] == payload["supplier_discovery"]
    assert "supplier_options" not in profile["raw_payload"]
    assert "economics" not in profile["raw_payload"]


def test_run_profile_supplier_price_discovery_refreshes_stale_russian_office_paper_queries(tmp_path) -> None:
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="supplier-price-russian-paper",
            url="https://market.mosreg.ru/Trade/ViewTrade/supplier-price-russian-paper",
            title="Paper tender",
            price=100000.0,
        )
    )
    store.upsert_product_profiles(
        "mosreg_market",
        "supplier-price-russian-paper",
        [
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="supplier-price-russian-paper",
                position_index=1,
                product_name="Бумага для офисной техники",
                normalized_name="Бумага для офисной техники",
                search_phrases=["Бумага для офисной техники"],
                okpd2="17.12.14.110",
                quantity=85,
                unit="Пачка",
                raw_payload={
                    "supplier_search": {
                        "status": "ready",
                        "queries": [
                            {
                                "query": "Бумага для офисной техники",
                                "kind": "normalized_name",
                                "priority": 1,
                                "quick_links": [
                                    {
                                        "label": "OfficeMag",
                                        "url": "https://www.officemag.ru/search/?q=%D0%91%D1%83%D0%BC%D0%B0%D0%B3%D0%B0+%D0%B4%D0%BB%D1%8F+%D0%BE%D1%84%D0%B8%D1%81%D0%BD%D0%BE%D0%B9+%D1%82%D0%B5%D1%85%D0%BD%D0%B8%D0%BA%D0%B8",
                                        "provider": "officemag",
                                        "link_kind": "catalog_search",
                                        "preset_id": "officemag_office_supplies",
                                    }
                                ],
                            }
                        ],
                    }
                },
            )
        ],
    )
    seen_queries: list[str] = []

    class RussianPaperCollector:
        provider = "catalog_officemag"

        def collect_with_diagnostics(self, query):
            query_text = query["query"]
            seen_queries.append(query_text)
            candidates = []
            if query_text == "бумага офисная а4":
                candidates = [
                    {
                        "name": "Бумага офисная А4, 500 листов",
                        "url": "https://www.officemag.ru/catalog/goods/111111/",
                        "unit_price": 498.0,
                        "availability": "in_stock",
                        "status": "candidate",
                        "source_query": query_text,
                        "source_kind": query["kind"],
                        "note": "OfficeMag catalog search result.",
                        "provider": "officemag",
                    }
                ]
            return {
                "candidates": candidates,
                "diagnostics": {
                    "provider": self.provider,
                    "queries_seen": 1,
                    "links_seen": len(query.get("quick_links") or []),
                    "links_skipped": 0,
                    "pages_fetched": 1 if candidates else 0,
                    "candidates_found": len(candidates),
                    "errors": [],
                },
            }

    payload = run_profile_supplier_price_discovery(
        store.database_path,
        "mosreg_market",
        "supplier-price-russian-paper",
        1,
        collectors=[RussianPaperCollector()],
    )

    assert seen_queries == [
        "Бумага для офисной техники",
        "бумага офисная",
        "бумага офисная а4",
        "бумага для принтера",
        "17.12.14.110 Бумага для офисной техники",
    ]
    assert payload["staged_count"] == 1
    detail = get_tender_payload(store.database_path, "mosreg_market", "supplier-price-russian-paper")
    profile = detail["product_profiles"][0]
    assert [query["query"] for query in profile["raw_payload"]["supplier_search"]["queries"]] == seen_queries
    assert profile["raw_payload"]["supplier_discovery"]["candidates"][0]["url"] == (
        "https://www.officemag.ru/catalog/goods/111111/"
    )


def test_run_tender_supplier_price_discovery_prepares_all_positions_and_summarizes_diagnostics(tmp_path) -> None:
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="supplier-price-discovery-bulk",
            url="https://market.mosreg.ru/Trade/ViewTrade/supplier-price-discovery-bulk",
            title="Office goods tender",
            price=100000.0,
        )
    )
    store.upsert_product_profiles(
        "mosreg_market",
        "supplier-price-discovery-bulk",
        [
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="supplier-price-discovery-bulk",
                position_index=1,
                product_name="Office paper A4",
                normalized_name="office paper a4",
                quantity=10,
                unit="pack",
            ),
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="supplier-price-discovery-bulk",
                position_index=2,
                product_name="Unknown custom item",
                normalized_name="unknown custom item",
                quantity=3,
                unit="pack",
            ),
        ],
    )

    class BulkCollector:
        provider = "bulk_test_catalog"

        def collect_with_diagnostics(self, query):
            query_text = str(query["query"])
            candidate = {
                "name": "Office paper A4 80 gsm",
                "url": "https://supplier.example/paper-a4",
                "unit_price": 925.0,
                "currency": "RUB",
                "vat_mode": "vat_included",
                "availability": "in_stock",
                "delivery_note": "Delivery included",
                "source_query": query_text,
                "source_kind": query["kind"],
                "provider": "bulk_test_catalog",
            }
            candidates = [candidate] if "paper" in query_text else []
            return {
                "candidates": candidates,
                "diagnostics": {
                    "provider": "bulk_test_catalog",
                    "queries_seen": 1,
                    "links_seen": len(query.get("quick_links") or []),
                    "links_skipped": 0,
                    "pages_fetched": 1,
                    "candidates_found": len(candidates),
                    "errors": [] if candidates else ["no visible price"],
                },
            }

    result = run_tender_supplier_price_discovery(
        store.database_path,
        "mosreg_market",
        "supplier-price-discovery-bulk",
        collectors=[BulkCollector()],
        max_positions=10,
    )

    detail = get_tender_payload(store.database_path, "mosreg_market", "supplier-price-discovery-bulk")
    profiles = {profile["position_index"]: profile for profile in detail["product_profiles"]}
    assert result["ok"] is True
    assert result["total_profiles"] == 2
    assert result["searched_count"] == 2
    assert result["positions"] == [
        {"position_index": 1, "status": "staged", "staged_count": 1},
        {
            "position_index": 2,
            "status": "no_candidates",
            "staged_count": 0,
            "error": "Новых кандидатов поставщиков не найдено.",
        },
    ]
    assert result["staged_count"] == 1
    assert result["no_candidates_count"] == 1
    assert result["diagnostics_by_provider"] == [
        {
            "provider": "bulk_test_catalog",
            "queries_seen": 2,
            "links_seen": 6,
            "links_skipped": 0,
            "pages_fetched": 2,
            "candidates_found": 1,
            "errors": ["no visible price"],
        }
    ]
    assert profiles[1]["raw_payload"]["supplier_search"]["status"] == "ready"
    assert profiles[1]["raw_payload"]["supplier_discovery"]["status"] == "pending_review"
    assert profiles[1]["price_candidates"][0]["provider"] == "bulk_test_catalog"
    assert "economics" not in profiles[1]["raw_payload"]
    assert profiles[2]["raw_payload"]["supplier_discovery"]["status"] == "no_candidates"


def test_run_tender_supplier_price_discovery_reports_position_before_slow_collectors(tmp_path) -> None:
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="supplier-price-discovery-progress",
            url="https://market.mosreg.ru/Trade/ViewTrade/supplier-price-discovery-progress",
            title="Office goods tender",
        )
    )
    store.upsert_product_profiles(
        "mosreg_market",
        "supplier-price-discovery-progress",
        [
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="supplier-price-discovery-progress",
                position_index=1,
                product_name="Office paper A4",
                normalized_name="office paper a4",
                quantity=10,
                unit="pack",
            )
        ],
    )

    progress_events: list[dict[str, Any]] = []

    class SlowCollector:
        provider = "slow_catalog"

        def collect_with_diagnostics(self, query):
            assert progress_events[-1]["searched_count"] == 1
            assert progress_events[-1]["positions"] == [
                {"position_index": 1, "status": "searching", "staged_count": 0}
            ]
            return {
                "candidates": [],
                "diagnostics": {
                    "provider": "slow_catalog",
                    "queries_seen": 1,
                    "links_seen": len(query.get("quick_links") or []),
                    "links_skipped": 0,
                    "pages_fetched": 1,
                    "candidates_found": 0,
                    "errors": ["no visible price"],
                },
            }

    run_tender_supplier_price_discovery(
        store.database_path,
        "mosreg_market",
        "supplier-price-discovery-progress",
        collectors=[SlowCollector()],
        max_positions=10,
        progress_callback=progress_events.append,
    )

    assert progress_events[0]["searched_count"] == 0
    assert progress_events[1]["searched_count"] == 1
    assert progress_events[1]["positions"][0]["status"] == "searching"
    assert progress_events[-1]["positions"][0]["status"] == "no_candidates"


def test_run_tender_supplier_price_discovery_can_limit_positions_per_run(tmp_path) -> None:
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="supplier-price-discovery-limited",
            url="https://market.mosreg.ru/Trade/ViewTrade/supplier-price-discovery-limited",
            title="Large tender",
        )
    )
    store.upsert_product_profiles(
        "mosreg_market",
        "supplier-price-discovery-limited",
        [
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="supplier-price-discovery-limited",
                position_index=1,
                product_name="Office paper A4",
                normalized_name="office paper a4",
                quantity=10,
                unit="pack",
            ),
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="supplier-price-discovery-limited",
                position_index=2,
                product_name="Office folders",
                normalized_name="office folders",
                quantity=5,
                unit="pack",
            ),
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="supplier-price-discovery-limited",
                position_index=3,
                product_name="Office pens",
                normalized_name="office pens",
                quantity=20,
                unit="pack",
            ),
        ],
    )

    class NoCandidateCollector:
        provider = "no_candidate_catalog"

        def collect_with_diagnostics(self, query):
            return {
                "candidates": [],
                "diagnostics": {
                    "provider": "no_candidate_catalog",
                    "queries_seen": 1,
                    "links_seen": len(query.get("quick_links") or []),
                    "links_skipped": 0,
                    "pages_fetched": 1,
                    "candidates_found": 0,
                    "errors": ["no visible price"],
                },
            }

    result = run_tender_supplier_price_discovery(
        store.database_path,
        "mosreg_market",
        "supplier-price-discovery-limited",
        collectors=[NoCandidateCollector()],
        max_positions=1,
    )

    assert result["ok"] is True
    assert result["total_profiles"] == 3
    assert result["searched_count"] == 1
    assert result["limited_count"] == 2
    assert result["partial"] is True
    assert result["positions"][0]["position_index"] == 1
    assert result["positions"][0]["status"] == "no_candidates"
    assert result["positions"][0]["staged_count"] == 0
    assert result["positions"][0]["error"]
    assert result["positions"][1:] == [
        {"position_index": 2, "status": "deferred", "staged_count": 0},
        {"position_index": 3, "status": "deferred", "staged_count": 0},
    ]


def test_run_profile_supplier_url_discovery_stages_visible_provider_candidate(tmp_path) -> None:
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="supplier-url-discovery",
            url="https://market.mosreg.ru/Trade/ViewTrade/supplier-url-discovery",
            title="Cement tender",
        )
    )
    store.upsert_product_profiles(
        "mosreg_market",
        "supplier-url-discovery",
        [
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="supplier-url-discovery",
                position_index=1,
                product_name="Cement waterproofing",
                normalized_name="cement waterproofing",
                raw_payload={"note": "keep me"},
            )
        ],
    )
    calls: list[str] = []

    payload = run_profile_supplier_url_discovery(
        store.database_path,
        "mosreg_market",
        "supplier-url-discovery",
        1,
        {
            "url": "https://petrovich.ru/product/101902/",
            "source_query": "cement waterproofing",
        },
        collectors=[
            price_discovery.ProviderCatalogCollector(
                "petrovich",
                fetch_text=lambda url: calls.append(url)
                or """
                   <html>
                     <body>
                       <h1>Cement waterproofing 15 kg</h1>
                       <p>2\u202f258 ₽</p>
                       <p>В корзину</p>
                     </body>
                   </html>
                   """,
            )
        ],
    )

    assert calls == ["https://petrovich.ru/product/101902/"]
    assert payload["supplier_discovery"]["collector_diagnostics"] == [
        {
            "provider": "catalog_petrovich",
            "queries_seen": 1,
            "links_seen": 1,
            "links_skipped": 0,
            "pages_fetched": 1,
            "candidates_found": 1,
            "errors": [],
        }
    ]
    candidate = payload["supplier_discovery"]["candidates"][0]
    assert candidate["provider"] == "petrovich"
    assert candidate["url"] == "https://petrovich.ru/product/101902/"
    assert candidate["unit_price"] == 2258.0
    assert candidate["source_query"] == "cement waterproofing"
    assert candidate["source_kind"] == "manual_product_url"
    assert candidate["review_status"] == "pending"
    detail = get_tender_payload(store.database_path, "mosreg_market", "supplier-url-discovery")
    profile = detail["product_profiles"][0]
    assert profile["raw_payload"]["note"] == "keep me"
    assert profile["raw_payload"]["supplier_discovery"] == payload["supplier_discovery"]
    assert "supplier_options" not in profile["raw_payload"]
    assert "economics" not in profile["raw_payload"]


def test_prepared_catalog_link_feeds_schema_org_product_discovery(tmp_path) -> None:
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="supplier-price-discovery-catalog",
            url="https://market.mosreg.ru/Trade/ViewTrade/supplier-price-discovery-catalog",
            title="Paper tender",
        )
    )
    store.upsert_product_profiles(
        "mosreg_market",
        "supplier-price-discovery-catalog",
        [
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="supplier-price-discovery-catalog",
                position_index=1,
                product_name="Office paper A4",
                normalized_name="office paper a4",
                raw_payload={
                    "supplier_catalog_preset_ids": [],
                    "supplier_catalogs": [
                        {
                            "label": "Supplier catalog",
                            "provider": "supplier_example",
                            "url_template": "https://supplier.example/search?q={query}",
                        }
                    ]
                },
            )
        ],
    )
    prepare_profile_supplier_search(
        store.database_path,
        "mosreg_market",
        "supplier-price-discovery-catalog",
        1,
    )
    pages = {
        "https://supplier.example/search?q=office+paper+a4": """
            <script type="application/ld+json">
            {
              "@context": "https://schema.org",
              "@type": "ItemList",
              "itemListElement": [
                {
                  "@type": "ListItem",
                  "item": {
                    "@type": "Product",
                    "name": "Office paper A4 80 gsm",
                    "url": "https://supplier.example/catalog/paper-a4"
                  }
                }
              ]
            }
            </script>
        """,
        "https://supplier.example/catalog/paper-a4": """
            <script type="application/ld+json">
            {
              "@context": "https://schema.org",
              "@type": "Product",
              "name": "Office paper A4 80 gsm",
              "url": "https://supplier.example/catalog/paper-a4",
              "offers": {
                "@type": "Offer",
                "price": "925",
                "priceCurrency": "RUB",
                "availability": "https://schema.org/InStock"
              }
            }
            </script>
        """,
    }
    calls: list[str] = []

    payload = run_profile_supplier_price_discovery(
        store.database_path,
        "mosreg_market",
        "supplier-price-discovery-catalog",
        1,
        collectors=[
            SchemaOrgProductCollector(
                fetch_text=lambda url: calls.append(url) or pages.get(url, "<html></html>")
            )
        ],
    )

    assert calls == [
        "https://supplier.example/search?q=office+paper+a4",
        "https://supplier.example/catalog/paper-a4",
    ]
    assert payload["supplier_discovery"]["collector_diagnostics"] == [
        {
            "provider": "schema_org_product",
            "queries_seen": 1,
            "links_seen": 3,
            "links_skipped": 2,
            "pages_fetched": 2,
            "candidates_found": 1,
            "errors": [],
        }
    ]
    assert payload["supplier_discovery"]["candidates"][0]["url"] == "https://supplier.example/catalog/paper-a4"
    assert payload["supplier_discovery"]["candidates"][0]["unit_price"] == 925.0
    assert payload["supplier_discovery"]["candidates"][0]["currency"] == "RUB"
    assert payload["supplier_discovery"]["candidates"][0]["confidence"] == "high"


def test_run_profile_supplier_price_discovery_skips_existing_candidates(tmp_path) -> None:
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="supplier-price-discovery-duplicates",
            url="https://market.mosreg.ru/Trade/ViewTrade/supplier-price-discovery-duplicates",
            title="Paper tender",
        )
    )
    store.upsert_product_profiles(
        "mosreg_market",
        "supplier-price-discovery-duplicates",
        [
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="supplier-price-discovery-duplicates",
                position_index=1,
                product_name="Office paper A4",
                raw_payload={
                    "supplier_search": {
                        "status": "ready",
                        "queries": [
                            {
                                "query": "office paper a4",
                                "kind": "normalized_name",
                                "priority": 1,
                                "quick_links": [
                                    {"label": "Supplier page", "url": "https://supplier.example/paper-a4"},
                                ],
                            }
                        ],
                    },
                    "supplier_discovery": {
                        "status": "pending_review",
                        "candidates": [
                            {
                                "name": "Office paper",
                                "url": "https://supplier.example/paper-a4",
                                "provider": "schema_org_product",
                                "review_status": "pending",
                            }
                        ],
                    },
                },
            )
        ],
    )
    calls: list[str] = []

    with pytest.raises(ValueError, match="Новых кандидатов поставщиков не найдено"):
        run_profile_supplier_price_discovery(
            store.database_path,
            "mosreg_market",
            "supplier-price-discovery-duplicates",
            1,
            collectors=[
                SchemaOrgProductCollector(
                    fetch_text=lambda url: calls.append(url)
                    or """
                       <script type="application/ld+json">
                       {
                         "@type":"Product",
                         "name":"Office paper",
                         "url":"https://supplier.example/paper-a4",
                         "offers":{"price":"925"}
                       }
                       </script>
                       """
                )
            ],
        )
    assert calls == ["https://supplier.example/paper-a4"]


def test_run_profile_supplier_price_discovery_records_diagnostics_without_candidates(tmp_path) -> None:
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="supplier-price-discovery-no-candidates",
            url="https://market.mosreg.ru/Trade/ViewTrade/supplier-price-discovery-no-candidates",
            title="Paper tender",
        )
    )
    store.upsert_product_profiles(
        "mosreg_market",
        "supplier-price-discovery-no-candidates",
        [
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="supplier-price-discovery-no-candidates",
                position_index=1,
                product_name="Office paper A4",
                raw_payload={
                    "supplier_search": {
                        "status": "ready",
                        "queries": [
                            {
                                "query": "office paper a4",
                                "kind": "normalized_name",
                                "priority": 1,
                                "quick_links": [
                                    {"label": "Supplier page", "url": "https://supplier.example/empty"},
                                ],
                            }
                        ],
                    }
                },
            )
        ],
    )

    class EmptyCollector:
        provider = "empty_public_catalog"

        def collect_with_diagnostics(self, query):
            return {
                "candidates": [],
                "diagnostics": {
                    "provider": "empty_public_catalog",
                    "queries_seen": 1,
                    "links_seen": 1,
                    "links_skipped": 0,
                    "pages_fetched": 1,
                    "candidates_found": 0,
                    "errors": ["no offer found"],
                },
            }

    with pytest.raises(ValueError, match="Новых кандидатов поставщиков не найдено"):
        run_profile_supplier_price_discovery(
            store.database_path,
            "mosreg_market",
            "supplier-price-discovery-no-candidates",
            1,
            collectors=[EmptyCollector()],
        )

    detail = get_tender_payload(store.database_path, "mosreg_market", "supplier-price-discovery-no-candidates")
    discovery = detail["product_profiles"][0]["raw_payload"]["supplier_discovery"]
    assert discovery == {
        "status": "no_candidates",
        "collector_diagnostics": [
            {
                "provider": "empty_public_catalog",
                "queries_seen": 1,
                "links_seen": 1,
                "links_skipped": 0,
                "pages_fetched": 1,
                "candidates_found": 0,
                "errors": ["no offer found"],
            }
        ],
        "candidates": [],
    }


def test_run_profile_supplier_price_discovery_prepares_missing_queries_from_profile_terms(tmp_path) -> None:
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="supplier-price-discovery-empty",
            url="https://market.mosreg.ru/Trade/ViewTrade/supplier-price-discovery-empty",
            title="Empty tender",
        )
    )
    store.upsert_product_profiles(
        "mosreg_market",
        "supplier-price-discovery-empty",
        [
            ProductProfile(
                tender_source="mosreg_market",
                tender_external_id="supplier-price-discovery-empty",
                position_index=1,
                product_name="Office paper A4",
            )
        ],
    )

    seen_queries: list[str] = []

    class ProfileTermCollector:
        provider = "profile_term_collector"

        def collect_with_diagnostics(self, query):
            seen_queries.append(query["query"])
            return {
                "candidates": [
                    {
                        "name": "Office paper A4",
                        "url": "https://supplier.example/office-paper-a4",
                        "unit_price": 920.0,
                        "availability": "in_stock",
                        "status": "candidate",
                        "source_query": query["query"],
                        "source_kind": query["kind"],
                        "note": "Profile term collector offer.",
                        "provider": "supplier_example",
                    }
                ],
                "diagnostics": {
                    "provider": self.provider,
                    "queries_seen": 1,
                    "links_seen": len(query.get("quick_links") or []),
                    "links_skipped": 0,
                    "pages_fetched": 1,
                    "candidates_found": 1,
                    "errors": [],
                },
            }

    payload = run_profile_supplier_price_discovery(
        store.database_path,
        "mosreg_market",
        "supplier-price-discovery-empty",
        1,
        collectors=[ProfileTermCollector()],
    )

    assert seen_queries == ["Office paper A4"]
    assert payload["staged_count"] == 1
    detail = get_tender_payload(store.database_path, "mosreg_market", "supplier-price-discovery-empty")
    profile = detail["product_profiles"][0]
    assert profile["raw_payload"]["supplier_search"]["queries"][0]["query"] == "Office paper A4"
