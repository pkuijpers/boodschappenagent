# Research: Ingredient Match Review & Correction

**Feature**: `003-ingredient-match-review`
**Branch**: `003-ingredient-match-review`

## In-session state persistence

**Decision**: Use `app.state` (same pattern as `app.state.boodschappenlijst`)
**Rationale**: The app is single-user; `app.state` is already used for the shopping list state. A new key `app.state.match_review_items: list[MatchReviewItem]` follows the established pattern and avoids adding a session library.
**Alternatives considered**: Cookie-based session (disproportionate complexity for a single-user app); database (violates YAGNI and constitution V)

---

## HTMX correction flow pattern

**Decision**: Two-step inline correction: clicking "Corrigeer" triggers `hx-get /boodschappen/zoek-product` which replaces a target div on the card with a search form + results. Selecting a product fires `hx-post /boodschappen/kies-product` which returns an OOB swap updating the card and the confirm button.
**Rationale**: This is idiomatic HTMX — no JS required, no page reload, the rest of the review stays visible. The existing project uses `hx-swap`, `hx-target`, and `hx-boost` throughout.
**Alternatives considered**: Modal dialog per item (more complex HTML, harder to keep focus on the list); separate page per correction (violates SC-002: max 3 interactions)

---

## preferred_article_id storage

**Decision**: Separate `data/match_preferences.json` file, keyed by normalized ingredient name. Not embedded in recipe or shopping list models.
**Rationale**: The spec says preferences are global per ingredient name across all recipes. Embedding in recipe JSON would require modifying the recipe repository. A dedicated file keeps the scope contained and follows the existing pattern (each domain concern has its own JSON file).
**Alternatives considered**: Extend `BoodschappenRegel` with `preferred_article_id` field (wrong layer — BoodschappenRegel is ephemeral, created fresh from the week menu each time); extend recipe `Ingredient` (too broad — preferences are AH-specific, not part of the recipe domain)

---

## When to apply preferences in matching

**Decision**: At the start of `zoek_producten()` in `integration.py`, before `smart_search()`. If a preference exists for an ingredient name, use it directly (skip smart_search). Verify the product still exists via a product lookup; if not orderable/found, fall back to `smart_search` and mark source as `"voorkeur_niet_beschikbaar"`.
**Rationale**: Keeps the lookup logic in one place (integration.py already owns the per-item matching loop). Preference check is fast (dict lookup) and transparent.
**Alternatives considered**: Apply preferences in the router (leaks business logic into HTTP layer); apply as post-processing (wastes API calls when preference is known)

---

## Confirm button disabled state

**Decision**: Server-rendered disabled attribute on the button, updated via HTMX OOB swap each time a `kies-product` call changes the review state.
**Rationale**: The server owns the truth about whether all items have a match. Checking in the template on each OOB swap is simpler than client-side JS counting.
**Alternatives considered**: Client-side JS counter (introduces JS dependency; violates constitution II spirit); full page refresh on each correction (too slow, poor UX)

---

## Quantity calculation for corrected products

**Decision**: Reuse the existing `bereken_aantal()` from `ah/quantity_calculator.py` with the newly selected product.
**Rationale**: The quantity calculation is already encapsulated and unit-aware. No change needed.
**Alternatives considered**: Ask user to confirm quantity (adds interaction beyond SC-002's 3-step budget)

---

## (Session 2026-05-15) Which items to save after bevestig-matches

**Decision**: Save a preference for an item when `item.product is not None AND (item.gecorrigeerd OR item.bron != "voorkeur")`.

Concretely:
- `bron == "voorkeur"`, not corrected → skip (preference already in storage, unchanged)
- `bron == "voorkeur"`, corrected → save (user explicitly chose a different product; overwrite)
- Any other bron, product found → save (new preference for next run; eliminates future review noise)

**Rationale**: The confirmed match review constitutes user validation of each auto-match. Items already loaded from a stored preference have already been validated in a prior session — re-saving them on every run is pointless.
**Alternatives considered**: Save unconditionally (harmless but wasteful re-saves of unchanged preferences); keep old behavior (save only corrections — defeats the stated requirement).

---

## (Session 2026-05-15) Product size display in match review card

**Decision**: Show `item.product.size` inline after the product title in `match_review_item.html`. No backend change needed.

**Rationale**: `Product.size` maps to `salesUnitSize` from the AH API and is already populated in the `Product` object for all code paths:
- Auto-match (smart_search): `Product.from_api()` reads `salesUnitSize`
- Preference lookup (`_zoek_met_voorkeur`): calls `search_products()` which returns full `Product` objects with `size`
- User correction (kies-product route): `size` is passed as a form field in `hx-vals` from `zoekresultaten_inner.html` and stored in the session `Product` object

No need to store `product_size` in `MatchVoorkeur` — YAGNI.
**Alternatives considered**: Store size in `MatchVoorkeur` for future offline display: rejected (size is always retrieved live; no offline use case exists).
