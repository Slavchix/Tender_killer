# Persistent Product Profiles Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist one searchable `ProductProfile` per tender line item, so tenders with 20-40 products can be analyzed, displayed, reported, and later sourced item by item.

**Architecture:** Keep `TenderItem` as the raw source-facing line item and add persistent `product_profiles` as the normalized market-search entity. Generate profiles in batch from tender payload, store them in SQLite with `source + external_id + position_index` uniqueness, expose them through API, and render them as a compact list-first UI.

**Tech Stack:** Python 3.12, SQLite, stdlib `sqlite3`, existing `tender_killer.product_profile`, existing `TenderStore`, pytest, Vite/React frontend.

---

## File Structure

- Modify `src/tender_killer/models.py`
  - Add `ProductProfile` dataclass for the persisted profile entity.
- Modify `src/tender_killer/product_profile.py`
  - Keep profile generation logic here.
  - Change output to the richer persistent shape.
  - Add helpers for 20-40 item batch profile generation.
- Modify `src/tender_killer/storage.py`
  - Add `product_profiles` table.
  - Add `upsert_product_profiles`, `get_product_profiles`, and `replace_product_profiles`.
  - Add JSON serialization helpers for profile fields.
- Modify `src/tender_killer/web_api.py`
  - Add DB table migration for local API compatibility.
  - Add rebuild/list/detail product profile endpoints.
  - Change `get_tender_payload` to prefer stored profiles and fallback to computed profiles only when none exist.
  - Add `product_profiles` to SQLite admin allowlist.
- Modify `src/tender_killer/reports.py`
  - Use persisted profile fields.
  - Add compact summary for many positions.
- Modify `web/src/App.jsx`
  - Replace the current card-only product profile view with list-first profile handling.
  - Add button to rebuild profiles.
- Modify `web/src/styles.css`
  - Add styles for profile summary counters, table/list rows, selected profile detail panel.
- Modify tests:
  - `tests/test_product_profile.py`
  - `tests/test_storage.py`
  - `tests/test_web_api.py`
  - `tests/test_reports.py`

---

### Task 1: Add Rich Product Profile Generation

**Files:**
- Modify: `src/tender_killer/product_profile.py`
- Test: `tests/test_product_profile.py`

- [ ] **Step 1: Write failing tests for 1 item, fallback, and 40 items**

Add these tests to `tests/test_product_profile.py`:

```python
def test_build_product_profiles_returns_persistent_shape_for_item():
    tender = {
        "source": "mosreg_market",
        "external_id": "3670001",
        "title": "Поставка огнетушителей",
        "category": "Хозтовары",
        "items": [
            {
                "position_index": 1,
                "name": "Огнетушитель",
                "details": "Огнетушитель порошковый ОП-4 (з) АВСЕ",
                "quantity": 52,
                "unit": "Штука",
                "unit_price": 732.0,
                "total_price": 38064.0,
                "classifier_code": "11.218.01.01.01.002",
                "classifier_type": "КОЗ-2",
                "okpd2": "28.29.22.110",
            }
        ],
        "document_records": [
            {"text_content": "Товар должен соответствовать ГОСТ. Требуется сертификат соответствия. Страна происхождения товара указывается в заявке."}
        ],
    }

    [profile] = build_product_profiles(tender)

    assert profile["tender_source"] == "mosreg_market"
    assert profile["tender_external_id"] == "3670001"
    assert profile["position_index"] == 1
    assert profile["product_name"] == "Огнетушитель"
    assert profile["normalized_name"] == "огнетушитель"
    assert profile["details"] == "Огнетушитель порошковый ОП-4 (з) АВСЕ"
    assert profile["quantity"] == 52
    assert profile["unit"] == "Штука"
    assert profile["unit_price"] == 732.0
    assert profile["total_price"] == 38064.0
    assert profile["classifier_code"] == "11.218.01.01.01.002"
    assert profile["classifier_type"] == "КОЗ-2"
    assert {"type": "koz2", "code": "11.218.01.01.01.002", "source": "tender_item"} in profile["classifiers"]
    assert {"type": "okpd2", "code": "28.29.22.110", "source": "tender_item"} in profile["classifiers"]
    assert "Огнетушитель порошковый ОП-4 (з) АВСЕ" in profile["required_characteristics"]
    assert "ГОСТ" in profile["standards"]
    assert "сертификат соответствия" in profile["cert_documents"]
    assert "страна происхождения" in profile["origin_country_requirements"]
    assert "Огнетушитель порошковый ОП-4 (з) АВСЕ" in profile["search_phrases"]
    assert profile["profile_status"] == "ready"
    assert profile["confidence"] >= 0.75
    assert profile["source"] == "item"
    assert profile["evidence"]["product_name"]["source"] == "tender_item"


def test_build_product_profiles_creates_needs_review_fallback_without_items():
    tender = {
        "source": "mosreg_market",
        "external_id": "3670002",
        "title": "Поставка хозяйственных товаров",
        "category": "Хозтовары",
        "okpd2": "25.73.10",
        "items": [],
        "document_records": [],
    }

    [profile] = build_product_profiles(tender)

    assert profile["position_index"] == 1
    assert profile["product_name"] == "Поставка хозяйственных товаров"
    assert profile["classifier_code"] == "25.73.10"
    assert profile["classifier_type"] == "ОКПД2"
    assert profile["profile_status"] == "needs_review"
    assert profile["source"] == "card"
    assert profile["confidence"] < 0.7


def test_build_product_profiles_supports_many_items():
    tender = {
        "source": "mosreg_market",
        "external_id": "3670040",
        "title": "Поставка материалов",
        "category": "Материалы",
        "items": [
            {
                "position_index": index,
                "name": f"Материал {index}",
                "details": f"Детальное описание материала {index}",
                "quantity": float(index),
                "unit": "Штука",
                "classifier_code": f"11.218.01.01.01.{index:03d}",
                "classifier_type": "КОЗ-2",
            }
            for index in range(1, 41)
        ],
        "document_records": [],
    }

    profiles = build_product_profiles(tender)

    assert len(profiles) == 40
    assert profiles[0]["position_index"] == 1
    assert profiles[-1]["position_index"] == 40
    assert profiles[-1]["product_name"] == "Материал 40"
    assert all(profile["source"] == "item" for profile in profiles)
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_product_profile.py -q
```

