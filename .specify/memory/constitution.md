<!--
SYNC IMPACT REPORT
==================
Version change: (none) → 1.0.0 (initial constitution — first ratification)

Modified principles:
  N/A (first creation; all placeholders replaced)

Added sections:
  - Core Principles (5 principles)
  - Technical Standards
  - Development Workflow
  - Governance

Removed sections:
  N/A

Templates reviewed:
  ✅ .specify/templates/plan-template.md — Constitution Check gate is generic;
     no outdated references found
  ✅ .specify/templates/spec-template.md — no constitution-specific tokens;
     no updates needed
  ✅ .specify/templates/tasks-template.md — task categorization aligns with TDD
     principle; no updates needed
  ℹ  .specify/templates/commands/ — directory does not exist; skipped

Deferred items:
  None — all placeholders resolved
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
(`ah-*`, `hf-*`, `muted-*`).

### V. Domain Modelling

All domain models MUST be frozen dataclasses. Serialization MUST use the
`to_dict()` / `from_dict()` pattern. Search and filter chains MUST use a
fluent interface. Data is persisted in JSON files under `data/`; no
relational database is used.

## Technical Standards

**Language**: Python 3.14+

**Package manager**: uv — MUST be used for all dependency management and
script execution (`uv run`, `uv add`, `uv sync`). Never use `pip` directly.

**Web framework**: FastAPI with Jinja2 server-side rendering; app factory
pattern via `create_app()` for testability.

**Frontend**: HTMX + Tailwind CSS (CDN) — no bundler, no SPA.

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

**Version**: 1.0.0 | **Ratified**: 2026-05-11 | **Last Amended**: 2026-05-11
