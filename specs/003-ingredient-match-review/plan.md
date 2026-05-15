# Implementation Plan: Ingredient Match Review & Correction

**Branch**: `003-ingredient-match-review` | **Date**: 2026-05-15 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/003-ingredient-match-review/spec.md`

## Summary

The ingredient match review feature (spec 003) was already implemented and deployed. This plan covers two targeted updates clarified in session 2026-05-15:

1. **Save all confirmed matches** — after the user confirms the match review, save ALL auto-matched items as preferences (not just manually corrected ones). Items already loaded from an existing preference are left unchanged unless explicitly corrected.
2. **Show product size in match review** — display the product's `size` field (e.g. "500 g") next to the product name in each match review card. The brand is not shown.

Both changes are minimal: one condition change in a route handler, one line addition in a template.

## Technical Context

**Language/Version**: Python 3.14+  
**Primary Dependencies**: FastAPI, Jinja2, HTMX, pytest  
**Storage**: JSON — `data/match_preferences.json` (via `MatchVoorkeurenRepository`)  
**Testing**: pytest (unit + web client), Playwright (E2E)  
**Target Platform**: Linux server; iPhone 13 viewport (390×844) for E2E  
**Project Type**: web-service  
**Performance Goals**: N/A — single-user local app  
**Constraints**: Server-side rendering only (HTMX); no SPA; touch targets ≥ 44×44 pt  
**Scale/Scope**: Single user; ~30–60 items per shopping list

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. TDD | ✓ PASS | New tests written before code changes |
| II. SSR | ✓ PASS | HTMX partial updates; no JSON API responses |
| III. Simplicity | ✓ PASS | Minimal: one condition change + one template line |
| IV. Code Quality | ✓ PASS | ruff check + format required before commit |
| V. Domain Modelling | ✓ PASS | Frozen dataclasses unchanged; no new model needed |
| VI. UI/UX | ✓ PASS | Size shown inline next to title; no new interactive element |

No gate violations.

## Project Structure

### Documentation (this feature)

```text
specs/003-ingredient-match-review/
├── plan.md              # This file
├── research.md          # Phase 0 — current implementation analysis
├── data-model.md        # Phase 1 — entity and save-logic specification
├── contracts/           # Phase 1 — endpoint behavioral contracts
└── tasks.md             # Phase 2 output (/speckit-tasks command)
```

### Source Code (affected files)

```text
src/boodschappenagent/
└── web/
    ├── routers/
    │   └── boodschappen.py          # bevestig_matches save-logic update
    └── templates/
        └── fragments/
            └── match_review_item.html  # product size display

tests/
└── web/
    └── test_boodschappen.py         # new tests for save-logic update + size display
```

No new files needed. No model changes needed.

## Complexity Tracking

> No constitution violations — table not required.
