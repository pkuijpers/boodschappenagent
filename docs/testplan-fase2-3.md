# Testplan: Fase 2 & 3 — Voorraadcheck & Boodschappenlijst

**Versie:** 1.0
**Datum:** 2026-03-03
**Bron:** `ui-ontwerp-albert.md` (scherm 5.3 & 5.4), `implementatieplan-ui.md` (fase 2 & 3)

## Doel

Dit testplan beschrijft de integratietests voor de volgende twee fasen van de UI:

1. **Fase 2 — Voorraadcheck** (scherm 5.3): "Heb je nog...?" Ja/Nee per product
2. **Fase 3 — Boodschappenlijst** (scherm 5.4): Geaggregeerde boodschappenlijst met secties

Deze fasen volgen direct op het voltooide weekoverzicht (fase 1). De backend modules (`boodschappenlijst`, `voorraadbeheer`) bestaan al — dit plan focust op de **web-laag** (routes, templates, HTMX-interacties).

---

## User flow

```
Weekoverzicht (fase 1, done)
        │
        │  "Verder naar boodschappen →"
        ▼
┌───────────────────────────────┐
│     VOORRAADCHECK (fase 2)   │
│  Houdbare producten: Ja/Nee  │
│  Verse basics: Ja/Nee        │
│  "Naar boodschappenlijst →"  │
└───────────────────────────────┘
        │
        ▼
┌───────────────────────────────┐
│   BOODSCHAPPENLIJST (fase 3) │
│  Secties: Vlees, Zuivel, ... │
│  Checkbox per item            │
│  + Handmatig toevoegen        │
│  "Verstuur naar AH →"        │
└───────────────────────────────┘
```

---

## Integratiegrenzen

```
┌─────────────┐     ┌────────────────────┐     ┌──────────────────────┐
│ WeekMenu    │────▶│ BoodschappenlijstGen│────▶│ Web: /voorraad       │
│ (app.state) │     │ + VoorraadChecker   │     │ Web: /boodschappen   │
└─────────────┘     └────────────────────┘     └──────────────────────┘
                           ▲                           ▲
                           │                           │
                    VoorraadRepository           HTMX swap/target
                    (JSON persistentie)          fragment vs full page
```

| Grens | Wat kan misgaan |
|-------|-----------------|
| WeekMenu → Generator | Ingrediënten niet geaggregeerd, verkeerde portie-schaling, HelloFresh/niet-thuis dagen meegeteld |
| Generator → Voorraad UI | Verkeerde groepering (houdbaar vs vers), items die op voorraad zijn toch getoond |
| Voorraad → Boodschappen | Voorraadstatus niet meegenomen, verse basics ontbreken, dubbele items |
| Boodschappen UI → Mutatie | Checkbox toggle werkt niet, handmatig toevoegen mislukt, hoeveelheid niet correct |

---

## Nieuwe routes

### Fase 2: Voorraadcheck

| Endpoint | Method | Doel |
|----------|--------|------|
| `/voorraad` | GET | Voorraadcheck pagina met suggesties gegroepeerd op type |
| `/voorraad/{item}/status` | POST | Toggle Ja/Nee voor een voorraaditem (HTMX swap) |
| `/voorraad/bevestig` | POST | Batch-update voorraad, redirect naar `/boodschappen` |

### Fase 3: Boodschappenlijst

| Endpoint | Method | Doel |
|----------|--------|------|
| `/boodschappen` | GET | Boodschappenlijst pagina met secties |
| `/boodschappen/{item_id}` | PATCH | Toggle checked (HTMX swap) |
| `/boodschappen/{item_id}` | DELETE | Verwijder van lijst (HTMX swap out) |
| `/boodschappen/toevoegen` | POST | Handmatig product toevoegen (HTMX append) |
| `/boodschappen/{item_id}/hoeveelheid` | PATCH | Hoeveelheid aanpassen |

---

## Nieuwe templates

