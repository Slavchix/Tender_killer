from __future__ import annotations

from tender_killer.analysis_context_pack_service import build_analysis_context_pack


def test_build_analysis_context_pack_classifies_roles_priorities_and_section_topics() -> None:
    documents = [
        {
            "name": "Приложение к проекту контракта, сост. 09.06.2026.zip",
            "document_type": "Приложения к контракта (ПИК)",
            "text_status": "ok",
            "text_content": (
                "Сведения об обязательствах сторон и порядке оплаты. "
                "Оплата 100% по фактическому объему в течение 5 рабочих дней после подписания УПД. "
                "Выплата аванса не предусмотрена. "
                "Место доставки товара: Московская область. "
                "Документ о приемке формируется в ПИК."
            ),
        },
        {
            "name": "Приложение к описанию объекта закупки: характеристики товара.docx",
            "document_type": "Приложение к Описанию объекта закупки",
            "text_status": "ok",
            "text_content": (
                "Приложение № 2 к Описанию объекта закупки. "
                "Требования к функциональным, техническим и качественным характеристикам товара. "
                "ОКПД2/КТРУ. Детализированное наименование товара."
            ),
        },
        {
            "name": "Статья 31.docx",
            "document_type": "Единые требования в соответствии с ч.1 ст. 31 44-ФЗ",
            "text_status": "ok",
            "text_content": (
                "Статья 31. Требования к участникам закупки. "
                "Участник закупки декларирует соответствие единым требованиям. "
                "Общая фраза: деятельность связана с поставкой товара."
            ),
        },
    ]

    context_pack = build_analysis_context_pack(
        documents,
        tender={"title": "Поставка системных блоков", "customer": "ГКУ МО"},
    )

    by_name = {document["name"]: document for document in context_pack["documents"]}
    pik = by_name["Приложение к проекту контракта, сост. 09.06.2026.zip"]
    spec_appendix = by_name["Приложение к описанию объекта закупки: характеристики товара.docx"]
    participant = by_name["Статья 31.docx"]

    assert context_pack["version"] == 1
    assert pik["document_role"] == "pik_obligations_payment"
    assert {"payment_terms", "advance", "acceptance_documents", "delivery_place"} <= set(pik["source_priority"])
    assert {"payment_terms", "advance", "acceptance_documents"} <= _topics(pik)
    assert spec_appendix["document_role"] == "technical_spec_appendix"
    assert "technical_characteristics" in spec_appendix["source_priority"]
    assert "technical_characteristics" in _topics(spec_appendix)
    assert participant["document_role"] == "participant_requirements"
    assert participant["source_priority"] == ["participant_requirements"]
    assert "delivery_place" not in _topics(participant)


def test_build_analysis_context_pack_flags_identity_mismatch_duplicates_and_unsupported_primary_docs() -> None:
    documents = [
        {
            "name": "Приложение 5 ООЗ.docx",
            "document_type": "Описание объекта закупки",
            "text_status": "ok",
            "text_content": (
                "Приложение 5 к Контракту. Описание объекта закупки. "
                "Наименование объекта закупки: Поставка велотренажеров спортивных. "
                "Код КТРУ: Системный блок."
            ),
        },
        {
            "name": "Проект контракта.docx",
            "document_type": "Проект контракта",
            "text_status": "ok",
            "text_content": "Предмет контракта: Поставка системных блоков. Штрафы и пени установлены контрактом.",
        },
        {
            "name": "Проект контракта копия.docx",
            "document_type": "Проект контракта",
            "text_status": "ok",
            "text_content": "Предмет контракта: Поставка системных блоков. Штрафы и пени установлены контрактом.",
        },
        {
            "name": "ООЗ.rar",
            "document_type": "Описание объекта закупки",
            "text_status": "error",
            "text_error": "unsupported archive",
            "text_content": "",
        },
    ]

    context_pack = build_analysis_context_pack(
        documents,
        tender={"title": "Поставка системных блоков", "customer": "ГКУ МО"},
    )

    by_name = {document["name"]: document for document in context_pack["documents"]}
    mismatch = by_name["Приложение 5 ООЗ.docx"]
    contract = by_name["Проект контракта.docx"]
    contract_copy = by_name["Проект контракта копия.docx"]
    unsupported = by_name["ООЗ.rar"]

    assert "subject_mismatch" in mismatch["mismatch_flags"]
    assert mismatch["tender_identity_match"]["subject"]["document_subject"] == "Поставка велотренажеров спортивных"
    assert contract["duplicate_group_id"]
    assert contract["duplicate_group_id"] == contract_copy["duplicate_group_id"]
    assert unsupported["document_role"] == "unsupported_primary"
    assert "missing_because_primary_doc_unread" in context_pack["expected_missing_reasons"]
    assert "subject_mismatch" in context_pack["mismatch_flags"]
    assert context_pack["metrics"]["duplicate_groups"] == 1


def test_build_analysis_context_pack_detects_service_payment_acceptance_penalty_and_warranty_topics() -> None:
    documents = [
        {
            "name": "service-tz.docx",
            "document_type": "technical specification",
            "text_status": "ok",
            "text_content": (
                "Техническое задание: оказание услуг по дезинфекции вентиляции. "
                "Работы закрываются актом выполненных работ. "
                "Гарантия на выполненные работы составляет 12 месяцев."
            ),
        },
        {
            "name": "service-contract.docx",
            "document_type": "contract",
            "text_status": "ok",
            "text_content": (
                "Проект контракта. Оплата производится после подписания акта. "
                "За нарушение сроков оказания услуг начисляется пеня."
            ),
        },
    ]

    context_pack = build_analysis_context_pack(documents)
    topics = set(context_pack["topic_coverage"])

    assert {"acceptance_documents", "payment_terms", "penalties", "warranty"} <= topics


def _topics(document: dict[str, object]) -> set[str]:
    return {
        str(item.get("topic"))
        for item in document.get("section_taxonomy", [])
        if isinstance(item, dict) and item.get("topic")
    }
