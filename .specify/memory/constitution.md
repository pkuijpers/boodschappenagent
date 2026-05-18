<!--
SYNC IMPACT REPORT
==================
Version change: 1.2.0 → 1.3.0

Bump rationale: MINOR — new Principle VII added to encode the modularity
architecture described in the 2026-05-15 modularity review. The principle
formalises the four coupling rules identified as violated issues and the
five structural properties identified as working well.

Modified principles:
  None — existing principles unchanged.

Added sections:
  VII. Module Boundaries and Coupling — four binding rules (façade access,
       no intrusive coupling, domain logic placement, dependency direction)
       plus three structural invariants to preserve.

Removed sections:
  None

Templates reviewed:
  ✅ .specify/templates/plan-template.md — Constitution Check section picks
     up new principle via "Gates determined based on constitution file";
     no template text changes needed.
  ✅ .specify/templates/spec-template.md — no updates needed.
  ✅ .specify/templates/tasks-template.md — no updates needed.
  ℹ  .specify/templates/commands/ — directory does not exist; skipped.

Deferred items:
  None
-->

# Boodschappenagent Constitution

## Core Principles

### I. Test-Driven Development (NON-NEGOTIABLE)

Every feature MUST follow the Red-Green-Refactor cycle: write a failing test
first, implement only enough code to make the test pass, then refactor.
Production code without a prior failing test is not acceptable.
AI-assisted development sessions MUST apply this discipline even for small
changes. Test runs MUST be delegated to the `test-reporter` subagent — never
run `uv run pytest` directly in main agentic sessions.

### II. Server-Side Rendering

The web layer MUST use FastAPI + Jinja2 + HTMX (HTML-over-the-wire). SPA
frameworks (React, Vue, Angular) are forbidden. All dynamic behavior MUST be
driven by HTMX partial page updates. The server renders complete HTML; the
client receives HTML, not JSON API responses.

### III. Simplicity (YAGNI)

Code MUST be written for the immediate requirement only. Abstractions for
hypothetical future requirements MUST NOT be introduced. Three similar lines
is acceptable before a shared helper is warranted. Speculative features,
error handling, and validation MUST NOT be added. No half-finished
implementations.

### IV. Code Quality Gates

All Python code MUST pass `ruff check` and `ruff format` before commit.
Line-length violations MUST be fixed. In templates, inline `style` attributes
and hardcoded hex color values are forbidden; all visual tokens MUST be
defined once in the Tailwind config inside `base.html` using semantic names
(`ah-*` for Albert Heijn brand, `hf-*` for HelloFresh, `muted-*` for
inactive/disabled states).

### V. Domain Modelling

All domain models MUST be frozen dataclasses. Serialization MUST use the
`to_dict()` / `from_dict()` pattern. Search and filter chains MUST use a
fluent interface. Data is persisted in JSON files under `data/`; no
relational database is used.

Seasonal suitability of recipes MUST be derived at runtime from a CO2-based
vegetable calendar, not from static tags on individual recipes. Seasonal tags
on recipes are forbidden.

### VI. UI/UX Design Philosophy

The UI MUST follow the "Systeem stelt voor, jij past aan" principle: the app
always opens with a fully populated weekly menu proposal — never a blank
screen. The user's task is to reject or replace, not to build from zero.

All interactive targets MUST be at least 44×44 pt (touch-first). The primary
platform is iOS/iPadOS (iPhone 13 viewport: 390×844 for E2E tests). All
screen transitions MUST use HTMX out-of-band updates: when a sheet is open
and the user triggers a change (dagtype, persons, shuffle recipe), the
background dagkaart MUST update in place while the sheet remains open. No
full-page reloads for within-session changes.

The weekly ordering flow is a fixed sequence:
Weekoverzicht → (optioneel) Recept vervangen / Shuffle → Ingredient-selectie →
Voorraadcheck → Matching → Match-review → AH Bevestiging.
Kookmodus is a separate daily flow, independent of the ordering flow.
No step MAY be skipped by the system; the user MAY choose to proceed past
any step directly.

### VII. Module Boundaries and Coupling

Code MUST respect the module boundaries defined by the domain map and must
not introduce unbalanced coupling between modules. Four binding rules apply:

**1. AHIntegratie is the single AH façade.**
All access to the AH API from the web layer MUST go through `AHIntegratie`.
Routers MUST NOT import `AHClient` directly. Business rules about AH
integration (list names, search limits, quantity calculation) MUST live
inside `AHIntegratie`, not in routers.

**2. No intrusive coupling.**
Callers MUST NOT access private members (`_attr`) of collaborating objects.
Integration MUST use the public API of the target module. Reaching past a
façade into its implementation details is forbidden.

**3. Domain logic belongs in domain modules.**
Business calculations and rules MUST NOT be placed in the HTTP delivery
layer. Routers are responsible for HTTP marshalling only: parsing request
data and serialising response data. Any logic that answers a domain question
(e.g., "how many units do we need?") MUST live in the relevant domain or
integration module.

**4. Dependency direction follows the domain pipeline.**
Module dependencies MUST flow in the direction of the domain pipeline:
`planner → boodschappenlijst → voorraadbeheer → ah`. A module that
transforms a type owned by another module belongs in the owning module.
Reverse dependencies (e.g., `voorraadbeheer` importing `boodschappenlijst`
models) MUST be eliminated by moving the code to the correct module.

Three structural invariants MUST be preserved:

- **Frozen dataclasses**: All domain models MUST remain frozen (`@dataclass(frozen=True)`).
  This eliminates mutation-based coupling where callers silently depend on
  shared mutable state.
- **Centralised dependency injection**: All object construction MUST remain
  in `dependencies.py`. The composition root MUST be explicit and
  test-overridable.
- **Generic utilities stay generic**: `IngredientNormalizer`, `PortionCalculator`,
  and similar utilities MUST remain domain-agnostic and injectable. They MUST
  NOT acquire domain-specific knowledge.

## Technical Standards

**Language**: Python 3.14+

**Package manager**: uv — MUST be used for all dependency management and
script execution (`uv run`, `uv add`, `uv sync`). Never use `pip` directly.

**Web framework**: FastAPI with Jinja2 server-side rendering; app factory
pattern via `create_app()` for testability.

**Frontend**: HTMX + Tailwind CSS (CDN) — no bundler, no SPA.
Color tokens defined in `base.html` Tailwind config:
`ah-blue (#00A0E2)`, `ah-blue-dark (#0077B3)`, `hf-orange (#FF6B00)`,
`muted-bg (#F5F5F5)`.

**Testing stack**: pytest for unit tests; Playwright for E2E tests
(iPhone 13 emulation, 390×844). E2E tests are marked `@pytest.mark.e2e`.

**Linting/Formatting**: ruff — MUST pass before every commit.

**Data storage**: JSON files under `data/` — no relational database.

**AH integration**: OAuth2 mobile API (`api.ah.nl/mobile-auth/v1/auth/token`,
client_id `appie`); GraphQL at `api.ah.nl/graphql`.

## Development Workflow

1. **Branch** — create a feature branch before any implementation work.
2. **Red** — write a failing unit test that describes the intended behavior.
3. **Green** — implement the minimum code to pass the test.
4. **Refactor** — improve code quality while keeping tests green.
5. **Lint** — run `uv run ruff check --fix .` and `uv run ruff format .`.
6. **Commit** — stage and commit with a descriptive message; check for
   unstaged files before finalizing.
7. **E2E** — for web features, run Playwright E2E tests after unit tests pass
   (`uv run pytest -m e2e`).

When working on web UI changes, the dev server MUST be started and the golden
path verified in a browser before reporting the task complete.

## Governance

This constitution supersedes all other development practices. Conflicts
between this document and any tool default, library convention, or prior
practice MUST be resolved in favor of this constitution.

**Amendment procedure**: Any change to core principles requires a version bump
per the versioning policy below, a completed Sync Impact Report prepended as
an HTML comment, and updates to all dependent templates before the change
takes effect.

**Versioning policy**:
- MAJOR — removal or backward-incompatible redefinition of a core principle
- MINOR — new principle or section added, or materially expanded guidance
- PATCH — wording clarifications, typo fixes, non-semantic refinements

**Compliance**: All agent-assisted development sessions MUST load this
constitution before starting work. All PRs MUST be verified against active
principles before merge.

Runtime development guidance: `CLAUDE.md`

**Version**: 1.3.0 | **Ratified**: 2026-05-11 | **Last Amended**: 2026-05-18