```
templates/
    pages/
        voorraad.html          # 5.3 Voorraadcheck
        boodschappen.html      # 5.4 Boodschappenlijst
    components/
        voorraaditem.html      # Ja/Nee toggle per item
        boodschapitem.html     # Checkbox + naam + hoeveelheid
```

---

## Nieuwe dependencies (web/dependencies.py)

```python
def get_voorraad_repository() -> VoorraadRepository:
    """VoorraadRepository met data/voorraad.json."""

def get_boodschappenlijst_generator() -> BoodschappenlijstGenerator:
    """Generator met IngredientNormalizer en PortionCalculator."""

def get_voorraad_checker() -> VoorraadChecker:
    """VoorraadChecker met VoorraadRepository."""

def get_boodschappenlijst_filter() -> BoodschappenlijstFilter:
    """BoodschappenlijstFilter met VoorraadRepository."""
```

---

## Testscenario's

### S6: Voorraadcheck laden (WeekMenu → VoorraadChecker → UI)

**Integratietest (TestClient)**

| # | Scenario | Input | Verwacht resultaat | Selector |
|---|----------|-------|--------------------|----------|
| S6.1 | Voorraadcheck toont twee secties | GET `/voorraad` met weekmenu + voorraad-items | Twee secties: "Houdbare producten" en "Verse basics" | `[data-testid="sectie-houdbaar"]`, `[data-testid="sectie-vers"]` |
| S6.2 | Houdbare items uit weekmenu | GET `/voorraad`, weekmenu bevat pasta-recept | "pasta" verschijnt als houdbaar item met context "(voor Spaghetti Bolognese)" | `[data-testid="voorraaditem"]` |
| S6.3 | Verse basics altijd zichtbaar | GET `/voorraad` | Verse basics (melk, eieren, boter, kaas, etc.) altijd getoond, ongeacht weekmenu | `[data-testid="sectie-vers"] [data-testid="voorraaditem"]` |
| S6.4 | Standaard Nee (niet op voorraad) | GET `/voorraad` | Elk item heeft standaard "Nee" actief (veilige default) | `[data-testid="voorraaditem"] [data-testid="status-nee"][data-actief="true"]` |
| S6.5 | Items met bestaande voorraad | GET `/voorraad`, pasta op voorraad in repository | "pasta" toont "Ja" als actief | `[data-testid="status-ja"][data-actief="true"]` |
| S6.6 | Zonder weekmenu → redirect | GET `/voorraad` zonder week_menu op app.state | Redirect naar `/week` (eerst menu maken) | — |
| S6.7 | Lege voorraad | GET `/voorraad`, geen items in VoorraadRepository | Toont minimaal verse basics (standaard suggesties) | `[data-testid="sectie-vers"]` |

**Twee varianten per endpoint:**

| # | Variant | Headers | Verwacht |
|---|---------|---------|----------|
| S6.1a | Browser (full page) | geen | Volledige HTML met `<html>`, tab-bar, header "Voorraadcheck" |
| S6.1b | HTMX (fragment) | `HX-Request: true` | HTML-fragment zonder `<html>` wrapper |

### S7: Voorraad status toggle (UI → VoorraadRepository → UI)

**Integratietest (TestClient)**

| # | Scenario | Input | Verwacht resultaat | Selector |
|---|----------|-------|--------------------|----------|
| S7.1 | Toggle Ja (op voorraad) | POST `/voorraad/pasta/status` met `op_voorraad=true` | Item update: "Ja" actief, "Nee" inactief; repository opgeslagen | `[data-testid="voorraaditem"][data-item="pasta"]` |
| S7.2 | Toggle Nee (niet op voorraad) | POST `/voorraad/pasta/status` met `op_voorraad=false` | Item update: "Nee" actief, "Ja" inactief | `[data-testid="voorraaditem"][data-item="pasta"]` |
| S7.3 | HTMX swap van enkel item | POST `/voorraad/pasta/status` | Response bevat precies 1 voorraaditem (niet hele pagina) | `[data-testid="voorraaditem"]` (count=1) |
| S7.4 | Onbekend item → 404 | POST `/voorraad/onbekend-item/status` | HTTP 404 | — |
| S7.5 | Zonder weekmenu → 404 | POST, geen week_menu | HTTP 404 | — |

