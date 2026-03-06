# Testplan: Fase 4 — AH-integratie (Web UI)

**Versie:** 1.0
**Datum:** 2026-03-06
**Bron:** `ui-ontwerp-albert.md` (scherm 5.5 & 5.6), `implementatieplan-ui.md` (fase 4), `poc-ah-integratie.md`

## Doel

Dit testplan beschrijft de integratietests voor de AH-integratie in de Web UI:

- **Login flow** — OAuth2 authenticatie via authorization code
- **Verstuur naar AH** — Boodschappenlijst synchroniseren naar AH favorieten-lijst
- **Bevestigingsscherm** — Resultaat tonen met gevonden/niet-gevonden producten

De backend modules (`AHClient`, `AHTokenManager`, `AHIntegratie`, `ProductScorer`, `quantity_calculator`) bestaan al en zijn getest. Dit plan focust op de **web-laag** (routes, templates, HTMX-interacties) en de **koppeling** met de bestaande AH-modules.

---

## User flow

```
Boodschappenlijst (fase 3, done)
        |
        |  "Verstuur naar AH ->"
        v
+-------------------------------+
|     AH STATUS CHECK           |
|  Tokens geldig? -> Verstuur   |
|  Niet ingelogd? -> Login      |
+-------------------------------+
        |                   |
   (ingelogd)         (niet ingelogd)
        |                   |
        v                   v
+----------------+  +-------------------+
| VERSTUUR       |  | LOGIN PAGINA      |
| Zoek producten |  | Instructies +     |
| Maak AH lijst  |  | code invoerveld   |
| Voeg toe       |  +-------------------+
+----------------+          |
        |                   v
        v          +-------------------+
+----------------+ | LOGIN VERWERKEN   |
| BEVESTIGING    | | Code -> tokens    |
| X producten    | | Redirect -> /ah   |
| in je mandje   | +-------------------+
| Niet gevonden  |
| Open AH ->     |
+----------------+
```

---

## Integratiegrenzen

```
+------------------+     +------------------+     +--------------------+
| Boodschappenlijst|---->| AHIntegratie     |---->| Web: /ah/*         |
| (app.state)      |     | (zoek + sync)    |     | Web: /boodschappen |
+------------------+     +------------------+     +--------------------+
                               |                          |
                         AHClient (API)            HTMX swap/target
                         AHTokenManager            fragment vs full page
```

| Grens | Wat kan misgaan |
|-------|-----------------|
| Boodschappenlijst -> AHIntegratie | Lege lijst, geen weekmenu, items zonder naam |
| AHTokenManager -> Login | Ongeldige code, verlopen refresh token, netwerk timeout |
| AHClient -> API | GraphQL errors, rate limiting, product niet gevonden |
| AHIntegratie -> Bevestiging | Niet-gevonden producten niet getoond, aantallen verkeerd |
| Web UI -> AH status | Token check faalt, redirect loop, foutmelding ontbreekt |

---

## Nieuwe routes

| Endpoint | Method | Doel |
|----------|--------|------|
| `/ah/status` | GET | Check of AH-tokens geldig zijn (JSON) |
| `/ah/login` | GET | Login-pagina met instructies en code-invoerveld |
| `/ah/login` | POST | Verwerk authorization code, sla tokens op |
| `/ah/logout` | POST | Verwijder tokens, redirect naar `/ah/login` |
| `/boodschappen/verstuur-naar-ah` | POST | Verstuur lijst naar AH, toon bevestiging |

---

## Nieuwe templates

```
templates/
    pages/
        ah_login.html          # Login pagina met instructies + code-veld
        ah_bevestiging.html    # Bevestigingsscherm (vinkje, aantallen, niet-gevonden)
```

---

## Nieuwe dependencies (web/dependencies.py)

```python
def get_ah_token_manager() -> AHTokenManager:
    """AHTokenManager met standaard token path."""

def get_ah_client() -> AHClient:
    """AHClient met AHTokenManager. Gooit exception als niet ingelogd."""

def get_ah_integratie() -> AHIntegratie:
    """AHIntegratie met AHClient."""
```

---

## Testscenario's

### S12: AH Login pagina

**Integratietest (TestClient)**

| # | Scenario | Input | Verwacht resultaat | Selector |
|---|----------|-------|--------------------|----------|
| S12.1 | Login pagina laadt | GET `/ah/login` | 200, pagina met instructies en code-invoerveld | `[data-testid="ah-login-form"]` |
| S12.2 | Login pagina toont login URL | GET `/ah/login` | Login URL naar `login.ah.nl` zichtbaar | `[data-testid="ah-login-url"]` |
| S12.3 | Login pagina heeft code-veld | GET `/ah/login` | Input veld voor authorization code | `input[name="code"]` |
| S12.4 | Login pagina heeft submit knop | GET `/ah/login` | "Inloggen" submit knop | `[data-testid="ah-login-submit"]` |

