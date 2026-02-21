# Implementatieplan: Albert UI

**Datum:** 2026-02-15
**Tech stack:** FastAPI + HTMX + Tailwind CSS + Playwright
**Bron:** `ui-ontwerp-albert.md`, `boodschappen-automatisering-plan.md`, `api/openapi.yaml`

---

## 1. Architectuuroverzicht

```
Browser (HTMX + Tailwind CSS)
    │
    │  HTML-fragmenten via HTMX
    │
FastAPI (server-side rendering)
    │
    │  Interne calls
    │
Bestaande Python-modules
(repository, planner, models, ah, voorraadbeheer)
```

### Waarom deze stack?

| Keuze | Rationale |
|-------|-----------|
| **FastAPI** | Async Python, Jinja2 templating, past bij bestaande Python-codebase |
| **HTMX** | Server-side rendering, minimale JS, snelle interacties (swap, boost) |
| **Tailwind CSS** | Utility-first, snel prototypen, mobiel-first responsive design |
| **Playwright** | E2E-tests voor de volledige user flow, al in POC-overwegingen voor AH |

### Geen SPA

De app is bewust **geen SPA**. HTMX vervangt alleen de relevante HTML-fragmenten bij interacties. FastAPI rendert volledige pagina's bij navigatie en HTML-partials bij HTMX-requests. Dit houdt de complexiteit laag en past bij het "één sessie, één flow"-principe.

---

## 2. Projectstructuur

```
src/boodschappenagent/
    web/                          # Nieuwe module
        __init__.py
        app.py                    # FastAPI app factory
        dependencies.py           # Dependency injection (repository, planner, etc.)
        routers/
            __init__.py
            menu.py               # /week, /week/shuffle, /week/dag/{dag}/vervang, etc.
            voorraad.py           # /voorraad
            boodschappen.py       # /boodschappen
            kookmodus.py          # /vandaag
            ah.py                 # /ah/login, /ah/verstuur
            settings.py           # /instellingen
        templates/
            base.html             # Layout: head, tailwind, htmx, tab-bar
            components/
                dagkaart.html         # Dagkaart component (3 states)
                dagkaart_hellofresh.html
                receptrij.html        # Receptrij in receptkiezer
                voorraaditem.html     # Ja/Nee voorraad-item
                boodschapitem.html    # Checkbox boodschap-item
                button.html           # Primaire/secundaire buttons
                filter_chips.html     # Categorie filter chips
                tab_bar.html          # Navigatie tab bar
            pages/
                week.html             # 5.1 Weekoverzicht
                receptkiezer.html     # 5.2 Receptkiezer (partial/sheet)
                porties.html          # 5.3 Porties kiezen (partial)
                voorraad.html         # 5.4 Voorraadcheck
                boodschappen.html     # 5.5 Boodschappenlijst
                ah_bevestiging.html   # 5.6 AH koppeling bevestiging
                vandaag.html          # 5.7 Kookmodus
                instellingen.html     # Instellingen
        static/
            css/
                app.css               # Tailwind input + custom kleuren
            js/
                htmx.min.js           # HTMX (vendored)

tests/
    web/
        conftest.py               # FastAPI TestClient fixtures
        test_menu_routes.py
        test_voorraad_routes.py
        test_boodschappen_routes.py
        test_kookmodus_routes.py
        test_ah_routes.py
    e2e/
        conftest.py               # Playwright fixtures
        test_weekly_flow.py       # Volledige weekflow E2E
        test_kookmodus.py         # Kookmodus E2E
```

---

## 3. Fasering

### Fase 0: Project setup

**Doel:** Werkende FastAPI-app met Tailwind, HTMX en eerste lege pagina.

- [x] Dependencies toevoegen: `fastapi`, `uvicorn`, `jinja2`, `python-multipart`
- [x] Dev-dependencies toevoegen: `playwright`, `httpx` (voor async TestClient)
- [x] `web/app.py` — FastAPI app factory met Jinja2 templating
- [x] `web/dependencies.py` — Dependency injection voor `RecipeRepository`, `MenuPlanner`, `MenuHistory`
- [x] `templates/base.html` — Layout met Tailwind CDN, HTMX, AH-kleurenpalet als CSS custom properties
- [x] `templates/components/tab_bar.html` — Tab-bar (Week / Vandaag / Instellingen)
- [x] Tailwind config met custom kleuren (AH Blauw `#00A0E2`, etc.)
- [x] Eerste route `GET /` → redirect naar `/week`
- [x] `GET /week` → rendert lege weekoverzicht-pagina met layout
- [x] Test: `TestClient` valideert dat `/week` een 200 teruggeeft met correcte HTML-structuur
- [ ] Playwright installeren: `playwright install chromium`

