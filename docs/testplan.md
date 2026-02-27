# Testplan: End-to-end integratietests

**Versie:** 1.1 — bijgewerkt voor UI v1.2 (dag aanpassen flow)

## Doel

Dit testplan beschrijft de integratietests die de samenwerking tussen modules valideren. De individuele modules (planner, repository, modellen) hebben al uitgebreide unit tests (440+). Dit plan focust op de **end-to-end flows** waarbij meerdere modules samenwerken om een gebruikersactie te voltooien.

## Eerste scope: weekmenu samenstellen

De eerste feature die end-to-end getest wordt is het samenstellen van een weekmenu. De gebruikersflow:

1. Gebruiker opent `/week` → ziet automatisch gegenereerd weekmenu
2. Gebruiker tapt op een dagkaart → dag-aanpassen sheet opent
3. Gebruiker wijzigt dagtype (Geen menu / Recept / HelloFresh)
4. Gebruiker past het aantal personen aan (2/3/4)
5. Gebruiker tikt "Ander recept" → variety-aware alternatief verschijnt
6. Gebruiker klikt 🔀 Shuffle → volledig nieuw weekvoorstel

---

## Testlagen

### Laag 1: Integratie (FastAPI TestClient)

Hoofdmoot van de tests. Gebruikt `TestClient` (geen draaiende server). Leest echte recepten uit de `data/recipes/` directory. User-generated data (history, weekmenu) wordt gemockt via `app.dependency_overrides`. Test de volledige keten van HTTP request → route → service → template rendering → HTML response.

**Tooling:** `pytest`, `FastAPI TestClient`, `BeautifulSoup`, `app.dependency_overrides`

### Laag 2: E2E (Playwright)

Beperkt tot flows die HTMX-interactie in de browser vereisen (DOM swaps, dynamische updates). Draait tegen een live server.

**Tooling:** `pytest`, `Playwright`, `pytest-playwright`

---

## Integratiegrenzen

Drie kritieke grenzen die getest moeten worden:

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│ Repository  │────▶│  MenuPlanner │────▶│  Web (HTML)  │
│ (recepten)  │     │  (selectie)  │     │  (templates) │
└─────────────┘     └──────────────┘     └─────────────┘
      ▲                    ▲                     ▲
      │                    │                     │
  seizoensfilter     variatie-logica      HTMX swap/target
  JSON laden         history check        fragment vs full page