**Twee varianten:**

| # | Variant | Headers | Verwacht |
|---|---------|---------|----------|
| S12.1a | Browser (full page) | geen | Volledige HTML met `<html>`, tab-bar, header "AH Koppeling" |
| S12.1b | HTMX (fragment) | `HX-Request: true` | HTML-fragment zonder `<html>` wrapper |

### S13: AH Login verwerken

**Integratietest (TestClient) — AHTokenManager gemockt**

| # | Scenario | Input | Verwacht resultaat |
|---|----------|-------|--------------------|
| S13.1 | Succesvolle login | POST `/ah/login` met `code=valid-code` | Redirect (303) naar `/boodschappen` |
| S13.2 | Login slaat tokens op | POST `/ah/login` met `code=valid-code` | `token_manager.login()` aangeroepen met code |
| S13.3 | Ongeldige code -> foutmelding | POST `/ah/login` met `code=invalid` (token_manager.login gooit exception) | 200, login pagina met foutmelding | `[data-testid="ah-login-error"]` |
| S13.4 | Lege code -> 422 | POST `/ah/login` met `code=` (leeg) | HTTP 422 |
| S13.5 | Login redirect behoudt doel | POST `/ah/login` met `code=valid&next=/boodschappen/verstuur-naar-ah` | Redirect naar opgegeven next URL |

### S14: AH Status check

**Integratietest (TestClient) — AHTokenManager gemockt**

| # | Scenario | Input | Verwacht resultaat |
|---|----------|-------|--------------------|
| S14.1 | Ingelogd -> status ok | GET `/ah/status`, token_manager.is_authenticated() = True | JSON `{"authenticated": true}` |
| S14.2 | Niet ingelogd -> status not ok | GET `/ah/status`, token_manager.is_authenticated() = False | JSON `{"authenticated": false}` |
| S14.3 | Verlopen tokens -> refresh poging | GET `/ah/status`, access token verlopen maar refresh lukt | JSON `{"authenticated": true}` |

### S15: Verstuur naar AH (succes flow)

**Integratietest (TestClient) — AHIntegratie gemockt**

| # | Scenario | Input | Verwacht resultaat | Selector |
|---|----------|-------|--------------------|----------|
| S15.1 | Verstuur toont bevestiging | POST `/boodschappen/verstuur-naar-ah`, ingelogd, boodschappenlijst aanwezig | 200, bevestigingsscherm met groen vinkje | `[data-testid="ah-bevestiging"]` |
| S15.2 | Bevestiging toont aantal producten | POST, 15 producten gevonden | "15 producten in je mandje" | `[data-testid="ah-aantal-producten"]` |
| S15.3 | Bevestiging toont lijst naam | POST, lijst "Boodschappen 2026-03-02" aangemaakt | Lijst naam zichtbaar | `[data-testid="ah-lijst-naam"]` |
| S15.4 | "Open Albert Heijn" link | POST, succesvol | Link naar ah.nl zichtbaar | `[data-testid="ah-open-link"]` |
| S15.5 | "Terug naar home" link | POST, succesvol | Link naar `/week` | `a[href="/week"]` |

### S16: Verstuur naar AH (niet-gevonden producten)

**Integratietest (TestClient) — AHIntegratie gemockt**

| # | Scenario | Input | Verwacht resultaat | Selector |
|---|----------|-------|--------------------|----------|
| S16.1 | Niet-gevonden sectie zichtbaar | POST, 2 van 15 niet gevonden | Sectie "Niet gevonden" met 2 items | `[data-testid="ah-niet-gevonden"]` |
| S16.2 | Niet-gevonden items tonen naam | POST, "verse basilicum" niet gevonden | "verse basilicum" in niet-gevonden lijst | `[data-testid="ah-niet-gevonden-item"]` |
| S16.3 | Geen niet-gevonden sectie | POST, alle producten gevonden | Geen "Niet gevonden" sectie | `[data-testid="ah-niet-gevonden"]` afwezig |
| S16.4 | Samenvatting in header | POST, 13 gevonden + 2 niet gevonden | "13 van 15 producten gevonden" | `[data-testid="ah-samenvatting"]` |

### S17: Verstuur naar AH (error scenarios)

**Integratietest (TestClient)**

