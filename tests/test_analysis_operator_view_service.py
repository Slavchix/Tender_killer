from __future__ import annotations

from tender_killer.analysis_operator_view_service import build_analysis_operator_view


def test_build_analysis_operator_view_prioritizes_blockers_and_groups_operator_sections():
    analysis = {
        "summary": "Supply office paper.",
        "status": "needs_review",
        "confidence": 0.82,
        "requirements": ["certificate"],
        "risks": ["contract security"],
        "red_flags": ["national regime"],
        "checklist": [
            {
                "label": "contract security",
                "category": "financial",
                "severity": "high",
                "evidence": "Security is 5%.",
            },
            {
                "label": "certificate",
                "category": "documents",
                "severity": "medium",
                "evidence": "Certificate is required.",
            },
            {
                "label": "short delivery",
                "category": "delivery",
                "severity": "high",
                "evidence": "Delivery in 3 days.",
            },
        ],
        "evidence_items": [
            {
                "id": "certificate-1",
                "label": "certificate",
                "category": "documents",
                "severity": "medium",
                "fragment": "Certificate is required.",
                "impact": "Check supplier documents.",
            }
        ],
    }
    documents = [
        {"name": "TZ.docx", "text_status": "ok"},
        {"name": "Contract.pdf", "text_status": "empty"},
    ]

    view = build_analysis_operator_view(analysis, documents)

    assert view["version"] == 2
    assert view["decision_brief"]["status"] == "manual_review"
    assert view["decision_brief"]["tone"] == "danger"
    assert view["decision_brief"]["primary_section"] == "blockers"
    assert view["decision_brief"]["confidence"] == 0.82
    assert view["metrics"] == {
        "requirements": 1,
        "risks": 2,
        "blockers": 3,
        "checklist": 3,
        "execution_terms": 0,
        "evidence": 1,
        "documents_ready": 1,
        "documents_total": 2,
    }

    sections = {section["id"]: section for section in view["sections"]}
    assert list(sections) == [
        "blockers",
        "requirements",
        "execution_terms",
        "price_factors",
        "documents",
        "evidence",
    ]
    assert [item["label"] for item in sections["blockers"]["items"]] == [
        "national regime",
        "contract security",
        "short delivery",
    ]
    assert [item["label"] for item in sections["requirements"]["items"]] == ["certificate"]
    assert [item["label"] for item in sections["price_factors"]["items"]] == [
        "contract security",
        "short delivery",
    ]
    assert sections["documents"]["items"][0]["label"] == "TZ.docx"
    assert sections["documents"]["items"][1]["status"] == "attention"
    assert sections["evidence"]["items"][0]["label"] == "certificate"


def test_build_analysis_operator_view_surfaces_execution_terms_between_core_sections():
    analysis = {
        "summary": "Supply office paper.",
        "status": "needs_review",
        "confidence": 0.74,
        "requirements": ["certificate"],
        "risks": [],
        "red_flags": [],
        "checklist": [
            {
                "label": "certificate",
                "category": "documents",
                "severity": "medium",
                "evidence": "Certificate is required.",
            }
        ],
        "execution_terms": [
            {
                "type": "delivery_deadline",
                "label": "Срок поставки",
                "value": "в течение 5 рабочих дней",
                "category": "delivery",
                "severity": "medium",
                "evidence": "Срок поставки товара: в течение 5 рабочих дней.",
            },
            {
                "type": "contract_security",
                "label": "Обеспечение исполнения",
                "value": "5 процентов от цены контракта",
                "category": "financial",
                "severity": "high",
                "evidence": "Обеспечение исполнения контракта составляет 5 процентов.",
            },
        ],
    }

    view = build_analysis_operator_view(analysis, [])

    assert view["metrics"]["execution_terms"] == 2
    assert [section["id"] for section in view["sections"]] == [
        "blockers",
        "requirements",
        "execution_terms",
        "price_factors",
        "documents",
        "evidence",
    ]
    execution_section = next(section for section in view["sections"] if section["id"] == "execution_terms")
    assert execution_section["title"] == "Условия исполнения"
    assert [item["label"] for item in execution_section["items"]] == [
        "Срок поставки",
        "Обеспечение исполнения",
    ]
    assert execution_section["items"][0]["description"] == "в течение 5 рабочих дней"
    assert execution_section["items"][1]["severity"] == "high"


