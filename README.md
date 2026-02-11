# Boodschappenagent

End-to-end grocery automation: van recepten naar een gevulde AH-winkelwagen.

## Systeemoverzicht

```
Receptendatabase ──> Menuplanner ──> Boodschappenlijst ──> AH-integratie
                                          ^
                                          │
                                    Voorraadbeheer
```

| Component | Status | Beschrijving |
|-----------|--------|--------------|
| Receptendatabase | Klaar | 30 recepten in JSON, zoeken op seizoen/categorie/tags |
| Menuplanner | Klaar | Weekmenu met variatie, seizoenslogica en geschiedenis |
| Boodschappenlijst | Gepland | Aggregatie en optimalisatie van ingredienten |
| Voorraadbeheer | Gepland | Voorraad bijhouden met slimme restock-suggesties |
| AH-integratie | POC | OAuth2 mobile API voor favorieten en bestellingen |

## Quickstart

```bash
uv sync                  # Installeer dependencies
uv run pytest            # Run tests (248 tests)
uv run ruff check .      # Lint
uv run ruff format .     # Format
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
    cli/                 # CLI tooling (digitize)

data/recipes/            # 30 recepten in 4 categorieen (gevogelte, vis, vlees, vegetarisch)

tests/                   # 248 unit tests, TDD
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

OAuth2 mobile API (`api.ah.nl`) voor favorieten en producten.

```python
from boodschappenagent import AHClient, AHTokenManager

token_manager = AHTokenManager("data/tokens.json")
token_manager.login(auth_code)  # eenmalig na OAuth2 flow

client = AHClient(token_manager)
lists = client.get_lists()
results = client.search_products("spaghetti")
```

### Portiecalculator

Schaalt recepten naar gewenst aantal porties met slimme afronding per eenheid.

```python
from boodschappenagent.utils import PortionCalculator

scaled = PortionCalculator.scale_recipe(recipe, porties=3)
```

## Development

TDD (red-green-refactor) is verplicht. Code quality via ruff.

```bash
uv run pytest -v                 # Verbose tests
uv run pytest --cov              # Coverage rapport
uv run pytest tests/test_menu_planner.py  # Specifiek testbestand
uv run ruff check --fix .        # Auto-fix lint issues
```
