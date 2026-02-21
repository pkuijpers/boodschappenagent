"""Dependency injection voor de web module."""

from pathlib import Path

from boodschappenagent.models import Recipe
from boodschappenagent.planner import MenuHistory, MenuPlanner
from boodschappenagent.repository import RecipeRepository

DATA_DIR = Path(__file__).resolve().parents[3] / "data"
RECIPE_DIRS = ["gevogelte", "vis", "vlees", "vegetarisch"]


def get_recipe_repository() -> RecipeRepository:
    """Geeft een RecipeRepository terug."""
    return RecipeRepository()


def get_menu_history() -> MenuHistory:
    """Geeft een MenuHistory terug met de standaard history file."""
    return MenuHistory(DATA_DIR / "history.json")


def get_all_recipes() -> list[Recipe]:
    """Geeft alle recepten terug uit alle categorieën."""
    repository = get_recipe_repository()
    recipes: list[Recipe] = []
    for subdir in RECIPE_DIRS:
        recipes.extend(repository.load_all(DATA_DIR / "recipes" / subdir))
    return recipes


def get_menu_planner() -> MenuPlanner:
    """Geeft een MenuPlanner terug met recepten en history."""
    repository = get_recipe_repository()
    history = get_menu_history()
    recipes = []
    for subdir in RECIPE_DIRS:
        recipes.extend(repository.load_all(DATA_DIR / "recipes" / subdir))
    return MenuPlanner(recipes=recipes, history=history)