**Definitie of done:** `uv run uvicorn boodschappenagent.web.app:create_app --factory` start, `/week` toont een gestylede lege pagina met tab-bar.

---

### Fase 1: Weekoverzicht (scherm 5.1)

**Doel:** Automatisch gegenereerd weekmenu tonen met dagkaarten.

#### 1a. Menu genereren en tonen

- [x] `GET /week` — Haalt huidig weekmenu op (of genereert nieuw via `MenuPlanner`)
- [x] `templates/pages/week.html` — Weekoverzicht met header ("Week {nr}"), shuffle-knop, lijst dagkaarten
- [x] `templates/components/dagkaart.html` — Component met 3 states:
  - **Recept:** Naam, porties, categorie-emoji, basis, "X mnd geleden"
  - **HelloFresh:** Oranje balk, niet interactief
  - **Niet thuis:** Grijze balk
- [x] "Verder naar boodschappen" knop onderaan
- [x] Tests: Weekoverzicht toont 7 dagen, correcte receptnamen, HelloFresh-dagen zijn oranje

#### 1b. Shuffle

- [x] `POST /week/shuffle` → HTMX swap van het weekoverzicht (`hx-target="#week-content"`)
- [x] Genereert volledig nieuw menu, rendert dagkaarten opnieuw
- [x] Test: Na shuffle zijn recepten anders (seed-based test)

#### 1c. Vervang recept (↻ knop)

- [x] `GET /week/dag/{dag}/receptkiezer` → Rendert receptkiezer als partial (sheet)
- [x] `templates/pages/receptkiezer.html` — Zoekbalk, filter chips, receptenlijst
- [x] `templates/components/receptrij.html` — Naam, categorie, basis, bereidingstijd, "laatst gegeten"
- [x] `GET /week/dag/{dag}/receptkiezer?search=...&categorie=...` → HTMX live zoeken
- [x] `POST /week/dag/{dag}/kies/{recipe_id}` → Toont portiescherm
- [x] `templates/pages/porties.html` — Portiekeuze (2/3/4), "Toevoegen" knop
- [x] `POST /week/dag/{dag}/bevestig` → Plaatst recept, swapt dagkaart
- [x] Tests:
  - Receptkiezer toont recepten gesorteerd op "lang niet gegeten"
  - Zoeken filtert live
  - Filter chips werken (meerdere selecteerbaar)
  - Na bevestiging is de dagkaart geüpdatet

---

### Fase 2: Voorraadcheck (scherm 5.4)

**Doel:** Checklist met "Heb je nog...?" Ja/Nee per product.

- [ ] `GET /voorraad` — Genereert check-suggesties op basis van weekmenu
- [ ] `templates/pages/voorraad.html` — Twee secties: "Houdbare producten", "Standaard boodschappen"
- [ ] `templates/components/voorraaditem.html` — Productnaam, context (welk recept), Ja/Nee toggles
- [ ] `POST /voorraad/{item}/status` → HTMX swap van individueel item (toggle Ja/Nee)
- [ ] Default: "Nee" (veilige default — liever te veel dan te weinig)
- [ ] `POST /voorraad/bevestig` → Batch-update inventory, redirect naar boodschappenlijst
- [ ] "Naar boodschappenlijst" knop onderaan
- [ ] Tests:
  - Voorraadcheck toont items gegroepeerd op type
  - Ja/Nee toggle werkt via HTMX
  - Batch-update slaat alle statussen op

---

### Fase 3: Boodschappenlijst (scherm 5.5)

**Doel:** Geaggregeerde boodschappenlijst met secties.

- [ ] `GET /boodschappen` — Genereert lijst op basis van weekmenu + voorraadstatus
- [ ] `templates/pages/boodschappen.html` — Secties (Vlees & vis, Zuivel, Groente, etc.)
- [ ] `templates/components/boodschapitem.html` — Checkbox, naam, hoeveelheid
- [ ] `PATCH /boodschappen/{item_id}` → Toggle checked (HTMX swap)
- [ ] `DELETE /boodschappen/{item_id}` → Verwijder van lijst (HTMX swap out)
- [ ] `POST /boodschappen/toevoegen` → Handmatig product toevoegen (HTMX append)
- [ ] `PATCH /boodschappen/{item_id}/hoeveelheid` → Hoeveelheid aanpassen
- [ ] "Verstuur naar AH" knop onderaan
- [ ] Tests:
  - Lijst toont geaggregeerde ingrediënten per sectie
  - Checkbox toggle werkt
  - Handmatig toevoegen verschijnt in "Handmatig toegevoegd" sectie
  - Hoeveelheden zijn correct (400g gehakt i.p.v. 2x 200g)

