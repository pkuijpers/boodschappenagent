# Route Contracts: Ingredient Match Review & Correction

**Feature**: `003-ingredient-match-review`
**Web framework**: FastAPI + Jinja2 + HTMX

---

## POST /boodschappen/verstuur-naar-ah *(MODIFIED)*

Previously created the AH list directly. Now runs matching and redirects to review.

**Request**: Form data — same `item_id` list as before (unchecked items filtered server-side)
**Guards**:
- Not authenticated → redirect `GET /ah/login`
- No `app.state.boodschappenlijst_model` → redirect `GET /week`

**Flow**:
1. Filter unchecked items from the form submission
2. Build `BoodschappenRegel` list from UI state
3. Call `zoek_producten()` — applies `MatchVoorkeurenRepository.get()` per item before `smart_search`
4. Convert each `ProductMatch` → `MatchReviewItem` (with UUID)
5. Store list in `app.state.match_review_items`
6. Redirect `303 → GET /boodschappen/match-review`

**Error**: If AH API unavailable during matching → render `ah_error.html` with message

---

## GET /boodschappen/match-review *(NEW)*

Shows the full match review page.

**Request**: No parameters
**Guard**: `app.state.match_review_items` empty or None → redirect `GET /boodschappen`

**Response**: Full HTML page (`pages/match_review.html`) with:
- One card per `MatchReviewItem` (uses `fragments/match_review_item.html`)
  - Ingredient name + quantity/unit
  - Matched product name + price (or "geen match gevonden" error state)
  - "Corrigeer" button (`hx-get /boodschappen/zoek-product?item_id=<id>`, `hx-target="#zoek-<id>"`)
  - Source badge: "voorkeur" / "niet gevonden" / etc.
- "Bevestig en maak AH-lijst aan" button
  - `disabled` attribute when any item has `product=None`
  - `hx-post /boodschappen/bevestig-matches`

---

## GET /boodschappen/zoek-product *(NEW — HTMX fragment)*

Product search for the correction flow. Called inline via HTMX.

**Request**: Query params
- `q` (str, required) — search term
- `item_id` (str, required) — UUID of the `MatchReviewItem` being corrected

**Guard**: `item_id` not in `app.state.match_review_items` → 404

**Response**: HTML fragment (`fragments/zoekresultaten.html`) — up to 10 products, each with:
- Product name, price, unit/size
- "Selecteer" button → `hx-post /boodschappen/kies-product`, fields: `item_id`, `article_id`
- Empty state: "Geen resultaten gevonden"

**Note**: This endpoint also serves as the real-time search (triggered by `hx-trigger="input changed delay:300ms"` on the search field)

---

## POST /boodschappen/kies-product *(NEW — HTMX fragment)*

Sets a user-selected product as the match for an item.

**Request**: Form data
- `item_id` (str) — UUID of the `MatchReviewItem`
- `article_id` (int) — AH product article ID

**Guards**:
- `item_id` not found → 404
- `article_id` not valid → 400

**Flow**:
1. Find `MatchReviewItem` by `item_id` in `app.state.match_review_items`
2. Fetch product details via `search_products(article_id)` or cached from prior search
3. Recalculate `aantal` with `bereken_aantal(regel, product)`
4. Update item: `product`, `bron="zoekopdracht"`, `gecorrigeerd=True`

**Response**: Two HTML fragments via HTMX OOB swap:
- Updated card HTML (`fragments/match_review_item.html`) targeting `#item-<id>`
- Updated confirm button state targeting `#bevestig-btn` (disabled/enabled based on all-matched check)

---

## POST /boodschappen/bevestig-matches *(NEW)*

Creates the AH list from confirmed matches and saves preferences.

**Request**: No extra body (reads from `app.state.match_review_items`)

**Guards**:
- Any item has `product=None` → 400 Bad Request (should not happen if button was enabled)
- Not authenticated → redirect `GET /ah/login`

**Flow**:
1. Create AH list via `create_list(naam)`
2. Add products via `add_products_to_list(lijst_id, [(article_id, aantal), ...])`
3. For each `MatchReviewItem` where `product is not None AND (gecorrigeerd=True OR bron != "voorkeur")`: call `MatchVoorkeurenRepository.save(MatchVoorkeur(...))`. Items with `bron == "voorkeur"` that were not corrected are skipped (preference already in storage).
4. Clear `app.state.match_review_items`
5. Build `SyncResultaat` from the confirmed matches

**Response**: Redirect `303 → GET /boodschappen/ah-bevestiging` (or render `pages/ah_bevestiging.html` directly)

---

## Template Target IDs (HTMX anchors)

| ID | Element | Updated by |
|----|---------|-----------|
| `#item-<uuid>` | Single match review card | `POST /kies-product` OOB |
| `#zoek-<uuid>` | Search area within a card | `GET /zoek-product` |
| `#bevestig-btn` | Confirm button | `POST /kies-product` OOB |
