# Test Reporter Memory

## Project Test Suite Status

- **Total tests**: 768 (includes 768 E2E tests, unit tests pass with E2E included)
- **Test command**: `uv run pytest -v` (excludes E2E by default per pyproject.toml)
- **Test framework**: pytest with pytest-playwright for E2E
- **Coverage**: Tests span: planner, repository, models, CLI, web routes, HTMX fragments, E2E UI

## Key Test Paths

- `tests/web/` — FastAPI TestClient routes (menu, receptkiezer, shufflen, genereren, etc.)
- `tests/e2e/` — Playwright E2E tests (live server, iPhone 13 viewport 390x844)
- `tests/planner/`, `tests/repository/`, `tests/models/`, `tests/cli/` — Unit tests for core modules

## Test Configuration

- `pyproject.toml` configures pytest to exclude E2E by default
- `tests/e2e/conftest.py` provides: live server fixture, test data (`TEST_WEEK_MENU`), iPhone 13 emulation
- Run with `uv run pytest` for unit tests only
- Run with `uv run pytest -m e2e` for E2E tests only

## Recent Run (2026-03-02)

**768 passed, 2 warnings in 47.05s**

- All tests passing
- 2 deprecation warnings from websockets and uvicorn (non-critical, related to Playwright infrastructure)
- No failures or errors