---

### Fase 4: AH-integratie (scherm 5.6)

**Doel:** Boodschappenlijst versturen naar Albert Heijn.

- [ ] `GET /ah/status` → Check of AH-tokens geldig zijn
- [ ] `GET /ah/login` → Login-pagina met instructies + code-invoerveld
- [ ] `POST /ah/login` → Verwerk authorization code, sla tokens op
- [ ] `POST /boodschappen/verstuur-naar-ah` → Verstuur lijst, toon bevestigingsscherm
- [ ] `templates/pages/ah_bevestiging.html` — Groen vinkje, "X producten in je mandje", "Open AH" link
- [ ] Foutafhandeling: producten die niet gevonden zijn tonen
- [ ] Tests:
  - Login flow werkt
  - Bevestigingsscherm toont correcte aantallen
  - "Niet gevonden" producten worden getoond

---

### Fase 5: Kookmodus (scherm 5.7)

**Doel:** "Wat eten we vandaag?" — dagelijks recept bekijken.

- [ ] `GET /vandaag` → Recept van vandaag uit bevestigd weekmenu
- [ ] `GET /vandaag?datum=2026-02-14` → Recept voor specifieke datum
- [ ] `templates/pages/vandaag.html` — Receptnaam, porties, ingrediëntenlijst, kookboekverwijzing
- [ ] Navigatie: "Gisteren" / "Morgen" links (HTMX swap)
- [ ] Lege state: geen menu voor vandaag
- [ ] Tests:
  - Toont correct recept voor vandaag
  - Navigatie tussen dagen werkt
  - Ingrediënten zijn geschaald naar porties
  - Kookboekverwijzing wordt getoond

---

### Fase 6: Instellingen

**Doel:** Basisconfiguratie.

- [ ] `GET /instellingen` — Instellingenpagina
- [ ] HelloFresh-dagen configureren (welke dagen van de week)
- [ ] Standaard porties per dag (doordeweeks/weekend)
- [ ] Standaard basisproducten beheren
- [ ] `PATCH /instellingen` → Opslaan via HTMX
- [ ] Tests:
  - HelloFresh-dagen worden opgeslagen en toegepast bij menu genereren
  - Standaard porties worden correct overgenomen

---

### Fase 7: E2E-tests met Playwright

**Doel:** Volledige user flow automatisch testen.

- [ ] `test_weekly_flow.py` — Complete wekelijkse flow:
  1. Open `/week` → Weekoverzicht met automatisch voorstel
  2. Klik shuffle → Nieuw voorstel
  3. Klik ↻ op een dag → Receptkiezer opent
  4. Zoek en selecteer recept → Portiescherm
  5. Bevestig → Dagkaart geüpdatet
  6. "Verder naar boodschappen" → Voorraadcheck
  7. Beantwoord Ja/Nee → Boodschappenlijst
  8. Controleer lijst → Verstuur naar AH
  9. Bevestigingsscherm
- [ ] `test_kookmodus.py` — Kookmodus navigatie
- [ ] `test_responsive.py` — Mobiel vs desktop viewport tests

---

## 4. HTMX-patronen

### Pagina-navigatie

Volledige pagina-loads via `hx-boost="true"` op de body. Alle interne links worden automatisch via HTMX geladen (alleen de body wordt vervangen).

### Partials vs volledige pagina's

Elke route detecteert of het een HTMX-request is via de `HX-Request` header:
- **HTMX-request:** Rendert alleen de partial (component/fragment)
- **Volledige request:** Rendert de hele pagina met `base.html` layout

```python
@router.get("/week")
async def week(request: Request):
    menu = get_or_generate_menu()
    template = "components/week_content.html" if is_htmx(request) else "pages/week.html"
    return templates.TemplateResponse(template, {"menu": menu, "request": request})
```

### Interactie-mapping

