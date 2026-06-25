from tender_killer.analysis_operator_context_service import build_context_operator_items


def test_build_context_operator_items_marks_subject_mismatch_as_blocker():
    items = build_context_operator_items(
        {
            "version": 1,
            "documents": [
                {
                    "name": "Проект контракта.docx",
                    "mismatch_flags": ["subject_mismatch"],
                    "tender_identity_match": {
                        "subject": {
                            "tender_title": "Поставка баскетбольного табло",
                            "document_subject": "Поставка офисной бумаги",
                        }
                    },
                }
            ],
        }
    )

    assert len(items) == 1
    assert items[0]["id"] == "context:проект-контрактаdocx:subject_mismatch"
    assert items[0]["label"] == "Документ не совпадает с карточкой закупки"
    assert items[0]["is_blocker"] is True
    assert items[0]["needs_review"] is True
    assert items[0]["source_label"] == "Проект контракта.docx"
    assert "Поставка офисной бумаги" in items[0]["fragment"]


def test_build_context_operator_items_marks_unsupported_primary_as_expected_missing():
    items = build_context_operator_items(
        {
            "version": 1,
            "documents": [
                {
                    "name": "ТЗ.pdf",
                    "document_role": "unsupported_primary",
                    "text_quality": {"text_error": "OCR не извлек текст"},
                }
            ],
        }
    )

    assert len(items) == 1
    assert items[0]["id"] == "context:тзpdf:unsupported_primary"
    assert items[0]["label"] == "Главный документ ТЗ не прочитан"
    assert items[0]["value"] == "OCR не извлек текст"
    assert items[0]["expected_missing"] is True
    assert items[0]["needs_review"] is True
    assert items[0]["is_blocker"] is False


def test_build_context_operator_items_ignores_unknown_context_versions():
    assert build_context_operator_items({"version": 2, "documents": []}) == []
    assert build_context_operator_items(None) == []