```

| Grens | Wat kan misgaan |
|-------|-----------------|
| Repository → Planner | Verkeerde seizoensfilter, lege receptenlijst, corrupt JSON |
| Planner → UI | Recept-data niet correct in template, verkeerde dagtype, ontbrekende emoji |
| UI → Planner (mutatie) | Shuffle POST geeft verkeerd fragment terug, state raakt out-of-sync, porties niet correct doorgerekend |

---

## Testscenario's

### S1: Weekmenu genereren (Repository → Planner → UI)

**Integratietest (TestClient)**

| # | Scenario | Input | Verwacht resultaat | Selector |
|---|----------|-------|--------------------|----------|
| S1.1 | Volledig weekmenu laden | GET `/week` met 7 dagen, alle thuis | 7 dagkaarten type `recept`, elk met receptnaam, porties, categorie-emoji | `[data-testid="dagkaart"][data-type="recept"]` |
| S1.2 | Menu met niet-thuis dagen | GET `/week`, dag 5 personen=0 | Dagkaart type `niet-thuis` zonder receptnaam | `[data-testid="dagkaart"][data-type="niet-thuis"]` |
| S1.3 | Menu met HelloFresh dag | GET `/week`, dag 2 in hellofresh_dagen | Dagkaart type `hellofresh` met HelloFresh styling | `[data-testid="dagkaart"][data-type="hellofresh"]` |
| S1.4 | Weeknummer correct | GET `/week` met week_start `2026-02-16` | Weeknummer 8 zichtbaar | `[data-testid="week-nummer"]` (toe te voegen) |
| S1.5 | Variatie: geen dubbele categorieën | GET `/week`, 5+ kookdagen | Geen twee opeenvolgende dagen met dezelfde categorie | Programmatisch: parse categorie per dagkaart |
| S1.6 | Leeg menu (geen recepten) | GET `/week` zonder week_menu | Lege staat / uitnodiging om menu te genereren | nader te bepalen |

**Twee varianten per endpoint:**

| # | Variant | Headers | Verwacht |
|---|---------|---------|----------|
| S1.1a | Browser (full page) | geen | Volledige HTML met `<html>`, `<head>`, Tailwind CDN, HTMX script |
| S1.1b | HTMX (fragment) | `HX-Request: true`, `HX-Target: week-content` | HTML-fragment zonder `<html>` wrapper |

### S2: Recept shufflen — "Ander recept" (UI → Planner → UI)

Wordt aangeroepen door de "🔀 Ander recept" knop in de dag-aanpassen sheet.
Retourneert een OOB-fragment van één dagkaart zodat de sheet open blijft.

**Integratietest (TestClient)**

| # | Scenario | Input | Verwacht resultaat | Selector |
|---|----------|-------|--------------------|----------|
| S2.1 | Shuffle enkel recept | POST `/week/shuffle` met `dag=0` | Dag 0 heeft ander recept dan origineel, overige dagen ongewijzigd | `[data-testid="dagkaart"][data-dag="0"]` |
| S2.2 | Shuffle respecteert variatie | POST `/week/shuffle` met `dag=3` | Nieuw recept verschilt in categorie/basis van buren (dag 2, dag 4) | Programmatisch |
| S2.3 | Shuffle niet-thuis dag | POST `/week/shuffle` met `dag=5` (niet-thuis) | HTTP 422 | — |
| S2.4 | Shuffle retourneert OOB dagkaart | POST `/week/shuffle` met `dag=0` | Geen `<html>` wrapper; precies **1** dagkaart in response (niet 7); geen `closeSheet` trigger | `[data-testid="dagkaart"]` (count=1) |

### S3: Weekmenu opnieuw genereren

**Integratietest (TestClient)**

| # | Scenario | Input | Verwacht resultaat |
|---|----------|-------|--------------------|
| S3.1 | Regenereer hele week | POST `/week/genereer` met dag-inputs (personen per dag) | Volledig nieuw menu, 7 dagkaarten |
| S3.2 | Regenereer met gewijzigde input | POST met dag 3 nu personen=0 | Dag 3 wordt niet-thuis, rest heeft recepten |
| S3.3 | Regenereer met HelloFresh | POST met dag 2 als HelloFresh | Dag 2 wordt HelloFresh type |
| S3.4 | Porties aanpassen voor 1 dag | POST met dag 1 personen van 2→4, rest ongewijzigd | Dag 1 toont 4 porties, recept ongewijzigd, ingrediënten geschaald | `[data-testid="dagkaart"][data-dag="1"] [data-testid="porties"]` |

### S5: Dag aanpassen (tap op dagkaart)

**Integratietest (TestClient)**

#### S5.1: Dagkaart is tappable

| # | Scenario | Input | Verwacht resultaat | Selector |
|---|----------|-------|--------------------|----------|
| S5.1.1 | Alle dagkaarten hebben tap-target | GET `/week` | Elke dagkaart heeft `hx-get="/week/dag/{N}/aanpassen"` en `hx-target="#sheet"` | `[data-testid="dagkaart"]` |
| S5.1.2 | HelloFresh-kaart is ook tappable | GET `/week`, dag 2 = HelloFresh | HelloFresh-kaart heeft `hx-get="/week/dag/2/aanpassen"` | `[data-type="hellofresh"]` |
| S5.1.3 | Geen losse ↻ knop | GET `/week` | Geen enkel element met `data-testid="vervang-dag-button"` | — |

#### S5.2: Dag-aanpassen sheet openen

| # | Scenario | Input | Verwacht resultaat | Selector |
|---|----------|-------|--------------------|----------|
| S5.2.1 | Sheet opent voor recept-dag | GET `/week/dag/0/aanpassen` | HTTP 200, bevat dagtype-selector, personen-selector, "Ander recept" knop | `[data-testid="dag-aanpassen"]` |
| S5.2.2 | Sheet opent voor niet-thuis dag | GET `/week/dag/5/aanpassen` (dag 5 = niet-thuis) | HTTP 200, dagtype-selector zichtbaar, **geen** personen-selector, **geen** "Ander recept" knop | — |
| S5.2.3 | Sheet opent voor HelloFresh dag | GET `/week/dag/2/aanpassen` (dag 2 = HF) | HTTP 200, dagtype-selector zichtbaar, **geen** personen-selector, **geen** "Ander recept" knop | — |
| S5.2.4 | Huidig dagtype is actief | GET `/week/dag/0/aanpassen` (recept-dag) | `[data-testid="dagtype-recept"]` heeft `data-actief="true"` | `[data-testid="dagtype-recept"][data-actief="true"]` |
| S5.2.5 | Huidige receptnaam zichtbaar | GET `/week/dag/0/aanpassen` | Naam van huidig recept staat in de sheet-header | — |
| S5.2.6 | Zonder weekmenu → 404 | GET `/week/dag/0/aanpassen`, geen week_menu | HTTP 404 | — |
| S5.2.7 | Ongeldige dag → 422 | GET `/week/dag/7/aanpassen` | HTTP 422 | — |

#### S5.3: Dagtype wijzigen

| # | Scenario | Input | Verwacht resultaat | Selector |
|---|----------|-------|--------------------|----------|
| S5.3.1 | Stel geen menu in | POST `/week/dag/0/stel-type-in` `type=geen_menu` | app.state: dag 0 personen=0; response-dagkaart `data-type="niet-thuis"` | `[data-type="niet-thuis"]` |
| S5.3.2 | Stel HelloFresh in | POST `/week/dag/0/stel-type-in` `type=hellofresh` | app.state: dag 0 in `hellofresh_dagen`; response-dagkaart `data-type="hellofresh"` | `[data-type="hellofresh"]` |
| S5.3.3 | Zet HelloFresh uit | POST `/week/dag/2/stel-type-in` `type=recept` (dag 2 was HF) | app.state: dag 2 **niet** meer in `hellofresh_dagen`; response-dagkaart `data-type="recept"` | `[data-type="recept"]` |
| S5.3.4 | Wijzigt alleen gevraagde dag | POST `/week/dag/0/stel-type-in` `type=geen_menu` | Overige 6 dagen ongewijzigd in app.state | — |
| S5.3.5 | Ongeldig type → 422 | POST `/week/dag/0/stel-type-in` `type=onbekend` | HTTP 422 | — |
| S5.3.6 | Zonder weekmenu → 404 | POST, geen week_menu | HTTP 404 | — |

#### S5.4: Personen aanpassen

| # | Scenario | Input | Verwacht resultaat | Selector |
|---|----------|-------|--------------------|----------|
| S5.4.1 | Stel 4 personen in | POST `/week/dag/0/stel-personen-in` `personen=4` | app.state: dag 0 personen=4; response-dagkaart toont "4" | `[data-testid="porties"]` |
| S5.4.2 | Sheet blijft open | POST `/week/dag/0/stel-personen-in` `personen=4` | Response headers bevatten **geen** `closeSheet` trigger | — |
| S5.4.3 | Wijzigt alleen gevraagde dag | POST `/week/dag/0/stel-personen-in` `personen=4` | Overige 6 dagen ongewijzigd in app.state | — |
| S5.4.4 | Niet-thuis dag → 422 | POST `/week/dag/5/stel-personen-in` (dag 5 = niet-thuis) | HTTP 422 | — |
| S5.4.5 | Zonder weekmenu → 404 | POST, geen week_menu | HTTP 404 | — |

---

### S4: Seizoensfiltering door de keten

**Integratietest (TestClient)**

| # | Scenario | Input | Verwacht resultaat |
|---|----------|-------|--------------------|
| S4.1 | Wintermenu | Seizoen=WINTER in context | Alleen winterrecepten of ALLE-seizoen recepten geselecteerd |
| S4.2 | Zomermenu | Seizoen=ZOMER in context | Alleen zomerrecepten of ALLE-seizoen recepten geselecteerd |

---

## E2E scenario's (Playwright)

Beperkt tot 3-5 flows die HTMX browser-interactie vereisen.

| # | Scenario | Stappen | Verificatie |
|---|----------|---------|-------------|
| E1 | Weekoverzicht laden | Navigeer naar `/week` | 7 dagkaarten zichtbaar, correcte receptnamen |
| E2 | Dag aanpassen sheet openen | Tap op dagkaart → wacht op sheet | Sheet opent met dagtype-selector, personen-selector en "Ander recept" knop |
| E3 | Hele week regenereren | Klik 🔀 shuffle-knop → wacht op DOM update | Alle dagkaarten updaten, `#week-content` is vervangen |
| E4 | Dag markeren als niet-thuis | Tap dagkaart → tap "Geen menu" in sheet | Dagkaart update naar type `niet-thuis` zonder page reload; sheet personen-selector verborgen |
| E5 | Dag markeren als HelloFresh | Tap dagkaart → tap "HelloFresh" in sheet | Dagkaart update naar type `hellofresh` met oranje styling; sheet "Ander recept" knop verborgen |
| E6 | Ander recept via sheet | Tap dagkaart → tap "🔀 Ander recept" | Dagkaart in achtergrond update; sheet blijft open; receptnaam in sheet-header wijzigt |
| E7 | Personen aanpassen via sheet | Tap dagkaart → tap "4" in personen-selector | Dagkaart toont "4 porties" zonder page reload; sheet blijft open |

