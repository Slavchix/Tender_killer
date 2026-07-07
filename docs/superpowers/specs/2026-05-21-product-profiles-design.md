# Product Profiles Design

Date: 2026-05-21

## Goal

Create `ProductProfile` as a persistent Tender Killer entity. A tender is not treated as one product. One tender can contain 1, 20, 40, or more line items, and each line item can produce its own product profile.

The profile is the bridge between procurement data and future product sourcing, margin calculation, and analyst/critic agents. `TenderItem` keeps what the source platform gave us. `ProductProfile` describes what Tender Killer needs to find and verify on the market.

## Core Idea

For every tender:

- parse and store tender-level data;
- parse and store raw line items in `tender_items`;
- generate one `product_profiles` row per item;
- if no structured items exist, create one fallback profile from the tender card;
- later enrich profiles with document extraction, LLM analysis, found supplier products, prices, and risk decisions.

This avoids the dangerous assumption that one procurement equals one product. A procurement with 40 materials should become 40 independent searchable profiles, plus one tender-level summary that says whether the entire tender is economically interesting.

## Data Model

Add a new SQLite table `product_profiles`.

Recommended fields:

```text
id
tender_source
tender_external_id
position_index

product_name
normalized_name
details
category

quantity
unit
unit_price
total_price

classifier_code
classifier_type
classifiers_json

required_characteristics_json
standards_json
cert_documents_json
brand_model_json
origin_country_requirements_json

search_phrases_json
stop_words_json
evidence_json

profile_status
confidence
source
created_at
updated_at
raw_payload_json
```

Unique key:

```text
tender_source + tender_external_id + position_index
```

This lets the system update a profile without duplicating it on repeated searches.

## Classifiers

Do not collapse all codes into `okpd2`.

Keep the current quick fields:

- `classifier_code`;
- `classifier_type`.

Also add `classifiers_json` for future multiple codes:

```json
[
  {"type": "okpd2", "code": "28.29.22.110", "source": "tender"},
  {"type": "koz2", "code": "11.218.01.01.01.002", "source": "mosreg"},
  {"type": "ktru", "code": "28.29.22.110-00000001", "source": "eis"},
  {"type": "okei", "code": "796", "name": "штука"},
  {"type": "tnved", "code": "...", "source": "certificate"}
]
```

The classifier narrows the search, but does not prove a commercial product matches the tender.

## Profile Generation Flow

1. `TenderItem` extraction produces raw items from source JSON/card/documents.
2. `ProductProfileBuilder` reads tender + items + document text + analysis.
3. For each item:
   - choose canonical product name;
   - preserve detailed name;
   - copy quantity, unit, unit price, total price;
   - normalize classifiers;
   - extract basic characteristics;
   - extract standards and required documents;
   - generate search phrases and stop words;
   - assign status and confidence.
4. Save profiles in SQLite through an upsert.
5. Return profiles through API and show them on the website.
6. Use profiles in Word reports.

If structured items are missing, build one fallback profile from the tender title/category/price and mark it as `needs_review`.

## Handling 20-40 Items

The UI and backend must treat product profiles as a collection.

Backend:

- profile generation runs in batch for all positions;
- each profile is independently saved and updated;
- search and later margin calculation are profile-level tasks;
- tender-level economics are calculated from all profile-level results.

Frontend:

- show a compact table/list of profiles, not one huge card;
- each row shows position number, product name, quantity, unit, classifier, status, and match state;
- selecting a row opens detailed profile information;
- add summary counters: total profiles, ready, needs review, matched, priced, rejected.

Future sourcing:

- a 40-position tender creates 40 sourcing tasks;
- each task can have candidates, supplier prices, availability, delivery, and compliance score;
- the tender is only “interesting” if enough critical positions are sourced with acceptable margin.

## Statuses

Profile-level statuses:

```text
draft
needs_review
ready
searching
matched
priced
rejected
```

Meaning:

