# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Boodschappenagent ("grocery agent") is an end-to-end grocery automation system that automates the weekly grocery process: plan a menu, generate a shopping list, and order at Albert Heijn.

### System Components

| Component | Status | Description |
|-----------|--------|-------------|
| Receptendatabase | Done | 30 recipes in JSON with ingredients, portions, seasons, tags |
| Menuplanner | Done | Weekly menu with variety constraints, season logic, history |
| Boodschappenlijst | Planned | Aggregate ingredients into optimized shopping list |
| Voorraadbeheer | Planned | Inventory tracking with smart restock suggestions |
| AH-integratie | POC | OAuth2 mobile API for favorites and orders |

### Development Phases

1. ~~Digitize recipes and set up database~~ (done)
2. ~~Build menu planner with portion calculation~~ (done)
3. Shopping list generator
4. Add inventory management
5. AH integration (after POC decision)

## Key Technical Decisions

- **Language**: Python 3.14+
- **Package management**: uv (use `uv` for all Python dependency and environment management)
- **Data storage**: JSON files (recipes in `data/recipes/`, history in `data/history.json`)
- **AH authentication**: OAuth2 mobile API (`api.ah.nl/mobile-auth/v1/auth/token`, client_id `appie`)
- **AH GraphQL**: `api.ah.nl/graphql` (mobile endpoint)

## Development Workflow

### TDD (Test-Driven Development)

All code must follow TDD principles:

1. **Red**: Write a failing unit test first
2. **Green**: Write the minimum code to make the test pass
3. **Refactor**: Improve the code while keeping tests green

Never write production code without a failing test first.

### Code Quality

All Python code must pass ruff linting and formatting:

```bash
uv run ruff check .           # Run linter
uv run ruff check --fix .     # Auto-fix linting issues
uv run ruff format .          # Format code
uv run ruff format --check .  # Check formatting without changing
```

### Testing

All code must have unit tests with good coverage:

```bash
uv run pytest                 # Run all tests
uv run pytest -v              # Verbose output
uv run pytest --cov           # Run with coverage report
uv run pytest tests/test_x.py # Run specific test file
```

## Commands

```bash
uv sync              # Install dependencies
uv add <package>     # Add a dependency
uv run python ...    # Run Python scripts
uv run pytest        # Run tests
uv run ruff check .  # Lint code
uv run ruff format . # Format code
```

## Project Structure

```
src/boodschappenagent/
    __init__.py              # Exports: AHClient, AHTokenManager, FavoriteList, Product
    models/
        __init__.py          # Exports: Recipe, Ingredient, Categorie, Basis, Seizoen
        enums.py             # Seizoen, Categorie, Basis enums
        ingredient.py        # Ingredient dataclass with scale()
        recipe.py            # Recipe dataclass with scale_to_portions(), to_dict/from_dict
    repository/
        __init__.py          # Exports: RecipeRepository, RecipeSearch
        recipe_repository.py # JSON load/save/delete for recipes
        recipe_search.py     # Fluent filtering API (seizoen, categorie, tags, naam)
    planner/
        __init__.py          # Exports: MenuPlanner, MenuHistory, DagInput, DagPlanning, WeekMenu
        models.py            # DagInput, DagPlanning, WeekMenu (frozen dataclasses)
        history.py           # MenuHistory (JSON persistence for menu history)
        menu_planner.py      # MenuPlanner (selection logic with variety + fallback)
    utils/
        __init__.py          # Exports: PortionCalculator
        portion_calculator.py # Scale recipes with smart rounding per unit
    ah/
        __init__.py          # Exports: AHClient, AHTokenManager, FavoriteList, Product
        auth.py              # AHTokenManager (OAuth2 token management)
        client.py            # AHClient (GraphQL queries, product search, list management)
        models.py            # Product, FavoriteList dataclasses
    digitizer/
        __init__.py          # Exports: BatchProcessor, PDFProcessor, RecipeExtractor
        pdf_processor.py     # PDF page extraction via PyMuPDF
        recipe_extractor.py  # Claude Vision API for recipe OCR
        batch_processor.py   # Batch processing of recipe PDFs
    cli/
        digitize.py          # CLI tool for bulk recipe digitization

data/
    recipes/                 # 30 recipes in 4 subdirectories
        gevogelte/           # 7 chicken/poultry recipes
        vis/                 # 5 fish recipes
        vlees/               # 6 meat recipes
        vegetarisch/         # 8 vegetarian recipes
        draft/               # Unprocessed recipe batches

tests/                       # 248 unit tests
docs/                        # Design documentation
```

### Key Imports

```python
from boodschappenagent import AHClient, AHTokenManager, Product, FavoriteList
from boodschappenagent.models import Recipe, Ingredient, Categorie, Basis, Seizoen
from boodschappenagent.repository import RecipeRepository, RecipeSearch
from boodschappenagent.planner import MenuPlanner, MenuHistory, DagInput, DagPlanning, WeekMenu
from boodschappenagent.utils import PortionCalculator
```

## Architecture Patterns

- **Frozen dataclasses** for all domain models (Recipe, Ingredient, DagInput, DagPlanning, WeekMenu)
- **`to_dict()` / `from_dict()`** pattern for JSON serialization
- **Fluent interface** for RecipeSearch (chained filtering)
- **Progressive constraint relaxation** in MenuPlanner (strict → relaxed fallback)
- **`random.Random(seed)`** for deterministic testing of random selection

## Documentation Lookup

Always use Context7 (via the `mcp__context7__resolve-library-id` and `mcp__context7__query-docs` tools) to look up documentation for libraries and frameworks. This ensures you get the most up-to-date information.
