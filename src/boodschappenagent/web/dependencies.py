"""Dependency injection voor de web module."""

from pathlib import Path

from boodschappenagent.planner import MenuHistory, MenuPlanner
from boodschappenagent.repository import RecipeRepository

DATA_DIR = Path(__file__).resolve().parents[3] / "data"


def get_recipe_repository() -> RecipeRepository:
    """Geeft een RecipeRepository terug met de standaard data directory."""
    return RecipeRepository(DATA_DIR / "recipes")


def get_menu_history() -> MenuHistory:
    """Geeft een MenuHistory terug met de standaard history file."""
    return MenuHistory(DATA_DIR / "history.json")


def get_menu_planner() -> MenuPlanner:
    """Geeft een MenuPlanner terug met repository en history."""
    repository = get_recipe_repository()
    history = get_menu_history()
    return MenuPlanner(repository=repository, history=history)
