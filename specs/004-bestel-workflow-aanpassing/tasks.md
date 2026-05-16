# Tasks: Bestel Workflow Aanpassing — Recept-ingrediëntselectie voor Voorraadcheck

**Input**: Design documents from `/specs/004-bestel-workflow-aanpassing/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/http-endpoints.md ✅

**Tests**: Opgenomen per TDD-principe (Red-Green-Refactor; zie CLAUDE.md en plan.md constitutiecheck).

**Organization**: Taken gegroepeerd per user story voor onafhankelijke implementatie en testen.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Kan parallel lopen (verschillende bestanden, geen onderlinge afhankelijkheden)
- **[Story]**: Welke user story ([US1], [US2], [US3])
- Exacte bestandspaden zijn opgenomen in elke taakomschrijving

---

## Phase 1: Setup — Redirect-aanpassingen en router-registratie

**Purpose**: Bestaande flow-aanpassingen die onmiddellijk vereist zijn zodat de nieuwe router straks een vaste plek heeft en de navigatiestroom klopt.

**⚠️ CRITICAL**: Geen user story-werk kan beginnen vóór deze fase compleet is.

- [X] T001 Registreer ingredient_selectie router (nog aan te maken) in `src/boodschappenagent/web/app.py` via `include_router`
- [X] T002 Update assertie in `tests/web/test_week_bevestig.py` (`test_bevestig_redirect_naar_voorraad`): verwacht redirect naar `/ingredient-selectie` in plaats van `/voorraad` (TDD red step — test faalt na dit)
- [X] T003 Update `POST /week/bevestig` redirect van `/voorraad` naar `/ingredient-selectie` in `src/boodschappenagent/web/routers/menu.py` (maakt T002 groen)
- [X] T004 Update back button in `src/boodschappenagent/web/templates/pages/voorraad.html` van `/week` naar `/ingredient-selectie`

**Checkpoint**: Bestaande tests groen; ingredient_selectie router geregistreerd (geeft 500 tot endpoints bestaan — acceptabel voor nu)

---

## Phase 2: User Story 1 — Ingredient-selectiescherm (Priority: P1) 🎯 MVP

**Goal**: De gebruiker kan vanuit het weekmenu naar een nieuw scherm navigeren, alle recept-ingrediënten per recept aan/uitvinken en hoeveelheden aanpassen, en vervolgens doorgaan naar de voorraadcheck.

**Independent Test**: Start het bestelproces vanuit het weekmenu en controleer dat het ingredient-selectiescherm verschijnt met alle recepten en ingrediënten, dat checkboxen en hoeveelheidsaanpassingen werken via HTMX, en dat "Verder naar voorraadcheck" redirect naar `/voorraad`.

### Tests voor User Story 1 (schrijf EERST — zorg dat ze FALEN vóór implementatie) ⚠️

- [X] T005 [P] [US1] Schrijf failing tests voor `GET /ingredient-selectie`: initialisatie vanuit `app.state.week_menu`, HTMX-fragment response, en bewaren bestaande selectie bij terug-navigatie in `tests/web/test_ingredient_selectie.py`
- [X] T006 [P] [US1] Schrijf failing tests voor `POST /ingredient-selectie/{item_id}/toggle`: toggling van `geselecteerd` in `app.state`, 404 bij onbekend id, en retour van ingredient_selectie_item.html fragment in `tests/web/test_ingredient_selectie.py`
- [X] T007 [P] [US1] Schrijf failing tests voor `PATCH /ingredient-selectie/{item_id}/hoeveelheid`: update van `hoeveelheid` in `app.state`, 404 bij onbekend id, en retour van bijgewerkt item-fragment in `tests/web/test_ingredient_selectie.py`
- [X] T008 [P] [US1] Schrijf failing test voor `POST /ingredient-selectie/bevestig`: verwacht 303 redirect naar `/voorraad`, en dat `app.state.ingredient_selectie` NIET gewist wordt (FR-011) in `tests/web/test_ingredient_selectie.py`

### Implementatie voor User Story 1

- [X] T009 [US1] Maak `src/boodschappenagent/web/routers/ingredient_selectie.py` aan met `GET /ingredient-selectie`: initialiseer `app.state.ingredient_selectie` als `list[dict]` vanuit `app.state.week_menu` (alleen als nog niet aanwezig of leeg); retourneert full page of HTMX-fragment op basis van `HX-Request` header; redirect 303 naar `/week` als `week_menu` ontbreekt
- [X] T010 [P] [US1] Maak `src/boodschappenagent/web/templates/pages/ingredient_selectie.html` aan: full page met header "Ingrediënten selecteren", back button → `/week`, receptgroepen met ingrediënten, en "Verder naar voorraadcheck" submit button
- [X] T011 [P] [US1] Maak `src/boodschappenagent/web/templates/fragments/ingredient_selectie_content.html` aan: HTMX-fragment (geen `<html>`-wrapper) met receptgroepen en ingrediëntenlijst — zelfde context als full page
- [X] T012 [US1] Maak `src/boodschappenagent/web/templates/components/ingredient_selectie_item.html` aan: checkbox (hx-post toggle), ingredientnaam, hoeveelheid-input (hx-patch hoeveelheid), eenheid; uitgegrijsd/doorgestreept styling wanneer `geselecteerd=False`; min. 44×44 pt touch targets
- [X] T013 [US1] Voeg `POST /ingredient-selectie/bevestig` endpoint toe aan `src/boodschappenagent/web/routers/ingredient_selectie.py` — **registreer deze route vóór de parametrische `/{item_id}`-routes** (FastAPI match-volgorde); laat `app.state.ingredient_selectie` intact; redirect 303 naar `/voorraad`
- [X] T014 [US1] Voeg `POST /ingredient-selectie/{item_id}/toggle` endpoint toe aan `src/boodschappenagent/web/routers/ingredient_selectie.py`: toggle `geselecteerd` in `app.state.ingredient_selectie`; retourneert `ingredient_selectie_item.html` component; 404 als `item_id` onbekend
- [X] T015 [US1] Voeg `PATCH /ingredient-selectie/{item_id}/hoeveelheid` endpoint toe aan `src/boodschappenagent/web/routers/ingredient_selectie.py`: update `hoeveelheid` (float) in `app.state.ingredient_selectie`; retourneert `ingredient_selectie_item.html` component; 404 als `item_id` onbekend

**Checkpoint**: User Story 1 is volledig functioneel en onafhankelijk testbaar via `uv run pytest tests/web/test_ingredient_selectie.py`

---

## Phase 3: User Story 2 — Bevestig-endpoint aggregeert recept-ingrediënten en voegt voorraadartikelen toe (Priority: P2)

**Goal**: Na de ingredient-selectie werkt de voorraadcheck ongewijzigd; na bevestiging worden de geselecteerde recept-ingrediënten geaggregeerd en samengevoegd met de voorraadartikelen tot één `Boodschappenlijst`.

**Independent Test**: Doorloop weekmenu → ingredient-selectie → voorraadcheck en controleer dat `POST /voorraad/bevestig` de geselecteerde ingrediënten correct aggregeert (hoeveelheden opgeteld per uniek ingredient), `voeg_pantry_toe()` aanroept, en de gecombineerde `Boodschappenlijst` gereed is voor matching.

### Tests voor User Story 2 (schrijf EERST — zorg dat ze FALEN vóór implementatie) ⚠️

- [X] T016 [P] [US2] Schrijf failing tests voor `voeg_pantry_toe(lijst)` methode: voegt VERS_BASIS en HOUDBAAR voorraadartikelen toe die niet al in de lijst zitten; voert stap 1 (filteren op voorraad) NIET uit in `tests/voorraadbeheer/test_filter.py`
- [X] T017 [P] [US2] Schrijf failing tests voor ingredient-aggregatielogica in `POST /voorraad/bevestig`: gelijke ingrediënten uit verschillende recepten worden samengevoegd (hoeveelheden opgeteld), niet-geselecteerde items worden weggelaten, `app.state.boodschappenlijst` bevat de gecombineerde regels in `tests/web/test_voorraadcheck.py`

### Implementatie voor User Story 2

- [X] T018 [US2] Implementeer `voeg_pantry_toe(self, lijst: Boodschappenlijst) -> Boodschappenlijst` op `BoodschappenlijstFilter` in `src/boodschappenagent/voorraadbeheer/filter.py`: kopieer stappen 2 en 3 van `filter_op_voorraad` (VERS_BASIS en HOUDBAAR toevoegen) zonder stap 1 (voorraad-filter)
- [X] T019 [US2] Implementeer aggregatielogica in `POST /voorraad/bevestig` in `src/boodschappenagent/web/routers/voorraad.py`: (1) lees `app.state.ingredient_selectie`, filter `geselecteerd=True`; (2) aggregeer per `(norm_naam, norm_eenheid)` via `IngredientNormalizer` (uit `boodschappenagent.boodschappenlijst.normalizer`, reeds aanwezig) en `PortionCalculator.round_quantity`; (3) maak `Boodschappenlijst`; (4) roep `BoodschappenlijstFilter.voeg_pantry_toe(lijst)` aan; (5) sla op in `app.state`

**Checkpoint**: User Stories 1 én 2 werken onafhankelijk; `tests/web/test_voorraadcheck.py` slaagt voor aggregatietests

---

## Phase 4: User Story 3 — Product matching start direct na voorraadcheck (Priority: P3)

**Goal**: Na bevestiging van de voorraadcheck wordt `AHIntegratie.zoek_producten()` direct aangeroepen op de gecombineerde boodschappenlijst en redirectt het systeem naar `/boodschappen/match-review` — geen tussenliggend scherm.

**Independent Test**: Doorloop de volledige flow en controleer dat na `POST /voorraad/bevestig` direct de match-review gestart wordt (redirect 303 naar `/boodschappen/match-review`), dat een lege gecombineerde lijst `ah_error.html` retourneert met `error_type=lege_lijst`, en dat de 003-match-review flow ongewijzigd werkt.

### Tests voor User Story 3 (schrijf EERST — zorg dat ze FALEN vóór implementatie) ⚠️

- [X] T020 [P] [US3] Schrijf failing test voor succesvolle bevestiging: `POST /voorraad/bevestig` met gevulde gecombineerde lijst redirectt 303 naar `/boodschappen/match-review` en slaat `match_review_items` op in `app.state` in `tests/web/test_voorraadcheck.py`
- [X] T021 [P] [US3] Schrijf failing test voor lege boodschappenlijst: `POST /voorraad/bevestig` met leeg `ingredient_selectie` én geen pantry-items retourneert 200 met `ah_error.html` en `error_type=lege_lijst` in `tests/web/test_voorraadcheck.py`
- [X] T022 [US3] Update `TestVoorraadBevestig.test_s8_1_redirect_naar_boodschappen` assertie: verwacht redirect naar `/boodschappen/match-review` (niet `/boodschappen`) in `tests/web/test_voorraadcheck.py`

### Implementatie voor User Story 3

- [X] T023 [US3] Breid `POST /voorraad/bevestig` uit in `src/boodschappenagent/web/routers/voorraad.py`: (1) AH auth check → redirect `/ah/login` bij ontbreken; (2) lege-lijst validatie → retourneer `ah_error.html` met `error_type=lege_lijst`; (3) roep `AHIntegratie.zoek_producten(lijst, voorkeuren_repo)` aan; (4) sla `match_review_items` op in `app.state`; (5) redirect 303 naar `/boodschappen/match-review` — voeg dependencies toe: `get_ah_token_manager`, `get_ah_integratie`, `get_match_voorkeuren_repository`
- [X] T024 [P] [US3] Voeg `lege_lijst` error_type toe aan `src/boodschappenagent/web/templates/pages/ah_error.html` met gebruikersvriendelijke melding dat de boodschappenlijst leeg is (was reeds aanwezig)

**Checkpoint**: Volledige flow is functioneel en getest; alle drie user stories werken end-to-end

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Afwerking en validatie die meerdere user stories raken.

- [X] T025 [P] Voeg E2E Playwright-test toe voor de volledige bestelflow (weekmenu → ingredient-selectie → voorraadcheck → match-review) in `tests/e2e/test_bestel_flow.py` (iPhone 13 viewport, 390×844)
- [X] T026 [P] Update `docs/implementatieplan-ui.md` met nieuwe werkstroom: Weekoverzicht → Ingredient-selectie → Voorraadcheck → Matching → Match-review
- [X] T027 Voer `uv run ruff check . && uv run ruff format .` uit en herstel eventuele linting-schendingen in gewijzigde bestanden
- [X] T033 Voer MINOR version bump uit in `.specify/memory/constitution.md`: (1) update Principle VI flow-volgorde naar "Weekoverzicht → Ingredient-selectie → Voorraadcheck → Matching → Match-review"; (2) verwijder "Boodschappenlijst" als aparte stap uit de vaste 6-stappen-reeks; (3) verhoog versie van 1.1.1 → 1.2.0; (4) voeg Sync Impact Report toe als HTML comment boven de constitutie

---

## Phase 6: Correcties na handmatig testen (FR-012, FR-013, navigatiebug)

**Purpose**: Drie problemen gevonden bij handmatig testen — weekmenu-wijziging reset niet, ingredient-selectie stijl wijkt af van /boodschappen, en back button op match-review gaat naar verkeerde pagina.

**Independent Test**: Handmatig doorlopen van de drie issues: (1) menu aanpassen en ingredient-selectie openen → selectie herstart; (2) ingredient-selectiescherm visueel gelijk aan /boodschappen; (3) back button op match-review → /voorraad.

### FR-012 — Weekmenu-wijziging reset ingredient-selectie

- [X] T028 [US1] Schrijf failing test in `tests/web/test_ingredient_selectie.py`: `GET /ingredient-selectie` met bestaande `app.state.ingredient_selectie` (gebouwd uit oud menu) maar gewijzigd `app.state.week_menu` (andere receptenset) → verwacht dat `ingredient_selectie` volledig gereset wordt en opnieuw gebouwd wordt vanuit het nieuwe weekmenu
- [X] T029 [US1] Implementeer weekmenu-wijzigingsdetectie in `GET /ingredient-selectie` handler in `src/boodschappenagent/web/routers/ingredient_selectie.py`: vergelijk de set van `recept_naam`-waarden in `app.state.ingredient_selectie` met de set van receptnamen in `app.state.week_menu`; als deze sets niet overeenkomen → reset `app.state.ingredient_selectie` en herbouw volledig vanuit `app.state.week_menu` (alle items `geselecteerd=True`)

### FR-009 — Back button match-review → /voorraad

- [X] T030 [US3] Schrijf failing test: controleer dat de `GET /boodschappen/match-review` pagina een back button bevat met `href="/voorraad"` (niet `/boodschappen`) in `tests/web/test_boodschappen.py` of `tests/e2e/test_bestel_flow.py`
- [X] T031 [US3] Update back button in `src/boodschappenagent/web/templates/pages/match_review.html`: wijzig `href` van `/boodschappen` naar `/voorraad` zodat terugnavigatie vanuit match-review correct naar de voorraadcheck gaat (conform FR-009 terugnavigatiestroom)

### FR-013 — Ingredient-selectie gebruikt zelfde componenten als /boodschappen

- [X] T032a [US1] Schrijf failing test in `tests/web/test_ingredient_selectie.py`: render het `ingredient_selectie_item.html` fragment voor een testitem en controleer dat het exact dezelfde Tailwind-klassen op checkbox-input en hoeveelheid-input bevat als het overeenkomstige boodschappenlijst-item-component (bijv. via BeautifulSoup-assertions op CSS-klassen en HTMX-attributen)
- [X] T032 [P] [US1] Inspecteer `src/boodschappenagent/web/templates/components/` en `src/boodschappenagent/web/templates/pages/boodschappen.html` voor de exacte checkbox-markup en hoeveelheden-selector; pas `src/boodschappenagent/web/templates/components/ingredient_selectie_item.html` aan zodat checkbox-input en hoeveelheid-input exact dezelfde Tailwind-klassen, input-types en HTMX-attributen gebruiken als het bestaande boodschappenlijst-item-component

### FR-013 Clarificatie (2026-05-16) — +/- knoppen met dynamische stapgrootte

**Context**: Na clarificatie sessie van 2026-05-16 is FR-013 preciezer gespecificeerd. De huidige `ingredient_selectie_item.html` gebruikt `<input type="number" step="any">` — dit moet vervangen worden door dezelfde grote ronde `-`/`+`-knoppen als `boodschapitem.html`, inclusief dynamische stapgrootte en disabled-state.

**Stapgrootte-logica** (uit `boodschapitem.html`):
- gram/ml: 25 onder 500; 100 vanaf 500
- lepel (eenheid bevat "lepel"): 0.5
- overig: 1
- Minimum hoeveelheid = 1 stapgrootte (minus-knop `disabled` aan ondergrens)
- Geen recept-sublabel ("voor [recept]") — items zijn al per recept gegroepeerd

- [ ] T035 [US1] Schrijf failing tests in `tests/web/test_ingredient_selectie.py` voor de geclarificeerde +/- UI: (1) controleer dat de rendered `ingredient_selectie_item.html` géén `<input type="number">` bevat maar wél twee `<button>`-elementen voor `-` en `+`; (2) controleer dat bij eenheid "gram" en hoeveelheid 200 de `hx-vals` van de minus-knop `{"hoeveelheid": "175"}` bevat (stap 25); (3) controleer dat bij hoeveelheid ≤ stapgrootte de minus-knop het `disabled`-attribuut heeft; (4) controleer dat er geen recept-sublabel in de rendered HTML staat
- [ ] T036 [US1] Update `src/boodschappenagent/web/templates/components/ingredient_selectie_item.html`: vervang `<input type="number">` + eenheid-span door de +/- button-layout uit `boodschapitem.html` — `stap_minus`/`stap_plus` berekening (gram/ml: 25/100 op 500-grens; lepel: 0.5; overig: 1); `hoeveelheid_minus`/`hoeveelheid_plus` pre-computatie; grote ronde knoppen (`w-9 h-9 rounded-full`) met `hx-patch="/ingredient-selectie/{{ item.id }}/hoeveelheid"` en `hx-vals`; hoeveelheid als `<span>` (niet input); minus-knop `disabled` wanneer `hoeveelheid <= stap_minus`; geen recept-sublabel

### Edge Case — Leeg weekmenu (geen recepten)

- [X] T034 [US1] Schrijf failing tests in `tests/web/test_ingredient_selectie.py` voor weekmenu zonder recepten (bijv. alleen 'niet-thuis'-dagen): `GET /ingredient-selectie` → `app.state.ingredient_selectie = []`, scherm laadt zonder redirect; `POST /ingredient-selectie/bevestig` → redirect 303 naar `/voorraad` (lege selectie is geldig); `POST /voorraad/bevestig` met alleen voorraadartikelen en lege recept-selectie → succesvol redirect naar `/boodschappen/match-review`

**Checkpoint**: Alle issues opgelost; full flow hertest met handmatige validatie

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Geen afhankelijkheden — start direct
- **User Story 1 (Phase 2)**: Vereist Phase 1 compleet — blokkeert US2 en US3
- **User Story 2 (Phase 3)**: Vereist US1 compleet (T015 aanwezig); US2 en US3 kunnen daarna parallel
- **User Story 3 (Phase 4)**: Vereist US2 compleet (aggregatielogica aanwezig)
- **Polish (Phase 5)**: Vereist US3 compleet
- **Correcties (Phase 6)**: Vereist US1 compleet (T028/T029/T032a/T032/T034 raken ingredient-selectie); US3 compleet (T030/T031 raken match-review)
- **Constitution (T033, onderdeel van Phase 5)**: Vereist volledige implementatie (Phases 1–4) — voer uit vóór merge naar main

### User Story Dependencies

- **US1 (P1)**: Start na Phase 1 — geen afhankelijkheid van andere stories
- **US2 (P2)**: Start na US1 — voegt aggregatielogica toe aan `POST /voorraad/bevestig`
- **US3 (P3)**: Start na US2 — voegt matching + redirect toe aan `POST /voorraad/bevestig`

### Binnen elke User Story

- Tests MOETEN geschreven en FAILEND zijn vóór implementatie (TDD red step)
- Templates kunnen parallel aan router-logica geschreven worden (verschillende bestanden)
- `ingredient_selectie_item.html` (T012) vereist dat T010/T011 de context-structuur bepalen
- `POST /ingredient-selectie/bevestig` (T013) moet in code vóór `/{item_id}/toggle` (T014) geregistreerd zijn

### Route-registratie volgorde in ingredient_selectie.py (KRITISCH)

FastAPI matcht routes op definitievolgorde. Verplichte volgorde:
1. `POST /ingredient-selectie/bevestig` (T013) — specifiek
2. `POST /ingredient-selectie/{item_id}/toggle` (T014) — parametrisch
3. `PATCH /ingredient-selectie/{item_id}/hoeveelheid` (T015) — parametrisch

---

## Parallel Opportunities

### Phase 1 (geen parallel — sequentieel)

T001 → T002 → T003 → T004 (T002 en T004 kunnen parallel na T001)

### User Story 1

```bash
# Schrijf tests parallel (T005, T006, T007, T008 — allemaal in test_ingredient_selectie.py):
Task: "GET /ingredient-selectie tests"       # T005
Task: "toggle endpoint tests"                # T006
Task: "hoeveelheid endpoint tests"           # T007
Task: "bevestig endpoint test"               # T008

