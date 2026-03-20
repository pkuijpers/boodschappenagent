# Test Reporter Memory

## Flaky Test Found (2026-03-20)

**FLAKY**: `tests/e2e/test_dag_aanpassen.py::TestDagTypeWijzigenUI::test_ander_recept_via_sheet[chromium]`
- Fails on every run (100% failure rate in 3 runs)
- Root cause: `MenuPlanner.vervang_recept()` fallback logic can select the same recipe when recipe pool is exhausted
- See `flaky-tests.md` for full analysis

## Project Test Suite Status

- **Total tests**: 933 unit + E2E tests
- **Test command**: `uv run pytest -v` (excludes E2E by default per pyproject.toml)
- **Test framework**: pytest with pytest-playwright for E2E
- **E2E test count**: 72 tests (11 selected in most recent runs)

## Key Test Paths

- `tests/web/` — FastAPI TestClient routes (menu, receptkiezer, shufflen, genereren, etc.)
- `tests/e2e/` — Playwright E2E tests (live server, iPhone 13 viewport 390x844)
- `tests/planner/`, `tests/repository/`, `tests/models/`, `tests/cli/` — Unit tests for core modules

## Test Configuration

- `pyproject.toml` configures pytest to exclude E2E by default
- `tests/e2e/conftest.py` provides: live server fixture, test data (`TEST_WEEK_MENU` with 5 recipes), iPhone 13 emulation
- Run with `uv run pytest` for unit tests only
- Run with `uv run pytest -m e2e` for E2E tests only

## Known Issues

1. **Flaky E2E Test**: Recipe shuffle can return same recipe due to limited test recipes (see flaky-tests.md)
