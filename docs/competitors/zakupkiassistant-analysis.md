# Zakupki Assistant Analysis

Date: 2026-05-22.

## Product Takeaways

Zakupki Assistant is strong at first contact. The user writes a natural-language request in Telegram, the bot extracts the business topic and geography, runs a search, shows examples, and offers immediate next actions: product search, AI analysis, similar tenders, and document download.

Tender Killer should not copy the "everything in Telegram" model. Telegram is too narrow for long position lists, economics, workflow status, supplier candidates, and evidence review. The stronger product shape is:

- Telegram: quick entry, notifications, short tender triage, and action buttons.
- Website: main workbench for filtering, documents, product profiles, suppliers, economics, and decisions.
- SQLite: source of truth for profiles, tenders, workflow, analysis, documents, and supplier data.

## What To Borrow

- Natural-language onboarding: "строительные материалы Москва МО до 2 млн 44-ФЗ".
- Search transparency: viewed, checked, relevant, source errors, law/region/source breakdown.
- Short Telegram tender cards with immediate buttons.
- "Get suppliers" flow based on tender positions.
- Similar tenders and competition analytics.
- Evidence-first document analysis with source fragments.

## What To Avoid

- Long Telegram message streams for 20-40 position tenders.
- Treating AI relevance as a black box.
- Running the whole workflow inside chat.
- Mixing quick search with permanent filters without making the difference clear.

## Current Implementation Direction

The first Tender Killer slice adds a quick-entry profile without removing existing filters. Free text in Telegram is parsed into a dedicated `quick-entry` profile. The bot shows a summary and a `Запустить быстрый поиск` button. Existing profiles remain active and editable.
