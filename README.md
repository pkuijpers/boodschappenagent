# Boodschappenagent

End-to-end grocery automation: van recepten naar een gevulde AH-winkelwagen.

## Systeemoverzicht

```
Receptendatabase ──> Menuplanner ──> Boodschappenlijst ──> AH-integratie
                                          ^
                                          │
                                    Voorraadbeheer

                        Web UI (FastAPI + HTMX + Tailwind)
                        └── Verbindt alle componenten in een browser-interface
```

| Component | Status | Beschrijving |
|-----------|--------|--------------|
| Receptendatabase | Klaar | 30 recepten in JSON, zoeken op seizoen/categorie/tags |
| Menuplanner | Klaar | Weekmenu met variatie, seizoenslogica en geschiedenis |
| Boodschappenlijst | Klaar | Aggregatie en optimalisatie van ingrediënten |
| Voorraadbeheer | Klaar | Voorraad bijhouden met slimme restock-suggesties |
| AH-integratie | POC | OAuth2 mobile API voor favorieten en bestellingen |
| Web UI | In ontwikkeling | FastAPI + HTMX + Tailwind CSS frontend |

## Quickstart

```bash
uv sync                  # Installeer dependencies
uv run pytest            # Run tests (440 unit tests)
uv run pytest -m e2e     # Run E2E tests (Playwright)
uv run ruff check .      # Lint
uv run ruff format .     # Format
uv run uvicorn boodschappenagent.web.app:create_app --factory --reload  # Start dev server
```

Vereist Python 3.14+.

## Projectstructuur

```
src/boodschappenagent/
    models/              # Recipe, Ingredient, enums (Categorie, Basis, Seizoen)
    repository/          # RecipeRepository (JSON), RecipeSearch (fluent filtering)
    planner/             # MenuPlanner, MenuHistory, DagInput/DagPlanning/WeekMenu
    utils/               # PortionCalculator
    ah/                  # AHClient, AHTokenManager (OAuth2 mobile API)
    digitizer/           # PDF-naar-recept extractie via Claude Vision
    cli/                 # CLI tooling (menu, voorraad, digitize)
    web/                 # FastAPI app, Jinja2 templates, HTMX + Tailwind

data/recipes/            # 30 recepten in 4 categorieen (gevogelte, vis, vlees, vegetarisch)

tests/                   # 440 unit tests, TDD
    web/                 # FastAPI route tests (TestClient)
    e2e/                 # Playwright E2E tests (live server, iPhone 13 emulatie)
docs/                    # Ontwerpdocumentatie
```

## Componenten

### Receptendatabase

30 gedigitaliseerde recepten als JSON, verdeeld over categorieen:

- **Categorie** (proteïnebron): vlees, gevogelte, vis, vegetarisch, veganistisch
- **Basis** (koolhydraat): pasta, rijst, aardappel, brood, geen
- **Seizoen**: lente, zomer, herfst, winter, alle

```python
from boodschappenagent.repository import RecipeRepository, RecipeSearch

recipes = RecipeRepository("data/recipes").load_all()
winter_vis = (RecipeSearch(recipes)
    .filter_by_seizoen(Seizoen.WINTER)
    .filter_by_categorie(Categorie.VIS)
    .results)
```

### Menuplanner

Automatische weekmenuplanning met:

- Seizoensfiltering
- Variatieconstraints (geen opeenvolgende zelfde categorie of basis)
- Progressieve constraint-relaxatie bij beperkte receptenpool
- Geschiedenischeck (recent gegeten recepten vermijden)
- Deterministische modus voor tests via `random_seed`

```python
from boodschappenagent.planner import MenuPlanner, MenuHistory, DagInput
from boodschappenagent.models import Seizoen

history = MenuHistory("data/history.json")
planner = MenuPlanner(recipes, history)

week = [DagInput(dag=i, personen=2) for i in range(7)]
week[3] = DagInput(dag=3, personen=0)  # donderdag niet thuis

menu = planner.plan_week(week, Seizoen.WINTER, "2026-02-09")
for dag in menu.dagen:
    if dag.recept:
        print(f"Dag {dag.dag}: {dag.recept.naam} ({dag.personen}p)")

# Recept vervangen met respect voor buren
menu = planner.vervang_recept(menu, dag=1, seizoen=Seizoen.WINTER)

# Opslaan in geschiedenis
history.add_week(menu)
```

### AH-integratie

OAuth2 mobile API (`api.ah.nl`) voor favorieten en producten. Tokens worden per worktree opgeslagen in `data/ah_tokens.json` (staat in `.gitignore`).

**Eenmalige login:**

1. Open deze URL in je browser:
   ```
   https://login.ah.nl/secure/oauth/authorize?client_id=appie&redirect_uri=appie://login-exit&response_type=code
   ```
2. Log in met je AH-account. De browser probeert daarna te redirecten naar `appie://login-exit?code=XXXX` — dat mislukt, maar de `code` staat in de adresbalk.
3. Wissel de code in:
   ```bash
   python -c "from boodschappenagent.ah.auth import AHTokenManager; AHTokenManager().login('JOUW_CODE_HIER')"
   ```

