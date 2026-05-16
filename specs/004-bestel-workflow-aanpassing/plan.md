# Implementation Plan: Bestel Workflow Aanpassing

**Branch**: `004-bestel-workflow-aanpassing` | **Date**: 2026-05-16 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/004-bestel-workflow-aanpassing/spec.md`

## Summary

Voeg een ingredient-selectiescherm toe tussen het weekmenu en de voorraadcheck. De gebruiker kan per recept-ingredient aan/uitvinken en de hoeveelheid aanpassen via dezelfde +/- UI als `/boodschappen` (inclusief dynamische stapgrootte). Na de voorraadcheck worden de geselecteerde recept-ingrediënten geaggregeerd en gecombineerd met de voorraadartikelen, waarna product matching direct start — zonder een apart boodschappenlijstscherm.

**Technische aanpak**: Nieuw `ingredient_selectie` router in FastAPI; `app.state.ingredient_selectie: list[dict]` voor in-memory sessiestate (conform bestaand `app.state.boodschappenlijst` patroon); `PATCH /voorraad/bevestig` aggregeert via `IngredientNormalizer` en roept nieuw `voeg_pantry_toe()` aan op `BoodschappenlijstFilter`; ingredient_selectie_item.html hergebruikt exact dezelfde +/- button markup en dynamische stapgrootte-logica als `boodschapitem.html`.

## Technical Context

**Language/Version**: Python 3.14+
**Primary Dependencies**: FastAPI, Jinja2, HTMX (CDN), Tailwind CSS (CDN), pytest, Playwright
**Storage**: In-memory `app.state` (geen persistentie voor ingredient-selectie sessiestate)
**Testing**: pytest (unit/integration via TestClient); Playwright (E2E, iPhone 13, `@pytest.mark.e2e`)
**Target Platform**: Mobiel (iPhone 13 viewport 390×844); Python server op Linux
**Project Type**: Web-service (FastAPI + SSR)
**Performance Goals**: Initialisatietijd ingredient-selectiescherm < 100ms (in-memory, max. ~105 items)
**Constraints**: Alle touch targets ≥ 44×44 pt; geen inline `style` attributen; hex-waarden alleen in Tailwind config in `base.html`
**Scale/Scope**: 1 gebruiker per sessie; max. 7 recepten × ~15 ingrediënten = max. ~105 items

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principe | Status | Toelichting |
|----------|--------|-------------|
| I. TDD (NON-NEGOTIABLE) | ✅ Pass | Alle taken volgen Red-Green-Refactor; tests in `tests/web/test_ingredient_selectie.py` en `tests/web/test_voorraadcheck.py` |
| II. Server-Side Rendering | ✅ Pass | FastAPI + Jinja2 + HTMX; geen SPA; alle responses zijn HTML (full page of fragment) |
| III. Simplicity (YAGNI) | ✅ Pass | `app.state` als `list[dict]` (geen frozen dataclass); geen extra abstractielagen; bestaande `IngredientNormalizer` hergebruikt |
| IV. Code Quality Gates | ✅ Pass | ruff check + format vereist (T027); geen inline `style`; hex alleen in Tailwind config |
| V. Domain Modelling | ✅ Pass | Ingredient-selectie gebruikt `list[dict]` conform bestaand patroon; geen nieuwe frozen dataclass |
| VI. UI/UX Design Philosophy | ✅ Pass | Vaste flow: Weekoverzicht → Ingredient-selectie → Voorraadcheck → Matching → Match-review; touch targets ≥ 44×44 pt; +/- knoppen identiek aan boodschapitem.html |

**Post-Phase-1 re-check**: ✅ — geen nieuwe schendingen geïntroduceerd; `voeg_pantry_toe()` is de minimale toevoeging aan `BoodschappenlijstFilter` (YAGNI gerespecteerd).

## Project Structure

### Documentation (this feature)

```text
specs/004-bestel-workflow-aanpassing/
├── plan.md                    # This file
├── spec.md                    # Feature specification
├── research.md                # Phase 0 output ✅
├── data-model.md              # Phase 1 output ✅
├── contracts/
│   └── http-endpoints.md      # Phase 1 output ✅
└── tasks.md                   # Phase 2 output ✅
```

### Source Code (gewijzigde en nieuwe bestanden)

```text
src/boodschappenagent/web/
├── app.py                                        # include_router(ingredient_selectie_router)
├── routers/
│   ├── ingredient_selectie.py                    # NIEUW — GET/POST endpoints
│   ├── menu.py                                   # GEWIJZIGD — POST /week/bevestig redirect
│   └── voorraad.py                               # GEWIJZIGD — POST /voorraad/bevestig
├── templates/
│   ├── components/
│   │   └── ingredient_selectie_item.html         # NIEUW — +/- buttons (zelfde als boodschapitem.html)
│   ├── fragments/
│   │   └── ingredient_selectie_content.html      # NIEUW — HTMX fragment
│   └── pages/
│       ├── ingredient_selectie.html              # NIEUW — full page
│       ├── match_review.html                     # GEWIJZIGD — back button → /voorraad
│       └── voorraad.html                         # GEWIJZIGD — back button → /ingredient-selectie

src/boodschappenagent/voorraadbeheer/
└── filter.py                                     # GEWIJZIGD — voeg_pantry_toe() methode toegevoegd

tests/
├── web/
│   ├── test_ingredient_selectie.py               # NIEUW — US1 tests
│   ├── test_voorraadcheck.py                     # GEWIJZIGD — US2+US3 tests
│   ├── test_boodschappen.py                      # GEWIJZIGD — back button assertie
│   └── test_week_bevestig.py                     # GEWIJZIGD — redirect assertie
└── e2e/
    └── test_bestel_flow.py                       # NIEUW — Playwright E2E
```

**Structure Decision**: Single project (Option 1). Web router en templates in bestaande structuur onder `src/boodschappenagent/web/`; geen aparte frontend/backend split.

---

## Implementatiestatus

Alle taken (T001–T034) zijn geïmplementeerd, met uitzondering van de geclarificeerde FR-013 UI:

| Fase | Status | Taken |
|------|--------|-------|
| Phase 1: Setup | ✅ | T001–T004 |
| Phase 2: US1 ingredient-selectiescherm | ✅ (deels) | T005–T015 — router + templates aanwezig; ingredient_selectie_item.html gebruikt nog text input |
| Phase 3: US2 aggregatie | ✅ | T016–T019 |
| Phase 4: US3 matching redirect | ✅ | T020–T024 |
| Phase 5: Polish | ✅ | T025–T027, T033 |
| Phase 6: Correcties | ✅ (deels) | T028–T031, T034 — T032a/T032 heropend (zie tasks.md) |
| **FR-013 UI clarificatie** | ✅ | T035–T036 — +/- knoppen met dynamische stapgrootte |

**Volledig geïmplementeerd**: `ingredient_selectie_item.html` gebruikt nu dezelfde +/- button-layout met dynamische stapgrootte als `boodschapitem.html`.
