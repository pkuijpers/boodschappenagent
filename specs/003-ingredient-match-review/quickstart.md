# Quickstart: Ingredient Match Review & Correction

**Feature**: `003-ingredient-match-review`
**Branch**: `003-ingredient-match-review`

## What this feature does

Inserts a match-review step between the shopping list and AH list creation.

**Before**: Verstuur → [match + create AH list] → Bevestiging
**After**: Verstuur → [match] → Review UI → [create AH list] → Bevestiging

## New Files

| File | Purpose |
|------|---------|
| `src/boodschappenagent/ah/preferences.py` | `MatchVoorkeur` dataclass + `MatchVoorkeurenRepository` |
| `src/boodschappenagent/web/templates/pages/match_review.html` | Full match review page |
| `src/boodschappenagent/web/templates/fragments/zoekresultaten.html` | HTMX product search results |
| `src/boodschappenagent/web/templates/fragments/match_review_item.html` | Single match card (OOB updates) |
| `tests/ah/test_preferences.py` | Unit tests: `MatchVoorkeur` + repository |
| `tests/e2e/test_match_review.py` | E2E: full match review flow |
| `data/match_preferences.json` | Saved preferences (auto-created on first save) |

## Modified Files

| File | Change |
|------|--------|
| `src/boodschappenagent/ah/integration.py` | `zoek_producten()` applies `MatchVoorkeurenRepository.get()` before `smart_search` |
| `src/boodschappenagent/web/routers/boodschappen.py` | `POST /verstuur-naar-ah` → match only + redirect; add `/match-review`, `/zoek-product`, `/kies-product`, `/bevestig-matches` |
| `src/boodschappenagent/web/dependencies.py` | Inject `MatchVoorkeurenRepository` |
| `tests/web/test_boodschappen.py` | Add tests for all new routes |

## Key Data Structures

```python
# Persisted preference (data/match_preferences.json)
@dataclass(frozen=True)
class MatchVoorkeur:
    ingredient_naam: str
    article_id: int
    product_naam: str
    updated_at: str

# In-session review state (app.state.match_review_items)
@dataclass
class MatchReviewItem:
    id: str              # UUID for HTMX targeting
    naam: str
    hoeveelheid: float | None
    eenheid: str
    product: Product | None
    bron: str            # "voorkeur" | "referentie" | "zoekopdracht" | "niet_gevonden" | "voorkeur_niet_beschikbaar"
    gecorrigeerd: bool
    aantal: int
```

## User Flow

1. User opens `/boodschappen` (shopping list)
2. Clicks "Verstuur naar AH" → `POST /boodschappen/verstuur-naar-ah`
3. Server matches all items (applies saved preferences first), stores in `app.state.match_review_items`
4. Redirects to `GET /boodschappen/match-review`
5. User sees all items with their matched products
6. For wrong matches: clicks "Corrigeer" → inline search appears (HTMX)
7. Types search term → results update in real-time (300ms debounce)
8. Clicks "Selecteer" on preferred product → card updates, button re-evaluates
9. Once all items have a match: "Bevestig en maak AH-lijst aan" becomes active
10. Click → `POST /boodschappen/bevestig-matches` → saves corrections as preferences → creates AH list
11. Redirects to existing `ah_bevestiging.html`

## Running Tests

```bash
# Unit tests
uv run pytest tests/ah/test_preferences.py
uv run pytest tests/web/test_boodschappen.py

# E2E
uv run playwright install  # one-time
uv run pytest -m e2e tests/e2e/test_match_review.py
uv run pytest -m e2e tests/e2e/test_match_review.py --headed  # with browser visible
```

## Linting

```bash
uv run ruff check --fix .
uv run ruff format .
```
