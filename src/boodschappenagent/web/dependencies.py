"""Dependency injection voor de web module."""

from pathlib import Path

from boodschappenagent.ah import AHClient, AHIntegratie, AHTokenManager
from boodschappenagent.boodschappenlijst import (
    BoodschappenlijstGenerator,
    IngredientNormalizer,
)
from boodschappenagent.models import Recipe
from boodschappenagent.planner import MenuHistory, MenuPlanner, SeizoenKalender
from boodschappenagent.repository import RecipeRepository
from boodschappenagent.utils import PortionCalculator
from boodschappenagent.voorraadbeheer import (
    BoodschappenlijstFilter,
    VoorraadChecker,
    VoorraadRepository,
)

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
    kalender = SeizoenKalender()
    return MenuPlanner(recipes=recipes, history=history, kalender=kalender)


def get_voorraad_repository() -> VoorraadRepository:
    """Geeft een VoorraadRepository terug met de standaard voorraad file."""
    return VoorraadRepository(DATA_DIR / "voorraad.json")


def get_boodschappenlijst_generator() -> BoodschappenlijstGenerator:
    """Geeft een BoodschappenlijstGenerator terug met IngredientNormalizer."""
    normalizer = IngredientNormalizer()
    calculator = PortionCalculator()
    return BoodschappenlijstGenerator(normalizer, calculator)


def get_voorraad_checker() -> VoorraadChecker:
    """Geeft een VoorraadChecker terug met VoorraadRepository."""
    repository = get_voorraad_repository()
    return VoorraadChecker(repository)


def get_boodschappenlijst_filter() -> BoodschappenlijstFilter:
    """Geeft een BoodschappenlijstFilter terug met VoorraadRepository."""
    repository = get_voorraad_repository()
    return BoodschappenlijstFilter(repository)


def get_ah_token_manager() -> AHTokenManager:
    """AHTokenManager met standaard token path."""
    return AHTokenManager()


def get_ah_client() -> AHClient:
    """AHClient met AHTokenManager."""
    token_manager = get_ah_token_manager()
    return AHClient(token_manager)


def get_ah_integratie() -> AHIntegratie:
    """AHIntegratie met AHClient."""
    client = get_ah_client()
    return AHIntegratie(client)