def test_build_analysis_operator_view_groups_analysis_facts_into_operator_blocks():
    analysis = {
        "summary": "Supply office paper.",
        "confidence": 0.81,
        "analysis_facts": {
            "version": 1,
            "metrics": {"total": 5, "blockers": 1, "price_factors": 1, "unbound": 1},
            "items": [
                {
                    "id": "subject:paper",
                    "kind": "subject",
                    "label": "Предмет",
                    "value": "Supply office paper.",
                    "category": "subject",
                    "severity": "medium",
                },
                {
                    "id": "blocker:national-regime",
                    "kind": "blocker",
                    "label": "национальный режим",
                    "value": "страна происхождения товара",
                    "category": "national_regime",
                    "severity": "high",
                    "document_name": "spec.docx",
                    "fragment": "Указывается страна происхождения товара.",
                    "impact": "Проверить до участия.",
                    "is_blocker": True,
                    "is_price_factor": False,
                },
                {
                    "id": "supplier_document:certificate",
                    "kind": "supplier_document",
                    "label": "сертификат/декларация",
                    "value": "сертификат соответствия",
                    "category": "documents",
                    "severity": "medium",
                    "document_name": "spec.docx",
                    "fragment": "Поставщик предоставляет сертификат.",
                    "impact": "Подготовить документ.",
                    "is_blocker": False,
                    "is_price_factor": False,
                },
                {
                    "id": "execution_term:delivery",
                    "kind": "execution_term",
                    "label": "Срок поставки",
                    "value": "5 рабочих дней",
                    "category": "delivery",
                    "severity": "medium",
                    "document_name": "contract.docx",
                    "fragment": "Срок поставки 5 рабочих дней.",
                    "impact": "Учесть в логистике.",
                    "is_blocker": False,
                    "is_price_factor": True,
                },
                {
                    "id": "requirement:license",
                    "kind": "requirement",
                    "label": "лицензия/СРО",
                    "value": "Нужна лицензия на работы.",
                    "category": "legal",
                    "severity": "high",
                    "document_name": "Документ не привязан",
                    "fragment": "Нужна лицензия на работы.",
                    "impact": "Проверить источник.",
                    "needs_review": True,
                    "is_blocker": True,
                    "is_price_factor": False,
                },
            ],
        },
    }

    view = build_analysis_operator_view(analysis, [])
    sections = {section["id"]: section for section in view["sections"]}

    assert view["decision_brief"]["primary_section"] == "blockers"
    assert view["metrics"]["facts"] == 5
    assert view["metrics"]["unbound_facts"] == 1
    assert sections["blockers"]["title"] == "Блокеры участия"
    assert sections["requirements"]["title"] == "Что подготовить"
    assert sections["execution_terms"]["title"] == "Исполнение договора"
    assert sections["price_factors"]["title"] == "Влияние на цену"
    assert sections["manual_review"]["title"] == "Проверить руками"
    assert [item["label"] for item in sections["blockers"]["items"]] == [
        "национальный режим",
        "лицензия/СРО",
    ]
    assert [item["label"] for item in sections["requirements"]["items"]] == ["сертификат/декларация"]
    assert [item["label"] for item in sections["execution_terms"]["items"]] == ["Срок поставки"]
    assert [item["label"] for item in sections["price_factors"]["items"]] == ["Срок поставки"]
    assert sections["manual_review"]["items"][0]["source"] == "Документ не привязан"


def test_build_analysis_operator_view_returns_pending_contract_without_analysis():
    view = build_analysis_operator_view(None, [{"name": "Spec.docx", "text_status": "pending"}])

    assert view["version"] == 2
    assert view["decision_brief"]["status"] == "pending"
    assert view["decision_brief"]["primary_section"] == "documents"
    assert view["metrics"]["documents_total"] == 1
    assert view["sections"][0]["id"] == "blockers"