Daarna werkt `bestel` automatisch en worden tokens ververst als ze verlopen.

```python
from boodschappenagent import AHClient, AHTokenManager

token_manager = AHTokenManager()  # laadt tokens uit data/ah_tokens.json
client = AHClient(token_manager)
lists = client.get_lists()
results = client.search_products("spaghetti")
```

### Web UI

Server-side rendered frontend met FastAPI, HTMX en Tailwind CSS. Geen SPA — HTMX vervangt HTML-fragmenten bij interacties.

```bash
uv run uvicorn boodschappenagent.web.app:create_app --factory --reload
# Open http://127.0.0.1:8000/week
```

**Status:** Fase 0 (project setup) afgerond. Base layout met Tailwind, HTMX, AH-kleurenpalet en tab-bar navigatie. Zie `docs/implementatieplan-ui.md` voor de volledige fasering.

### Portiecalculator

Schaalt recepten naar gewenst aantal porties met slimme afronding per eenheid.

```python
from boodschappenagent.utils import PortionCalculator

scaled = PortionCalculator.scale_recipe(recipe, porties=3)
```

## CLI Gebruik

### Weekmenu plannen en bestellen

De volledige workflow van menu plannen tot bestellen bij AH:

```bash
# 1. Weekmenu genereren (seizoen wordt automatisch gedetecteerd)
uv run python -m boodschappenagent.cli.menu plan

# 2. Menu bekijken
uv run python -m boodschappenagent.cli.menu toon

# 3. Recept vervangen (bijv. dinsdag)
uv run python -m boodschappenagent.cli.menu vervang di

# 4. Boodschappenlijst genereren
uv run python -m boodschappenagent.cli.menu boodschappen

# 5. Bestellen bij Albert Heijn
uv run python -m boodschappenagent.cli.menu bestel

# 6. Menu accepteren (opslaan in geschiedenis)
uv run python -m boodschappenagent.cli.menu accepteer
```

**Opties bij `plan`:**

| Optie | Beschrijving | Voorbeeld |
|-------|-------------|-----------|
| `-p`, `--personen` | Standaard personen per dag (default: 2) | `-p 4` |
| `-v`, `--vrij` | Vrije dagen (komma-gescheiden) | `--vrij za,zo` |
| `-d`, `--dagen` | Per-dag personen (dag:aantal) | `--dagen ma:4,vr:3` |
| `-s`, `--seizoen` | Seizoen override (auto-detect) | `--seizoen winter` |
| `-w`, `--week` | Week startdatum | `--week 2026-03-02` |

**Opties bij `vervang`:**

| Optie | Beschrijving | Voorbeeld |
|-------|-------------|-----------|
| `-p`, `--personen` | Wijzig aantal personen | `vervang di -p 4` |
| `-v`, `--vrij` | Markeer dag als vrij | `vervang do --vrij` |
| `-s`, `--seizoen` | Seizoen override | `vervang di -s zomer` |

**Opties bij `bestel`:**

| Optie | Beschrijving | Voorbeeld |
|-------|-------------|-----------|
| `-f`, `--filter-voorraad` | Filter items op voorraad | `bestel -f` |
| `-n`, `--naam` | Naam voor de AH lijst | `bestel -n "Week 10"` |
| `-r`, `--ref` | AH referentielijst ID | `bestel --ref <list_id>` |

### Voorraadbeheer

Beheer je voorraad om boodschappenlijsten te optimaliseren:

```bash
# Voorraad initialiseren met standaard items
uv run python -m boodschappenagent.cli.voorraad init

# Voorraad bekijken
uv run python -m boodschappenagent.cli.voorraad toon

# Item markeren als op voorraad of leeg
uv run python -m boodschappenagent.cli.voorraad set pasta --op
uv run python -m boodschappenagent.cli.voorraad set melk --leeg

# Interactieve wekelijkse voorraadcheck
uv run python -m boodschappenagent.cli.voorraad check

# Synchroniseer voorraad met receptendatabase (ontdek nieuwe items)
uv run python -m boodschappenagent.cli.voorraad sync
```

## Development

TDD (red-green-refactor) is verplicht. Code quality via ruff.

```bash
uv run pytest -v                 # Verbose tests
uv run pytest --cov              # Coverage rapport
uv run pytest tests/test_menu_planner.py  # Specifiek testbestand
uv run ruff check --fix .        # Auto-fix lint issues
```

### E2E Tests (Playwright)

E2E tests draaien een live FastAPI-server met testdata en emuleren een iPhone 13 (390x844).

```bash
uv run playwright install        # Eenmalig: installeer browsers
uv run pytest -m e2e             # Run E2E tests (headless)
uv run pytest -m e2e --headed    # Run E2E tests met zichtbare browser
```

Tests zijn gemarkeerd met `@pytest.mark.e2e` en staan in `tests/e2e/`.
