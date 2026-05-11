# Tasks: Menu Variety — 80/20 Seasonal/Full-Catalogue Mix

**Input**: Design documents from `/specs/001-menu-variety-ratio/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓

**Scope**: Surgical change — one constant, one renamed parameter, one helper method, two call sites.  
**Only changed files**: `src/boodschappenagent/planner/menu_planner.py`, `tests/test_menu_planner.py`  
**TDD**: NON-NEGOTIABLE — write failing tests before any implementation.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Exact file paths included in all descriptions

---

## Phase 1: Setup

**Purpose**: Establish a verified green baseline before touching any production code.

- [X] T001 Read `src/boodschappenagent/planner/menu_planner.py` to understand the current `_filter_candidates_with_fallback()`, `plan_week()`, and `vervang_recept()` method signatures and call sites

**Checkpoint**: Current codebase understood — test baseline is green.

---

## Phase 2: Foundational (Blocking Prerequisite)

**Purpose**: Rename the `seasonal` parameter to `pool` in `_filter_candidates_with_fallback()`. This rename is required before any user story work because Change 3–5 all pass a pool (not necessarily seasonal) to this method. Behaviour is unchanged.

**⚠️ CRITICAL**: All user story phases depend on this rename being complete first.

- [X] T002 Rename parameter `seasonal` → `pool` (and update all internal references) in `_filter_candidates_with_fallback()` in `src/boodschappenagent/planner/menu_planner.py`; update the `ValueError` error message accordingly

**Checkpoint**: Rename complete and existing tests still pass.

---

## Phase 3: User Story 1 — Generate Varied Weekly Menu (Priority: P1) 🎯 MVP

**Goal**: Each day in the weekly menu independently draws from the seasonal pool (80%) or the full catalogue (20%).

**Independent Test**: Generate many seeded weekly menus and verify approximately 20% of daily selections come from outside the seasonal pool.

### Tests for User Story 1 ⚠️ Write FIRST — must FAIL before implementation

- [X] T003 [US1] Write failing `test_80_procent_seizoens_gemiddeld` in new `TestVarietieProbabilistisch` class in `tests/test_menu_planner.py`: generate many menus with varied seeds, assert ~80% of days draw from the seasonal pool (within ±10% tolerance per SC-001); verify the seasonal pool is built from `groenten_seizoenskalender` by asserting the fixture recipes match expected calendar membership
- [X] T004 [US1] Write failing `test_20_procent_volledig_assortiment` in `TestVarietieProbabilistisch` in `tests/test_menu_planner.py`: assert that at least one day across many runs selects a non-seasonal recipe
- [X] T005 [US1] Write failing `test_vervang_recept_gebruikt_ook_probabilistische_selectie` in `TestVarietieProbabilistisch` in `tests/test_menu_planner.py`: assert that `vervang_recept()` also applies the 80/20 pool selection (not always seasonal)

### Implementation for User Story 1

- [X] T006 [US1] Add module-level constant `SEIZOENS_KANS = 0.8` (after imports) and `_kies_pool()` helper method in `src/boodschappenagent/planner/menu_planner.py`; guard: `if self._rng.random() < SEIZOENS_KANS and seasonal: return seasonal; return self._recipes`
- [X] T007 [US1] Apply `_kies_pool()` in `plan_week()` in `src/boodschappenagent/planner/menu_planner.py`: replace direct `seasonal` pass to `_filter_candidates_with_fallback` with `pool = self._kies_pool(seasonal)` then pass `pool`
- [X] T008 [US1] Apply `_kies_pool()` in `vervang_recept()` in `src/boodschappenagent/planner/menu_planner.py`: same replacement as T007

**Checkpoint**: T003–T005 now pass. User Story 1 is fully functional.

---

## Phase 4: User Story 2 — Variety Constraints Still Applied (Priority: P2)

**Goal**: History exclusion and category diversity apply regardless of which pool a recipe is drawn from.

**Independent Test**: Generate menus for multiple consecutive weeks; verify no recipe appears in back-to-back weeks regardless of which pool it was drawn from.

**Note**: No new implementation is required — `_filter_candidates_with_fallback()` already applies all variety constraints to whatever pool it receives. This phase covers test coverage and fixes existing tests that assume exclusive seasonal selection.

### Tests for User Story 2 ⚠️ Write FIRST — must FAIL before fixing

- [X] T009 [US2] Write `test_variatie_constraints_gelden_voor_beide_pools` in `TestVarietieProbabilistisch` in `tests/test_menu_planner.py`: force the 20% draw via seed, assert no recently-used recipe appears in the result; also generate two consecutive weekly menus and assert no recipe appears in both (SC-003 consecutive-week guarantee, applicable regardless of which pool each day drew from)

### Update Existing Tests That Will Break

- [X] T010 [US2] Update `TestPlanWeekCo2Filtering.test_alleen_seizoensgeschikte_recepten` in `tests/test_menu_planner.py`: change assertion from "only seasonal recipes" to "seasonal recipes are preferred" (most seeds pick seasonal); the test should use a fixed seed that always draws the 80% case, or check the distribution over many runs

**Checkpoint**: T009 passes. Existing `TestPlanWeekCo2Filtering` tests are green again. User Story 2 verified.

---

## Phase 5: User Story 3 — Graceful Fallback When Seasonal Pool Is Empty (Priority: P3)

**Goal**: When the seasonal pool is empty on an 80% draw, the planner falls back to the full catalogue rather than failing.

**Independent Test**: With all seasonal recipes in the history window, the planner still produces a complete 7-day menu without errors.

**Note**: The `and seasonal` guard in `_kies_pool()` (added in T006) already implements this fallback. This phase adds test coverage to lock in the behaviour.

### Tests for User Story 3 ⚠️ Write FIRST — should already PASS if T006 is correct

- [X] T011 [US3] Write `test_fallback_bij_lege_seizoenspool` in `TestVarietieProbabilistisch` in `tests/test_menu_planner.py`: construct a planner where all seasonal recipes are in the history window, assert `plan_week()` succeeds and fills all days from the full catalogue

**Checkpoint**: T011 passes. All three user stories verified end-to-end.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T012 [P] Run `uv run ruff check --fix .` and `uv run ruff format .` to ensure all modified files pass code quality gates before commit

**Checkpoint**: Ruff clean. All tests green. Feature complete.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup; **BLOCKS all user story phases**
- **User Stories (Phase 3–5)**: All depend on Phase 2 completion
  - US1 (Phase 3) must complete before US2/US3 (their tests require the implementation)
  - US2 (Phase 4) can start as soon as Phase 3 implementation tasks (T006–T008) are done
  - US3 (Phase 5) can start as soon as T006 is done (`_kies_pool()` is the implementation)
- **Polish (Phase 6)**: After all desired user stories are complete

### User Story Dependencies

- **US1 (P1)**: Starts after Phase 2 — foundational for US2 and US3
- **US2 (P2)**: Tests can be written after T002; implementation verification after T006–T008
- **US3 (P3)**: Tests can be written after T002; implementation already covered by T006

### Within Each Phase

- Tests MUST be written and confirmed FAILING before implementation
- T006 (`_kies_pool`) must precede T007 (`plan_week`) and T008 (`vervang_recept`)
- T007 and T008 are independent and could be done in parallel

---

## Parallel Opportunities

```
Phase 2: T002 (single file rename — no parallelism)

