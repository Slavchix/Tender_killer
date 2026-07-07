# Economics And Price Tracking Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add reliable tender/product price tracking first, then build the economics workflow on top of separate source prices, supplier costs, margin, risk reserve, and decision hints.

**Architecture:** SQLite remains the source of truth. `tenders.price` continues to mean NMC/start contract price for economics; competitor/current participant prices are stored separately so we never overwrite NMC with a bid. Every search/detail refresh records price snapshots, then API payloads expose a compact `price_change` object that the React tender/product card can render as "was / became".

**Tech Stack:** Python stdlib, SQLite, existing `TenderStore`, existing source adapters, React in `web/src/App.jsx`, contract tests in `tests/test_frontend_contract.py`, service tests in `tests/test_price_tracking.py` and economics tests.

---

## Definitions

- `nmc_price`: official NMC/start purchase price. This is the current meaning of `tenders.price`.
- `current_offer_price`: current participant/best offer price when the source exposes it. This is the price that can produce "участник снизил цену".
- `item_total_price`: source total price for a product position. This is useful for product card history, but it is not the same as competitor/bid price unless the source explicitly says so.
- `supplier_cost`: our internal cost from supplier options or manual economics inputs.
- `target_bid_price`: our planned bid price. It is a future manual/scenario value and must not overwrite source prices.

## File Map

- Modify `src/tender_killer/schema.py`: add price snapshot table and migration helpers.
- Modify `src/tender_killer/models.py`: add optional `current_price` fields only after adapter support is added.
- Modify `src/tender_killer/storage.py`: record NMC and item price snapshots during upsert.
- Create `src/tender_killer/price_tracking.py`: compact price history/change helpers.
- Modify `src/tender_killer/tender_detail_service.py`: include `price_change`, `price_history`, and item/profile price changes in detail payloads.
- Modify source adapters under `src/tender_killer/sources/`: map `current_offer_price` only when a source field is confirmed.
- Modify `web/src/App.jsx`: render price change banners in the tender card and selected product/profile card.
- Modify `web/src/styles.css`: add compact price change styles.
- Create `tests/test_price_tracking.py`: schema/storage/service tests for price snapshots and change calculation.
- Extend `tests/test_tender_detail_service.py`: API payload includes price change.
- Extend `tests/test_frontend_contract.py`: UI contract keeps the price change banner.
- Extend `tests/test_economics.py` and `tests/test_economics_service.py`: economics uses NMC/current offer correctly.

---

## Task 1: Add Price Snapshot Schema

**Files:**
- Modify: `src/tender_killer/schema.py`
- Test: `tests/test_schema.py`

- [ ] **Step 1: Write the failing schema test**

Add to `tests/test_schema.py`:

```python
def test_schema_creates_tender_price_snapshots_table(tmp_path):
    import sqlite3

    from tender_killer.schema import initialize_schema

    database_path = tmp_path / "db.sqlite"
    with sqlite3.connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        initialize_schema(connection)
        columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(tender_price_snapshots)").fetchall()
        }

    assert {
        "id",
        "source",
        "external_id",
        "price_kind",
        "price",
        "currency",
        "observed_at",
        "raw_payload_json",
    }.issubset(columns)
```

