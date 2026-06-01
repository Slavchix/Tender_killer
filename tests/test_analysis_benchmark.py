from __future__ import annotations

import pytest

from tender_killer.analysis import analyze_tender_texts


BENCHMARK_CASES = [
    {
        "name": "medical_goods",
        "texts": [
            """
            Техническое задание: поставка расходных медицинских изделий.
            Поставщик предоставляет копию регистрационного удостоверения Росздравнадзора,
            декларацию о соответствии и паспорт качества на каждую партию.
            Остаточный срок годности товара на дату поставки должен быть не менее 12 месяцев.
            Срок поставки товара: в течение 5 рабочих дней.
            Оплата производится в течение 7 рабочих дней после подписания документа о приемке.
            Обеспечение исполнения контракта составляет 5 процентов.
            """
        ],
        "expected_labels": {
            "регистрационное удостоверение",
            "сертификат/декларация",
            "паспорт качества",
            "срок годности",
            "срок поставки",
            "обеспечение исполнения контракта",
        },
        "expected_terms": {"delivery_deadline", "payment_terms", "contract_security"},
        "absent_labels": set(),
    },
    {
        "name": "noise_only",
        "texts": [
            """
            Документы закупки хранятся в архиве в течение 3 лет.
            Пользователь принимает лицензионное соглашение производителя программного обеспечения.
            Конфиденциальность действует в течение трех лет после исполнения договора.
            """
        ],
        "expected_labels": set(),
        "expected_terms": set(),
        "absent_labels": {"короткий срок поставки", "лицензия/СРО"},
    },
    {
        "name": "service_with_sro",
        "texts": [
            """
            Техническое задание: выполнение работ по обслуживанию инженерных систем.
            Исполнитель должен иметь действующее членство в СРО.
            За нарушение сроков выполнения работ начисляется пеня.
            Гарантийный срок на выполненные работы составляет 12 месяцев.
            """
        ],
        "expected_labels": {"лицензия/СРО", "штрафы/пени", "гарантия"},
        "expected_terms": {"warranty_period", "penalties"},
        "absent_labels": {"короткий срок поставки"},
    },
]


@pytest.mark.parametrize("case", BENCHMARK_CASES, ids=[case["name"] for case in BENCHMARK_CASES])
def test_analysis_benchmark_cases(case):
    result = analyze_tender_texts(case["texts"])

    labels = set(result.requirements + result.risks + result.red_flags)
    terms = {term["type"] for term in result.execution_terms}

    assert case["expected_labels"] <= labels
    assert case["expected_terms"] <= terms
    assert labels.isdisjoint(case["absent_labels"])
