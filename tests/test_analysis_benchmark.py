from __future__ import annotations

import pytest

from tender_killer.analysis import analyze_tender_texts
from tender_killer.analysis_benchmark_service import REQUIRED_TZ_BENCHMARK_CATEGORIES
from tender_killer.analysis_benchmark_service import TZ_BENCHMARK_TARGET_CASE_COUNT
from tender_killer.analysis_benchmark_service import load_tz_benchmark_cases
from tender_killer.analysis_benchmark_service import run_tz_benchmark_suite
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


def test_tz_benchmark_scorer_tracks_context_pack_expectations():
    case = {
        "name": "real_system_blocks_context",
        "category": "small_supply",
        "expected_labels": [],
        "expected_terms": [],
        "expected_conflicts": [],
        "expected_missing": [],
        "expected_document_roles": [
            "technical_spec_appendix",
            "pik_obligations_payment",
            "unsupported_primary",
        ],
        "expected_context_topics": ["payment_terms", "advance", "technical_characteristics"],
        "expected_context_missing_reasons": ["missing_because_primary_doc_unread"],
        "expected_mismatch_flags": ["subject_mismatch"],
        "absent_labels": [],
    }
    analysis = {
        "context_pack": {
            "version": 1,
            "documents": [
                {"name": "OOZ.docx", "document_role": "technical_spec_appendix"},
                {"name": "PIK.zip", "document_role": "pik_obligations_payment"},
                {"name": "OOZ.rar", "document_role": "unsupported_primary"},
            ],
            "topic_coverage": {
                "payment_terms": {"count": 1, "documents": ["PIK.zip"]},
                "advance": {"count": 1, "documents": ["PIK.zip"]},
                "technical_characteristics": {"count": 1, "documents": ["OOZ.docx"]},
            },
            "expected_missing_reasons": ["missing_because_primary_doc_unread"],
            "mismatch_flags": ["subject_mismatch"],
        }
    }

    score = score_tz_benchmark_case(case, analysis)
    summary = summarize_tz_benchmark_scores([score])

    assert score["matched_document_roles"] == [
        "pik_obligations_payment",
        "technical_spec_appendix",
        "unsupported_primary",
    ]
    assert score["missed_document_roles"] == []
    assert score["matched_context_topics"] == ["advance", "payment_terms", "technical_characteristics"]
    assert score["missed_context_topics"] == []
    assert score["matched_context_missing_reasons"] == ["missing_because_primary_doc_unread"]
    assert score["matched_mismatch_flags"] == ["subject_mismatch"]
    assert score["recall"] == 1.0
    assert summary["context_quality"]["found"] == 8
    assert summary["context_quality"]["missed"] == 0


def test_load_tz_benchmark_cases_exposes_product_fixture_contract():
    cases = load_tz_benchmark_cases()

    categories = {case["category"] for case in cases}
    context_cases = [case for case in cases if case.get("expected_document_roles")]

    assert len(cases) >= TZ_BENCHMARK_TARGET_CASE_COUNT["min"]
    assert len(cases) <= TZ_BENCHMARK_TARGET_CASE_COUNT["max"]
    assert categories >= set(REQUIRED_TZ_BENCHMARK_CATEGORIES)
    assert len(context_cases) >= 5
    for case in cases:
        assert case["name"]
        assert case["category"] in REQUIRED_TZ_BENCHMARK_CATEGORIES
        assert case["texts"] and all(isinstance(text, str) and text.strip() for text in case["texts"])
        assert isinstance(case["expected_labels"], list)
        assert isinstance(case["expected_terms"], list)
        assert isinstance(case["expected_conflicts"], list)
        assert isinstance(case["expected_missing"], list)
        assert isinstance(case["absent_labels"], list)
        assert isinstance(case["expected_document_roles"], list)
        assert isinstance(case["expected_context_topics"], list)
        assert isinstance(case["expected_context_missing_reasons"], list)
        assert isinstance(case["expected_mismatch_flags"], list)


def test_run_tz_benchmark_suite_reports_saas_quality_metrics():
    suite = run_tz_benchmark_suite(
        [
            {
                "name": "service_with_sro_runner",
                "category": "services",
                "texts": [
                    """
                    Техническое задание: выполнение работ по обслуживанию инженерных систем.
                    Исполнитель должен иметь действующее членство в СРО.
                    Работы закрываются актом выполненных работ.
                    За нарушение сроков выполнения работ начисляется пеня.
                    Гарантийный срок на выполненные работы составляет 12 месяцев.
                    """
                ],
                "expected_labels": [
                    "лицензия/СРО",
                    "акт выполненных работ",
                    "штрафы/пени",
                    "гарантия",
                ],
                "expected_terms": ["warranty_period", "penalties"],
                "expected_conflicts": [],
                "expected_missing": ["условия оплаты"],
                "absent_labels": ["короткий срок поставки"],
            },
            {
                "name": "supply_missing_payment_runner",
                "category": "small_supply",
                "texts": [
                    """
                    Техническое задание: поставка офисной бумаги А4.
                    Поставщик предоставляет сертификат соответствия.
                    Поставка товара осуществляется в течение 5 рабочих дней.
                    """
                ],
                "expected_labels": ["сертификат/декларация", "срок поставки"],
                "expected_terms": ["delivery_deadline"],
                "expected_conflicts": [],
                "expected_missing": ["условия оплаты", "приемка и закрывающие документы"],
                "absent_labels": ["лицензия/СРО"],
            },
        ]
    )

    summary = suite["summary"]

    assert suite["version"] == 1
    assert summary["cases"] == 2
    assert summary["case_count_gap"] == TZ_BENCHMARK_TARGET_CASE_COUNT["min"] - 2
    assert summary["coverage_status"] == "needs_more_cases"
    assert summary["quality_gates"]["target_case_count"]["passed"] is False
    assert summary["quality_gates"]["required_categories"]["passed"] is False
    assert summary["category_scores"]["services"]["cases"] == 1
    assert summary["category_scores"]["small_supply"]["cases"] == 1
    assert summary["fact_quality"]["found"] >= 9
    assert summary["fact_quality"]["missed"] == 0
    assert summary["fact_quality"]["hallucinated"] == 0
    assert summary["fact_quality"]["expected_missing_caught"] >= 3
    assert summary["fact_quality"]["conflicts_caught"] == 0