- [ ] **Step 2: Run red test**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_schema.py::test_schema_creates_tender_price_snapshots_table -q -p no:cacheprovider --basetemp pytest-cache-files-price-schema-red
```

Expected: fails because `tender_price_snapshots` does not exist.

- [ ] **Step 3: Implement schema**

In `initialize_schema`, call `ensure_price_snapshots_table(connection)` after `ensure_tenders_table(connection)`.

Add:

```python
def ensure_price_snapshots_table(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS tender_price_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            external_id TEXT NOT NULL,
            price_kind TEXT NOT NULL,
            price REAL NOT NULL,
            currency TEXT NOT NULL DEFAULT 'RUB',
            observed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            raw_payload_json TEXT NOT NULL DEFAULT '{}',
            FOREIGN KEY (source, external_id) REFERENCES tenders(source, external_id)
                ON DELETE CASCADE
        )
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_tender_price_snapshots_lookup
        ON tender_price_snapshots(source, external_id, price_kind, observed_at)
        """
    )
```

- [ ] **Step 4: Run green test**

Run the same test. Expected: pass.

- [ ] **Step 5: Commit**

```powershell
git add src/tender_killer/schema.py tests/test_schema.py
git commit -m "Add tender price snapshot schema"
```

---

## Task 2: Record NMC Price Snapshots On Upsert

**Files:**
- Modify: `src/tender_killer/storage.py`
- Test: `tests/test_price_tracking.py`

- [ ] **Step 1: Write failing storage test**

Create `tests/test_price_tracking.py`:

```python
from tender_killer.models import Tender
from tender_killer.storage import TenderStore


def test_store_records_price_snapshot_only_when_nmc_changes(tmp_path):
    store = TenderStore(tmp_path / "db.sqlite")
    store.initialize()

    base = Tender(
        source="mosreg_market",
        external_id="price-1",
        url="https://example.test/price-1",
        title="Поставка топлива",
        price=100_000,
    )
    store.upsert_many([base])
    store.upsert_many([base])
    store.upsert_many([base.__class__(**{**base.__dict__, "price": 95_000})])

    with store._connect() as connection:
        rows = connection.execute(
            """
            SELECT price_kind, price
            FROM tender_price_snapshots
            WHERE source = ? AND external_id = ?
            ORDER BY id
            """,
            ("mosreg_market", "price-1"),
        ).fetchall()

    assert [(row["price_kind"], row["price"]) for row in rows] == [
        ("nmc", 100_000),
        ("nmc", 95_000),
    ]
```

- [ ] **Step 2: Run red test**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_price_tracking.py::test_store_records_price_snapshot_only_when_nmc_changes -q -p no:cacheprovider --basetemp pytest-cache-files-price-upsert-red
```

Expected: fails because no snapshot is recorded.

- [ ] **Step 3: Implement snapshot recording**

In `TenderStore.upsert_many`, after tender upsert and before replacing items/documents, call:

```python
self._record_price_snapshot(connection, tender, "nmc", tender.price)
```

Add private method:

```python
def _record_price_snapshot(
    self,
    connection: sqlite3.Connection,
    tender: Tender,
    price_kind: str,
    price: float | None,
) -> None:
    if price is None:
        return
    latest = connection.execute(
        """
        SELECT price
        FROM tender_price_snapshots
        WHERE source = ? AND external_id = ? AND price_kind = ?
        ORDER BY observed_at DESC, id DESC
        LIMIT 1
        """,
        (tender.source, tender.external_id, price_kind),
    ).fetchone()
    if latest is not None and float(latest["price"]) == float(price):
        return
    connection.execute(
        """
        INSERT INTO tender_price_snapshots (
            source, external_id, price_kind, price, currency, raw_payload_json
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            tender.source,
            tender.external_id,
            price_kind,
            float(price),
            tender.currency or "RUB",
            json.dumps(tender.raw_payload, ensure_ascii=False),
        ),
    )
```

- [ ] **Step 4: Run green test**

Run the same test. Expected: pass.

- [ ] **Step 5: Run storage tests**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_storage.py tests\test_price_tracking.py -q -p no:cacheprovider --basetemp pytest-cache-files-price-storage
```

- [ ] **Step 6: Commit**

```powershell
git add src/tender_killer/storage.py tests/test_price_tracking.py
git commit -m "Record tender price snapshots"
```

---

## Task 3: Expose Latest Price Change In Tender Payload

**Files:**
- Create: `src/tender_killer/price_tracking.py`
- Modify: `src/tender_killer/tender_detail_service.py`
- Test: `tests/test_price_tracking.py`, `tests/test_tender_detail_service.py`

- [ ] **Step 1: Write failing service test**

Add to `tests/test_price_tracking.py`:

