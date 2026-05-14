# Tasks: Ingredient Match Review & Correction

**Input**: Design documents from `/specs/003-ingredient-match-review/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/routes.md ✅, contracts/ui-design.md ✅, quickstart.md ✅

**Tests**: TDD is required per constitution check in plan.md — all new routes, repository, and integration changes get failing tests first.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Exact file paths included in all descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the new module file that all user stories depend on.

- [X] T001 Create `src/boodschappenagent/ah/preferences.py` as new module with imports and empty class stubs for `MatchVoorkeur`, `MatchReviewItem`, and `MatchVoorkeurenRepository`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared models and color tokens used across all three user stories. MUST complete before any user story work begins.

**⚠️ CRITICAL**: All user story implementations depend on `MatchVoorkeur`, `MatchReviewItem`, and the Tailwind color tokens defined here.

- [X] T002 Write failing tests for `MatchVoorkeur` frozen dataclass (to_dict, from_dict, validation: non-empty ingredient_naam, positive article_id, valid ISO 8601 updated_at) in `tests/ah/test_preferences.py`
- [X] T003 Write failing tests for `MatchReviewItem` mutable dataclass (field types, gecorrigeerd defaults to False, bron accepts the five string values per data-model.md — note: "referentie" = matched from existing AH reference list in integration.py) in `tests/ah/test_preferences.py`
- [X] T004 Implement `MatchVoorkeur` frozen dataclass with `to_dict()`/`from_dict()` and validation rules (normalize to lowercase, assert positive article_id) in `src/boodschappenagent/ah/preferences.py`
- [X] T005 Implement `MatchReviewItem` mutable dataclass with all fields per data-model.md (id: str UUID, naam, hoeveelheid, eenheid, product, bron, gecorrigeerd, aantal) in `src/boodschappenagent/ah/preferences.py`
- [X] T006 Add `ah-blue-light`, `ah-green`, and `border-l-ah-green` color tokens to Tailwind config in `src/boodschappenagent/web/templates/base.html` under `tailwind.config.theme.extend.colors`

**Checkpoint**: Foundation ready — `MatchVoorkeur`, `MatchReviewItem`, and color tokens in place. User story implementation can begin.

---

## Phase 3: User Story 1 — Bekijk matchresultaten vóór aanmaken AH-lijst (Priority: P1) 🎯 MVP

**Goal**: When the user clicks "Verstuur naar AH", the system matches all items and shows a review overview before creating the AH list. The AH list is only created after the user confirms.

**Independent Test**: Start the match process from the shopping list and verify the match review page appears with all items and their matched products, without an AH list being created.

### Tests for User Story 1

> **Write these tests FIRST — ensure they FAIL before implementation**

- [X] T007 [US1] Write failing tests for modified `POST /boodschappen/verstuur-naar-ah` (converts items to MatchReviewItems, stores in app.state.match_review_items, returns 303 redirect to /boodschappen/match-review) in `tests/web/test_boodschappen.py`
- [X] T008 [US1] Write failing tests for `GET /boodschappen/match-review` (returns 200 with all match items rendered, redirects 303 to /boodschappen when app.state.match_review_items is empty/None) in `tests/web/test_boodschappen.py`
- [X] T009 [US1] Write failing tests for `POST /boodschappen/bevestig-matches` (creates AH list, clears app.state.match_review_items, returns 303 redirect; returns 400 when any item has product=None; returns 303 redirect to /ah/login when not authenticated) in `tests/web/test_boodschappen.py`

### Implementation for User Story 1

- [X] T010 [P] [US1] Create `src/boodschappenagent/web/templates/fragments/match_review_item.html` with state 1 (matched: ingredient name, quantity/unit, product name, price, "Corrigeer" button, bron badge) and state 3 (no match: amber border, "Zoek product" action, "Geen match gevonden" per ui-design.md)
- [X] T011 [P] [US1] Create `src/boodschappenagent/web/templates/pages/match_review.html` with page layout (back link header, card list using `match_review_item.html`, sticky confirm button bar with disabled/active states per ui-design.md)
- [X] T012 [US1] Modify `POST /boodschappen/verstuur-naar-ah` in `src/boodschappenagent/web/routers/boodschappen.py` to call `zoek_producten()`, convert each `ProductMatch` to `MatchReviewItem` with UUID, store list in `app.state.match_review_items`, redirect 303 to `/boodschappen/match-review`
- [X] T013 [US1] Implement `GET /boodschappen/match-review` in `src/boodschappenagent/web/routers/boodschappen.py` (render `pages/match_review.html` with items from app.state, redirect to `/boodschappen` if state empty)
- [X] T014 [US1] Implement `POST /boodschappen/bevestig-matches` in `src/boodschappenagent/web/routers/boodschappen.py` (guards: not authenticated → redirect 303 `/ah/login`; any item has product=None → 400; create AH list via `create_list(naam)` where naam is derived from the current shopping list context + `add_products_to_list(lijst_id, [(article_id, aantal), ...])`; clear `app.state.match_review_items`; redirect 303 to `/boodschappen/ah-bevestiging`)

**Checkpoint**: User Story 1 fully functional — user can start matching, review the overview, and create the AH list. No corrections yet.

---

## Phase 4: User Story 2 — Corrigeer een onjuiste match (Priority: P2)

**Goal**: The user can replace an incorrect product match by clicking "Corrigeer", searching for an alternative, and selecting it inline. The card and confirm button update via HTMX without a page reload.

**Independent Test**: Select an ingredient in the match review, search for an alternative product, select it, and verify the ingredient is now linked to the new product and the confirm button state is updated.

### Tests for User Story 2

> **Write these tests FIRST — ensure they FAIL before implementation**

- [X] T015 [US2] Write failing tests for `GET /boodschappen/zoek-product?q=&item_id=` (returns HTML fragment with up to 10 products, returns 404 for unknown item_id, returns empty state fragment when no results) in `tests/web/test_boodschappen.py`
- [X] T016 [US2] Write failing tests for `POST /boodschappen/kies-product` (updates MatchReviewItem in state: product, bron="zoekopdracht", gecorrigeerd=True, recalculated aantal; returns OOB swap with updated card and confirm button; 404 for unknown item_id; 400 for invalid article_id) in `tests/web/test_boodschappen.py`

### Implementation for User Story 2

- [X] T017 [P] [US2] Create `src/boodschappenagent/web/templates/fragments/zoekresultaten.html` (product list with name, price, unit/size, "Kies" button per product; empty state "Geen resultaten gevonden"; HTMX hx-post to /kies-product with item_id and article_id per ui-design.md)
- [X] T018 [P] [US2] Update `src/boodschappenagent/web/templates/fragments/match_review_item.html` to add state 4 (search open: search input with hx-trigger="input changed delay:300ms", hx-get="/boodschappen/zoek-product", close button) and state 5 (corrected: border-l-4 border-l-ah-green, checkmark icon, "gecorrigeerd" badge per ui-design.md)
- [X] T019 [US2] Implement `GET /boodschappen/zoek-product` in `src/boodschappenagent/web/routers/boodschappen.py` (validate item_id in state, call AH product search with query `q`, render `fragments/zoekresultaten.html` with up to 10 results)
- [X] T020 [US2] Implement `POST /boodschappen/kies-product` in `src/boodschappenagent/web/routers/boodschappen.py` (find item by item_id, fetch product details, recalculate aantal via `bereken_aantal()`, update item fields, return HTMX OOB swap: updated card `#item-<id>` + updated confirm button `#bevestig-btn`)

