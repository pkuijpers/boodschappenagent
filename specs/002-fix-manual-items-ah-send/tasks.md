# Tasks: Handmatig toegevoegde artikelen meesturen naar AH

**Input**: Design documents from `specs/002-fix-manual-items-ah-send/`  
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅

**TDD vereist** (Constitution Principe I): schrijf falende tests FIRST, verifieer dat ze falen, implementeer daarna.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Kan parallel uitgevoerd worden (andere bestanden, geen actieve afhankelijkheden)
- **[Story]**: Welk user story dit task bij hoort

---

## Phase 1: Setup (Gedeelde Infrastructure)

**Purpose**: Test fixture toevoegen die beide test-fases nodig hebben

- [ ] T001 [P] Voeg fixture `setup_boodschappenlijst_met_handmatig` toe aan `tests/web/conftest.py` (direct na `setup_boodschappenlijst` fixture, na regel 405) — stelt `app_with_ah.state.boodschappenlijst_model` in als sentinel-Boodschappenlijst (week_start=WEEK_START, 1 regel "pasta") én `app_with_ah.state.boodschappenlijst` als lijst met 2 items: `{id:"menu-1", naam:"pasta", hoeveelheid:500, eenheid:"g", checked:False, handmatig:False, eerste_recept:"Pasta bolognese", extra_aantal:0}` én `{id:"handmatig-1", naam:"zeep", hoeveelheid:1, eenheid:"stuks", checked:False, handmatig:True, eerste_recept:None, extra_aantal:0}`

---

## Phase 2: User Story 1 — Handmatig artikel wordt meegestuurd naar AH (Priority: P1) 🎯 MVP

**Goal**: Alle niet-gecheckte items (menu én handmatig) worden verstuurd naar AH bij klikken op 'Verstuur naar AH'

**Independent Test**: Voeg handmatig "zeep" toe aan de boodschappenlijst, klik 'Verstuur naar AH', en controleer dat `sync_naar_lijst` is aangeroepen met een `Boodschappenlijst` die "zeep" bevat

### Tests voor User Story 1 (schrijf EERST — zorg dat ze FALEN vóór implementatie)

- [ ] T002 [P] [US1] Maak class `TestVerstuurNaarAHHandmatig` en voeg test `test_s20_1_handmatig_item_wordt_meegestuurd` toe aan `tests/web/test_ah_integratie.py` — gebruikt `setup_boodschappenlijst_met_handmatig`; `mock_token_manager.is_authenticated.return_value = True`; `mock_ah_integratie.sync_naar_lijst.return_value = sync_resultaat_succes`; POST naar `/boodschappen/verstuur-naar-ah`; assert dat `mock_ah_integratie.sync_naar_lijst` is aangeroepen; assert dat naam "zeep" voorkomt in de namen van `mock_ah_integratie.sync_naar_lijst.call_args[0][0].regels`; assert naam "pasta" ook aanwezig is
- [ ] T003 [US1] Voeg test `test_s20_2_gemengde_lijst_alle_items_meegestuurd` toe aan `TestVerstuurNaarAHHandmatig` in `tests/web/test_ah_integratie.py` — stel `app_with_ah.state.boodschappenlijst` in met 3 menu-items en 2 handmatige items (totaal 5); assert `sync_naar_lijst` aangeroepen met `Boodschappenlijst` van 5 regels (`len(call_args[0][0].regels) == 5`)
- [ ] T004 [US1] Voeg test `test_s20_3_alleen_handmatige_items_worden_verstuurd` toe aan `TestVerstuurNaarAHHandmatig` in `tests/web/test_ah_integratie.py` — stel `app_with_ah.state.boodschappenlijst_model` in als niet-None sentinel met lege regels (`regels=[]`), `boodschappenlijst` als 2 handmatige items; assert `sync_naar_lijst` aangeroepen met lijst van 2 regels
- [ ] T005 [US1] Verifieer dat tests T002-T004 FALEN (red) — delegeer aan test-reporter subagent voor `tests/web/test_ah_integratie.py::TestVerstuurNaarAHHandmatig`

### Implementatie voor User Story 1

- [ ] T006 [US1] Implementeer fix in `src/boodschappenagent/web/routers/boodschappen.py`:
  1. Voeg `BoodschappenRegel` toe aan import op regel 12: `from boodschappenagent.boodschappenlijst.models import Boodschappenlijst, BoodschappenRegel`
  2. In `verstuur_naar_ah()`: hernoem `lijst = _get_boodschappenlijst(request)` naar `sentinel = _get_boodschappenlijst(request)` en gebruik `sentinel` voor de None-check en redirect
  3. Vervang de `checked_namen`-filterlogica (huidige regels 234-237) door: `te_versturen = [item for item in _get_items(request) if not item.get("checked")]`
  4. Vervang de leegcheck `if len(lijst.regels) == 0` door `if not te_versturen`
  5. Voeg conversie toe: `regels = [BoodschappenRegel(naam=item["naam"], hoeveelheid=item["hoeveelheid"], eenheid=item["eenheid"], originele_namen=frozenset({item["naam"]})) for item in te_versturen]`
  6. Bouw nieuwe lijst: `lijst = Boodschappenlijst(week_start=sentinel.week_start, regels=regels)`
  7. Geef `lijst` door aan `ah_integratie.sync_naar_lijst(lijst)` (ongewijzigd)
