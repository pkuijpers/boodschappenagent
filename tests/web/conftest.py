"""FastAPI TestClient fixtures voor web integratietests."""

from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from boodschappenagent.planner import MenuHistory, MenuPlanner
from boodschappenagent.repository import RecipeRepository
from boodschappenagent.web.app import create_app
from boodschappenagent.web.dependencies import get_menu_history

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
RECIPE_DIRS = ["gevogelte", "vis", "vlees", "vegetarisch"]


@pytest.fixture
def recipe_repository() -> RecipeRepository:
    """Echte RecipeRepository met data/recipes/ — niet gemockt."""
    return RecipeRepository()


@pytest.fixture
def menu_history(tmp_path) -> MenuHistory:
    """Lege MenuHistory op tmp_path (geen echte history.json)."""
    return MenuHistory(tmp_path / "history.json")


@pytest.fixture
def menu_planner(recipe_repository, menu_history) -> MenuPlanner:
    """Echte MenuPlanner met vaste random_seed voor determinisme."""
    recipes = []
    for subdir in RECIPE_DIRS:
        recipes.extend(recipe_repository.load_all(DATA_DIR / "recipes" / subdir))
    return MenuPlanner(recipes=recipes, history=menu_history, random_seed=42)


@pytest.fixture
def app_with_overrides(menu_history) -> FastAPI:
    """App met dependency_overrides voor alleen user-generated data (history).

    RecipeRepository en MenuPlanner draaien echt.
    """
    app = create_app()
    app.dependency_overrides[get_menu_history] = lambda: menu_history
    return app


@pytest.fixture
def client(app_with_overrides) -> TestClient:
    """TestClient met echte recepten en gemockte user data."""
    return TestClient(app_with_overrides)


@pytest.fixture
def htmx_client(app_with_overrides) -> TestClient:
    """TestClient die standaard HTMX headers meestuurt."""
    return TestClient(
        app_with_overrides,
        headers={
            "HX-Request": "true",
            "HX-Target": "week-content",
        },
    )