| UI-actie | HTMX-attribuut | Route | Swap |
|----------|---------------|-------|------|
| Shuffle week | `hx-post="/week/shuffle"` | `POST /week/shuffle` | `#week-content` |
| Vervang recept | `hx-get="/week/dag/0/receptkiezer"` | `GET /week/dag/{dag}/receptkiezer` | `#sheet` (modal) |
| Zoek recept | `hx-get` + `hx-trigger="keyup changed delay:300ms"` | `GET /week/dag/{dag}/receptkiezer?search=...` | `#recepten-lijst` |
| Filter chip | `hx-get` + `hx-include="[name='categorie']"` | `GET /week/dag/{dag}/receptkiezer?categorie=...` | `#recepten-lijst` |
| Kies recept | `hx-post="/week/dag/0/kies/spaghetti-bolognese"` | `POST /week/dag/{dag}/kies/{recipe_id}` | `#sheet` |
| Bevestig porties | `hx-post="/week/dag/0/bevestig"` | `POST /week/dag/{dag}/bevestig` | `#dag-0` + sluit sheet |
| Voorraad Ja/Nee | `hx-post="/voorraad/pasta/status"` | `POST /voorraad/{item}/status` | `#voorraad-pasta` |
| Toggle boodschap | `hx-patch="/boodschappen/item-001"` | `PATCH /boodschappen/{item_id}` | `#item-001` |
| Verstuur naar AH | `hx-post="/boodschappen/verstuur-naar-ah"` | `POST /boodschappen/verstuur-naar-ah` | body (volledig scherm) |
| Dag navigatie | `hx-get="/vandaag?datum=2026-02-14"` | `GET /vandaag?datum=...` | `#vandaag-content` |

---

## 5. Tailwind-configuratie

### Custom kleuren (AH-palet)

```javascript
// tailwind.config.js (of inline in base.html via CDN config)
colors: {
    ah: {
        blue: '#00A0E2',
        'blue-dark': '#0077B3',
        'blue-light': '#E6F4FA',
        orange: '#FF6B00',
        green: '#4CAF50',
    }
}
```

### Responsive breakpoints

```
sm: 640px   → Mobiel landscape
md: 768px   → iPad portrait (split-view start)
lg: 1024px  → iPad landscape
```

### Mobiel-first approach

Alle componenten worden ontworpen voor mobiel. iPad split-view (sectie 7 uit ontwerp) wordt via `md:` breakpoint geactiveerd:

```html
<div class="md:grid md:grid-cols-[300px_1fr]">
    <div><!-- Weekoverzicht (altijd zichtbaar) --></div>
    <div class="hidden md:block"><!-- Receptkiezer (alleen iPad) --></div>
</div>
```

---

## 6. Testsstrategie

### Laag 1: Unit tests (pytest + TestClient)

- Elke route krijgt unit tests via FastAPI's `TestClient`
- Test zowel volledige pagina-requests als HTMX partial-requests
- Valideer HTML-structuur (juiste elementen, correcte data)
- Mock de repository/planner laag via dependency injection

### Laag 2: E2E tests (Playwright)

- Test de volledige user flow in een echte browser
- Gebruik Playwright's `page.locator()` voor assertions
- Test op mobiel viewport (375x812) en iPad viewport (768x1024)
- Draait tegen een live FastAPI-server met test-data

```python
# tests/e2e/conftest.py
@pytest.fixture(scope="session")
def app_server():
    """Start FastAPI server met test-data voor E2E tests."""
    ...

@pytest.fixture
async def page(browser):
    page = await browser.new_page(viewport={"width": 375, "height": 812})
    yield page
    await page.close()
```

### TDD per fase

Conform de CLAUDE.md richtlijnen: elke feature begint met een falende test.

```
1. Schrijf falende test (route geeft 404 of ontbrekend element)
2. Implementeer route + template
3. Test slaagt
4. Refactor (extractie naar components, styling)
```

---

## 7. Dependencies

### Toe te voegen aan `pyproject.toml`

```toml
dependencies = [
    # ... bestaande dependencies ...
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.34.0",
    "jinja2>=3.1.0",
    "python-multipart>=0.0.20",
]

[dependency-groups]
dev = [
    # ... bestaande dev dependencies ...
    "httpx>=0.28.0",
    "playwright>=1.50.0",
]
```

---

## 8. Niet in scope (v1)

Deze items worden bewust uitgesteld:

- PWA / service worker / offline support
- Receptfoto's
- Delen met andere gebruikers
- Meerdere weken vooruit plannen
- Micro-animaties (staggered fade-in, confetti) — functioneel eerst, polish later
- iPad split-view — responsive layout wordt voorbereid, maar focus is mobiel