**Checkpoint**: User Stories 1 and 2 both functional — user can review matches and correct any incorrect ones inline.

---

## Phase 5: User Story 3 — Bewaar voorkeurs-match per ingredient (Priority: P3)

**Goal**: Corrected article IDs are saved globally per ingredient name so future shopping lists automatically use the right product. The matching step applies saved preferences before falling back to AH search.

**Independent Test**: Correct a match, restart the match process with the same ingredient, and verify the saved preference is applied automatically without requiring another correction.

### Tests for User Story 3

> **Write these tests FIRST — ensure they FAIL before implementation**

- [X] T021 [P] [US3] Write failing tests for `MatchVoorkeurenRepository` (get returns None for unknown name, get returns MatchVoorkeur for known name, save upserts by ingredient_naam, delete is no-op for missing name, auto-creates `data/match_preferences.json` on first save) in `tests/ah/test_preferences.py`
- [X] T022 [P] [US3] Write failing tests for modified `zoek_producten()` applying preferences (preference found and product available → bron="voorkeur"; preference found but product unavailable → fallback to smart_search, bron="voorkeur_niet_beschikbaar"; no preference → bron="zoekopdracht" or "niet_gevonden") in `tests/ah/test_integration.py`
- [X] T023 [P] [US3] Write failing tests for preference saving in `POST /boodschappen/bevestig-matches` (items with gecorrigeerd=True trigger MatchVoorkeurenRepository.save; items with gecorrigeerd=False do not) in `tests/web/test_boodschappen.py`

### Implementation for User Story 3

- [X] T024 [US3] Implement `MatchVoorkeurenRepository` in `src/boodschappenagent/ah/preferences.py` (get by normalized ingredient_naam, save/upsert into dict and write to `data/match_preferences.json`, delete by name, auto-create file on first save)
- [X] T025 [US3] Add `MatchVoorkeurenRepository` dependency to `src/boodschappenagent/web/dependencies.py` (instantiate with path `data/match_preferences.json`, inject into router via FastAPI dependency)
- [X] T026 [US3] Modify `zoek_producten()` in `src/boodschappenagent/ah/integration.py` to call `MatchVoorkeurenRepository.get(ingredient_naam)` per item before `smart_search()`: if preference found, verify product still orderable; set `bron` to `"voorkeur"` or `"voorkeur_niet_beschikbaar"` accordingly
- [X] T027 [US3] Update `POST /boodschappen/bevestig-matches` in `src/boodschappenagent/web/routers/boodschappen.py` to iterate `match_review_items` and call `MatchVoorkeurenRepository.save(MatchVoorkeur(...))` for each item where `gecorrigeerd=True`
- [X] T028 [P] [US3] Update `src/boodschappenagent/web/templates/fragments/match_review_item.html` to add state 2 (voorkeur badge: `bg-ah-blue-light text-ah-blue` per ui-design.md) and state 6 (voorkeur niet beschikbaar: amber warning text per ui-design.md)