Expected: fail because the current builder does not return persistent fields such as `tender_source`, `normalized_name`, `classifiers`, `standards`, `cert_documents`, `profile_status`, and `evidence`.

- [ ] **Step 3: Implement the richer profile shape**

In `src/tender_killer/product_profile.py`, update `_profile` signature and return shape:

```python
def _profile(
    *,
    tender_source: str | None,
    tender_external_id: str | None,
    position_index: int,
    product_name: str,
    details: str | None,
    category: str | None,
    okpd2: str | None,
    classifier_code: str | None,
    classifier_type: str | None,
    quantity: Any,
    unit: str | None,
    unit_price: Any,
    total_price: Any,
    required_characteristics: list[str],
    standards: list[str],
    cert_documents: list[str],
    origin_country_requirements: list[str],
    source: str,
) -> dict[str, Any]:
    normalized_name = _normalize_name(product_name)
    classifiers = _classifiers(
        okpd2=okpd2,
        classifier_code=classifier_code,
        classifier_type=classifier_type,
    )
    status = _profile_status(source, product_name, classifier_code, required_characteristics)
    return {
        "tender_source": tender_source,
        "tender_external_id": tender_external_id,
        "position_index": position_index,
        "product_name": product_name,
        "normalized_name": normalized_name,
        "details": details,
        "category": category,
        "okpd2": okpd2,
        "quantity": quantity,
        "unit": unit,
        "unit_price": unit_price,
        "total_price": total_price,
        "classifier_code": classifier_code,
        "classifier_type": classifier_type,
        "classifiers": classifiers,
        "required_characteristics": required_characteristics,
        "standards": standards,
        "cert_documents": cert_documents,
        "brand_model": [],
        "origin_country_requirements": origin_country_requirements,
        "search_phrases": _search_phrases(product_name, details, okpd2, classifier_code),
        "stop_words": list(DEFAULT_STOP_WORDS),
        "evidence": _evidence(source, bool(details), bool(classifier_code)),
        "profile_status": status,
        "confidence": _confidence(status, source, classifier_code, details),
        "source": source,
        "raw_payload": {},
    }
```

Add helpers:

```python
def _normalize_name(value: str) -> str:
    return re.sub(r"\s+", " ", value.lower()).strip()


def _classifiers(*, okpd2: str | None, classifier_code: str | None, classifier_type: str | None) -> list[dict[str, str]]:
    values: list[dict[str, str]] = []
    if classifier_code:
        values.append(
            {
                "type": _classifier_key(classifier_type),
                "code": classifier_code,
                "source": "tender_item",
            }
        )
    if okpd2 and okpd2 != classifier_code:
        values.append({"type": "okpd2", "code": okpd2, "source": "tender_item"})
    return values


def _classifier_key(value: str | None) -> str:
    normalized = (value or "unknown").lower()
    if "коз" in normalized:
        return "koz2"
    if "ктру" in normalized:
        return "ktru"
    if "окпд" in normalized:
        return "okpd2"
    return "unknown"


def _profile_status(source: str, product_name: str, classifier_code: str | None, characteristics: list[str]) -> str:
    if source == "card":
        return "needs_review"
    if not product_name or not classifier_code:
        return "needs_review"
    return "ready" if characteristics else "draft"


def _confidence(status: str, source: str, classifier_code: str | None, details: str | None) -> float:
    score = 0.35
    if source == "item":
        score += 0.25
    if classifier_code:
        score += 0.20
    if details:
        score += 0.20
    if status == "needs_review":
        return min(score, 0.65)
    return min(score, 0.95)


def _evidence(source: str, has_details: bool, has_classifier: bool) -> dict[str, Any]:
    evidence: dict[str, Any] = {"product_name": {"source": "tender_item" if source == "item" else "tender_card"}}
    if has_details:
        evidence["details"] = {"source": "tender_item", "field": "details"}
    if has_classifier:
        evidence["classifier_code"] = {"source": "tender_item", "field": "classifier_code"}
    return evidence
```

Split document extraction into separate lists:

```python
def _standards(text: str) -> list[str]:
    lower = text.lower()
    values: list[str] = []
    if "гост" in lower:
        values.append("ГОСТ")
    if "ту " in lower or "технические условия" in lower:
        values.append("ТУ")
    if "тр тс" in lower or "тр еаэс" in lower:
        values.append("ТР ТС/ТР ЕАЭС")
    return _unique(values)


def _cert_documents(text: str) -> list[str]:
    lower = text.lower()
    values: list[str] = []
    if "сертификат" in lower:
        values.append("сертификат соответствия")
    if "деклараци" in lower:
        values.append("декларация соответствия")
    if "регистрационное удостоверение" in lower:
        values.append("регистрационное удостоверение")
    if "сгр" in lower or "свидетельство о государственной регистрации" in lower:
        values.append("СГР")
    return _unique(values)


def _origin_country_requirements(text: str) -> list[str]:
    lower = text.lower()
    values: list[str] = []
    if "страна происхождения" in lower:
        values.append("страна происхождения")
    if "российск" in lower and "товар" in lower:
        values.append("российский товар")
    return _unique(values)
```

