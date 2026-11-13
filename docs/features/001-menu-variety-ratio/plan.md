# Implementation Plan: Menu Variety — 80/20 Seasonal/Full-Catalogue Mix

**Branch**: `001-menu-variety-ratio` | **Date**: 2026-05-11 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `specs/001-menu-variety-ratio/spec.md`

## Summary

For each day in the weekly menu, the planner draws a random number: with 80% probability it selects a recipe from the seasonal pool (recipes whose vegetables are in season per the `groenten_seizoenskalender`); with 20% probability it selects from the full recipe catalogue without season constraints. All existing variety constraints (history, category, basis) continue to apply. If the seasonal pool is empty, the planner falls back to the full catalogue unconditionally.

The change is surgical: one new constant and two modified methods in `menu_planner.py`. No model changes, no new files, no API surface changes.

## Technical Context

**Language/Version**: Python 3.14+  
**Primary Dependencies**: None new — uses existing `SeizoenKalender`, `RecipeSearch`, `MenuHistory`  
**Storage**: N/A — no persistence changes  
**Testing**: pytest (unit tests in `tests/test_menu_planner.py`)  
**Target Platform**: Linux (Raspberry Pi deployment)  
**Project Type**: Library (planner module within boodschappenagent package)  
**Performance Goals**: No change from baseline  
**Constraints**: YAGNI — no abstractions beyond immediate need  
**Scale/Scope**: Single planner class, two methods

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. TDD (NON-NEGOTIABLE) | PASS | All tests written before implementation; `test-reporter` subagent used for test runs |
| II. Server-Side Rendering | N/A | Backend-only change; no web layer touched |
| III. Simplicity (YAGNI) | PASS | One constant + two method edits; no new abstraction layers |
| IV. Code Quality Gates | PASS | `ruff check` + `ruff format` required before commit |
| V. Domain Modelling | PASS | No model changes; frozen dataclasses unchanged |

## Project Structure

### Documentation (this feature)

```text
specs/001-menu-variety-ratio/
├── plan.md              # This file
├── research.md          # Phase 0 findings
├── data-model.md        # Phase 1 — no changes needed
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source Code (affected files only)

```text
src/boodschappenagent/
└── planner/
    └── menu_planner.py   # Only changed file

tests/
└── test_menu_planner.py  # New test class added
```

## Phase 0: Research Findings

**File**: [research.md](research.md)

### Finding 1 — Season detection is already calendar-based

The `MenuPlanner` already imports and uses `SeizoenKalender` via `RecipeSearch.filter_by_co2_maand()`. The `seizoen` attribute on `Recipe` is not consulted by the planner at all. The spec's clarification ("seizoen attribuut is obsolete") matches the production code exactly. No migration or deprecation work is needed.

### Finding 2 — `_filter_candidates_with_fallback()` is already pool-agnostic

The method signature is `(self, seasonal: list[Recipe], ...)` but it treats the list as a generic pool: it filters by `used_ids` and `recent_ids`, progressively relaxes constraints, and raises only when the pool is entirely empty. Renaming the parameter is the only refactor needed (to `pool`). Behaviour is unchanged.

### Finding 3 — Full catalogue is already stored on the planner

`self._recipes` holds the complete recipe list. The seasonal pool is a filtered subset. The 20% draw simply uses `self._recipes` as the pool — no new dependency or constructor argument needed.

### Finding 4 — `vervang_recept()` uses the same pattern

Both `plan_week()` and `vervang_recept()` call `_filter_candidates_with_fallback(seasonal, ...)`. Both need the same 80/20 probabilistic draw applied before the call.

### Decision summary

| Decision | Chosen | Alternatives rejected |
|----------|--------|-----------------------|
| Probability constant location | Module-level constant `SEIZOENS_KANS = 0.8` | Constructor parameter (over-engineered for current need) |
| Pool fallback trigger | `if self._rng.random() < SEIZOENS_KANS and seasonal` | Catch ValueError (more complex, not needed) |
| Parameter rename | `pool` (was `seasonal`) in `_filter_candidates_with_fallback` | Leave as `seasonal` (misleading when passing full catalogue) |

## Phase 1: Design

### Data Model

No data model changes. `Recipe`, `DagInput`, `DagPlanning`, `WeekMenu` are all unchanged.

**File**: [data-model.md](data-model.md) — not generated; no entities change.

### Interface Contracts

No external interface changes. `MenuPlanner` public API (`plan_week`, `vervang_recept`) signatures are unchanged. Behaviour change is internal.

### Implementation Design

#### Change 1 — New module-level constant

```python
# In menu_planner.py, after imports
SEIZOENS_KANS = 0.8
```

#### Change 2 — Rename parameter in `_filter_candidates_with_fallback`

```python
def _filter_candidates_with_fallback(
    self,
    pool: list[Recipe],        # was: seasonal
    used_ids: set[str],
    recent_ids: set[str],
    vorige: DagPlanning | None,
) -> list[Recipe]:
```

All internal references to `seasonal` inside the method body change to `pool`. The error message updates accordingly.

#### Change 3 — Probabilistic pool selection helper

```python
def _kies_pool(self, seasonal: list[Recipe]) -> list[Recipe]:
    """Kies 80% seizoenspool of 20% volledig assortiment per dag."""
    if self._rng.random() < SEIZOENS_KANS and seasonal:
        return seasonal
    return self._recipes
```

The `and seasonal` guard handles FR-005: if the seasonal pool is empty, always fall back to the full catalogue regardless of the random draw.

#### Change 4 — Apply in `plan_week()`

Replace the existing call site:

```python
# Before
candidates = self._filter_candidates_with_fallback(
    seasonal, used_ids, recent_ids, vorige
)

# After
pool = self._kies_pool(seasonal)
candidates = self._filter_candidates_with_fallback(
    pool, used_ids, recent_ids, vorige
)
```

#### Change 5 — Apply in `vervang_recept()`

Same replacement as Change 4 inside `vervang_recept()`.

### Test Plan

New test class `TestVarietieProbabilistisch` in `tests/test_menu_planner.py`:

| Test | What it verifies |
|------|-----------------|
| `test_80_procent_seizoens_gemiddeld` | Over many seeded runs, approximately 80% of days use a seasonal recipe |
| `test_20_procent_volledig_assortiment` | At least some runs pick a non-seasonal recipe for a given day |
| `test_fallback_bij_lege_seizoenspool` | When seasonal pool is empty, all days are filled from full catalogue |
| `test_variatie_constraints_gelden_voor_beide_pools` | History exclusion and category diversity apply regardless of which pool is selected |
| `test_vervang_recept_gebruikt_ook_probabilistische_selectie` | `vervang_recept()` also applies 80/20 selection |

Existing tests must continue to pass unchanged — the behaviour for a 7-day menu with a seeded RNG is different now (pool can vary per day), so tests that assert specific recipe choices by seed will need their seeds updated if they break. Tests that assert structural properties (no duplicates, valid day count, etc.) are unaffected.