### S8: Voorraad bevestigen (batch update → redirect)

**Integratietest (TestClient)**

| # | Scenario | Input | Verwacht resultaat |
|---|----------|-------|--------------------|
| S8.1 | Bevestig voorraad → redirect | POST `/voorraad/bevestig` | HTTP 303 redirect naar `/boodschappen` |
| S8.2 | Alle statussen opgeslagen | POST `/voorraad/bevestig` na Ja/Nee toggles | VoorraadRepository bevat correcte op_voorraad waarden |
| S8.3 | Zonder weekmenu → redirect | POST `/voorraad/bevestig`, geen week_menu | Redirect naar `/week` |

---

### S9: Boodschappenlijst laden (WeekMenu → Generator → Filter → UI)

**Integratietest (TestClient)**

| # | Scenario | Input | Verwacht resultaat | Selector |
|---|----------|-------|--------------------|----------|
| S9.1 | Lijst toont secties | GET `/boodschappen` met weekmenu | Meerdere secties zichtbaar (bijv. "Vlees & vis", "Zuivel", "Groente & fruit") | `[data-testid="boodschappen-sectie"]` |
| S9.2 | Ingrediënten geaggregeerd | GET `/boodschappen`, 2 recepten met ui | "ui" verschijnt 1x met opgetelde hoeveelheid (bijv. "4 stuks") | `[data-testid="boodschapitem"]` |
| S9.3 | HelloFresh-dagen uitgesloten | GET `/boodschappen`, dag 2 = HelloFresh | Ingrediënten van dag 2 niet in de lijst | Programmatisch |
| S9.4 | Niet-thuis dagen uitgesloten | GET `/boodschappen`, dag 5 = niet-thuis | Ingrediënten van dag 5 niet in de lijst | Programmatisch |
| S9.5 | Porties correct geschaald | GET `/boodschappen`, dag 0 = 4 personen (recept voor 2) | Hoeveelheden verdubbeld t.o.v. basisportie | Programmatisch |
| S9.6 | Op-voorraad items gefilterd | GET `/boodschappen`, pasta op voorraad | "pasta" niet in de lijst | Programmatisch |
| S9.7 | Verse basics toegevoegd | GET `/boodschappen`, melk niet op voorraad | "melk" verschijnt in de lijst (1 liter) | `[data-testid="boodschapitem"][data-item="melk"]` |
| S9.8 | Aantal producten in header | GET `/boodschappen` | Header toont "Week X · N producten" | `[data-testid="boodschappen-header"]` |
| S9.9 | Zonder weekmenu → redirect | GET `/boodschappen` zonder week_menu | Redirect naar `/week` | — |
| S9.10 | Lege lijst (alles op voorraad) | GET `/boodschappen`, alles op voorraad | Lege-staat bericht ("Niets te bestellen!") | `[data-testid="lege-lijst"]` |

**Twee varianten per endpoint:**

| # | Variant | Headers | Verwacht |
|---|---------|---------|----------|
| S9.1a | Browser (full page) | geen | Volledige HTML met `<html>`, tab-bar, header "Boodschappenlijst" |
| S9.1b | HTMX (fragment) | `HX-Request: true` | HTML-fragment zonder `<html>` wrapper |

### S10: Boodschappenlijst interacties (UI → mutatie → UI)

**Integratietest (TestClient)**

