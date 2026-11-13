# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Boodschappenagent ("grocery agent") automates the weekly grocery process: plan a menu, generate a shopping list, check inventory, and order at Albert Heijn. Design docs of completed features live in `docs/features/`.

## Project Conventions

- Always check existing codebase before creating new files or scripts — reuse existing CLI tools and modules
- When editing files, double-check you are editing the correct file (e.g., testplan.md vs test code files, menu.py vs client.py)
- Use `uv` for all dependency management and script execution — never `pip` directly
- All Python code must pass `uv run ruff check .` and `uv run ruff format .`; fix any line-length violations before committing

## Testing

- **Always delegate test runs to the `test-reporter` subagent** — never run `uv run pytest` directly via Bash
- Follow TDD: write a failing test first (red), implement the minimum to pass (green), then refactor. Never write production code without a failing test first.
- When implementing test plan steps, use the exact naming conventions specified in the plan — do not invent alternative naming schemes
- E2E tests (Playwright, iPhone 13 viewport 390×844) are marked `@pytest.mark.e2e` and excluded from the default run: `uv run pytest -m e2e -n auto` (parallel, ~3x faster)

## Git Workflow

- When asked to commit, always check for unstaged files before finalizing
- Support amending commits when user requests it
- When rebasing, always verify the result compiles/tests pass before reporting success
- Create a feature branch before any implementation work
- For web UI changes: start the dev server (`uv run uvicorn boodschappenagent.web.app:create_app --factory --reload`) and verify the golden path in a browser before reporting the task complete

## Architecture Patterns

- **Frozen dataclasses** for all domain models
- **`to_dict()` / `from_dict()`** pattern for JSON serialization
- **Fluent interface** for search/filter chains (e.g. RecipeSearch)
- **Progressive constraint relaxation** in MenuPlanner (strict → relaxed fallback)
- **`random.Random(seed)`** for deterministic testing of random selection
- **Server-side rendering** with FastAPI + Jinja2 + HTMX (no SPA, HTML-over-the-wire)
- **App factory pattern** in `web/app.py` with `create_app()` for testability

## Design Principles

- **Simplicity (YAGNI)**: write code for the immediate requirement only. No abstractions for hypothetical future needs; three similar lines are fine before extracting a helper. No speculative features, error handling or validation. No half-finished implementations.
- **Seasons**: seasonal suitability of recipes is derived at runtime from a CO2-based vegetable calendar. Seasonal tags on individual recipes are forbidden.
- **Data**: JSON files under `data/` — no relational database.

## Module Boundaries

1. **`AHIntegratie` is the single AH façade.** Routers never import `AHClient` directly. AH business rules (list names, search limits, quantity calculation) live in `AHIntegratie`, not in routers.
2. **No intrusive coupling.** Never access private members (`_attr`) of collaborating objects; use the public API.
3. **Domain logic belongs in domain modules.** Routers only do HTTP marshalling (parse request, serialise response). Anything answering a domain question ("how many units do we need?") lives in the relevant domain/integration module.
4. **Dependency direction follows the pipeline:** `planner → boodschappenlijst → voorraadbeheer → ah`. Code that transforms a type belongs in the module that owns that type; eliminate reverse dependencies.

Invariants to preserve:
- All domain models stay frozen (`@dataclass(frozen=True)`).
- All object construction stays in `web/dependencies.py` (explicit, test-overridable composition root).
- Generic utilities (`IngredientNormalizer`, `PortionCalculator`, …) stay domain-agnostic and injectable.

UI/UX principles and styling conventions for the web layer live in `src/boodschappenagent/web/CLAUDE.md`.

## Documentation Lookup

Always use Context7 (via the `mcp__context7__resolve-library-id` and `mcp__context7__query-docs` tools) to look up documentation for libraries and frameworks. This ensures you get the most up-to-date information.
