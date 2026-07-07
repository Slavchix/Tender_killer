from __future__ import annotations

import importlib
import importlib.util


def _metadata_service():
    spec = importlib.util.find_spec("tender_killer.analysis_fact_metadata_service")
    assert spec is not None
    return importlib.import_module("tender_killer.analysis_fact_metadata_service")


def test_structured_metadata_builds_document_context_and_typed_fields():
    service = _metadata_service()

    metadata = service.structured_metadata(
        label="Оплата",
        category="payment",
        term_type="payment",
        text="Оплата 30% в течение 5 рабочих дней поставщиком после приемки.",
        document_name="payment.docx",
        document_roles={"payment.docx": "pik_obligations_payment"},
        document_contexts={
            "payment.docx": {
                "document_role": "pik_obligations_payment",
                "document_role_confidence": "high",
                "source_priority": ["payment_terms", "acceptance_process"],
                "section_taxonomy": [
                    {"topic": "payment_terms"},
                    {"topic": "acceptance_process"},
                    {"topic": "payment_terms"},
                ],
                "mismatch_flags": ["conflicting_revision"],
                "text_quality": {"status": "ok"},
            }
        },
    )

    assert metadata["document_role"] == "pik_obligations_payment"
    assert metadata["context_document_role"] == "pik_obligations_payment"
    assert metadata["context_document_role_confidence"] == "high"
    assert metadata["context_source_priority"] == ["payment_terms", "acceptance_process"]
    assert metadata["context_source_authority"] == "primary_for_topic"
    assert metadata["context_source_reason"] == "pik_obligations_payment covers payment_terms"
    assert metadata["context_topics"] == ["payment_terms", "acceptance_process"]
    assert metadata["context_mismatch_flags"] == ["conflicting_revision"]
    assert metadata["context_text_quality"] == "ok"
    assert metadata["document_stage"] == "acceptance"
    assert metadata["amount_percent"] == 30
    assert metadata["amount_type"] == "financial_condition"
    assert metadata["days"] == 5
    assert metadata["deadline_type"] == "payment"
    assert metadata["responsible_party"] == "supplier"


def test_metadata_service_exposes_semantic_keys_and_operator_impact():
    service = _metadata_service()

    assert service.semantic_key("страна происхождения товара", "national_regime") == "national_regime"
    assert service.semantic_key("Требуется лицензия СРО", "legal") == "license_sro"
    assert service.semantic_key("Обеспечение исполнения контракта", "financial") == "contract_security"
    assert service.semantic_key("Габариты", "standards") == ""

    assert service.impact("legal", "high").startswith("Проверить до участия")
    assert service.impact("documents", "medium").startswith("Проверить наличие документа")
    assert service.impact("payment", "medium").startswith("Учесть в сроках")