Update `build_product_profiles` to pass tender source/id, details, unit prices, and extracted lists into `_profile`.

- [ ] **Step 4: Run product profile tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_product_profile.py -q
```

Expected: pass.

- [ ] **Step 5: Commit**

```powershell
git add src/tender_killer/product_profile.py tests/test_product_profile.py
git commit -m "Add rich product profile builder"
```

---

### Task 2: Persist Product Profiles in SQLite

**Files:**
- Modify: `src/tender_killer/models.py`
- Modify: `src/tender_killer/storage.py`
- Test: `tests/test_storage.py`

- [ ] **Step 1: Write failing storage tests**

Add to `tests/test_storage.py`:

```python
def test_store_upserts_product_profiles_without_duplicates(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    profiles = [
        {
            "tender_source": "mosreg_market",
            "tender_external_id": "3670001",
            "position_index": 1,
            "product_name": "Огнетушитель",
            "normalized_name": "огнетушитель",
            "details": "ОП-4",
            "category": "Хозтовары",
            "quantity": 52.0,
            "unit": "Штука",
            "unit_price": 732.0,
            "total_price": 38064.0,
            "classifier_code": "11.218.01.01.01.002",
            "classifier_type": "КОЗ-2",
            "classifiers": [{"type": "koz2", "code": "11.218.01.01.01.002", "source": "tender_item"}],
            "required_characteristics": ["ОП-4"],
            "standards": ["ГОСТ"],
            "cert_documents": ["сертификат соответствия"],
            "brand_model": [],
            "origin_country_requirements": ["страна происхождения"],
            "search_phrases": ["Огнетушитель ОП-4"],
            "stop_words": ["б/у"],
            "evidence": {"product_name": {"source": "tender_item"}},
            "profile_status": "ready",
            "confidence": 0.95,
            "source": "item",
            "raw_payload": {},
        }
    ]

    store.upsert_product_profiles("mosreg_market", "3670001", profiles)
    store.upsert_product_profiles("mosreg_market", "3670001", [{**profiles[0], "product_name": "Огнетушитель порошковый"}])

    saved = store.get_product_profiles("mosreg_market", "3670001")

    assert len(saved) == 1
    assert saved[0]["product_name"] == "Огнетушитель порошковый"
    assert saved[0]["classifiers"] == [{"type": "koz2", "code": "11.218.01.01.01.002", "source": "tender_item"}]
    assert saved[0]["profile_status"] == "ready"


def test_store_persists_many_product_profiles(tmp_path):
    store = TenderStore(tmp_path / "tenders.sqlite")
    store.initialize()
    profiles = [
        {
            "tender_source": "mosreg_market",
            "tender_external_id": "3670040",
            "position_index": index,
            "product_name": f"Материал {index}",
            "normalized_name": f"материал {index}",
            "details": None,
            "category": "Материалы",
            "quantity": float(index),
            "unit": "Штука",
            "unit_price": None,
            "total_price": None,
            "classifier_code": f"11.218.01.01.01.{index:03d}",
            "classifier_type": "КОЗ-2",
            "classifiers": [{"type": "koz2", "code": f"11.218.01.01.01.{index:03d}", "source": "tender_item"}],
            "required_characteristics": [],
            "standards": [],
            "cert_documents": [],
            "brand_model": [],
            "origin_country_requirements": [],
            "search_phrases": [f"Материал {index}"],
            "stop_words": [],
            "evidence": {},
            "profile_status": "draft",
            "confidence": 0.75,
            "source": "item",
            "raw_payload": {},
        }
        for index in range(1, 41)
    ]

    store.upsert_product_profiles("mosreg_market", "3670040", profiles)

    saved = store.get_product_profiles("mosreg_market", "3670040")
    assert len(saved) == 40
    assert saved[39]["position_index"] == 40
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_storage.py -q
```

Expected: fail because `TenderStore` does not have profile methods or table.

- [ ] **Step 3: Add `ProductProfile` dataclass**

In `src/tender_killer/models.py`, add:

```python
@dataclass(slots=True)
class ProductProfile:
    tender_source: str
    tender_external_id: str
    position_index: int
    product_name: str
    normalized_name: str | None = None
    details: str | None = None
    category: str | None = None
    quantity: float | None = None
    unit: str | None = None
    unit_price: float | None = None
    total_price: float | None = None
    classifier_code: str | None = None
    classifier_type: str | None = None
    classifiers: list[dict[str, Any]] = field(default_factory=list)
    required_characteristics: list[str] = field(default_factory=list)
    standards: list[str] = field(default_factory=list)
    cert_documents: list[str] = field(default_factory=list)
    brand_model: list[str] = field(default_factory=list)
    origin_country_requirements: list[str] = field(default_factory=list)
    search_phrases: list[str] = field(default_factory=list)
    stop_words: list[str] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)
    profile_status: str = "draft"
    confidence: float = 0.0
    source: str = "item"
    raw_payload: dict[str, Any] = field(default_factory=dict)