```python
from tender_killer.price_tracking import latest_price_change


def test_latest_price_change_reports_decrease(tmp_path):
    store = TenderStore(tmp_path / "db.sqlite")
    store.initialize()
    tender = Tender(
        source="mosreg_market",
        external_id="price-2",
        url="https://example.test/price-2",
        title="Поставка топлива",
        price=100_000,
    )
    store.upsert_many([tender])
    store.upsert_many([tender.__class__(**{**tender.__dict__, "price": 93_500})])

    change = latest_price_change(store.database_path, "mosreg_market", "price-2", "nmc")

    assert change == {
        "price_kind": "nmc",
        "direction": "decreased",
        "previous_price": 100_000.0,
        "current_price": 93_500.0,
        "delta": -6_500.0,
        "delta_percent": -6.5,
    }
```

- [ ] **Step 2: Implement `latest_price_change`**

Create `src/tender_killer/price_tracking.py`:

```python
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


def latest_price_change(
    database_path: str | Path,
    source: str,
    external_id: str,
    price_kind: str = "nmc",
) -> dict[str, Any] | None:
    with sqlite3.connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT price_kind, price, observed_at
            FROM tender_price_snapshots
            WHERE source = ? AND external_id = ? AND price_kind = ?
            ORDER BY observed_at DESC, id DESC
            LIMIT 2
            """,
            (source, external_id, price_kind),
        ).fetchall()
    if len(rows) < 2:
        return None
    current, previous = rows[0], rows[1]
    current_price = float(current["price"])
    previous_price = float(previous["price"])
    delta = round(current_price - previous_price, 2)
    if delta < 0:
        direction = "decreased"
    elif delta > 0:
        direction = "increased"
    else:
        direction = "unchanged"
    delta_percent = round((delta / previous_price) * 100, 2) if previous_price else None
    return {
        "price_kind": str(current["price_kind"]),
        "direction": direction,
        "previous_price": previous_price,
        "current_price": current_price,
        "delta": delta,
        "delta_percent": delta_percent,
    }
```

- [ ] **Step 3: Add payload test**

Add to `tests/test_tender_detail_service.py`:

```python
def test_get_tender_payload_includes_latest_price_change(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    tender = Tender(
        source="mosreg_market",
        external_id="price-change",
        url="https://example.test/price-change",
        title="Поставка топлива",
        price=100000.0,
    )
    store.upsert_many([tender])
    store.upsert_many([tender.__class__(**{**tender.__dict__, "price": 95000.0})])

    detail = get_tender_payload(store.database_path, "mosreg_market", "price-change")

    assert detail["price_change"]["direction"] == "decreased"
    assert detail["price_change"]["previous_price"] == 100000.0
    assert detail["price_change"]["current_price"] == 95000.0
```

- [ ] **Step 4: Wire payload**

In `src/tender_killer/tender_detail_service.py`, import:

```python
from tender_killer.price_tracking import latest_price_change
```

Before `return payload`, add:

```python
payload["price_change"] = latest_price_change(database_path, source, external_id, "current_offer") or latest_price_change(
    database_path, source, external_id, "nmc"
)
```

- [ ] **Step 5: Run tests**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_price_tracking.py tests\test_tender_detail_service.py -q -p no:cacheprovider --basetemp pytest-cache-files-price-service
```

- [ ] **Step 6: Commit**

```powershell
git add src/tender_killer/price_tracking.py src/tender_killer/tender_detail_service.py tests/test_price_tracking.py tests/test_tender_detail_service.py
git commit -m "Expose tender price changes"
```

---

## Task 4: Render Price Change In Tender/Product Card

**Files:**
- Modify: `web/src/App.jsx`
- Modify: `web/src/styles.css`
- Test: `tests/test_frontend_contract.py`

- [ ] **Step 1: Add failing frontend contract**

Add:

```python
def test_tender_card_renders_price_change_banner():
    app_source = APP_SOURCE.read_text(encoding="utf-8")
    styles_source = STYLES_SOURCE.read_text(encoding="utf-8")

    assert "function PriceChangeBanner" in app_source
    assert "<PriceChangeBanner priceChange={tender.price_change} />" in app_source
    assert "участник снизил цену" in app_source
    assert ".price-change-banner" in styles_source
    assert ".price-change-banner.decreased" in styles_source
    assert find_mojibake(app_source, APP_SOURCE) == []
    assert find_mojibake(styles_source, STYLES_SOURCE) == []