**Wachtstrategie:** `page.wait_for_selector()` na elke HTMX-interactie om DOM-updates af te wachten.

---

## Test fixtures

### Integratietests: `tests/web/conftest.py`

```python
@pytest.fixture
def recipe_repository() -> RecipeRepository:
    """Echte RecipeRepository met data/recipes/ — niet gemockt."""

@pytest.fixture
def menu_history(tmp_path) -> MenuHistory:
    """Lege MenuHistory op tmp_path (geen echte history.json)."""

@pytest.fixture
def menu_planner(recipe_repository, menu_history) -> MenuPlanner:
    """Echte MenuPlanner met vaste random_seed voor determinisme."""

@pytest.fixture
def app_with_overrides(menu_history) -> FastAPI:
    """App met dependency_overrides voor alleen user-generated data (history).
    RecipeRepository en MenuPlanner draaien echt."""

@pytest.fixture
def client(app_with_overrides) -> TestClient:
    """TestClient met echte recepten en gemockte user data."""

@pytest.fixture
def htmx_client(client) -> TestClient:
    """TestClient die standaard HTMX headers meestuurt."""
```

### E2E tests: `tests/e2e/conftest.py`

Bestaande fixtures volstaan. Uitbreiden met:

```python
@pytest.fixture
def week_page_with_shuffle(page, live_server_url):
    """Navigeer naar /week en wacht tot shuffle-knoppen klikbaar zijn."""
```

