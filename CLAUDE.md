# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Conventions

- This is a Python project using FastAPI, HTMX, and pytest
- Always check existing codebase before creating new files or scripts — reuse existing CLI tools and modules
- When editing files, double-check you are editing the correct file (e.g., testplan.md vs test code files, menu.py vs client.py)
- Use ruff for linting; fix any line-length violations before committing

## Testing

- Always run the full test suite (`pytest` or equivalent) after any code changes before committing
- Follow TDD workflow: write failing tests first (red), then implement (green), then refactor
- When implementing test plan steps, use the exact naming conventions specified in the plan — do not invent alternative naming schemes

## Git Workflow

- When asked to commit, always check for unstaged files before finalizing
- Support amending commits when user requests it
- When rebasing, always verify the result compiles/tests pass before reporting success

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
| Web UI | In progress | FastAPI + HTMX + Tailwind CSS frontend (fase 0 done) |

### Development Phases

1. ~~Digitize recipes and set up database~~ (done)
2. ~~Build menu planner with portion calculation~~ (done)
3. Shopping list generator
4. Add inventory management
5. AH integration (after POC decision)
6. **Web UI** — FastAPI + HTMX + Tailwind CSS (fase 0 done, see `docs/implementatieplan-ui.md`)

## Key Technical Decisions

- **Language**: Python 3.14+
- **Package management**: uv (use `uv` for all Python dependency and environment management)
- **Data storage**: JSON files (recipes in `data/recipes/`, history in `data/history.json`)
- **AH authentication**: OAuth2 mobile API (`api.ah.nl/mobile-auth/v1/auth/token`, client_id `appie`)
- **AH GraphQL**: `api.ah.nl/graphql` (mobile endpoint)
- **Web framework**: FastAPI with Jinja2 server-side rendering
- **Frontend**: HTMX (HTML-over-the-wire, no SPA) + Tailwind CSS (CDN)
- **E2E testing**: Playwright

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
uv run pytest                 # Run all tests (excludes E2E by default)
uv run pytest -v              # Verbose output
uv run pytest --cov           # Run with coverage report
uv run pytest tests/test_x.py # Run specific test file
```

### E2E Testing (Playwright)

E2E tests use Playwright and are marked with `@pytest.mark.e2e`. They run a live FastAPI server with test data (iPhone 13 viewport, 390x844).

```bash
uv run playwright install     # Install browsers (one-time setup)
uv run pytest -m e2e          # Run E2E tests only
uv run pytest -m e2e --headed # Run E2E tests with visible browser
```

E2E test structure:
- `tests/e2e/conftest.py` — Fixtures: live server with test data (`TEST_WEEK_MENU`), iPhone 13 emulation
- `tests/e2e/test_week_overview.py` — Week overview page tests (dagkaarten, HelloFresh, niet-thuis, navigatie)

## Commands

```bash
uv sync              # Install dependencies
uv add <package>     # Add a dependency
uv run python ...    # Run Python scripts
uv run pytest        # Run tests (excludes E2E)
uv run pytest -m e2e # Run E2E tests (Playwright)
uv run ruff check .  # Lint code
uv run ruff format . # Format code
uv run uvicorn boodschappenagent.web.app:create_app --factory --reload  # Start dev server
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
    web/
        __init__.py          # Exports: create_app
        app.py               # FastAPI app factory with Jinja2 templating
        dependencies.py      # Dependency injection (RecipeRepository, MenuPlanner, MenuHistory)
        routers/
            __init__.py
            menu.py          # GET / (redirect), GET /week (weekoverzicht)
        templates/
            base.html        # Layout: Tailwind CDN, HTMX, AH color palette
            components/
                tab_bar.html # Tab bar navigation (Week / Vandaag / Instellingen)
            pages/
                week.html    # Week overview page
        static/
            css/app.css      # Custom Tailwind styles

data/
    recipes/                 # 30 recipes in 4 subdirectories
        gevogelte/           # 7 chicken/poultry recipes
        vis/                 # 5 fish recipes
        vlees/               # 6 meat recipes
        vegetarisch/         # 8 vegetarian recipes
        draft/               # Unprocessed recipe batches

tests/                       # 440 unit tests
    web/                     # FastAPI route tests (TestClient)
    e2e/                     # Playwright E2E tests (live server, iPhone 13 emulation)
docs/                        # Design documentation
```

### Key Imports

```python
from boodschappenagent import AHClient, AHTokenManager, Product, FavoriteList
from boodschappenagent.models import Recipe, Ingredient, Categorie, Basis, Seizoen
from boodschappenagent.repository import RecipeRepository, RecipeSearch
from boodschappenagent.planner import MenuPlanner, MenuHistory, DagInput, DagPlanning, WeekMenu
from boodschappenagent.utils import PortionCalculator
from boodschappenagent.web import create_app
```

## Architecture Patterns

- **Frozen dataclasses** for all domain models (Recipe, Ingredient, DagInput, DagPlanning, WeekMenu)
- **`to_dict()` / `from_dict()`** pattern for JSON serialization
- **Fluent interface** for RecipeSearch (chained filtering)
- **Progressive constraint relaxation** in MenuPlanner (strict → relaxed fallback)
- **`random.Random(seed)`** for deterministic testing of random selection
- **Server-side rendering** with FastAPI + Jinja2 + HTMX (no SPA, HTML-over-the-wire)
- **App factory pattern** in `web/app.py` with `create_app()` for testability

## Styling Conventions

All colors and visual tokens are defined **once** in the Tailwind config in `base.html`. Never use inline `style` attributes or hardcoded hex color codes in templates.

- **Use Tailwind utility classes** (`bg-ah-blue`, `text-hf-text`, `bg-muted-bg`) — never inline `style="color: #..."`.
- **Add new colors to the Tailwind config** in `base.html` under `tailwind.config.theme.extend.colors` before using them in templates.
- **Use semantic color names** grouped by domain: `ah-*` (Albert Heijn brand), `hf-*` (HelloFresh), `muted-*` (inactive/disabled states).

## Documentation Lookup

Always use Context7 (via the `mcp__context7__resolve-library-id` and `mcp__context7__query-docs` tools) to look up documentation for libraries and frameworks. This ensures you get the most up-to-date information.