```

- [ ] **Step 4: Add table creation**

In `TenderStore.initialize`, after `tender_items`, create `product_profiles`:

```python
connection.execute(
    """
    CREATE TABLE IF NOT EXISTS product_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tender_source TEXT NOT NULL,
        tender_external_id TEXT NOT NULL,
        position_index INTEGER NOT NULL,
        product_name TEXT NOT NULL,
        normalized_name TEXT,
        details TEXT,
        category TEXT,
        quantity REAL,
        unit TEXT,
        unit_price REAL,
        total_price REAL,
        classifier_code TEXT,
        classifier_type TEXT,
        classifiers_json TEXT NOT NULL,
        required_characteristics_json TEXT NOT NULL,
        standards_json TEXT NOT NULL,
        cert_documents_json TEXT NOT NULL,
        brand_model_json TEXT NOT NULL,
        origin_country_requirements_json TEXT NOT NULL,
        search_phrases_json TEXT NOT NULL,
        stop_words_json TEXT NOT NULL,
        evidence_json TEXT NOT NULL,
        profile_status TEXT NOT NULL,
        confidence REAL NOT NULL,
        source TEXT NOT NULL,
        raw_payload_json TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(tender_source, tender_external_id, position_index)
    )
    """
)
```

- [ ] **Step 5: Add upsert/read helpers**

In `TenderStore`, add:

```python
def upsert_product_profiles(self, source: str, external_id: str, profiles: list[dict[str, Any]]) -> None:
    with self._connect() as connection:
        rows = [_serialize_product_profile(source, external_id, profile) for profile in profiles]
        if not rows:
            connection.execute(
                "DELETE FROM product_profiles WHERE tender_source = ? AND tender_external_id = ?",
                (source, external_id),
            )
            return
        connection.executemany(
            """
            INSERT INTO product_profiles (
                tender_source, tender_external_id, position_index, product_name, normalized_name,
                details, category, quantity, unit, unit_price, total_price, classifier_code,
                classifier_type, classifiers_json, required_characteristics_json, standards_json,
                cert_documents_json, brand_model_json, origin_country_requirements_json,
                search_phrases_json, stop_words_json, evidence_json, profile_status,
                confidence, source, raw_payload_json
            )
            VALUES (
                :tender_source, :tender_external_id, :position_index, :product_name, :normalized_name,
                :details, :category, :quantity, :unit, :unit_price, :total_price, :classifier_code,
                :classifier_type, :classifiers_json, :required_characteristics_json, :standards_json,
                :cert_documents_json, :brand_model_json, :origin_country_requirements_json,
                :search_phrases_json, :stop_words_json, :evidence_json, :profile_status,
                :confidence, :source, :raw_payload_json
            )
            ON CONFLICT(tender_source, tender_external_id, position_index) DO UPDATE SET
                product_name = excluded.product_name,
                normalized_name = excluded.normalized_name,
                details = excluded.details,
                category = excluded.category,
                quantity = excluded.quantity,
                unit = excluded.unit,
                unit_price = excluded.unit_price,
                total_price = excluded.total_price,
                classifier_code = excluded.classifier_code,
                classifier_type = excluded.classifier_type,
                classifiers_json = excluded.classifiers_json,
                required_characteristics_json = excluded.required_characteristics_json,
                standards_json = excluded.standards_json,
                cert_documents_json = excluded.cert_documents_json,
                brand_model_json = excluded.brand_model_json,
                origin_country_requirements_json = excluded.origin_country_requirements_json,
                search_phrases_json = excluded.search_phrases_json,
                stop_words_json = excluded.stop_words_json,
                evidence_json = excluded.evidence_json,
                profile_status = excluded.profile_status,
                confidence = excluded.confidence,
                source = excluded.source,
                raw_payload_json = excluded.raw_payload_json,
                updated_at = CURRENT_TIMESTAMP
            """,
            rows,
        )
        indexes = [int(row["position_index"]) for row in rows]
        placeholders = ", ".join(["?"] * len(indexes))
        connection.execute(
            f"""
            DELETE FROM product_profiles
            WHERE tender_source = ? AND tender_external_id = ?
              AND position_index NOT IN ({placeholders})
            """,
            [source, external_id, *indexes],
        )


def get_product_profiles(self, source: str, external_id: str) -> list[dict[str, Any]]:
    with self._connect() as connection:
        rows = connection.execute(
            """
            SELECT * FROM product_profiles
            WHERE tender_source = ? AND tender_external_id = ?
            ORDER BY position_index
            """,
            (source, external_id),
        ).fetchall()
    return [_product_profile_row_to_payload(row) for row in rows]
```

Add module helpers:

```python
def _serialize_product_profile(source: str, external_id: str, profile: dict[str, Any]) -> dict[str, Any]:
    return {
        "tender_source": profile.get("tender_source") or source,
        "tender_external_id": profile.get("tender_external_id") or external_id,
        "position_index": int(profile.get("position_index") or 1),
        "product_name": str(profile.get("product_name") or "Товар не указан"),
        "normalized_name": profile.get("normalized_name"),
        "details": profile.get("details"),
        "category": profile.get("category"),
        "quantity": profile.get("quantity"),
        "unit": profile.get("unit"),
        "unit_price": profile.get("unit_price"),
        "total_price": profile.get("total_price"),
        "classifier_code": profile.get("classifier_code"),
        "classifier_type": profile.get("classifier_type"),
        "classifiers_json": json.dumps(profile.get("classifiers") or [], ensure_ascii=False),
        "required_characteristics_json": json.dumps(profile.get("required_characteristics") or [], ensure_ascii=False),
        "standards_json": json.dumps(profile.get("standards") or [], ensure_ascii=False),
        "cert_documents_json": json.dumps(profile.get("cert_documents") or [], ensure_ascii=False),
        "brand_model_json": json.dumps(profile.get("brand_model") or [], ensure_ascii=False),
        "origin_country_requirements_json": json.dumps(profile.get("origin_country_requirements") or [], ensure_ascii=False),
        "search_phrases_json": json.dumps(profile.get("search_phrases") or [], ensure_ascii=False),
        "stop_words_json": json.dumps(profile.get("stop_words") or [], ensure_ascii=False),
        "evidence_json": json.dumps(profile.get("evidence") or {}, ensure_ascii=False),
        "profile_status": profile.get("profile_status") or "draft",
        "confidence": float(profile.get("confidence") or 0.0),
        "source": profile.get("source") or "item",
        "raw_payload_json": json.dumps(profile.get("raw_payload") or {}, ensure_ascii=False),
    }