---

## Mocking strategie

**Principe:** Alleen externe API-calls (Albert Heijn) worden gemockt via `respx`. Alle interne logica draait echt — inclusief de receptendatabase.

### Niet mocken (echt draaien)

| Dependency | Toelichting |
|------------|-------------|
| `RecipeRepository` | Leest de echte `data/recipes/` JSON bestanden. Dit test ook of recepten correct geparsed worden. |
| `MenuPlanner` | Echte planner met `random_seed` voor determinisme. Test de werkelijke selectie- en variatielogica. |
| `PortionCalculator` | Echte berekening. Test dat ingrediënten correct geschaald worden bij porties-aanpassingen. |

### Wel mocken (user-generated data & externe APIs)

| Dependency | Mock methode | Toelichting |
|------------|-------------|-------------|
| `MenuHistory` | `app.dependency_overrides[get_menu_history]` | In-memory history (geen `data/history.json` disk I/O). Voorkomt testafhankelijkheid van eerdere runs. |
| `WeekMenu` (huidig menu) | `app.state.week_menu` | Testdata op app state. Voorkomt dat tests afhangen van eerder gegenereerd menu. |
| `hellofresh_dagen` | `app.state.hellofresh_dagen` | Testdata op app state. |
| AH API (`ah/` module) | `respx` | Mock alle calls naar `api.ah.nl` (OAuth2 token endpoint, GraphQL). Enige externe dependency die gemockt wordt. |

---

## Assertie-conventies

1. **CSS selectors** gebaseerd op `data-testid` en `data-*` attributen (nooit op tekst of classnames)
2. Selectors corresponderen 1-op-1 met `hx-target` en `hx-swap` in templates
3. **BeautifulSoup** voor HTML parsing in integratietests
4. **HTMX fragment check:** response bevat geen `<html>` tag bij HTMX requests
5. **Full page check:** response bevat `<html>`, Tailwind CDN link, HTMX script tag