Phase 3 Tests (write all before implementing):
  T003 → T004 → T005  (all same file, serial)

Phase 3 Implementation:
  T006 (prerequisite for T007 and T008)
  T007 and T008 can be done sequentially (same file, low risk of conflict)

Phase 4–5 Tests:
  T009, T010, T011 (same file, serial)

Phase 6:
  T012 (parallel safe — linting only)
```

---

## Implementation Strategy

### MVP (User Story 1 Only)

1. Phase 1: Read current implementation (T001)
2. Phase 2: Rename parameter (T002)
3. Phase 3: Write failing tests (T003–T005), implement (T006–T008)
4. **STOP and VALIDATE**: Run test suite, verify T003–T005 pass
5. Phase 6: Ruff (T012)

### Full Delivery (All User Stories)

1. MVP steps above
2. Phase 4: Write T009, fix T010 — verify variety constraints
3. Phase 5: Write T011 — verify graceful fallback
4. Phase 6: Ruff (T012)
5. Commit with all tests green

---

## Notes

- [P] tasks = different files or no shared state, safe to run in parallel
- [Story] label maps each task to its user story for traceability
- TDD is NON-NEGOTIABLE: no implementation before a failing test exists
- Use `random.Random(seed)` for deterministic test scenarios
- Delegate all test runs to the `test-reporter` subagent — never run `uv run pytest` directly
- Commit after each phase checkpoint; do not batch all phases into one commit
