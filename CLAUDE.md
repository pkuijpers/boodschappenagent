# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Boodschappenagent ("grocery agent") is an end-to-end grocery automation system. The project is currently in POC/planning phase.

### System Components

1. **Receptendatabase** — Recipe storage with ingredients, portions, seasons, and tags
2. **Menuplanner** — Automated weekly menu suggestions based on season and variety
3. **Voorraadbeheer** — Inventory tracking with smart restock suggestions
4. **Boodschappenlijst-generator** — Aggregates and optimizes shopping lists
5. **AH-integratie** — Albert Heijn integration for placing orders

### Development Phases

1. Digitize recipes and set up database
2. Build menu planner with portion calculation
3. Shopping list generator
4. Add inventory management
5. AH integration (after POC decision)

## Integration Approaches Under Evaluation

Two approaches are being evaluated for AH integration:

1. **Optie B: Mijn Lijstje API** - Reverse-engineering AH's internal API to add products to a shopping list programmatically. Preferred if API endpoints are stable and accessible.

2. **Optie C: Browser Automation (Playwright)** - Automating browser interactions to search and add products. Fallback option if API approach fails.

## Key Technical Decisions (Pending POC Results)

- **Language**: Python 3.14+
- **Package management**: uv (use `uv` for all Python dependency and environment management)
- **Database**: SQLite or JSON files (TBD)
- **Frontend**: Simple web UI or CLI, with PWA for mobile access
- **Browser automation**: Playwright (if needed for AH integration)
- **Authentication**: Cookie-based session management (both AH approaches)
- **Product mapping**: Ingredient-to-search-term translation with fallback strategies

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
src/
└── boodschappenagent/       # Main package (src-layout)
    ├── __init__.py          # Exports: AHClient, FavoriteList, Product
    └── ah_client.py         # AH API client

tests/                       # Unit tests
├── conftest.py
├── test_ah_client.py
└── test_10_products.py

poc-ah-lijstje/              # POC documentation
└── API_DOCUMENTATION.md
```

### Usage

```python
from boodschappenagent import AHClient, Product, FavoriteList
```

## Test Products

The POC uses a standard set of 10 products to evaluate both approaches: halfvolle melk, scharrelei, rundergehakt, verse spinazie, knoflook, Parmezaanse kaas, spaghetti, passata, verse basilicum, and pancetta.

## Documentation Lookup

Always use Context7 (via the `mcp__context7__resolve-library-id` and `mcp__context7__query-docs` tools) to look up documentation for libraries and frameworks. This ensures you get the most up-to-date information.
