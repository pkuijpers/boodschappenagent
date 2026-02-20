# Testplan: End-to-end integratietests

## Doel

Dit testplan beschrijft de integratietests die de samenwerking tussen modules valideren. De individuele modules (planner, repository, modellen) hebben al uitgebreide unit tests (440+). Dit plan focust op de **end-to-end flows** waarbij meerdere modules samenwerken om een gebruikersactie te voltooien.

## Eerste scope: weekmenu samenstellen

De eerste feature die end-to-end getest wordt is het samenstellen van een weekmenu. De gebruikersflow:

1. Gebruiker opent `/week` → ziet automatisch gegenereerd weekmenu
2. Gebruiker markeert dagen als niet-thuis of HelloFresh
3. Gebruiker past het aantal personen aan voor een specifieke dag
4. Gebruiker klikt "opnieuw genereren" → nieuw menu met aangepaste input
5. Gebruiker shufflet een enkel recept → alleen die dag wordt vervangen

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

### S2: Recept shufflen (UI → Planner → UI)

**Integratietest (TestClient)**

| # | Scenario | Input | Verwacht resultaat | Selector |
|---|----------|-------|--------------------|----------|
| S2.1 | Shuffle enkel recept | POST `/week/shuffle` met `dag=0` | Dag 0 heeft ander recept dan origineel, overige dagen ongewijzigd | `[data-testid="dagkaart"][data-dag="0"]` |
| S2.2 | Shuffle respecteert variatie | POST `/week/shuffle` met `dag=3` | Nieuw recept verschilt in categorie/basis van buren (dag 2, dag 4) | Programmatisch |
| S2.3 | Shuffle niet-thuis dag | POST `/week/shuffle` met `dag=5` (niet-thuis) | Foutmelding of no-op | HTTP status of foutbericht |
| S2.4 | Shuffle retourneert fragment | POST `/week/shuffle`, HTMX headers | HTML-fragment dat past in `#week-content` | Geen `<html>` wrapper |

### S3: Weekmenu opnieuw genereren

**Integratietest (TestClient)**

| # | Scenario | Input | Verwacht resultaat |
|---|----------|-------|--------------------|
| S3.1 | Regenereer hele week | POST `/week/genereer` met dag-inputs (personen per dag) | Volledig nieuw menu, 7 dagkaarten |
| S3.2 | Regenereer met gewijzigde input | POST met dag 3 nu personen=0 | Dag 3 wordt niet-thuis, rest heeft recepten |
| S3.3 | Regenereer met HelloFresh | POST met dag 2 als HelloFresh | Dag 2 wordt HelloFresh type |
| S3.4 | Porties aanpassen voor 1 dag | POST met dag 1 personen van 2→4, rest ongewijzigd | Dag 1 toont 4 porties, recept ongewijzigd, ingrediënten geschaald | `[data-testid="dagkaart"][data-dag="1"] [data-testid="porties"]` |

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
| E2 | Recept shufflen | Klik shuffle-knop op dagkaart → wacht op DOM update | Dagkaart update zonder page reload, receptnaam veranderd |
| E3 | Hele week regenereren | Klik "opnieuw genereren" → wacht op DOM update | Alle dagkaarten updaten, `#week-content` is vervangen |
| E4 | Dag markeren als niet-thuis | Toggle niet-thuis op een dag → genereer | Dagkaart verandert naar type `niet-thuis` |
| E5 | Dag markeren als HelloFresh | Toggle HelloFresh op een dag → genereer | Dagkaart verandert naar type `hellofresh` met oranje styling |

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
| `[data-testid="dagkaart"]` | Dagkaart container | S1.*, E1, E2 |
| `[data-testid="dagkaart"][data-type="recept"]` | Dagkaart met recept | S1.1 |
| `[data-testid="dagkaart"][data-type="hellofresh"]` | HelloFresh dagkaart | S1.3, E5 |
| `[data-testid="dagkaart"][data-type="niet-thuis"]` | Niet-thuis dagkaart | S1.2, E4 |
| `[data-testid="dagkaart"][data-dag="N"]` | Dagkaart voor dag N | S2.1 |
| `[data-testid="porties"]` | Aantal porties | S1.1, S3.4 |
| `[data-testid="categorie"]` | Categorie indicator | S1.1, S1.5 |
| `[data-testid="basis"]` | Basis indicator | S1.5 |
| `[data-testid="shuffle-button"]` | Shuffle knop per dag | S2.*, E2 |
| `[data-testid="week-content"]` | Week content container (`hx-target`) | S2.4, E2, E3 |
| `[data-testid="genereer-button"]` | Genereer/regenereer knop | S3.*, E3 |

---

## Implementatievolgorde

1. **Fixtures opzetten** — `tests/web/conftest.py` uitbreiden met bovenstaande fixtures
2. **S1: Weekmenu laden** — Bestaande tests uitbreiden met HTMX fragment variant en BeautifulSoup asserties
3. **S2: Shuffle** — Eerst route `POST /week/shuffle` implementeren (TDD), dan integratietests
4. **S3: Regenereren** — Route `POST /week/genereer` implementeren (TDD), dan integratietests
5. **S4: Seizoensfiltering** — Integratietest met verschillende seizoenen
6. **E2-E5: Playwright** — E2E tests voor HTMX-interacties zodra routes bestaan

---

## Wat niet in scope is

- Performance tests
- Accessibility tests
- JSON API contract tests (niet van toepassing, geen JSON API)
- AH-integratie tests (apart traject)
- Visuele regressie tests