# Maak templates parallel aan router (verschillende bestanden):
Task: "ingredient_selectie.py router (T009)" 
Task: "ingredient_selectie.html (T010)"
Task: "ingredient_selectie_content.html (T011)"
Task: "ingredient_selectie_item.html (T012)"
```

### User Story 2

```bash
# Tests parallel:
Task: "voeg_pantry_toe tests (T016)"
Task: "aggregatie tests in test_voorraadcheck (T017)"

# Implementatie sequentieel (T019 vereist T018):
Task: "voeg_pantry_toe() methode (T018)" → "aggregatie in POST /voorraad/bevestig (T019)"
```

### User Story 3

```bash
# Tests parallel (T020, T021 — zelfde bestand, maar onafhankelijke test cases):
Task: "matching redirect test (T020)"
Task: "lege lijst test (T021)"
Task: "Update S8.1 assertie (T022)" + "ah_error.html lege_lijst (T024)"  # parallel
```

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Voltooi Phase 1: Setup
2. Voltooi Phase 2: User Story 1 (ingredient-selectiescherm)
3. **STOP en VALIDEER**: Test US1 onafhankelijk — `uv run pytest tests/web/test_ingredient_selectie.py`
4. Demo: gebruiker kan weekmenu → ingredient-selectie → (handmatig naar /voorraad) doorlopen

### Incremental Delivery

1. Phase 1 → foundation klaar (bestaande tests groen)
2. Phase 2 (US1) → ingredient-selectiescherm werkt → demo/valideer
3. Phase 3 (US2) → aggregatie + voorraadartikelen werkt → deel van flow testbaar
4. Phase 4 (US3) → volledige flow werkend → e2e valideer
5. Phase 5 → polish en afronden

---

## Notes

- [P] = verschillende bestanden, geen onderlinge afhankelijkheden in die fase
- [US1]/[US2]/[US3] label traceert taak naar user story
- TDD: tests MOETEN FALEN vóór implementatie — nooit groen beginnen
- Hanteer `app.state.ingredient_selectie` als `list[dict]` (niet als frozen dataclass) conform bestaand `app.state.boodschappenlijst` patroon
- Route-volgorde in ingredient_selectie.py is kritisch: `bevestig` vóór `{item_id}/toggle`
- Constitution update (MINOR versie-bump): zie T033 in Phase 5 — uitvoeren vóór merge naar main
- `IngredientNormalizer` is reeds aanwezig in `boodschappenagent.boodschappenlijst.normalizer`
