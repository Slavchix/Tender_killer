from __future__ import annotations

import pytest

from tender_killer.analysis import analyze_tender_texts
from tender_killer.analysis_benchmark_service import REQUIRED_TZ_BENCHMARK_CATEGORIES
from tender_killer.analysis_benchmark_service import score_tz_benchmark_case
from tender_killer.analysis_benchmark_service import summarize_tz_benchmark_scores


BENCHMARK_CASES = [
    {
        "name": "medical_goods",
        "texts": [
            """
            Техническое задание: поставка расходных медицинских изделий.
            Поставщик предоставляет копию регистрационного удостоверения Росздравнадзора,
            декларацию о соответствии и паспорт качества на каждую партию.
            Остаточный срок годности товара на дату поставки должен быть не менее 12 месяцев.
            Товар должен поставляться в заводской упаковке, с соблюдением температурного режима хранения.
            Изделия должны быть стерильными.
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
            "температурный режим хранения",
            "стерильность",
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
            У исполнителя должен быть квалифицированный персонал с подтвержденным опытом.
            Работы закрываются актом выполненных работ.
            За нарушение сроков выполнения работ начисляется пеня.
            Гарантийный срок на выполненные работы составляет 12 месяцев.
            """
        ],
        "expected_labels": {"лицензия/СРО", "квалифицированный персонал", "акт выполненных работ", "штрафы/пени", "гарантия"},
        "expected_terms": {"warranty_period", "penalties"},
        "absent_labels": {"короткий срок поставки"},
    },
    {
        "name": "construction_installation",
        "texts": [
            """
            Техническое задание: поставка, монтаж и пусконаладка насосного оборудования.
            Оборудование должно соответствовать ГОСТ и техническим условиям производителя.
            Поставщик выполняет монтаж, пусконаладочные работы и инструктаж персонала заказчика.
            Требуется гарантия не менее 24 месяцев.
            """
        ],
        "expected_labels": {"ГОСТ/ТУ", "монтаж/пусконаладка", "инструктаж заказчика", "гарантия"},
        "expected_terms": {"warranty_period"},
        "absent_labels": set(),
    },
    {
        "name": "electronics_equivalent",
        "texts": [
            """
            Техническое задание: поставка аккумуляторных батарей.
            Допускается поставка эквивалента при полной совместимости с имеющимся оборудованием.
            Участник должен подтвердить совместимость товара техническим описанием производителя.
            Гарантийный срок на товар составляет 12 месяцев.
            """
        ],
        "expected_labels": {"эквивалент", "совместимость", "гарантия"},
        "expected_terms": {"warranty_period"},
        "absent_labels": set(),
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


def test_tz_benchmark_scorer_tracks_fact_quality_conflicts_and_coverage():
    case = {
        "name": "advance_conflict",
        "category": "conflicting_documents",
        "expected_labels": ["Аванс", "условия оплаты"],
        "expected_terms": ["advance_payment"],
        "expected_conflicts": ["Аванс"],
        "expected_missing": ["приемка и закрывающие документы"],
        "absent_labels": ["лицензия/СРО"],
    }
    analysis = {
        "requirements": ["условия оплаты"],
        "risks": [],
        "red_flags": [],
        "execution_terms": [{"type": "advance_payment", "label": "Аванс"}],
        "operator_view": {
            "metrics": {"conflicts": 1, "expected_missing": 1},
            "sections": [
                {
                    "id": "acceptance_payment",
                    "items": [
                        {
                            "id": "advance",
                            "label": "Аванс",
                            "kind": "execution_term",
                            "conflict_flags": ["Разные условия аванса"],
                        },
                        {
                            "id": "expected:closing_documents",
                            "label": "приемка и закрывающие документы",
                            "kind": "expected_check",
                            "expected_missing": True,
                        },
                    ],
                }
            ],
        },
    }

    score = score_tz_benchmark_case(case, analysis)
    summary = summarize_tz_benchmark_scores([score])

    assert score["category"] == "conflicting_documents"
    assert score["matched_labels"] == ["Аванс", "условия оплаты"]
    assert score["missed_labels"] == []
    assert score["matched_terms"] == ["advance_payment"]
    assert score["matched_conflicts"] == ["Аванс"]
    assert score["matched_expected_missing"] == ["приемка и закрывающие документы"]
    assert score["false_positive_labels"] == []
    assert score["recall"] == 1.0
    assert score["precision"] == 1.0
    assert score["manual_review_required"] is True
    assert summary["target_case_count"] == {"min": 20, "max": 30}
    assert "conflicting_documents" in summary["categories"]
    assert set(REQUIRED_TZ_BENCHMARK_CATEGORIES) >= {
        "small_supply",
        "cartridges_paper",
        "construction_materials",
        "services",
        "advance_payment",
        "no_advance",
        "conflicting_documents",
        "poor_ocr",
        "multiple_revisions",
    }
