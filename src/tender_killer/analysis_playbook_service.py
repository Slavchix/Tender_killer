from __future__ import annotations

from typing import Any


def build_analysis_playbooks(items: list[dict[str, Any]], metrics: dict[str, Any] | None = None) -> dict[str, Any]:
    metrics = metrics if isinstance(metrics, dict) else {}
    conflicts = [item for item in items if item.get("conflict_flags")]
    blockers = [
        item
        for item in items
        if item.get("is_blocker") or item.get("severity") == "high" or item.get("needs_review")
    ]
    missing = [item for item in items if item.get("expected_missing")]

    playbooks: list[dict[str, Any]] = []
    if conflicts:
        playbooks.append(_contradictions_playbook(conflicts))
    if conflicts or missing or metrics.get("unbound_facts"):
        playbooks.append(_clarification_playbook(conflicts, missing))
    if blockers or conflicts:
        playbooks.append(_skip_playbook(blockers, conflicts))
        playbooks.append(_dangerous_terms_playbook(blockers, conflicts))

    return {"version": 1, "items": playbooks}


def _contradictions_playbook(conflicts: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "id": "contradictions",
        "title": "Противоречия в документах",
        "severity": "high",
        "summary": "Есть взаимоисключающие или разные числовые условия. Нужна ручная сверка редакций.",
        "what_to_do": [
            "Сравнить источник, дату и редакцию документов.",
            "Зафиксировать применимую формулировку до расчета цены и подачи заявки.",
        ],
        "when_to_use": ["У одного условия найдено несколько несовместимых формулировок."],
        "clarification_request": "Направить запрос разъяснений с цитатами конфликтующих фрагментов.",
        "skip_conditions": ["Заказчик не снял противоречие до дедлайна подачи заявки."],
        "dangerous_for_supplier": ["Можно рассчитать цену или комплект документов по неверной редакции."],
        "source_fact_ids": _fact_ids(conflicts),
    }


def _clarification_playbook(conflicts: list[dict[str, Any]], missing: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "id": "clarification_request",
        "title": "Когда писать запрос разъяснений",
        "severity": "medium" if not conflicts else "high",
        "summary": "Запрос нужен, если условие влияет на допуск, цену, сроки или закрывающие документы.",
        "what_to_do": [
            "Сформулировать вопрос коротко и приложить ссылку на пункт документа.",
            "Не считать спорное условие подтвержденным до ответа заказчика.",
        ],
        "when_to_use": [
            "Есть противоречие между документами.",
            "Ожидаемое условие не найдено, но влияет на участие или оплату.",
        ],
        "clarification_request": "Попросить указать применимую редакцию и точный порядок исполнения условия.",
        "skip_conditions": [],
        "dangerous_for_supplier": [],
        "source_fact_ids": _fact_ids([*conflicts, *missing]),
    }


def _skip_playbook(blockers: list[dict[str, Any]], conflicts: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "id": "skip_procurement",
        "title": "Когда пропускать закупку",
        "severity": "high",
        "summary": "Пропускать стоит, если стоп-фактор нельзя снять до подачи заявки или он делает исполнение нерентабельным.",
        "what_to_do": [
            "Проверить, можно ли закрыть документы и требования до дедлайна.",
            "Если стоп-фактор не снимается, зафиксировать причину отказа от участия.",
        ],
        "when_to_use": ["Есть блокер участия, высокий риск отклонения или неразрешенное противоречие."],
        "clarification_request": "",
        "skip_conditions": [
            "Нет лицензии, СРО, подтверждения страны происхождения или обязательного документа.",
            "Противоречие влияет на цену/допуск и не снято заказчиком.",
        ],
        "dangerous_for_supplier": [],
        "source_fact_ids": _fact_ids([*blockers, *conflicts]),
    }


def _dangerous_terms_playbook(blockers: list[dict[str, Any]], conflicts: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "id": "supplier_dangerous_terms",
        "title": "Опасные условия для поставщика",
        "severity": "medium" if not conflicts else "high",
        "summary": "Условия могут повлиять на допуск, оборотку, сроки исполнения или приемку.",
        "what_to_do": [
            "Передать условия в ручную проверку и в расчет рискового резерва.",
            "Не считать заявку готовой, пока оператор не подтвердил применимость условия.",
        ],
        "when_to_use": ["Есть блокеры, ручная проверка или условия с финансовым/юридическим влиянием."],
        "clarification_request": "",
        "skip_conditions": [],
        "dangerous_for_supplier": [
            "Риск отклонения заявки.",
            "Риск задержки оплаты или неподписания закрывающих документов.",
            "Риск исполнения по более жесткой редакции документа.",
        ],
        "source_fact_ids": _fact_ids([*blockers, *conflicts]),
    }


def _fact_ids(items: list[dict[str, Any]]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        fact_id = str(item.get("id") or "").strip()
        if not fact_id or fact_id in seen:
            continue
        seen.add(fact_id)
        result.append(fact_id)
    return result[:8]