- `draft`: profile was created automatically;
- `needs_review`: important fields are missing or ambiguous;
- `ready`: enough data to search suppliers;
- `searching`: sourcing job is running;
- `matched`: candidate products were found;
- `priced`: economics were calculated;
- `rejected`: item cannot be matched or is unsuitable.

Tender-level status should be separate and derived later from all profiles:

```text
needs_review
interesting
partial
skip
```

Example: if 38 of 40 profiles are priced but 2 critical items cannot be found, tender status may be `partial` or `needs_review`, not automatically `interesting`.

## Evidence

Every important profile field should be traceable.

`evidence_json` should store where a value came from:

```json
{
  "product_name": {"source": "tender_item", "field": "name"},
  "classifier_code": {"source": "tender_item", "field": "classifier_code"},
  "standards": [{"source": "document", "document_id": 12, "snippet": "ГОСТ ..."}],
  "cert_documents": [{"source": "analysis", "snippet": "сертификат соответствия"}]
}
```

This is important for the future critic agent. The critic should not only say “this matches”, it should explain why.

## Search Profile

Each product profile produces search data:

- exact phrases;
- broad phrases;
- classifier phrases;
- standards phrases;
- exclude terms;
- must-have characteristics.

Example:

```json
{
  "exact": ["огнетушитель порошковый ОП-4 АВСЕ"],
  "broad": ["огнетушитель ОП-4", "огнетушитель порошковый"],
  "with_standards": ["огнетушитель ОП-4 ГОСТ сертификат"],
  "with_classifier": ["огнетушитель ОП-4 11.218.01.01.01.002"],
  "exclude": ["б/у", "уценка", "ремонт", "услуга"]
}
```

## API

Add or extend endpoints:

```text
POST /api/tenders/{source}/{external_id}/product-profiles/rebuild
GET  /api/tenders/{source}/{external_id}/product-profiles
GET  /api/tenders/{source}/{external_id}/product-profiles/{position_index}
```

For MVP, `get_tender_payload` can continue returning `product_profiles`, but the source should be the SQLite table once profiles exist.

## Website

Replace the current single profile presentation with a list-first view:

- summary counters;
- product profile table;
- selected profile details;
- profile status;
- search phrases;
- requirements/standards/certificates;
- source/evidence snippets;
- button: `Обновить профили`.

For many items, the default view must stay compact. The user should not scroll through 40 full cards.

## Word Report

The Word report should include:

- tender-level summary;
- table of all product profiles;
- detailed sections only for selected/important/problematic profiles;
- future margin section by profile;
- tender-level total economics.

For 20-40 items, the report must not become unreadable. The first page should answer: how many positions, how many are ready, how many need review, and whether the tender is worth continuing.

## Error Handling

- If item data is missing, create fallback profile and mark `needs_review`.
- If classifier type is unknown, keep code but mark classifier as `unknown`.
- If documents are not extracted yet, do not block profile creation; mark standards/certificates as incomplete.
- If profile generation fails for one item, continue other items and report failed position indexes.

## Testing

Unit tests:

- one tender with one item creates one profile;
- one tender with 40 items creates 40 profiles;
- repeated rebuild updates profiles without duplicates;
- missing items creates one fallback profile;
- classifier code/type are preserved;
- search phrases include product name and classifier;
- statuses are assigned correctly.

Integration tests:

- API rebuild stores profiles in SQLite;
- `get_tender_payload` returns stored profiles;
- Word report includes multiple profiles;
- website can display many profiles without relying on one-card layout.

## Implementation Direction

Implementation should be incremental:

1. Add model/table/upsert/read methods.
2. Move current computed profile builder to persistent storage.
3. Add rebuild API.
4. Change website to list-first product profiles.
5. Update Word report.
6. Add tests for 20-40 item tenders.

The next implementation should not start supplier parsing yet. First, make the profile layer reliable, inspectable, and persistent.

