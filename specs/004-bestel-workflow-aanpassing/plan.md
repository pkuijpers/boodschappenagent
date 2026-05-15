# Implementation Plan: Bestel Workflow Aanpassing — Recept-ingrediëntselectie voor Voorraadcheck

**Branch**: `004-bestel-workflow-aanpassing` | **Date**: 2026-05-15 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/004-bestel-workflow-aanpassing/spec.md`

## Summary

Voeg een ingredient-selectiescherm toe tussen het weekmenu en de voorraadcheck, zodat de gebruiker per recept kan beslissen welke ingrediënten besteld moeten worden en in welke hoeveelheid. Na de voorraadcheck worden de geselecteerde recept-ingrediënten en de pantry-items samengevoegd en start product matching direct — het bestaande boodschappenlijst-scherm valt buiten de normale bestelflow.

**Nieuwe stappenvolgorde**: Weekoverzicht → Ingredient-selectie → Voorraadcheck → [aggregatie + matching] → Match-review → AH Bevestiging

## Technical Context

**Language/Version**: Python 3.14+
**Primary Dependencies**: FastAPI 0.111+, Jinja2, HTMX 1.9+, BeautifulSoup4 (tests), pytest
**Storage**: In-memory `app.state` voor sessiedata (geen persistentie nodig voor ingredient-selectie)
**Testing**: pytest + FastAPI TestClient; Playwright E2E
**Target Platform**: Web server (Uvicorn); primair mobiel (iPhone 13, 390×844)
**Project Type**: Web application (FastAPI + HTMX server-side rendering)
**Performance Goals**: Ingredient-selectie initialisatie < 100ms (in-memory operatie op weekmenu)
**Constraints**: Mobiel-first (min. 44×44 pt touch targets); geen SPA; HTML-over-the-wire
**Scale/Scope**: Enkelvoudige gebruiker, lokaal; weekmenu bevat maximaal 7 recepten, elk max ~15 ingrediënten

## Constitution Check

*Re-check after Phase 1 design completed below.*

| Gate | Status | Notes |
|------|--------|-------|
| TDD (Principle I) | ✅ PASS | Plan volgt Red-Green-Refactor per stap |
| Server-side rendering (Principle II) | ✅ PASS | Alle nieuwe schermen zijn FastAPI + Jinja2 + HTMX |
| YAGNI (Principle III) | ✅ PASS | Geen speculatieve abstraties; IngredientSelectieItems zijn dicts (zelfde patroon als boodschappenlijst) |
| Code quality gates (Principle IV) | ✅ PASS | Ruff check/format verplicht voor commit |
| Domain modelling (Principle V) | ✅ PASS | Sessiestate in app.state als dicts (niet gepersisteerd); geen extra frozen dataclass nodig |
| UI/UX design (Principle VI) | ⚠️ DEVIATION | Constitution vermeldt volgorde "Voorraadcheck → Boodschappenlijst"; na deze feature is de volgorde "Ingredient-selectie → Voorraadcheck → Matching". **Justified**: spec FR-009 definieert de nieuwe canonieke volgorde. Constitution-sectie VI vereist een MINOR-versie-bump na deze feature. |

**Gate-oordeel**: Geen blokkerende schendingen. De workflow-volgorde in Principe VI wijkt af en vereist een constitution-update na implementatie, maar is afdoende gerechtvaardigd door de spec.

## Project Structure

### Documentation (this feature)

```text
specs/004-bestel-workflow-aanpassing/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── contracts/
│   └── http-endpoints.md  # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit-tasks command)
```

### Source Code (repository root)

```text
src/boodschappenagent/web/
    routers/
        ingredient_selectie.py   # NEW — GET /ingredient-selectie, POST .../toggle, PATCH .../hoeveelheid, POST .../bevestig
        voorraad.py              # MODIFIED — POST /voorraad/bevestig → start matching
        menu.py                  # MODIFIED — POST /week/bevestig → redirect /ingredient-selectie
    templates/
        pages/
            ingredient_selectie.html     # NEW
            voorraad.html                # MODIFIED — back button → /ingredient-selectie
        fragments/
            ingredient_selectie_content.html  # NEW
        components/
            ingredient_selectie_item.html    # NEW
    app.py               # MODIFIED — include ingredient_selectie router

src/boodschappenagent/voorraadbeheer/
    filter.py            # MODIFIED — add voeg_pantry_toe() method

tests/web/
    test_ingredient_selectie.py  # NEW
    test_week_bevestig.py        # MODIFIED — redirect assertion
    test_voorraadcheck.py        # MODIFIED — S8.1 redirect assertion
```

**Structure Decision**: Enkelvoudige web applicatie (Option 1 + web app varianten). De ingredient_selectie router volgt dezelfde structuur als de bestaande voorraad en boodschappen routers.

## Complexity Tracking

Geen constitution-schendingen die rechtvaardiging vereisen.