def _product_profile_row_to_payload(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "tender_source": row["tender_source"],
        "tender_external_id": row["tender_external_id"],
        "position_index": row["position_index"],
        "product_name": row["product_name"],
        "normalized_name": row["normalized_name"],
        "details": row["details"],
        "category": row["category"],
        "quantity": row["quantity"],
        "unit": row["unit"],
        "unit_price": row["unit_price"],
        "total_price": row["total_price"],
        "classifier_code": row["classifier_code"],
        "classifier_type": row["classifier_type"],
        "classifiers": json.loads(row["classifiers_json"] or "[]"),
        "required_characteristics": json.loads(row["required_characteristics_json"] or "[]"),
        "standards": json.loads(row["standards_json"] or "[]"),
        "cert_documents": json.loads(row["cert_documents_json"] or "[]"),
        "brand_model": json.loads(row["brand_model_json"] or "[]"),
        "origin_country_requirements": json.loads(row["origin_country_requirements_json"] or "[]"),
        "search_phrases": json.loads(row["search_phrases_json"] or "[]"),
        "stop_words": json.loads(row["stop_words_json"] or "[]"),
        "evidence": json.loads(row["evidence_json"] or "{}"),
        "profile_status": row["profile_status"],
        "confidence": row["confidence"],
        "source": row["source"],
        "raw_payload": json.loads(row["raw_payload_json"] or "{}"),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }
```

- [ ] **Step 6: Run storage tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_storage.py -q
```

Expected: pass.

- [ ] **Step 7: Commit**

```powershell
git add src/tender_killer/models.py src/tender_killer/storage.py tests/test_storage.py
git commit -m "Persist product profiles"
```

---

### Task 3: Add Product Profile API and Rebuild Flow

**Files:**
- Modify: `src/tender_killer/web_api.py`
- Test: `tests/test_web_api.py`

- [ ] **Step 1: Write failing API tests**

Add to `tests/test_web_api.py`:

```python
def test_rebuild_product_profiles_endpoint_persists_profiles(tmp_path):
    db_path = tmp_path / "tenders.sqlite"
    store = TenderStore(db_path)
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="3670001",
            url="https://market.mosreg.ru/Trade/ViewTrade/3670001",
            title="Поставка огнетушителей",
            items=[
                TenderItem(
                    name="Огнетушитель",
                    details="Огнетушитель порошковый ОП-4",
                    quantity=52,
                    unit="Штука",
                    classifier_code="11.218.01.01.01.002",
                    classifier_type="КОЗ-2",
                    okpd2="28.29.22.110",
                )
            ],
        )
    )

    payload = rebuild_product_profiles(db_path, "mosreg_market", "3670001")

    assert payload["ok"] is True
    assert payload["summary"]["total"] == 1
    assert payload["summary"]["ready"] == 1
    assert payload["product_profiles"][0]["product_name"] == "Огнетушитель"

    detail = get_tender_payload(db_path, "mosreg_market", "3670001")
    assert detail["product_profiles"][0]["product_name"] == "Огнетушитель"


def test_get_tender_payload_prefers_stored_product_profiles(tmp_path):
    db_path = tmp_path / "tenders.sqlite"
    store = TenderStore(db_path)
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="3670002",
            url="https://market.mosreg.ru/Trade/ViewTrade/3670002",
            title="Поставка материалов",
            items=[TenderItem(name="Материал из карточки")],
        )
    )
    store.upsert_product_profiles(
        "mosreg_market",
        "3670002",
        [
            {
                "tender_source": "mosreg_market",
                "tender_external_id": "3670002",
                "position_index": 1,
                "product_name": "Сохраненный профиль",
                "normalized_name": "сохраненный профиль",
                "details": None,
                "category": None,
                "quantity": None,
                "unit": None,
                "unit_price": None,
                "total_price": None,
                "classifier_code": None,
                "classifier_type": None,
                "classifiers": [],
                "required_characteristics": [],
                "standards": [],
                "cert_documents": [],
                "brand_model": [],
                "origin_country_requirements": [],
                "search_phrases": ["Сохраненный профиль"],
                "stop_words": [],
                "evidence": {},
                "profile_status": "draft",
                "confidence": 0.5,
                "source": "item",
                "raw_payload": {},
            }
        ],
    )

    payload = get_tender_payload(db_path, "mosreg_market", "3670002")

    assert payload["product_profiles"][0]["product_name"] == "Сохраненный профиль"


def test_rebuild_product_profiles_handles_many_items(tmp_path):
    db_path = tmp_path / "tenders.sqlite"
    store = TenderStore(db_path)
    store.initialize()
    store.upsert_tender(
        Tender(
            source="mosreg_market",
            external_id="3670040",
            url="https://market.mosreg.ru/Trade/ViewTrade/3670040",
            title="Поставка материалов",
            items=[TenderItem(name=f"Материал {index}") for index in range(1, 41)],
        )
    )

    payload = rebuild_product_profiles(db_path, "mosreg_market", "3670040")

    assert payload["summary"]["total"] == 40
    assert len(payload["product_profiles"]) == 40
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_web_api.py -q
```

Expected: fail because `rebuild_product_profiles` does not exist and `get_tender_payload` still computes profiles directly.

- [ ] **Step 3: Add product profile summary helper**

In `src/tender_killer/web_api.py`, add:

