# Implementation Plan: Ingredient Match Review & Correction

**Branch**: `003-ingredient-match-review` | **Date**: 2026-05-14 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/003-ingredient-match-review/spec.md`

## Summary

Add a match-review step between the shopping list and AH list creation. The existing "Verstuur naar AH" button now triggers product matching first, shows a review UI where the user can correct mismatches, and only creates the AH list once all items have a confirmed match. Corrections are saved per ingredient name globally so future lists benefit from remembered preferences.

The implementation extends the existing `ah/integration.py` matching pipeline with a preferences lookup step, adds three new web routes, two new templates, and a new `MatchVoorkeurenRepository` backed by `data/match_preferences.json`.

## Technical Context

**Language/Version**: Python 3.14+
**Primary Dependencies**: FastAPI, Jinja2, HTMX, pytest, Playwright (E2E), uv
**Storage**: JSON files under `data/` — new file: `data/match_preferences.json`
**Testing**: pytest (unit), Playwright (E2E, iPhone 13 emulation)
**Target Platform**: Linux server / iPhone 13 viewport (390×844)
**Project Type**: web-service
**Performance Goals**: Matching N items via AH API should complete before page render; no explicit SLA, but all N calls run sequentially as today
**Constraints**: AH API availability required; no offline fallback; confirm button disabled until all items have a match
**Scale/Scope**: Single-user household app; ~10–30 ingredients per list

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. TDD | ✅ PASS | All new routes, repository, and integration changes get failing tests first |
| II. Server-Side Rendering | ✅ PASS | Match review page and correction flow use HTMX partials — no SPA |
| III. Simplicity | ✅ PASS | Only what the spec requires: preferences storage, review page, correction HTMX flow |
| IV. Code Quality Gates | ✅ PASS | ruff check/format before every commit; no inline styles or hex codes in templates |
| V. Domain Modelling | ✅ PASS | New `MatchVoorkeur` uses frozen dataclass + to_dict/from_dict; persisted in JSON under `data/` |
| VI. UI/UX | ✅ PASS | Touch targets ≥44×44 pt; HTMX partial updates for correction flow; new step fits fixed sequence: Boodschappenlijst → **[new] Match Review** → AH Mandje |

No violations. No Complexity Tracking entry needed.

## Project Structure

### Documentation (this feature)

```text
specs/003-ingredient-match-review/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── routes.md        # HTTP route contracts
│   └── ui-design.md     # Card states & visual design
└── tasks.md             # Phase 2 output (speckit-tasks — not created here)
```

### Source Code

```text
src/boodschappenagent/
    ah/
        preferences.py         # NEW — MatchVoorkeur dataclass + MatchVoorkeurenRepository
        integration.py         # MODIFIED — apply preferred_article_id in zoek_producten
    web/
        routers/
            boodschappen.py    # MODIFIED — split verstuur-naar-ah; add match-review + bevestig routes
        templates/
            pages/
                match_review.html          # NEW — match review full page
            fragments/
                zoekresultaten.html        # NEW — HTMX product search results fragment
                match_review_item.html     # NEW — single match review card (for OOB updates)
        dependencies.py        # MODIFIED — add MatchVoorkeurenRepository dependency

tests/
    ah/
        test_preferences.py    # NEW — unit tests for MatchVoorkeur + MatchVoorkeurenRepository
        test_integration.py    # MODIFIED — test preferred_article_id lookup path
    web/
        test_boodschappen.py   # MODIFIED — tests for new routes
    e2e/
        test_match_review.py   # NEW — E2E for full flow

data/
    match_preferences.json     # NEW (auto-created on first save)
```

**Structure Decision**: Single-project layout. This feature extends existing modules in `ah/` and `web/routers/` — no new top-level packages needed.