| # | Scenario | Input | Verwacht resultaat | Selector |
|---|----------|-------|--------------------|----------|
| S10.1 | Toggle checked | PATCH `/boodschappen/{item_id}` met `checked=true` | Item krijgt checked styling (doorgestreept) | `[data-testid="boodschapitem"][data-checked="true"]` |
| S10.2 | Toggle unchecked | PATCH `/boodschappen/{item_id}` met `checked=false` | Item is weer normaal | `[data-testid="boodschapitem"][data-checked="false"]` |
| S10.3 | HTMX swap van enkel item | PATCH `/boodschappen/{item_id}` | Response bevat precies 1 boodschapitem | `[data-testid="boodschapitem"]` (count=1) |
| S10.4 | Verwijder item | DELETE `/boodschappen/{item_id}` | Leeg response (HTMX swap-out verwijdert element) | — |
| S10.5 | Handmatig toevoegen | POST `/boodschappen/toevoegen` met `naam=bananen&hoeveelheid=6&eenheid=stuks` | Nieuw item verschijnt in response | `[data-testid="boodschapitem"][data-item="bananen"]` |
| S10.6 | Handmatig toevoegen zonder naam → 422 | POST `/boodschappen/toevoegen` met lege naam | HTTP 422 | — |
| S10.7 | Hoeveelheid aanpassen | PATCH `/boodschappen/{item_id}/hoeveelheid` met `hoeveelheid=8` | Item toont nieuwe hoeveelheid | `[data-testid="boodschapitem"] [data-testid="hoeveelheid"]` |
| S10.8 | Onbekend item → 404 | PATCH `/boodschappen/onbekend-id` | HTTP 404 | — |
| S10.9 | Producttelling update na verwijdering | DELETE `/boodschappen/{item_id}` | OOB update van header met nieuwe count | `[data-testid="boodschappen-header"]` |
| S10.10 | Producttelling update na toevoegen | POST `/boodschappen/toevoegen` | OOB update van header met nieuwe count | `[data-testid="boodschappen-header"]` |

---

## S11: Navigatie tussen fasen

**Integratietest (TestClient)**

| # | Scenario | Input | Verwacht resultaat | Selector |
|---|----------|-------|--------------------|----------|
| S11.1 | Week → Voorraad link | GET `/week` | "Verder naar boodschappen" link wijst naar `/voorraad` | `[data-testid="verder-button"]` |
| S11.2 | Voorraad → Boodschappen link | GET `/voorraad` | "Naar boodschappenlijst" link/knop aanwezig | `[data-testid="naar-boodschappen-button"]` |
| S11.3 | Boodschappen → AH link | GET `/boodschappen` | "Verstuur naar AH" knop aanwezig | `[data-testid="verstuur-naar-ah-button"]` |
| S11.4 | Boodschappen ← Terug naar voorraad | GET `/boodschappen` | "Terug" link wijst naar `/voorraad` | `a[href="/voorraad"]` |
| S11.5 | Voorraad ← Terug naar week | GET `/voorraad` | "Terug" link wijst naar `/week` | `a[href="/week"]` |

---

## E2E scenario's (Playwright)

| # | Scenario | Stappen | Verificatie |
|---|----------|---------|-------------|
| E8 | Voorraadcheck laden | Navigeer naar `/voorraad` | Twee secties zichtbaar, items met Ja/Nee toggles |
| E9 | Voorraad toggle | Tap "Ja" op een item | Button highlight wisselt naar "Ja", geen page reload |
| E10 | Voorraad → Boodschappen flow | Toggle items → tap "Naar boodschappenlijst" | Boodschappenlijst toont gefilterde items (voorraad-items uitgesloten) |
| E11 | Boodschappenlijst laden | Navigeer naar `/boodschappen` | Secties zichtbaar, items met checkbox en hoeveelheid |
| E12 | Boodschap afvinken | Tap checkbox op een item | Item krijgt doorgestreept styling, geen page reload |
| E13 | Product handmatig toevoegen | Tap "+ Voeg product toe" → vul naam/hoeveelheid in → bevestig | Nieuw item verschijnt in "Handmatig toegevoegd" sectie |
| E14 | Volledige flow: Week → Voorraad → Boodschappen | Start op `/week` → "Verder" → toggle voorraad → "Naar boodschappenlijst" → controleer lijst | Boodschappenlijst klopt: voorraad-items uitgesloten, hoeveelheden correct, verse basics aanwezig |

