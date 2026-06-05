from __future__ import annotations

from tender_killer.supplier_product_matcher import supplier_product_name_matches_query


def test_cartridge_query_rejects_other_product_families() -> None:
    query = "cartridge for electrophotographic printing devices"

    assert supplier_product_name_matches_query(query, "Sakura W1510X cartridge for HP LaserJet Pro 4003") is True
    assert supplier_product_name_matches_query(query, "Office paper A4, 80 gsm, 500 sheets") is False
    assert supplier_product_name_matches_query(query, "Evacuation sign Direction arrow, 10 pieces") is False
    assert supplier_product_name_matches_query(query, "Body sponge with massage effect") is False


def test_russian_cartridge_query_rejects_office_paper() -> None:
    query = "\u041a\u0430\u0440\u0442\u0440\u0438\u0434\u0436 \u0434\u043b\u044f \u044d\u043b\u0435\u043a\u0442\u0440\u043e\u0444\u043e\u0442\u043e\u0433\u0440\u0430\u0444\u0438\u0447\u0435\u0441\u043a\u0438\u0445 \u043f\u0435\u0447\u0430\u0442\u0430\u044e\u0449\u0438\u0445 \u0443\u0441\u0442\u0440\u043e\u0439\u0441\u0442\u0432"

    assert supplier_product_name_matches_query(query, "\u041a\u0430\u0440\u0442\u0440\u0438\u0434\u0436 Sakura W1510X \u0434\u043b\u044f HP LaserJet Pro 4003") is True
    assert supplier_product_name_matches_query(query, "\u0411\u0443\u043c\u0430\u0433\u0430 \u043e\u0444\u0438\u0441\u043d\u0430\u044f A4, 80 \u0433/\u043c2") is False


def test_office_paper_query_rejects_unrelated_stationery() -> None:
    query = "office paper 80 gsm A4"

    assert supplier_product_name_matches_query(query, "BRAUBERG office paper, A4, 80 gsm") is True
    assert supplier_product_name_matches_query(query, "BRAUBERG Office 2-ring binder, 75 mm") is False
    assert supplier_product_name_matches_query(query, "Sakura W1510X cartridge for HP LaserJet Pro 4003") is False


def test_russian_office_paper_query_rejects_colored_and_safety_goods() -> None:
    query = (
        "\u0411\u0443\u043c\u0430\u0433\u0430 \u0434\u043b\u044f "
        "\u043e\u0444\u0438\u0441\u043d\u043e\u0439 \u0442\u0435\u0445\u043d\u0438\u043a\u0438, "
        "\u041c\u0430\u0440\u043a\u0430 \u0431\u0443\u043c\u0430\u0433\u0438: "
        "\u041d\u0435 \u043d\u0438\u0436\u0435 \u0421, \u0424\u043e\u0440\u043c\u0430\u0442: \u04104"
    )

    assert supplier_product_name_matches_query(
        query,
        "\u0411\u0443\u043c\u0430\u0433\u0430 \u043e\u0444\u0438\u0441\u043d\u0430\u044f A4, "
        "500 \u043b\u0438\u0441\u0442\u043e\u0432, \u0431\u0435\u043b\u0430\u044f, 80 \u0433/\u043c2",
    ) is True
    assert supplier_product_name_matches_query(
        query,
        "\u0411\u0443\u043c\u0430\u0433\u0430 \u0446\u0432\u0435\u0442\u043d\u0430\u044f BRAUBERG, "
        "\u04104, 80 \u0433/\u043c2, 250 \u043b., \u0438\u043d\u0442\u0435\u043d\u0441\u0438\u0432",
    ) is False
    assert supplier_product_name_matches_query(
        query,
        "\u0417\u043d\u0430\u043a \u044d\u0432\u0430\u043a\u0443\u0430\u0446\u0438\u043e\u043d\u043d\u044b\u0439 "
        "\u041d\u0430\u043f\u0440\u0430\u0432\u043b\u044f\u044e\u0449\u0430\u044f "
        "\u0441\u0442\u0440\u0435\u043b\u043a\u0430",
    ) is False


