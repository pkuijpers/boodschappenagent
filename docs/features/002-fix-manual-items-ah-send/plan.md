# Implementation Plan: Handmatig toegevoegde artikelen meesturen naar AH

**Branch**: `002-fix-manual-items-ah-send` | **Date**: 2026-05-13 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `specs/002-fix-manual-items-ah-send/spec.md`

## Summary

Handmatig toegevoegde artikelen worden niet meegestuurd naar AH omdat `verstuur_naar_ah()` alleen de `boodschappenlijst_model` gebruikt (een frozen `Boodschappenlijst` met uitsluitend menu-gegenereerde items), terwijl handmatige items alleen in de UI-itemslijst (`boodschappenlijst`) leven. De fix: bouw de `Boodschappenlijst` voor AH-sync af van de UI-itemslijst, die beide typen bevat.

## Technical Context

**Language/Version**: Python 3.14+  
**Primary Dependencies**: FastAPI, HTMX, pytest, ruff  
**Storage**: JSON files (data/) — geen database  
**Testing**: pytest (unit + web), Playwright (E2E)  
**Target Platform**: Linux server (web-service)  
**Project Type**: web-service  
**Performance Goals**: Standaard web app (p95 < 1s)  
**Constraints**: TDD, Server-Side Rendering (HTMX), ruff linting vereist

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principe | Status | Toelichting |
|----------|--------|-------------|
| I. TDD (NON-NEGOTIABLE) | ✅ Pass | Falende test schrijven voor implementatie |
| II. Server-Side Rendering | ✅ Pass | Geen SPA-wijzigingen; HTMX + Jinja2 behouden |
| III. Simplicity (YAGNI) | ✅ Pass | Minimale, gerichte fix in één functie |
| IV. Code Quality Gates | ✅ Pass | ruff check + format vereist vóór commit |
| V. Domain Modelling | ✅ Pass | `BoodschappenRegel` frozen dataclass; patroon behouden |

Geen constitution violations. Geen Complexity Tracking vereist.

## Project Structure

### Documentation (this feature)

```text
specs/002-fix-manual-items-ah-send/
├── plan.md              # Dit bestand
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source Code (repository root)

```text
src/boodschappenagent/
    web/
        routers/
            boodschappen.py   # Fix in verstuur_naar_ah() (regel 216-261)

tests/
    web/
        test_ah_integratie.py # Nieuwe tests in TestVerstuurNaarAHHandmatig
```

**Structure Decision**: Single project layout. Enkel `boodschappen.py` (router) en de bestaande test-suite worden aangepast.
