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

- **Language**: Python 3.9+
- **Package management**: uv (use `uv` for all Python dependency and environment management)
- **Database**: SQLite or JSON files (TBD)
- **Frontend**: Simple web UI or CLI, with PWA for mobile access
- **Browser automation**: Playwright (if needed for AH integration)
- **Authentication**: Cookie-based session management (both AH approaches)
- **Product mapping**: Ingredient-to-search-term translation with fallback strategies

## Commands

```bash
uv sync              # Install dependencies
uv add <package>     # Add a dependency
uv run python ...    # Run Python scripts
uv run pytest        # Run tests
```

## Project Structure (Planned)

```
poc-ah-lijstje/          # API approach
├── ah_client.py         # API wrapper
├── product_mapper.py    # Ingredient → AH product mapping
└── test_poc.py

poc-ah-playwright/       # Browser automation approach
├── ah_automation.py     # Main automation script
├── auth/                # Saved browser sessions
└── test_poc.py
```

## Test Products

The POC uses a standard set of 10 products to evaluate both approaches: halfvolle melk, scharrelei, rundergehakt, verse spinazie, knoflook, Parmezaanse kaas, spaghetti, passata, verse basilicum, and pancetta.

## Documentation Lookup

Always use Context7 (via the `mcp__context7__resolve-library-id` and `mcp__context7__query-docs` tools) to look up documentation for libraries and frameworks. This ensures you get the most up-to-date information.