| # | Scenario | Input | Verwacht resultaat | Selector |
|---|----------|-------|--------------------|----------|
| S17.1 | Niet ingelogd -> redirect login | POST `/boodschappen/verstuur-naar-ah`, niet ingelogd | Redirect (303) naar `/ah/login` |
| S17.2 | Geen boodschappenlijst -> redirect | POST, geen boodschappenlijst in state | Redirect (303) naar `/week` |
| S17.3 | Lege boodschappenlijst -> foutmelding | POST, boodschappenlijst met 0 items | 200, foutmelding "Geen producten om te versturen" | `[data-testid="ah-lege-lijst"]` |
| S17.4 | AH API fout -> foutmelding | POST, AHIntegratie gooit exception | 200, foutmelding met uitleg | `[data-testid="ah-api-error"]` |
| S17.5 | Token verlopen bij versturen -> redirect login | POST, token refresh mislukt (exception) | Redirect (303) naar `/ah/login` |

### S18: AH Logout

**Integratietest (TestClient)**

| # | Scenario | Input | Verwacht resultaat |
|---|----------|-------|--------------------|
| S18.1 | Logout verwijdert tokens | POST `/ah/logout` | Redirect naar `/ah/login`, tokens verwijderd |
| S18.2 | Logout als niet ingelogd | POST `/ah/logout`, geen tokens | Redirect naar `/ah/login` (geen error) |

### S19: Navigatie updates

**Integratietest (TestClient)**

| # | Scenario | Input | Verwacht resultaat | Selector |
|---|----------|-------|--------------------|----------|
| S19.1 | "Verstuur naar AH" knop op boodschappenlijst | GET `/boodschappen` | Knop wijst naar POST `/boodschappen/verstuur-naar-ah` | `[data-testid="verstuur-naar-ah-button"]` |
| S19.2 | "Verstuur naar AH" knop disabled als niet ingelogd | GET `/boodschappen`, niet ingelogd | Knop toont "Log eerst in bij AH" of link naar `/ah/login` | `[data-testid="ah-login-nodig"]` |
| S19.3 | Bevestiging -> Week link | GET bevestigingspagina | "Terug naar home" link naar `/week` | `a[href="/week"]` |

---

## E2E scenario's (Playwright)

Alle AH API calls worden gemockt in E2E tests (geen echte AH API calls).
E2E tests worden **niet apart aan het eind** geschreven, maar **direct na de bijbehorende integratietest** in elke stap (zie Implementatievolgorde).

| # | Scenario | Stappen | Verificatie | Implementatiestap |
|---|----------|---------|-------------|-------------------|
| E15 | Login pagina laden | Navigeer naar `/ah/login` | Instructies zichtbaar, code-invoerveld, login URL, submit knop | Stap 1 |
| E16 | Login flow (succes) | Vul code in op `/ah/login` -> submit | Redirect naar `/boodschappen`, geen foutmelding | Stap 2 |
| E17 | Login flow (fout) | Vul ongeldige code in -> submit | Foutmelding zichtbaar op login pagina, code-veld nog zichtbaar | Stap 2 |
| E18 | Verstuur naar AH (succes) | Login -> boodschappenlijst -> tap "Verstuur naar AH" | Bevestigingsscherm: groen vinkje, aantal producten, "Open AH" link | Stap 4 |
| E19 | Niet-gevonden producten | Verstuur met 2 onvindbare producten | Niet-gevonden sectie met productnamen zichtbaar | Stap 5 |
| E20 | Verstuur zonder login -> login redirect | Navigeer naar `/boodschappen` -> tap "Verstuur naar AH" zonder login | Redirect naar `/ah/login` pagina | Stap 6 |
| E21 | Volledige flow: Boodschappen -> AH | Start op `/boodschappen` -> "Verstuur naar AH" -> bevestiging -> "Terug naar home" | Hele flow werkt zonder errors, eindig op `/week` | Stap 7 |

**Wachtstrategie:** `page.wait_for_selector()` na elke HTMX-interactie om DOM-updates af te wachten.

---

## Data-testid contract

Nieuwe `data-testid` attributen voor fase 4:

| Selector | Element | Gebruikt in |
|----------|---------|-------------|
| `[data-testid="ah-login-form"]` | Login formulier container | S12.1, E15 |
| `[data-testid="ah-login-url"]` | AH login URL (link/tekst) | S12.2, E15 |
| `[data-testid="ah-login-submit"]` | Login submit knop | S12.4, E15, E16 |
| `[data-testid="ah-login-error"]` | Foutmelding bij login | S13.3, E17 |
| `[data-testid="ah-bevestiging"]` | Bevestigingsscherm container | S15.1, E18 |
| `[data-testid="ah-aantal-producten"]` | "X producten in je mandje" tekst | S15.2, E18 |
| `[data-testid="ah-lijst-naam"]` | Naam van aangemaakte AH lijst | S15.3 |
| `[data-testid="ah-open-link"]` | "Open Albert Heijn" link | S15.4, E18 |
| `[data-testid="ah-niet-gevonden"]` | Niet-gevonden producten sectie | S16.1, S16.3, E19 |
| `[data-testid="ah-niet-gevonden-item"]` | Niet-gevonden product item | S16.2, E19 |
| `[data-testid="ah-samenvatting"]` | Samenvatting ("X van Y gevonden") | S16.4, E18 |
| `[data-testid="ah-lege-lijst"]` | Lege lijst foutmelding | S17.3 |
| `[data-testid="ah-api-error"]` | API foutmelding | S17.4 |
| `[data-testid="ah-login-nodig"]` | "Log eerst in bij AH" indicator | S19.2 |
| `[data-testid="verstuur-naar-ah-button"]` | "Verstuur naar AH" knop (al bestaand) | S19.1 |

---

## Test fixtures

### Integratietests: `tests/web/conftest.py` — uitbreidingen

```python
@pytest.fixture
def mock_token_manager() -> MagicMock:
    """Gemockte AHTokenManager (geen echte tokens/API calls)."""

@pytest.fixture
def mock_token_manager_authenticated(mock_token_manager) -> MagicMock:
    """AHTokenManager die is_authenticated() = True retourneert."""

@pytest.fixture
def mock_token_manager_unauthenticated(mock_token_manager) -> MagicMock:
    """AHTokenManager die is_authenticated() = False retourneert."""

@pytest.fixture
def mock_ah_integratie() -> MagicMock:
    """Gemockte AHIntegratie (geen echte AH API calls)."""

@pytest.fixture
def sync_resultaat_succes() -> SyncResultaat:
    """SyncResultaat met 15 gevonden producten, 0 niet gevonden."""

@pytest.fixture
def sync_resultaat_deels() -> SyncResultaat:
    """SyncResultaat met 13 gevonden producten, 2 niet gevonden."""

@pytest.fixture
def app_with_ah(app_with_overrides, mock_token_manager, mock_ah_integratie):
    """App met dependency_overrides voor AH token manager en integratie."""
```

### E2E tests: `tests/e2e/conftest.py` — uitbreidingen

```python
@pytest.fixture
def mock_ah_api(monkeypatch):
    """Mock alle AH API calls voor E2E tests.

    - AHTokenManager.login() -> succesvol (slaat tokens op)
    - AHTokenManager.is_authenticated() -> True na login
    - AHIntegratie.sync_naar_lijst() -> SyncResultaat met testdata
    """
```

---

## Mocking strategie

### Altijd mocken (externe API)

| Dependency | Mock methode | Toelichting |
|------------|-------------|-------------|
| `AHTokenManager` | `app.dependency_overrides[get_ah_token_manager]` | Geen echte OAuth2 tokens. Mock `login()`, `is_authenticated()`, `get_access_token()`. |
| `AHClient` | `app.dependency_overrides[get_ah_client]` | Geen echte GraphQL calls. Mock alle API methodes. |
| `AHIntegratie` | `app.dependency_overrides[get_ah_integratie]` | Geen echte product search/sync. Return voorgedefinieerde `SyncResultaat`. |

### Niet mocken (state management)

| Dependency | Toelichting |
|------------|-------------|
| `app.state.boodschappenlijst` | Echte in-memory boodschappenlijst state (zoals in fase 3). |
| `app.state.week_menu` | Echte testdata op app state. |
| Route logic | Echte redirect/error logica — test de controller laag. |

---

## Assertie-conventies

Identiek aan fase 2-3 testplan:

1. **CSS selectors** gebaseerd op `data-testid` en `data-*` attributen
2. **BeautifulSoup** voor HTML parsing in integratietests
3. **HTMX fragment check:** response bevat geen `<html>` tag bij HTMX requests
4. **Full page check:** response bevat `<html>`, Tailwind CDN link, HTMX script tag

---

## Implementatievolgorde

Elke stap volgt het patroon: **unit/integratietest (red) -> implementatie (green) -> E2E test -> refactor**. De E2E test wordt direct na de integratietest geschreven en uitgevoerd, zodat de feedback loop zo kort mogelijk is.

### Stap 0: Setup