```python
def _product_profile_summary(profiles: list[dict[str, Any]]) -> dict[str, int]:
    statuses = [str(profile.get("profile_status") or "draft") for profile in profiles]
    return {
        "total": len(profiles),
        "draft": statuses.count("draft"),
        "needs_review": statuses.count("needs_review"),
        "ready": statuses.count("ready"),
        "searching": statuses.count("searching"),
        "matched": statuses.count("matched"),
        "priced": statuses.count("priced"),
        "rejected": statuses.count("rejected"),
    }
```

- [ ] **Step 4: Add rebuild function**

In `src/tender_killer/web_api.py`, add:

```python
def rebuild_product_profiles(database_path: str | Path, source: str, external_id: str) -> dict[str, Any]:
    store = TenderStore(database_path)
    store.initialize()
    tender = get_tender_payload(database_path, source, external_id, include_product_profiles=False)
    profiles = build_product_profiles(tender)
    store.upsert_product_profiles(source, external_id, profiles)
    saved = store.get_product_profiles(source, external_id)
    return {"ok": True, "summary": _product_profile_summary(saved), "product_profiles": saved}
```

Change `get_tender_payload` signature:

```python
def get_tender_payload(
    database_path: str | Path,
    source: str,
    external_id: str,
    *,
    include_product_profiles: bool = True,
) -> dict[str, Any]:
```

At the end of `get_tender_payload`, replace direct computation:

```python
if include_product_profiles:
    store = TenderStore(database_path)
    stored_profiles = store.get_product_profiles(source, external_id)
    payload["product_profiles"] = stored_profiles or build_product_profiles(payload)
    payload["product_profile_summary"] = _product_profile_summary(payload["product_profiles"])
else:
    payload["product_profiles"] = []
    payload["product_profile_summary"] = _product_profile_summary([])
```

- [ ] **Step 5: Add endpoints to the HTTP handler**

In `do_POST`, add route before generic errors:

```python
if parsed.path.startswith("/api/tenders/") and parsed.path.endswith("/product-profiles/rebuild"):
    identity = _parse_tender_action_path(parsed.path, "product-profiles/rebuild")
    if not identity:
        self._send_json({"error": "invalid product profile path"}, status=400)
        return
    payload = rebuild_product_profiles(self.server.settings.database_path, identity[0], identity[1])
    self._send_json(payload)
    return
```

In `do_GET`, add route:

```python
if parsed.path.startswith("/api/tenders/") and parsed.path.endswith("/product-profiles"):
    identity = _parse_tender_action_path(parsed.path, "product-profiles")
    if not identity:
        self._send_json({"error": "invalid product profile path"}, status=400)
        return
    store = TenderStore(self.server.settings.database_path)
    store.initialize()
    profiles = store.get_product_profiles(identity[0], identity[1])
    self._send_json({"summary": _product_profile_summary(profiles), "product_profiles": profiles})
    return
```

- [ ] **Step 6: Add `product_profiles` to SQLite admin allowlist**

Change:

```python
DATABASE_VIEW_TABLES = ("tenders", "tender_items", "tender_documents", "tender_analysis", "tender_workflow")
```

to:

```python
DATABASE_VIEW_TABLES = ("tenders", "tender_items", "product_profiles", "tender_documents", "tender_analysis", "tender_workflow")
```

- [ ] **Step 7: Run API tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_web_api.py -q
```

Expected: pass.

- [ ] **Step 8: Commit**

```powershell
git add src/tender_killer/web_api.py tests/test_web_api.py
git commit -m "Add product profile API"
```

---

### Task 4: Update Word Report for Many Product Profiles

**Files:**
- Modify: `src/tender_killer/reports.py`
- Test: `tests/test_reports.py`

- [ ] **Step 1: Write failing report test for many profiles**

Add to `tests/test_reports.py`:

```python
def test_build_tender_report_docx_summarizes_many_product_profiles(tmp_path):
    payload = {
        "title": "Поставка материалов",
        "external_id": "3670040",
        "source": "mosreg_market",
        "url": "https://market.mosreg.ru/Trade/ViewTrade/3670040",
        "customer": "Заказчик",
        "region": "Московская область",
        "status": "Прием предложений",
        "price": 100000.0,
        "deadline_at": "2026-05-28T12:00:00",
        "items": [],
        "document_records": [],
        "analysis": None,
        "product_profile_summary": {"total": 40, "ready": 35, "needs_review": 5, "draft": 0, "matched": 0, "priced": 0, "rejected": 0, "searching": 0},
        "product_profiles": [
            {
                "position_index": index,
                "product_name": f"Материал {index}",
                "quantity": float(index),
                "unit": "Штука",
                "classifier_code": f"11.218.01.01.01.{index:03d}",
                "classifier_type": "КОЗ-2",
                "profile_status": "ready" if index <= 35 else "needs_review",
                "search_phrases": [f"Материал {index}"],
                "required_characteristics": [],
                "standards": [],
                "cert_documents": [],
            }
            for index in range(1, 41)
        ],
    }

    content = build_tender_report_docx(payload)
    path = tmp_path / "report.docx"
    path.write_bytes(content)
    document_xml = _docx_text(path)

    assert "Товарные профили: 40" in document_xml
    assert "Готовы к поиску: 35" in document_xml
    assert "Требуют проверки: 5" in document_xml
    assert "Материал 40" in document_xml
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_reports.py -q
```

Expected: fail because the report lacks profile summary.

- [ ] **Step 3: Add profile summary section**

In `build_tender_report_docx`, before detailed profile loop:

```python
summary = tender.get("product_profile_summary") or _profiles_summary(product_profiles)
paragraphs.extend(
    [
        ("Сводка товарных профилей", "heading"),
        (f"Товарные профили: {summary.get('total', 0)}", "normal"),
        (f"Готовы к поиску: {summary.get('ready', 0)}", "normal"),
        (f"Требуют проверки: {summary.get('needs_review', 0)}", "normal"),
        (f"Найдены товары: {summary.get('matched', 0)}", "normal"),
        (f"Посчитана экономика: {summary.get('priced', 0)}", "normal"),
        (f"Отклонены: {summary.get('rejected', 0)}", "normal"),
    ]
)
```

Add helper:

```python
def _profiles_summary(profiles: list[dict[str, Any]]) -> dict[str, int]:
    statuses = [str(profile.get("profile_status") or "draft") for profile in profiles]
    return {
        "total": len(profiles),
        "ready": statuses.count("ready"),
        "needs_review": statuses.count("needs_review"),
        "matched": statuses.count("matched"),
        "priced": statuses.count("priced"),
        "rejected": statuses.count("rejected"),
    }