- [ ] T007 [US1] Verifieer dat T002-T004 nu SLAGEN én dat bestaande tests S15-S17 en `TestVerstuurNaarAHCheckedItems` ongewijzigd slagen (green) — delegeer aan test-reporter subagent voor `tests/web/test_ah_integratie.py`

**Checkpoint**: User Story 1 volledig functioneel — handmatige items gaan mee naar AH, bestaande gedrag intact

---

## Phase 3: User Story 2 — Bevestiging toont correct aantal (Priority: P2)

**Goal**: Na het versturen toont de bevestigingspagina de volledige flow, ook voor gemengde lijsten

**Independent Test**: Na POST met gemengde lijst verschijnt `[data-testid="ah-bevestiging"]` (geen foutpagina)

### Tests voor User Story 2

- [ ] T008 [US2] Voeg test `test_s20_4_bevestiging_flow_met_handmatig` toe aan `TestVerstuurNaarAHHandmatig` in `tests/web/test_ah_integratie.py` — gebruikt `setup_boodschappenlijst_met_handmatig`; `is_authenticated = True`; mock `sync_naar_lijst` retourneert `sync_resultaat_succes`; POST `/boodschappen/verstuur-naar-ah`; assert response status 200; assert `soup(response).select_one('[data-testid="ah-bevestiging"]') is not None`
- [ ] T009 [US2] Verifieer dat T008 slaagt (verwacht groen na US1-fix) — delegeer aan test-reporter subagent; als test faalt: controleer `pages/ah_bevestiging.html` op correcte `data-testid`

**Checkpoint**: User Stories 1 en 2 volledig functioneel

---

## Phase 4: Polish & Cross-Cutting Concerns

- [ ] T010 [P] Ruff linting: `uv run ruff check --fix src/boodschappenagent/web/routers/boodschappen.py` — fix eventuele line-length of stijlproblemen
- [ ] T011 [P] Ruff formatting: `uv run ruff format src/boodschappenagent/web/routers/boodschappen.py` — controleer opmaak
- [ ] T012 Volledige test suite (unit + web, niet E2E): delegeer aan test-reporter subagent — geen regressions

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Geen dependencies — start direct
- **US1 tests (T002-T004)**: T001 moet klaar zijn (fixture nodig in conftest.py)
  - T002 kan parallel met T001 (ander bestand), maar fixture moet beschikbaar zijn vóór test-run
  - T003 na T002 (zelfde bestand, zelfde class)
  - T004 na T003 (zelfde bestand, zelfde class)
- **US1 verificatie (T005)**: Na T001-T004
- **US1 implementatie (T006)**: Na T005 (tests moeten falen bevestigd zijn)
- **US1 groen (T007)**: Na T006
- **US2 (T008-T009)**: Na T007 (US1 moet groen zijn)
- **Polish (T010-T012)**: Na T009

### User Story Dependencies

- **US1 (P1)**: Kan starten na Setup — geen andere user story dependencies
- **US2 (P2)**: Kan starten na US1 is groen — US2 bouwt voort op US1 fix

### Within Each User Story

```
Tests schrijven (T002-T004) → Falen bevestigen (T005) → Implementeren (T006) → Slagen bevestigen (T007)
```

### Parallel Opportunities

- T001 (conftest) en T002 (test class in ander bestand) kunnen parallel
- T010 en T011 (ruff check/format) kunnen parallel

---

## Parallel Example: User Story 1

```
# Stap 1 — parallel schrijven (verschillende bestanden):
Task T001: "fixture in tests/web/conftest.py"
Task T002: "test class in tests/web/test_ah_integratie.py"

# Stap 2 — sequentieel (zelfde bestand):
Task T003: "tweede testmethode in TestVerstuurNaarAHHandmatig"
Task T004: "derde testmethode in TestVerstuurNaarAHHandmatig"
```

---

## Implementation Strategy

### MVP (User Story 1 Only)

1. Complete Phase 1: Setup (T001)
2. Schrijf falende tests T002-T004 (rood)
3. Bevestig falen T005
4. Implementeer fix T006
5. Bevestig groen T007
6. **STOP en VALIDEER**: handmatige items gaan naar AH — kernbug opgelost

### Full Delivery

1. MVP afmaken (US1 groen)
2. US2 toevoegen T008-T009
3. Polish T010-T012

---

## Notes

- [P] taken zijn in andere bestanden of hebben geen actieve afhankelijkheden
- TDD-cyclus MOET gevolgd worden: rood → groen, nooit overslaan
- Test-reporter subagent delegeren voor alle pytest-runs (nooit `uv run pytest` direct)
- `BoodschappenRegel.originele_namen` eist een non-empty frozenset — gebruik `frozenset({item["naam"]})`
- Sentinel-gebruik: `boodschappenlijst_model` blijft als initialized-check en week_start bron; de `.regels` worden niet meer gebruikt in `verstuur_naar_ah()`
- Bestaande S17.2 test (`boodschappenlijst_model = None` → redirect) blijft ongewijzigd werken na fix