---

## Data-testid contract

Overzicht van `data-testid` attributen die als contract dienen tussen templates en tests:

| Selector | Element | Gebruikt in |
|----------|---------|-------------|
| `[data-testid="dagkaart"]` | Dagkaart container (tappable) | S1.*, S5.1, E1–E7 |
| `[data-testid="dagkaart"][data-type="recept"]` | Dagkaart met recept | S1.1, S5.3 |
| `[data-testid="dagkaart"][data-type="hellofresh"]` | HelloFresh dagkaart | S1.3, S5.3, E5 |
| `[data-testid="dagkaart"][data-type="niet-thuis"]` | Niet-thuis dagkaart | S1.2, S5.3, E4 |
| `[data-testid="dagkaart"][data-dag="N"]` | Dagkaart voor dag N | S2.1, S2.4 |
| `[data-testid="porties"]` | Aantal porties | S1.1, S3.4, S5.4, E7 |
| `[data-testid="categorie"]` | Categorie indicator | S1.1, S1.5 |
| `[data-testid="basis"]` | Basis indicator | S1.5 |
| `[data-testid="genereer-button"]` | 🔀 Shuffle knop (hele week) | S3.*, E3 |
| `[data-testid="week-content"]` | Week content container (`hx-target`) | S3.*, E3 |
| `[data-testid="dag-aanpassen"]` | Dag-aanpassen sheet container | S5.2 |
| `[data-testid="dagtype-selector"]` | Dagtype selector container | S5.2, S5.3, E2, E4, E5 |
| `[data-testid="dagtype-geen-menu"]` | "Geen menu" knop | S5.2, S5.3, E4 |
| `[data-testid="dagtype-recept"]` | "Recept" knop | S5.2, S5.3 |
| `[data-testid="dagtype-hellofresh"]` | "HelloFresh" knop | S5.2, S5.3, E5 |
| `[data-testid="dagtype-*"][data-actief="true"]` | Actief geselecteerd dagtype | S5.2.4 |
| `[data-testid="personen-selector"]` | Personen selector container | S5.2, S5.4, E7 |
| `[data-testid="ander-recept-button"]` | "🔀 Ander recept" knop | S5.2, E6 |

---

## Implementatievolgorde

1. **Fixtures opzetten** — `tests/web/conftest.py` uitbreiden met bovenstaande fixtures
2. **S1: Weekmenu laden** — Bestaande tests uitbreiden met HTMX fragment variant en BeautifulSoup asserties
3. **S5.1: Dagkaart tappable** — Dagkaart `hx-get` toevoegen, ↻ knop verwijderen; `test_dag_aanpassen.py` klasse `TestDagkaartTappable`
4. **S5.2: Dag-aanpassen sheet** — Route `GET /week/dag/{dag}/aanpassen` + template; `TestDagAanpassenOpenen`
5. **S5.3: Dagtype selector** — Routes `POST /week/dag/{dag}/stel-type-in`; `TestDagTypeSelector`
6. **S5.4: Personen selector** — Route `POST /week/dag/{dag}/stel-personen-in`; `TestPersonenSelector`
7. **S2: Shuffle (OOB)** — `POST /week/shuffle` response wijzigen naar OOB single dagkaart; `TestAnderRecept` + update `TestShuffleRetourneertFragment`
8. **S3: Regenereren** — Route `POST /week/genereer` (al grotendeels geïmplementeerd)
9. **S4: Seizoensfiltering** — Integratietest met verschillende seizoenen
10. **E2–E7: Playwright** — E2E tests voor HTMX sheet-interacties; `test_dag_aanpassen.py` (E2E)

**Testbestanden die wijzigen bij fase 1c implementatie:**
- Nieuw: `tests/web/test_dag_aanpassen.py` (S5.1–S5.4 + S2 "Ander recept")
- Update: `tests/web/test_recept_shufflen.py` — `TestShuffleRetourneertFragment` (S2.4)
- Verwijder: `tests/web/test_receptkiezer.py` (vervalt: zoeken, filterchips, receptenlijst, kies/bevestig routes)

---

## Wat niet in scope is

- Performance tests
- Accessibility tests
- JSON API contract tests (niet van toepassing, geen JSON API)
- AH-integratie tests (apart traject)
- Visuele regressie tests