**Wachtstrategie:** `page.wait_for_selector()` na elke HTMX-interactie om DOM-updates af te wachten.

---

## Data-testid contract

Nieuwe `data-testid` attributen voor fase 2 & 3:

| Selector | Element | Gebruikt in |
|----------|---------|-------------|
| `[data-testid="sectie-houdbaar"]` | Houdbare producten sectie | S6.1, E8 |
| `[data-testid="sectie-vers"]` | Verse basics sectie | S6.1, S6.3, S6.7, E8 |
| `[data-testid="voorraaditem"]` | Voorraaditem container | S6.2, S6.3, S7.3, E9 |
| `[data-testid="voorraaditem"][data-item="X"]` | Voorraaditem voor specifiek product | S7.1, S7.2 |
| `[data-testid="status-ja"]` | "Ja" toggle button | S6.5, S7.1, E9 |
| `[data-testid="status-nee"]` | "Nee" toggle button | S6.4, S7.2, E9 |
| `[data-testid="status-ja"][data-actief="true"]` | Actieve "Ja" toggle | S6.5 |
| `[data-testid="status-nee"][data-actief="true"]` | Actieve "Nee" toggle | S6.4 |
| `[data-testid="naar-boodschappen-button"]` | "Naar boodschappenlijst" knop | S8.1, S11.2, E10 |
| `[data-testid="boodschappen-header"]` | Header met "Week X · N producten" | S9.8, S10.9, S10.10 |
| `[data-testid="boodschappen-sectie"]` | Boodschappenlijst sectie container | S9.1, E11 |
| `[data-testid="boodschapitem"]` | Boodschapitem container | S9.2, S10.3, E12 |
| `[data-testid="boodschapitem"][data-item="X"]` | Boodschapitem voor specifiek product | S9.7, S10.5 |
| `[data-testid="boodschapitem"][data-checked="true"]` | Afgevinkt boodschapitem | S10.1, E12 |
| `[data-testid="boodschapitem"][data-checked="false"]` | Niet-afgevinkt boodschapitem | S10.2 |
| `[data-testid="hoeveelheid"]` | Hoeveelheid in boodschapitem | S10.7 |
| `[data-testid="voeg-toe-button"]` | "+ Voeg product toe" knop | S10.5, E13 |
| `[data-testid="verstuur-naar-ah-button"]` | "Verstuur naar AH" knop | S11.3 |
| `[data-testid="lege-lijst"]` | Lege-staat boodschappenlijst | S9.10 |
| `[data-testid="verder-button"]` | "Verder naar boodschappen" link (week pagina) | S11.1 |

---

## Test fixtures

### Integratietests: `tests/web/conftest.py` — uitbreidingen

```python
@pytest.fixture
def voorraad_repository(tmp_path) -> VoorraadRepository:
    """VoorraadRepository op tmp_path (geen echte voorraad.json)."""

@pytest.fixture
def voorraad_met_pasta(voorraad_repository) -> VoorraadRepository:
    """VoorraadRepository met pasta op voorraad."""

@pytest.fixture
def boodschappenlijst_generator() -> BoodschappenlijstGenerator:
    """Echte BoodschappenlijstGenerator met IngredientNormalizer."""

@pytest.fixture
def boodschappenlijst_filter(voorraad_repository) -> BoodschappenlijstFilter:
    """BoodschappenlijstFilter met gemockte voorraad."""

@pytest.fixture
def app_with_voorraad(app_with_overrides, voorraad_repository):
    """App met dependency_overrides voor VoorraadRepository."""
```