def test_russian_office_paper_procurement_title_matches_plain_office_paper() -> None:
    query = "\u041f\u043e\u0441\u0442\u0430\u0432\u043a\u0430 \u0431\u0443\u043c\u0430\u0433\u0438 \u0434\u043b\u044f \u043e\u0444\u0438\u0441\u043d\u043e\u0439 \u0442\u0435\u0445\u043d\u0438\u043a\u0438"

    assert supplier_product_name_matches_query(
        query,
        "\u0411\u0443\u043c\u0430\u0433\u0430 \u043e\u0444\u0438\u0441\u043d\u0430\u044f A4, 80 \u0433/\u043c2, 500 \u043b\u0438\u0441\u0442\u043e\u0432",
    ) is True
    assert supplier_product_name_matches_query(
        query,
        "\u0417\u043d\u0430\u043a \u044d\u0432\u0430\u043a\u0443\u0430\u0446\u0438\u043e\u043d\u043d\u044b\u0439 "
        "\u041d\u0430\u043f\u0440\u0430\u0432\u043b\u044f\u044e\u0449\u0430\u044f \u0441\u0442\u0440\u0435\u043b\u043a\u0430",
    ) is False
    assert supplier_product_name_matches_query(
        query,
        "\u041a\u0430\u0440\u0442\u0440\u0438\u0434\u0436 Sakura W1510X \u0434\u043b\u044f HP LaserJet Pro 4003",
    ) is False


def test_russian_stationery_queries_reject_other_stationery_families() -> None:
    assert supplier_product_name_matches_query(
        "\u0420\u0443\u0447\u043a\u0430 \u043a\u0430\u043d\u0446\u0435\u043b\u044f\u0440\u0441\u043a\u0430\u044f",
        "\u0420\u0443\u0447\u043a\u0430 \u0448\u0430\u0440\u0438\u043a\u043e\u0432\u0430\u044f STAFF, "
        "\u0421\u0418\u041d\u042f\u042f, \u0443\u0437\u0435\u043b 1 \u043c\u043c",
    ) is True
    assert supplier_product_name_matches_query(
        "\u0420\u0443\u0447\u043a\u0430 \u043a\u0430\u043d\u0446\u0435\u043b\u044f\u0440\u0441\u043a\u0430\u044f",
        "\u0417\u043d\u0430\u043a \u043f\u043e\u0436\u0430\u0440\u043d\u043e\u0439 "
        "\u0431\u0435\u0437\u043e\u043f\u0430\u0441\u043d\u043e\u0441\u0442\u0438",
    ) is False
    assert supplier_product_name_matches_query(
        "\u041a\u043b\u0435\u0439\u043a\u0430\u044f \u043b\u0435\u043d\u0442\u0430",
        "\u041a\u043b\u0435\u0439\u043a\u0430\u044f \u043b\u0435\u043d\u0442\u0430 "
        "\u0443\u043f\u0430\u043a\u043e\u0432\u043e\u0447\u043d\u0430\u044f, 48 \u043c\u043c \u0445 66 \u043c",
    ) is True
    assert supplier_product_name_matches_query(
        "\u041a\u043b\u0435\u0439\u043a\u0430\u044f \u043b\u0435\u043d\u0442\u0430",
        "\u0420\u0443\u0447\u043a\u0430 \u0448\u0430\u0440\u0438\u043a\u043e\u0432\u0430\u044f STAFF",
    ) is False
    assert supplier_product_name_matches_query(
        "\u0422\u043e\u0447\u0438\u043b\u043a\u0430 "
        "\u043a\u0430\u043d\u0446\u0435\u043b\u044f\u0440\u0441\u043a\u0430\u044f "
        "\u0434\u043b\u044f \u043a\u0430\u0440\u0430\u043d\u0434\u0430\u0448\u0435\u0439",
        "1",
    ) is False


def test_unknown_family_still_requires_meaningful_overlap() -> None:
    query = "submersible drainage pump GNOM 16-16Tr 380 V"

    assert supplier_product_name_matches_query(query, "GNOM 16-16 submersible drainage pump") is True
    assert supplier_product_name_matches_query(query, "Office paper A4 80 gsm") is False