```

- [ ] **Step 4: Run report tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_reports.py -q
```

Expected: pass.

- [ ] **Step 5: Commit**

```powershell
git add src/tender_killer/reports.py tests/test_reports.py
git commit -m "Summarize product profiles in reports"
```

---

### Task 5: Change Website to List-First Product Profiles

**Files:**
- Modify: `web/src/App.jsx`
- Modify: `web/src/styles.css`

- [ ] **Step 1: Add state for selected profile and rebuild action**

In `TenderDetail`, add:

```jsx
const [productProfiles, setProductProfiles] = useState(tender.product_profiles || [])
const [productProfileSummary, setProductProfileSummary] = useState(tender.product_profile_summary || null)
const [selectedProfileIndex, setSelectedProfileIndex] = useState(0)
const [profilesLoading, setProfilesLoading] = useState(false)
```

Add effect:

```jsx
useEffect(() => {
  setProductProfiles(tender.product_profiles || [])
  setProductProfileSummary(tender.product_profile_summary || null)
  setSelectedProfileIndex(0)
}, [tender.source, tender.external_id, tender.product_profiles, tender.product_profile_summary])
```

Add handler:

```jsx
function rebuildProductProfiles() {
  setProfilesLoading(true)
  fetch(`/api/tenders/${encodeURIComponent(tender.source)}/${encodeURIComponent(tender.external_id)}/product-profiles/rebuild`, {
    method: 'POST',
  })
    .then((response) => response.json())
    .then((payload) => {
      setProductProfiles(payload.product_profiles || [])
      setProductProfileSummary(payload.summary || null)
      setSelectedProfileIndex(0)
    })
    .finally(() => setProfilesLoading(false))
}
```

- [ ] **Step 2: Replace product profile card rendering**

Replace the current `tender.product_profiles.map(...)` block with:

```jsx
<section className="detail-section product-profile-section">
  <div className="section-heading-row">
    <h3>Товарные профили</h3>
    <button className="secondary-button" onClick={rebuildProductProfiles} disabled={profilesLoading}>
      {profilesLoading ? 'Обновляю...' : 'Обновить профили'}
    </button>
  </div>

  <ProfileSummary summary={productProfileSummary} total={productProfiles.length} />

  {productProfiles.length ? (
    <div className="profile-layout">
      <div className="profile-list">
        {productProfiles.map((profile, index) => (
          <button
            key={`${profile.position_index}-${profile.product_name}`}
            className={index === selectedProfileIndex ? 'profile-row selected' : 'profile-row'}
            onClick={() => setSelectedProfileIndex(index)}
          >
            <span className="profile-position">#{profile.position_index}</span>
            <span className="profile-name">{profile.product_name}</span>
            <span className="profile-meta">{formatQuantity(profile.quantity, profile.unit)}</span>
            <span className="profile-meta">{profile.classifier_type || 'код'} {profile.classifier_code || 'не найден'}</span>
            <span className={`profile-status ${profile.profile_status || 'draft'}`}>{profileStatusLabel(profile.profile_status)}</span>
          </button>
        ))}
      </div>
      <ProductProfileDetail profile={productProfiles[selectedProfileIndex]} />
    </div>
  ) : (
    <p className="muted-text">Товарные профили пока не сформированы.</p>
  )}
</section>
```

Add components near existing helper components:

```jsx
function ProfileSummary({ summary, total }) {
  const data = summary || { total }
  return (
    <div className="profile-summary-grid">
      <Info label="Всего позиций" value={data.total ?? total ?? 0} />
      <Info label="Готовы" value={data.ready ?? 0} />
      <Info label="Проверить" value={data.needs_review ?? 0} />
      <Info label="Найдены" value={data.matched ?? 0} />
      <Info label="Посчитаны" value={data.priced ?? 0} />
      <Info label="Отклонены" value={data.rejected ?? 0} />
    </div>
  )
}


function ProductProfileDetail({ profile }) {
  if (!profile) {
    return <div className="profile-detail muted-text">Выбери позицию из списка</div>
  }
  return (
    <div className="profile-detail">
      <h4>{profile.product_name}</h4>
      <Info label="Детальное описание" value={profile.details || 'не найдено'} />
      <Info label="Код классификатора" value={profile.classifier_code || 'не найден'} />
      <Info label="Тип классификатора" value={profile.classifier_type || 'не указан'} />
      <Info label="Количество" value={formatQuantity(profile.quantity, profile.unit)} />
      <Info label="Статус" value={profileStatusLabel(profile.profile_status)} />
      <AnalysisList title="Характеристики" items={profile.required_characteristics} empty="Характеристики пока не найдены" />
      <AnalysisList title="Стандарты" items={profile.standards} empty="ГОСТ/ТУ пока не найдены" />
      <AnalysisList title="Документы" items={profile.cert_documents} empty="Сертификаты/декларации пока не найдены" />
      <AnalysisList title="Поисковые фразы" items={profile.search_phrases} empty="Поисковые фразы пока не сформированы" />
      <AnalysisList title="Стоп-слова" items={profile.stop_words} empty="Стоп-слова пока не заданы" danger />
    </div>
  )
}
```

