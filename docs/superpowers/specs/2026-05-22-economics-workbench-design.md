# Economics Workbench Design

## Goal

Move all money-related work into the `Экономика` tab:

- manual product costs;
- supplier candidates;
- selected supplier for calculation;
- margin and bid thresholds;
- automatic draft cost estimates with visible assumptions and evidence.

The `Товары` tab becomes a product passport: what the tender asks for, quantities, codes, requirements, search phrases, and document evidence.

## Non-Goals

- Do not submit bids, sign documents, log in for the user, or perform legally significant actions.
- Do not treat NMC/start price as a participant bid.
- Do not silently overwrite manual prices with automatic estimates.
- Do not present tax or legal conclusions as guaranteed truth. The system can calculate by configured assumptions and show what needs review.

## UX Shape

### Products Tab

The products area should be read-only for economics:

- position name, quantity, unit, source price, total;
- OKPD2/classifier;
- requirements and evidence from documents;
- search phrases and stop words;
- a compact action/link to open this position in `Экономика`.

This keeps product review clean and prevents the user from hunting for financial controls in two places.

### Economics Tab

The economics tab becomes the workbench:

- top summary: NMC, total cost, break-even, minimum bid, interesting bid, margin, missing inputs;
- position list: one row per product profile with status, quantity, supplier cost, selected supplier, warning flags;
- selected position panel:
  - manual cost fields: unit cost, total cost, logistics, documents, other;
  - supplier candidates: add/edit candidate, price, availability, note;
  - selected supplier: one candidate can be marked as used in calculation;
  - automatic estimate: parsed values, assumptions, confidence, and evidence;
  - requirements that affect cost: delivery, packaging, warranty, certificates, national regime.

Manual input always wins. Automatic estimates fill empty fields or appear as suggestions until accepted.

## Automatic Cost Calculation

Automatic calculation is a rule-based draft engine, not a hidden AI decision.

Inputs:

- product profile fields: quantity, unit, product name, unit price, total price;
- tender document text and extracted snippets;
- supplier candidates and selected supplier;
- user/company settings when available.

Detected cost drivers:

- VAT assumptions: VAT included, VAT excluded, no VAT/USN, unknown;
- delivery and unloading;
- packaging;
- certificates/declarations;
- warranty and replacement risk;
- contract security or bank guarantee hints;
- payment delay / post-payment terms;
- penalties and short delivery terms;
- national regime / origin country constraints.

Output per position:

- `estimated_unit_cost`;
- `estimated_total_cost`;
- `tax_mode`;
- `vat_rate_percent`;
- `hidden_costs`;
- `risk_reserve`;
- `confidence`;
- `evidence`;
- `needs_review`.

Every automatic number must show why it exists. Example: "delivery +1.5% because delivery/unloading found in TZ", "VAT unknown, using profile default".

## Calculation Rules

Initial defaults should be conservative and configurable:

- VAT rate: 20% when VAT is explicitly needed and no other rate is configured;
- delivery reserve: from existing `RISK_RESERVE_RATES`;
- packaging/certificates/warranty reserves: from rule table;
- hidden costs are additive and visible;
- margin thresholds use existing `LOW_MARGIN_PERCENT` and `INTERESTING_MARGIN_PERCENT`.

Manual override rules:

- if user enters `unit_cost` or `total_cost`, automatic product cost is not applied over it;
- if user selects supplier, supplier price becomes the default cost candidate;
- automatic estimates can suggest logistics/documents/other costs, but each value remains editable;
- user can ignore automatic estimates without changing source data.

## Data Model Direction

Keep the current flat `raw_payload.economics` fields for compatibility:

- `unit_cost`;
- `total_cost`;
- `logistics_cost`;
- `documents_cost`;
- `other_costs`.

Add structured optional fields without breaking existing readers:

- `raw_payload.economics_auto`: calculated draft with assumptions and evidence;
- `raw_payload.supplier_options`: existing supplier list;
- `raw_payload.selected_supplier_option_index`: selected supplier candidate for calculation;
- `raw_payload.cost_review`: status and user note if needed.

Longer term, these can move into normalized SQLite tables after the workflow stabilizes.

## API Flow

Existing endpoints can support the first UX move:

- save manual economics input;
- add supplier option;
- get tender detail payload.

New endpoints needed after relocation:

- select supplier option for calculation;
- run automatic economics estimate for one position;
- run automatic economics estimate for all positions;
- accept automatic estimate into manual fields.

## Testing

Backend tests:

- economics keeps NMC as revenue;
- selected supplier updates cost candidate;
- automatic estimate does not overwrite manual values;
- hidden costs and VAT assumptions are visible in payload;
- unknown tax mode marks `needs_review`.

Frontend contract tests:

- product detail no longer owns money forms as the primary workflow;
- economics tab renders product position list;
- economics tab renders manual cost form for selected position;
- economics tab renders supplier options for selected position;
- automatic estimate panel shows assumptions/evidence and accept action.

## Implementation Phases

1. Move manual cost and supplier forms from product detail into economics tab without changing storage.
2. Add selected supplier option and make it feed the economics calculation.
3. Add automatic estimate payload and rule engine with evidence.
4. Add UI for running/accepting automatic estimates.
5. Surface dashboard attention signals: missing costs, low margin, auto estimate needs review, price changed below threshold.

## Open Decisions Resolved

- `Товары` is for understanding the tender.
- `Экономика` is for deciding whether and how to work the tender.
- Manual values override automatic values.
- Automatic estimates are suggestions with evidence.
- Telegram remains notifications/quick entry only.
