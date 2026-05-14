# Data Model: Ingredient Match Review & Correction

**Feature**: `003-ingredient-match-review`
**Branch**: `003-ingredient-match-review`

## Entities

### MatchVoorkeur (persisted)

A saved product preference for an ingredient name. Scoped globally — same preference applies across all recipes.

**File**: `data/match_preferences.json`
**Key**: `ingredient_naam` (normalized, lowercase)

```python
@dataclass(frozen=True)
class MatchVoorkeur:
    ingredient_naam: str   # Normalized ingredient name (lowercase)
    article_id: int        # AH product article ID
    product_naam: str      # Denormalized product name (for display without extra lookup)
    updated_at: str        # ISO 8601 datetime string
```

**Validation rules**:
- `ingredient_naam`: non-empty, lowercased, stripped
- `article_id`: positive integer
- `updated_at`: valid ISO 8601 datetime string

**Serialization**: `to_dict()` / `from_dict()`, stored as a JSON dict keyed by `ingredient_naam`.

---

### MatchVoorkeurenRepository

Manages load/save of `MatchVoorkeur` objects in `data/match_preferences.json`. Auto-creates the file on first save.

```python
class MatchVoorkeurenRepository:
    def __init__(self, path: Path): ...
    def get(self, ingredient_naam: str) -> MatchVoorkeur | None: ...
    def save(self, voorkeur: MatchVoorkeur) -> None: ...   # upsert
    def delete(self, ingredient_naam: str) -> None: ...    # no-op if missing
```

---

### MatchReviewItem (in-memory / session)

Represents a single item in the match review UI. Held in `app.state.match_review_items` between `POST /boodschappen/verstuur-naar-ah` and `POST /boodschappen/bevestig-matches`.

```python
@dataclass
class MatchReviewItem:
    id: str                    # UUID — stable identifier for HTMX targeting
    naam: str                  # Display name of ingredient
    hoeveelheid: float | None  # Requested quantity
    eenheid: str               # Unit (gram, liter, stuks, …)
    product: Product | None    # Matched AH product; None = geen match
    bron: str                  # "voorkeur" | "voorkeur_niet_beschikbaar" | "referentie" |
                               # "zoekopdracht" | "niet_gevonden"
    gecorrigeerd: bool         # True if user explicitly changed the match in review UI
    aantal: int                # Calculated quantity for AH list (from bereken_aantal)
```

Not persisted — lives in `app.state` for the current session only. Cleared after `bevestig-matches` succeeds.

---

## State Transitions

```
[BoodschappenRegel / Handmatig item in app.state.boodschappenlijst]
        │
        ▼ POST /boodschappen/verstuur-naar-ah
        │
        ├─ preference found & product available  → MatchReviewItem(bron="voorkeur")
        ├─ preference found but unavailable      → MatchReviewItem(bron="voorkeur_niet_beschikbaar")
        ├─ matched from reference list           → MatchReviewItem(bron="referentie")
        ├─ matched from AH search               → MatchReviewItem(bron="zoekopdracht")
        └─ no match                             → MatchReviewItem(bron="niet_gevonden", product=None)
                │
                ▼ GET /boodschappen/match-review (user reviews)
                │
                └─ user clicks "Corrigeer"
                        │
                        ▼ GET /boodschappen/zoek-product?q=...&item_id=...
                        │  → HTML fragment: search results
                        │
                        ▼ POST /boodschappen/kies-product
                        │  → MatchReviewItem(gecorrigeerd=True, product=chosen)
                        │  → OOB card update + confirm button state update
                │
                ▼ POST /boodschappen/bevestig-matches (all items have product ≠ None)
                │
                ├─ gecorrigeerd=True  → save MatchVoorkeur to data/match_preferences.json
                └─ AH list created   → redirect to ah_bevestiging.html
```

---

## JSON File Structure

### `data/match_preferences.json`

```json
{
    "melk": {
        "ingredient_naam": "melk",
        "article_id": 123456,
        "product_naam": "AH Volle melk 1L",
        "updated_at": "2026-05-14T10:00:00"
    },
    "oregano": {
        "ingredient_naam": "oregano",
        "article_id": 789012,
        "product_naam": "AH Oregano gedroogd 15g",
        "updated_at": "2026-05-14T10:01:00"
    }
}
```

---

## Relationship to Existing Models

| Existing Model | Relationship |
|----------------|-------------|
| `BoodschappenRegel` | Source for `MatchReviewItem` — naam, hoeveelheid, eenheid are copied; BoodschappenRegel itself is not modified |
| `Product` (ah/models.py) | Referenced by `MatchReviewItem.product`; unchanged |
| `ProductMatch` (ah/integration.py) | Intermediate result of `zoek_producten()`; converted to `MatchReviewItem` for session storage |
| `SyncResultaat` (ah/integration.py) | Returned by the new `maak_ah_lijst_van_review()` path after bevestig-matches |