```

- [ ] **Step 2: Implement banner**

In `TenderDetails`, render after `<TenderDecisionSummary ... />`:

```jsx
<PriceChangeBanner priceChange={tender.price_change} />
```

Add component:

```jsx
function PriceChangeBanner({ priceChange }) {
  if (!priceChange || priceChange.direction === 'unchanged') return null
  const label = priceChange.direction === 'decreased' ? 'участник снизил цену' : 'цена выросла'
  return (
    <div className={`price-change-banner ${priceChange.direction}`}>
      <strong>{label}</strong>
      <span>Было {formatMoney(priceChange.previous_price)} · стало {formatMoney(priceChange.current_price)}</span>
      <em>{formatPercent(priceChange.delta_percent)}</em>
    </div>
  )
}
```

- [ ] **Step 3: Style banner**

Add:

```css
.price-change-banner {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 6px 10px;
  align-items: center;
  padding: 10px;
  background: #1b2622;
  border: 1px solid #33443d;
  border-radius: 7px;
}

.price-change-banner strong {
  color: #eef8f2;
  overflow-wrap: anywhere;
}

.price-change-banner span {
  color: #b8cbc4;
  font-size: 12px;
}

.price-change-banner em {
  color: #0d160f;
  background: #6edc61;
  border-radius: 999px;
  padding: 4px 7px;
  font-size: 12px;
  font-style: normal;
  font-weight: 800;
}

.price-change-banner.increased em {
  color: #ffe0a6;
  background: #3c3320;
  border: 1px solid #6c5730;
}
```

- [ ] **Step 4: Run frontend tests**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_frontend_contract.py -q -p no:cacheprovider --basetemp pytest-cache-files-price-ui
```

- [ ] **Step 5: Commit**

```powershell
git add web/src/App.jsx web/src/styles.css tests/test_frontend_contract.py
git commit -m "Show tender price changes"
```

---

## Task 5: Audit Source Fields For Current Offer Price

**Files:**
- Modify: relevant source adapter tests under `tests/test_sources.py` or `tests/test_models_and_normalization.py`
- Modify: `src/tender_killer/models.py`
- Modify: source adapters under `src/tender_killer/sources/`

- [ ] **Step 1: Keep `tenders.price` as NMC**

Do not repurpose `Tender.price`. Add optional fields only after a source field is confirmed:

```python
current_price: float | None = None
current_price_at: datetime | None = None
```

- [ ] **Step 2: Add source-specific tests**

For each confirmed source field, write a fixture test that proves:

```python
assert tender.price == 98084.0
assert tender.current_price == 92000.0
```

If a source does not expose current participant price, assert:

```python
assert tender.current_price is None
```

- [ ] **Step 3: Store `current_offer` snapshots**

After model/storage support exists, call:

```python
self._record_price_snapshot(connection, tender, "current_offer", tender.current_price)
```

- [ ] **Step 4: UI wording rule**

Only render "участник снизил цену" for `price_kind === "current_offer"`.

For `price_kind === "nmc"`, render "цена закупки изменилась", because this may be source correction rather than a participant bid.

---

## Task 6: Economics V1 - Cost Inputs And Margin

**Files:**
- Modify: `src/tender_killer/economics.py`
- Modify: `src/tender_killer/economics_service.py`
- Modify: `web/src/App.jsx`
- Test: `tests/test_economics.py`, `tests/test_economics_service.py`, `tests/test_frontend_contract.py`

- [ ] **Step 1: Preserve current NMC behavior**

Economics revenue uses:

```python
revenue = _number(tender.get("price"))
```

Do not switch revenue to `current_offer_price` automatically.

- [ ] **Step 2: Add max-profitable-bid calculation**

Add to `build_economics_summary` when costs are known:

```python
break_even_price = estimated_total_cost
minimum_margin_price = _round_money(estimated_total_cost / (1 - LOW_MARGIN_PERCENT / 100))
interesting_price = _round_money(estimated_total_cost / (1 - INTERESTING_MARGIN_PERCENT / 100))
```

Expected fields:

```python
"break_even_price": break_even_price,
"minimum_margin_price": minimum_margin_price,
"interesting_price": interesting_price,
```

- [ ] **Step 3: Add tests**

Example:

```python
def test_build_economics_summary_returns_bid_thresholds():
    summary = build_economics_summary({
        "price": 100000,
        "product_profiles": [
            {
                "product_name": "Бензин",
                "quantity": 1000,
                "raw_payload": {"economics": {"unit_cost": 70, "logistics_cost": 1000}},
            }
        ],
    })

    assert summary["break_even_price"] == 71000.0
    assert summary["minimum_margin_price"] > summary["break_even_price"]
    assert summary["interesting_price"] > summary["minimum_margin_price"]
```

- [ ] **Step 4: UI**

In the economics tab, show:

- NMC
- current participant price if available
- total cost
- break-even price
- minimum profitable bid
- current margin

- [ ] **Step 5: Commit**

```powershell
git add src/tender_killer/economics.py src/tender_killer/economics_service.py web/src/App.jsx tests/test_economics.py tests/test_economics_service.py tests/test_frontend_contract.py
git commit -m "Add economics bid thresholds"
```

---

## Task 7: Supplier Option Selection

**Files:**
- Modify: `src/tender_killer/supplier_option_service.py`
- Modify: API route/handler files if a new endpoint is needed.
- Modify: `web/src/App.jsx`
- Test: `tests/test_supplier_option_service.py`, `tests/test_web_api.py`, `tests/test_frontend_contract.py`

- [ ] **Step 1: Add selected supplier action**

Add service function:

```python
def select_supplier_option(database_path, source, external_id, position_index, option_index):
    ...
```

It sets selected option status to `selected`, keeps other options as `candidate`, and copies `unit_price` to `raw_payload.economics.unit_cost`.

- [ ] **Step 2: Add API endpoint**

`POST /api/tenders/{source}/{external_id}/product-profiles/{position_index}/supplier-options/{option_index}/select`

- [ ] **Step 3: Add UI button**

In supplier option list:

```jsx
<button onClick={() => selectSupplierOption(profile, index)} type="button">
  Взять в расчет
</button>
```

- [ ] **Step 4: Tests**

Assert selected supplier updates economics summary immediately.

- [ ] **Step 5: Commit**

```powershell
git add src/tender_killer/supplier_option_service.py src/tender_killer/api_routes.py src/tender_killer/api_handlers.py web/src/App.jsx tests/test_supplier_option_service.py tests/test_web_api.py tests/test_frontend_contract.py
git commit -m "Select supplier option for economics"
```

---

## Task 8: Dashboard And Attention Signals

**Files:**
- Modify: `src/tender_killer/tender_query_service.py` or add a small dashboard service if query logic grows.
- Modify: `web/src/App.jsx`
- Test: query/web/frontend tests.

- [ ] **Step 1: Add price-change attention items**

Dashboard should surface:

- current offer decreased
- current offer below minimum profitable bid
- missing supplier costs
- low margin

- [ ] **Step 2: Keep notifications separate**

Telegram remains notification-only. Do not move the economics workflow into Telegram.

- [ ] **Step 3: Commit**

```powershell
git add src/tender_killer web/src/App.jsx tests
git commit -m "Surface economics attention signals"
```

---

## Verification Commands

Run focused tests after each task. Before pushing a completed slice:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_price_tracking.py tests\test_economics.py tests\test_economics_service.py tests\test_tender_detail_service.py tests\test_frontend_contract.py -q -p no:cacheprovider --basetemp pytest-cache-files-economics-focused
```

Then run the full suite outside sandbox:

```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp pytest-cache-files-full
```

Expected final result after the first full implementation: all existing tests plus the new price/economics tests pass.

---

## Recommended Execution Order

1. Price snapshot schema.
2. Snapshot recording for NMC.
3. API `price_change`.
4. UI banner "было / стало".
5. Source audit for true `current_offer_price`.
6. Economics bid thresholds.
7. Supplier option selection.
8. Dashboard attention signals.

This order lets us ship useful price history immediately while avoiding the dangerous mistake of treating NMC corrections as participant bid reductions.
