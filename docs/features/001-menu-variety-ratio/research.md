# Research: Menu Variety — 80/20 Seasonal/Full-Catalogue Mix

**Date**: 2026-05-11 | **Feature**: `001-menu-variety-ratio`

## Finding 1 — Season detection is already calendar-based

**Decision**: No migration work needed.  
**Rationale**: `MenuPlanner` uses `RecipeSearch.filter_by_co2_maand()` which calls `SeizoenKalender.recept_is_seizoensgeschikt()`. The `seizoen` attribute on `Recipe` is never consulted in the planner. The spec clarification and the production code are already aligned.  
**Alternatives considered**: Migrating from `seizoen` attribute → rejected because it is already unused in the planner.

## Finding 2 — `_filter_candidates_with_fallback()` is pool-agnostic

**Decision**: Rename parameter from `seasonal` to `pool`; no logic changes.  
**Rationale**: The method applies variety constraints (used_ids, recent_ids, category, basis) progressively against whatever list it receives. It never inspects season attributes. Passing the full catalogue instead of the seasonal subset works without any logic change.  
**Alternatives considered**: Duplicate the method for each pool type → rejected (YAGNI, identical logic).

## Finding 3 — Full catalogue available as `self._recipes`

**Decision**: Use `self._recipes` directly for the 20% unconstrained draw.  
**Rationale**: `MenuPlanner.__init__` already stores the full recipe list. No new constructor argument or dependency injection is required.  
**Alternatives considered**: Pass full catalogue as a parameter per call → rejected (unnecessary; it is invariant for the lifetime of the planner).

## Finding 4 — Both `plan_week()` and `vervang_recept()` need the same change

**Decision**: Extract pool selection into `_kies_pool()` helper; apply in both methods.  
**Rationale**: Avoids duplication of the 80/20 logic across two call sites.  
**Alternatives considered**: Inline the draw in each method → rejected (duplication).

## Existing test impact

Tests in `TestCO2SeizoenFiltering` assert that *only* seasonal recipes are chosen. With the new probabilistic behaviour these assertions are no longer always true. Affected tests must be updated to assert that seasonal recipes are *preferred* (most runs) rather than *exclusive*.

Tests using fixed seeds that happen to always draw the 80% case will still pass; tests that assert exact recipe selection by seed may need seed values updated after the implementation is in place.