**Checkpoint**: All three user stories functional — review, correct, and preferences are saved and applied automatically on next run.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: E2E validation and code quality across the full feature.

- [X] T029 [P] Write E2E tests for the full match review flow in `tests/e2e/test_match_review.py` (iPhone 13 emulation: start match process, verify review page, correct one item, verify card update, confirm all, verify redirect to ah-bevestiging; also verify confirm button stays disabled when one item has no match)
- [X] T030 Fix any ruff lint/format violations across all modified Python files (`src/boodschappenagent/ah/preferences.py`, `src/boodschappenagent/ah/integration.py`, `src/boodschappenagent/web/routers/boodschappen.py`, `src/boodschappenagent/web/dependencies.py`)
- [X] T031 Handle AH API error in `POST /boodschappen/verstuur-naar-ah` in `src/boodschappenagent/web/routers/boodschappen.py` — when `zoek_producten()` raises an exception (API unavailable), render `src/boodschappenagent/web/templates/pages/ah_error.html` with an error message (per contracts/routes.md)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Phase 2
- **User Story 2 (Phase 4)**: Depends on Phase 3 (US2 adds to the review page built in US1)
- **User Story 3 (Phase 5)**: Depends on Phase 2; integrates with US1 (bevestig-matches) and US2 (gecorrigeerd flag) but can be developed independently
- **Polish (Phase 6)**: Depends on all user stories complete

### User Story Dependencies

- **US1 (P1)**: Depends on Foundational. No dependency on US2 or US3.
- **US2 (P2)**: Extends the review page from US1 (adds inline correction to existing cards). Logically sequential.
- **US3 (P3)**: Extends `zoek_producten()` and `bevestig-matches`. Can be developed in parallel with US2 after Foundational.

### Within Each User Story

- Tests MUST be written first and MUST FAIL before implementation begins
- Models/dataclasses before services/repositories
- Templates can be developed in parallel with route implementation (different files)
- All tests in a story marked [P] can be written in parallel

### Parallel Opportunities

- **Phase 2**: T002 then T003 sequentially (same file `tests/ah/test_preferences.py`); T004 and T005 can run in parallel (different classes in same file — or sequentially)
- **Phase 3**: T007 → T008 → T009 sequentially (same file `tests/web/test_boodschappen.py`); T010, T011 (templates) can run in parallel with each other and with test writing
- **Phase 4**: T015 then T016 sequentially (same file `tests/web/test_boodschappen.py`); T017, T018 (templates) in parallel
- **Phase 5**: T021, T022, T023 (tests) in parallel; T028 can run in parallel with T024–T027

---

## Parallel Example: User Story 1

```bash
# Write tests for US1 sequentially (all add to the same file):
Task T007: "Tests for POST /verstuur-naar-ah in tests/web/test_boodschappen.py"
Task T008: "Tests for GET /match-review in tests/web/test_boodschappen.py"
Task T009: "Tests for POST /bevestig-matches in tests/web/test_boodschappen.py"

# Create templates in parallel with each other (different files, no conflict):
Task T010: "Create match_review_item.html fragment"
Task T011: "Create match_review.html page"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001)
2. Complete Phase 2: Foundational (T002–T006) — CRITICAL
3. Complete Phase 3: User Story 1 (T007–T014)
4. **STOP and VALIDATE**: Delegate test run to test-reporter subagent (Constitution I — never run `uv run pytest` directly in agentic sessions)
5. Demo: full match-review flow works, AH list only created after confirmation

### Incremental Delivery

1. Setup + Foundational → Models and color tokens ready
2. User Story 1 → Review page visible, AH list deferred until confirmation (**MVP**)
3. User Story 2 → Inline corrections possible
4. User Story 3 → Preferences saved, applied automatically next time
5. Polish → E2E validated, lint clean

---

## Notes

- [P] tasks = different files, no data dependencies — safe to parallelise
- [US1/US2/US3] label maps task to specific user story for traceability
- `app.state.match_review_items` is the single source of truth during the review session; clear it only on successful `POST /bevestig-matches`
- `MatchVoorkeurenRepository` is injected via FastAPI dependency; use a test-specific fixture path in tests (not `data/match_preferences.json`) to avoid polluting real data
- Templates use Tailwind color tokens defined in `base.html` — never inline `style` attributes or hex codes
- Touch targets must be ≥44×44 pt per constitution principle VI