Add helpers:

```jsx
function profileStatusLabel(status) {
  return {
    draft: 'Черновик',
    needs_review: 'Проверить',
    ready: 'Готов',
    searching: 'Поиск',
    matched: 'Найдено',
    priced: 'Расчет',
    rejected: 'Отклонено',
  }[status] || 'Черновик'
}


function formatQuantity(quantity, unit) {
  if (quantity === null || quantity === undefined || quantity === '') {
    return unit || 'не указано'
  }
  return `${quantity} ${unit || ''}`.trim()
}
```

- [ ] **Step 3: Add CSS**

In `web/src/styles.css`, add:

```css
.section-heading-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.profile-summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  margin-bottom: 12px;
}

.profile-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(280px, 0.85fr);
  gap: 12px;
}

.profile-list {
  display: flex;
  flex-direction: column;
  max-height: 520px;
  overflow: auto;
  border: 1px solid var(--border);
  border-radius: 8px;
}

.profile-row {
  display: grid;
  grid-template-columns: 48px minmax(180px, 1fr) 90px 160px 92px;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 10px;
  border: 0;
  border-bottom: 1px solid var(--border);
  background: transparent;
  color: var(--text);
  text-align: left;
  cursor: pointer;
}

.profile-row:hover,
.profile-row.selected {
  background: rgba(104, 222, 92, 0.09);
}

.profile-position,
.profile-meta {
  color: var(--muted);
  font-size: 12px;
}

.profile-name {
  font-weight: 700;
  overflow-wrap: anywhere;
}

.profile-status {
  justify-self: end;
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 12px;
  border: 1px solid var(--border);
}

.profile-status.ready,
.profile-status.matched,
.profile-status.priced {
  color: var(--green);
}

.profile-status.needs_review {
  color: var(--warning);
}

.profile-detail {
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 12px;
  min-height: 280px;
}

@media (max-width: 1100px) {
  .profile-layout {
    grid-template-columns: 1fr;
  }

  .profile-row {
    grid-template-columns: 42px minmax(160px, 1fr) 82px;
  }

  .profile-row .profile-meta:nth-of-type(2),
  .profile-row .profile-status {
    display: none;
  }
}
```

- [ ] **Step 4: Build frontend**

Run:

```powershell
cd web
& "C:\Users\zinin.v.a\Desktop\node-v24.15.0-win-x64\node-v24.15.0-win-x64\node.exe" "node_modules\vite\bin\vite.js" build
```

Expected: Vite build succeeds.

- [ ] **Step 5: Commit**

```powershell
git add web/src/App.jsx web/src/styles.css
git commit -m "Show product profiles as a list"
```

---

### Task 6: Full Verification and Memory Update

**Files:**
- Modify: `memory/project-context.md`

- [ ] **Step 1: Run focused backend tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_product_profile.py tests/test_storage.py tests/test_web_api.py tests/test_reports.py -q
```

Expected: all pass.

- [ ] **Step 2: Run full backend tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest --basetemp .pytest-tmp-product-profiles -q
```

Expected: all pass.

- [ ] **Step 3: Run frontend build**

Run:

```powershell
cd web
& "C:\Users\zinin.v.a\Desktop\node-v24.15.0-win-x64\node-v24.15.0-win-x64\node.exe" "node_modules\vite\bin\vite.js" build
```

Expected: build succeeds.

- [ ] **Step 4: Update memory**

Append to `memory/project-context.md`:

```markdown
## Persistent product profiles checkpoint

Дата: 2026-05-21.

- `ProductProfile` стал отдельной постоянной сущностью в SQLite.
- Один тендер теперь может иметь много товарных профилей: по одному на каждую позицию закупки.
- Это важно для закупок с 20-40 товарами: поиск, подбор поставщиков, будущий расчет маржи и агент-критик должны работать на уровне позиции, а не только тендера.
- `product_profiles` хранит товарное имя, детальное описание, количество, единицу, цену, классификаторы, характеристики, ГОСТ/ТУ, сертификаты/декларации, поисковые фразы, стоп-слова, статус и уверенность.
- Сайт показывает товарные профили списком с компактной сводкой и детальной панелью выбранной позиции.
- Word-отчет показывает сводку по всем товарным профилям, чтобы отчеты по закупкам с множеством позиций оставались читаемыми.
```

- [ ] **Step 5: Commit**

```powershell
git add memory/project-context.md
git commit -m "Document persistent product profiles"
```

- [ ] **Step 6: Final status check**

Run:

```powershell
git status --short
```

Expected: only unrelated pre-existing working tree changes remain, or empty status if the branch was clean before implementation.

---

## Self-Review

Spec coverage:

- Persistent `product_profiles` table: Task 2.
- One profile per line item and 40-item support: Tasks 1, 2, 3, 5.
- API rebuild/list flow: Task 3.
- List-first website: Task 5.
- Word summary for many positions: Task 4.
- Error handling for missing items: Task 1 and Task 3 fallback path.
- Testing: every task has focused tests; Task 6 runs full verification.

No placeholder requirements remain. Function names are consistent across tasks:

- `build_product_profiles`
- `upsert_product_profiles`
- `get_product_profiles`
- `rebuild_product_profiles`
- `_product_profile_summary`

The plan does not start supplier parsing. It stops at persistent, inspectable, rebuildable product profiles.

