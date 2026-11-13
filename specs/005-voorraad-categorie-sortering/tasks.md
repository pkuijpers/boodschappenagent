# Tasks: Voorraadlijst Sortering op Categorie

**Input**: Design documents from `specs/005-voorraad-categorie-sortering/`
**Branch**: `005-voorraad-categorie-sortering`
**Date**: 2026-05-27

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2)

---

## Phase 1: Setup

*Geen setup vereist — projectstructuur bestaat al; alle doelbestanden zijn geïdentificeerd in plan.md.*

---

## Phase 2: Foundational (Blocking Prerequisite)

**Purpose**: Domeinmodule `ah/afdeling.py` met `Afdeling` enum en `categorie_naar_afdeling()`. Beide user stories bouwen hierop voort.

**⚠️ CRITICAL**: Beide user story fasen kunnen pas starten als deze fase compleet is.

- [X] T001 Schrijf parametrized failing unit tests voor `categorie_naar_afdeling()` (alle 16 gevallen uit plan.md §Stap 4) in `tests/test_afdeling.py`
- [X] T002 Implementeer `Afdeling` str-enum, `AFDELING_VOLGORDE` dict en `categorie_naar_afdeling()` functie in `src/boodschappenagent/ah/afdeling.py`
- [X] T003 [P] Exporteer `Afdeling`, `AFDELING_VOLGORDE` en `categorie_naar_afdeling` vanuit `src/boodschappenagent/ah/__init__.py`

**Checkpoint**: `uv run pytest tests/test_afdeling.py` — alle 16 parametrized tests groen.

---

## Phase 3: User Story 1 — Items gesorteerd op winkellocatie (Priority: P1) 🎯 MVP

**Goal**: Voorraadpagina toont producten gesorteerd in volgorde koelkast → voorraadkast → diepvries → overig.

**Independent Test**: Open de voorraadpagina met producten uit meerdere categorieën. Controleer dat melk bovenaan staat, conserven in het midden, en diepvriesgroenten onderaan — zonder sectieheaders.

### Tests voor User Story 1 ⚠️ Schrijf EERST — verwacht ROOD

- [X] T004 [US1] Breid `TEST_VOORRAAD_PRODUCTEN` fixture uit met 5 producten in 3 categorieën (Zuivel, Pasta, Diepvries) in `tests/web/conftest.py`
- [X] T005 [US1] Schrijf failing integration tests die bevestigen dat een koelkastproduct vóór een diepvriesproduct verschijnt in de DOM-respons van `GET /voorraad` in `tests/web/test_voorraadcheck.py`

### Implementatie voor User Story 1

- [X] T006 [US1] Voeg `"category": p.category` toe aan de item-dict in `_haal_voorraad_producten()` in `src/boodschappenagent/web/routers/voorraad.py`
- [X] T007 [US1] Voeg `afdeling` veld toe via `categorie_naar_afdeling(item["category"])` en sorteer `items` op `AFDELING_VOLGORDE[item["afdeling"]]` in `_build_voorraad_context()` in `src/boodschappenagent/web/routers/voorraad.py`

**Checkpoint**: `uv run pytest tests/web/test_voorraadcheck.py` — alle bestaande tests plus T005-assertions groen. DOM-volgorde is koelkast → voorraadkast → diepvries.

---

## Phase 4: User Story 2 — Zichtbare categoriescheiding (Priority: P2)

**Goal**: Sectieheaders ("Koelkast", "Voorraadkast", "Diepvries") verschijnen boven elke gevulde groep; lege secties tonen geen header.

**Independent Test**: Open de voorraadpagina met producten uit 2 van de 3 secties. Controleer dat de betreffende sectieheaders zichtbaar zijn en de ontbrekende sectie géén header toont.

### Tests voor User Story 2 ⚠️ Schrijf EERST — verwacht ROOD

- [X] T008 [US2] Schrijf failing integration tests die bevestigen dat "Koelkast"- en "Diepvries"-sectieheaders aanwezig zijn in de HTML-respons, en dat de "Diepvries"-header ontbreekt wanneer er geen diepvriesproducten zijn in `tests/web/test_voorraadcheck.py`

### Implementatie voor User Story 2

- [X] T009 [US2] Vervang de huidige `{% for item in voorraad_items %}` loop door een `groupby('afdeling')`-loop met `<h3>` sectieheaders per gevulde groep in `src/boodschappenagent/web/templates/fragments/voorraad_content.html`

**Checkpoint**: `uv run pytest tests/web/test_voorraadcheck.py` — alle tests groen inclusief sectieheader-assertions. Lege secties produceren geen header.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: E2E verificatie en code-kwaliteit borging.

- [X] T010 [P] Schrijf Playwright E2E test die de sorteervolgorde van secties op de voorraadpagina verifieert (koelkastsectie vóór diepvriessectie) in `tests/e2e/test_voorraadcheck.py`
- [X] T011 [P] Voer `uv run ruff check --fix .` en `uv run ruff format .` uit op alle gewijzigde Python-bestanden

**Checkpoint**: `uv run pytest -m e2e` groen; `uv run ruff check .` meldt geen fouten.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundational (Phase 2)**: Geen externe dependencies — kan direct starten. **BLOKKEERT Phase 3 en Phase 4**.
- **User Story 1 (Phase 3)**: Afhankelijk van Phase 2 (T002, T003). Kan starten zodra Phase 2 compleet is.
- **User Story 2 (Phase 4)**: Afhankelijk van Phase 3 (T007 — `afdeling` veld in items vereist voor groupby). Kan starten zodra Phase 3 compleet is.
- **Polish (Phase 5)**: Afhankelijk van Phase 4. T010 en T011 kunnen parallel.

### Within Each User Story

- Tests (T004/T005, T008) MOETEN worden geschreven en ROOD zijn vóór implementatie
- Fixtures (T004) vóór tests (T005)
- Router-aanpassingen (T006) vóór context-logica (T007)

### Parallel Opportunities

- T003 kan parallel aan T002 zodra `afdeling.py` bestaat (T002 voltooid)
- T010 en T011 (Phase 5) kunnen parallel

---

## Parallel Example: Phase 2

```bash
# Stap 1 — tests schrijven (red):
Task: "T001 — schrijf tests/test_afdeling.py"

# Stap 2 — implementatie (green):
Task: "T002 — implementeer src/boodschappenagent/ah/afdeling.py"

# Stap 3 — export (parallel met andere cleanup):
Task: "T003 — update src/boodschappenagent/ah/__init__.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Voltooi Phase 2: Foundational — `afdeling.py` + tests groen
2. Voltooi Phase 3: User Story 1 — gesorteerde voorraadpagina
3. **STOP en VALIDEER**: open voorraadpagina; bevestig correcte volgorde
4. Demo/deploy als P1 voldoende is

### Incremental Delivery

1. Phase 2 klaar → `categorie_naar_afdeling()` getest en werkend
2. Phase 3 klaar → sortering zichtbaar op pagina (MVP!)
3. Phase 4 klaar → sectieheaders toegevoegd (volledige feature)
4. Phase 5 klaar → E2E verificatie + schone code

---

## Notes

- [P] = verschillende bestanden, geen onderlinge afhankelijkheden
- TDD-volgorde per fase: test schrijven (red) → implementeren (green) → refactor
- `uv run pytest tests/test_afdeling.py` na T002 om red→green te bevestigen
- `uv run pytest tests/web/test_voorraadcheck.py` na T007 en na T009
- `uv run pytest -m e2e` alleen na T010 (Playwright vereist)
- Geen nieuwe datapersistentie, geen nieuwe API-calls — zuivere transformatielaag
