from __future__ import annotations

import importlib
import importlib.util


def _fact_source_service():
    spec = importlib.util.find_spec("tender_killer.analysis_fact_source_service")
    assert spec is not None
    return importlib.import_module("tender_killer.analysis_fact_source_service")


def test_document_source_prefers_explicit_page_or_context_binding():
    service = _fact_source_service()

    source = service.document_source(
        {
            "document_name": "manual.docx",
            "source_page": "2",
            "source_label": "manual.docx · стр. 2",
            "source_context": "Раздел с условиями оплаты.",
        },
        "Оплата после приемки.",
        [],
    )

    assert source == {
        "document_name": "manual.docx",
        "source_page": "2",
        "source_label": "manual.docx · стр. 2",
        "source_context": "Раздел с условиями оплаты.",
    }


def test_document_source_finds_document_by_fragment_when_explicit_binding_is_missing():
    service = _fact_source_service()

    source = service.document_source(
        {},
        "Поставщик предоставляет сертификат соответствия.",
        [
            {
                "name": "spec.docx",
                "text_content": "Техническое задание. Поставщик предоставляет сертификат соответствия.",
            }
        ],
    )

    assert source["document_name"] == "spec.docx"
    assert source["source_label"] == "spec.docx · стр. не определена"
    assert "Поставщик предоставляет сертификат соответствия" in source["source_context"]


def test_source_helpers_normalize_page_labels_and_evidence_sources():
    service = _fact_source_service()

    assert service.page_number("3") == 3
    assert service.page_number("0") is None
    assert service.source_label("contract.pdf", 3) == "contract.pdf · стр. 3"
    assert service.source_label("contract.pdf", None) == "contract.pdf · стр. не определена"
    assert service.evidence_sources("contract.pdf", "contract.pdf · стр. 3", "Оплата 100%.") == [
        {
            "document_name": "contract.pdf",
            "source_label": "contract.pdf · стр. 3",
            "fragment": "Оплата 100%.",
        }
    ]
    assert service.evidence_sources("contract.pdf", "contract.pdf · стр. 3", "") == []