- **Dependencies opzetten** — `web/dependencies.py` uitbreiden met `get_ah_token_manager`, `get_ah_client`, `get_ah_integratie`
- **Test fixtures opzetten** — `tests/web/conftest.py` en `tests/e2e/conftest.py` uitbreiden met AH mocks
- **Router registreren** — `web/routers/ah.py` aanmaken, router mounten in `app.py`

### Stap 1: Login pagina

| Fase | Wat |
|------|-----|
| Unit test (red) | S12.1-S12.4: Login pagina laadt, toont URL, code-veld, submit knop |
| Implementatie (green) | `GET /ah/login` route + `ah_login.html` template |
| E2E test | E15: Navigeer naar `/ah/login`, verifieer instructies, code-veld, URL, submit knop |
| Refactor | Template styling, AH-kleurenpalet |

### Stap 2: Login verwerken

| Fase | Wat |
|------|-----|
| Unit test (red) | S13.1-S13.5: Succesvolle login, token opslag, ongeldige code, lege code, redirect |
| Implementatie (green) | `POST /ah/login` route met token_manager.login() |
| E2E test | E16 + E17: Login flow succes (code invullen -> redirect) + fout (foutmelding zichtbaar) |
| Refactor | Foutmelding styling, form validation |

### Stap 3: Status check + Logout

| Fase | Wat |
|------|-----|
| Unit test (red) | S14.1-S14.3: Status JSON responses + S18.1-S18.2: Logout |
| Implementatie (green) | `GET /ah/status` + `POST /ah/logout` routes |
| E2E test | — (status is JSON endpoint, geen visuele E2E nodig; logout getest als onderdeel van stap 6) |
| Refactor | — |

### Stap 4: Verstuur naar AH (succes)

| Fase | Wat |
|------|-----|
| Unit test (red) | S15.1-S15.5: Bevestigingsscherm met vinkje, aantal, lijst naam, links |
| Implementatie (green) | `POST /boodschappen/verstuur-naar-ah` route + `ah_bevestiging.html` template |
| E2E test | E18: Login -> boodschappenlijst -> "Verstuur naar AH" -> bevestigingsscherm controleren |
| Refactor | Bevestiging styling, groen vinkje animatie |

### Stap 5: Niet-gevonden producten

| Fase | Wat |
|------|-----|
| Unit test (red) | S16.1-S16.4: Niet-gevonden sectie, items, afwezigheid, samenvatting |
| Implementatie (green) | Niet-gevonden sectie in `ah_bevestiging.html` |
| E2E test | E19: Verstuur met 2 onvindbare producten -> niet-gevonden sectie controleren |
| Refactor | Niet-gevonden styling |

### Stap 6: Error scenarios + navigatie

| Fase | Wat |
|------|-----|
| Unit test (red) | S17.1-S17.5: Niet ingelogd redirect, geen lijst, lege lijst, API fout, token verlopen |
| Implementatie (green) | Error handling in verstuur route, redirects |
| E2E test | E20: Verstuur zonder login -> redirect naar `/ah/login` |
| Refactor | — |

### Stap 7: Navigatie updates

| Fase | Wat |
|------|-----|
| Unit test (red) | S19.1-S19.3: Knop status op boodschappenlijst, login-nodig indicator |
| Implementatie (green) | Boodschappenlijst template updaten met AH login status |
| E2E test | E21: Volledige flow: boodschappen -> verstuur -> bevestiging -> terug naar home |
| Refactor | Knop styling, login-nodig indicator |

### Overzicht: welke E2E bij welke stap

| Stap | Unit tests | E2E tests |
|------|-----------|-----------|
| 0 | — | — |
| 1 | S12 | E15 |
| 2 | S13 | E16, E17 |
| 3 | S14, S18 | — |
| 4 | S15 | E18 |
| 5 | S16 | E19 |
| 6 | S17 | E20 |
| 7 | S19 | E21 |

**Testbestanden:**
- Nieuw: `tests/web/test_ah_integratie.py` (S12, S13, S14, S15, S16, S17, S18)
- Uitbreiding: `tests/web/test_navigatie.py` (S19)
- Nieuw: `tests/e2e/test_ah_integratie.py` (E15, E16, E17, E18, E19, E20, E21)

---

## Wat niet in scope is

- Echte AH API calls in tests (alles gemockt)
- Token refresh achtergrond-job (handmatig bij actie)
- "Lijstje naar mandje" functionaliteit (handmatig in AH app)
- Meerdere AH accounts
- Product mapping configuratie UI
- Kookmodus (fase 5 — apart testplan)
- Instellingen (fase 6 — apart testplan)
