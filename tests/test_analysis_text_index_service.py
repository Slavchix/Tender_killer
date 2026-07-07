from __future__ import annotations

from tender_killer.analysis_text_index_service import build_analysis_text_index


def test_build_analysis_text_index_classifies_documents_sections_chunks_and_quality():
    documents = [
        {
            "name": "Описание объекта закупки.docx",
            "document_type": "Описание объекта закупки",
            "text_status": "ok",
            "text_content": (
                "Раздел 1. Предмет\nПоставка бумаги для печати.\f"
                "Раздел 2. Требования к товару\nПоставщик предоставляет сертификат соответствия."
            ),
        },
        {
            "name": "Проект контракта.docx",
            "document_type": "Проект контракта",
            "text_status": "ok",
            "text_content": "Раздел 5. Приемка\nОплата в течение 7 рабочих дней после приемки.",
        },
        {
            "name": "НМЦК.xlsx",
            "document_type": "Обоснование НМЦК",
            "text_status": "ok",
            "text_content": "Наименование\tЦена\nБумага\t100",
        },
        {
            "name": "scan.pdf",
            "document_type": "Скан",
            "text_status": "empty",
            "text_content": "",
        },
    ]

    text_index = build_analysis_text_index(documents)

    roles = {document["name"]: document["document_role"] for document in text_index["documents"]}
    spec = next(document for document in text_index["documents"] if document["name"] == "Описание объекта закупки.docx")
    empty_scan = next(document for document in text_index["documents"] if document["name"] == "scan.pdf")

    assert text_index["version"] == 1
    assert text_index["metrics"]["documents"] == 4
    assert text_index["metrics"]["chunks"] >= 4
    assert text_index["metrics"]["attention"] == 1
    assert roles["Описание объекта закупки.docx"] == "technical_specification"
    assert roles["Проект контракта.docx"] == "contract"
    assert roles["НМЦК.xlsx"] == "nmck"
    assert spec["quality"]["status"] == "ok"
    assert spec["quality"]["pages"] == 2
    assert spec["quality"]["chunks"] >= 2
    assert any(section["title"].startswith("Раздел 2") for section in spec["sections"])
    assert any(
        chunk["page"] == 2
        and chunk["section"].startswith("Раздел 2")
        and "сертификат соответствия" in chunk["text"]
        for chunk in spec["chunks"]
    )
    assert empty_scan["quality"]["status"] == "empty"
    assert empty_scan["chunks"] == []
