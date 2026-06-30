from __future__ import annotations

import importlib
import importlib.util


def _participation_map_service():
    spec = importlib.util.find_spec("tender_killer.reports_participation_map")
    assert spec is not None
    return importlib.import_module("tender_killer.reports_participation_map")


def _flat_text(elements: list[tuple[str, object, str]]) -> str:
    parts: list[str] = []
    for kind, payload, _style in elements:
        if kind == "table":
            for row in payload:
                parts.extend(str(value) for value in row)
        else:
            parts.append(str(payload))
    return "\n".join(parts)


def test_participation_map_elements_render_operator_decision_sources_and_appendix():
    service = _participation_map_service()

    operator_view = {
        "action_plan": [
            {
                "title": "Проверить допуск",
                "next_step": "Сверить СРО до подачи заявки",
                "items": ["СРО", "лицензия"],
            }
        ],
        "major_blocks": [
            {
                "id": "decision_risks",
                "items": [
                    {
                        "label": "СРО",
                        "description": "Без СРО заявку могут отклонить",
                        "operator_action": "Проверить право участника выполнять работы",
                        "source_binding": {
                            "source_label": "ТЗ.docx · стр. 2",
                            "label": "источник подтвержден",
                        },
                        "confidence_level": {"label": "уверенность высокая"},
                        "fragment": "Требуется членство в СРО",
                        "priority": 10,
                    }
                ],
            }
        ],
    }

    elements = service.participation_map_elements(
        tender={
            "title": "Поставка табло",
            "customer": "Школа N1",
            "price": 100000,
            "deadline_at": "2026-07-10",
            "source": "mosreg",
            "url": "https://example.test/tender",
        },
        analysis={"confidence": 0.93},
        documents=[{"name": "ТЗ.docx", "document_type": "ТЗ", "text_status": "ok"}],
        operator_view=operator_view,
        decision={
            "title": "Нужна ручная проверка",
            "summary": "Сначала проверить допуск.",
            "reasons": ["есть риск по СРО"],
        },
    )

    text = _flat_text(elements)

    assert "КАРТА УЧАСТИЯ" in text
    assert "Поставка табло" in text
    assert "Нужна ручная проверка" in text
    assert "СРО" in text
    assert "Проверить право участника выполнять работы" in text
    assert "Проверить допуск" in text
    assert "ТЗ.docx · стр. 2" in text
    assert "ТЗ.docx" in text