---

## Mocking strategie

### Niet mocken (echt draaien)

| Dependency | Toelichting |
|------------|-------------|
| `BoodschappenlijstGenerator` | Echte aggregatie + normalisatie. Test de volledige keten van WeekMenu → Boodschappenlijst. |
| `IngredientNormalizer` | Echte synoniemen. Test dat "uien" → "ui" correct werkt door de keten heen. |
| `PortionCalculator` | Echte afronding. Test dat 2.5 stuks → 3 stuks correct wordt afgerond. |
| `BoodschappenlijstFilter` | Echte filtering. Test dat op-voorraad items correct worden uitgesloten. |

### Wel mocken (user-generated data)

| Dependency | Mock methode | Toelichting |
|------------|-------------|-------------|
| `VoorraadRepository` | `app.dependency_overrides[get_voorraad_repository]` | In-memory repository (geen disk I/O). |
| `WeekMenu` (huidig menu) | `app.state.week_menu` | Testdata op app state (zoals in fase 1). |
| `Boodschappenlijst` (huidige lijst) | `app.state.boodschappenlijst` | In-memory state voor mutaties (toggle, verwijder, toevoegen). |

---

## Assertie-conventies

Identiek aan fase 1 testplan:

1. **CSS selectors** gebaseerd op `data-testid` en `data-*` attributen
2. **BeautifulSoup** voor HTML parsing in integratietests
3. **HTMX fragment check:** response bevat geen `<html>` tag bij HTMX requests
4. **Full page check:** response bevat `<html>`, Tailwind CDN link, HTMX script tag

---

## Implementatievolgorde

1. **Dependencies opzetten** — `web/dependencies.py` uitbreiden met voorraad/boodschappen factories
2. **S11.1: Navigatie link updaten** — "Verder naar boodschappen" wijst naar `/voorraad` i.p.v. `/boodschappen`
3. **S6: Voorraadcheck pagina** — Route `GET /voorraad` + template `voorraad.html` + component `voorraaditem.html`
4. **S7: Voorraad toggle** — Route `POST /voorraad/{item}/status` + HTMX swap
5. **S8: Voorraad bevestigen** — Route `POST /voorraad/bevestig` + redirect
6. **S9: Boodschappenlijst pagina** — Route `GET /boodschappen` + template `boodschappen.html` + component `boodschapitem.html`
7. **S10.1-S10.3: Toggle checked** — Route `PATCH /boodschappen/{item_id}`
8. **S10.4: Verwijder item** — Route `DELETE /boodschappen/{item_id}`
9. **S10.5-S10.6: Handmatig toevoegen** — Route `POST /boodschappen/toevoegen`
10. **S10.7: Hoeveelheid aanpassen** — Route `PATCH /boodschappen/{item_id}/hoeveelheid`
11. **S10.9-S10.10: OOB header updates** — Producttelling update bij mutaties
12. **E8-E14: Playwright** — E2E tests voor HTMX interacties

**Testbestanden:**
- Nieuw: `tests/web/test_voorraadcheck.py` (S6, S7, S8)
- Nieuw: `tests/web/test_boodschappenlijst.py` (S9, S10)
- Nieuw: `tests/web/test_navigatie.py` (S11)
- Nieuw: `tests/e2e/test_voorraadcheck.py` (E8, E9, E10)
- Nieuw: `tests/e2e/test_boodschappenlijst.py` (E11, E12, E13)
- Nieuw: `tests/e2e/test_volledige_flow.py` (E14)

---

## Wat niet in scope is

- AH-integratie (fase 4 — apart testplan)
- Kookmodus (fase 5 — apart testplan)
- Instellingen (fase 6 — apart testplan)
- Performance tests
- Accessibility tests
- Visuele regressie tests
- Secties/categorieën toewijzen aan ingrediënten (bijv. "Vlees & vis") — vereist een mapping die nog ontworpen moet worden
