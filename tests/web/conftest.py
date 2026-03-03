"""FastAPI TestClient fixtures voor web integratietests."""

import pytest
from bs4 import BeautifulSoup
from fastapi import FastAPI
from fastapi.testclient import TestClient

from boodschappenagent.models import Basis, Categorie, Ingredient, Seizoen
from boodschappenagent.models.recipe import Recipe
from boodschappenagent.planner import (
    DagPlanning,
    MenuHistory,
    MenuPlanner,
    SeizoenKalender,
    WeekMenu,
)
from boodschappenagent.repository import RecipeRepository
from boodschappenagent.web.app import create_app
from boodschappenagent.web.dependencies import (
    DATA_DIR,
    RECIPE_DIRS,
    get_all_recipes,
    get_menu_history,
    get_menu_planner,
)

WEEK_START = "2026-02-16"  # Week 8


# --- Recipe test data ---


def _make_recipe(id: str, naam: str, categorie: Categorie, basis: Basis) -> Recipe:
    """Helper om een minimaal Recipe object te maken."""
    return Recipe(
        id=id,
        naam=naam,
        categorie=categorie,
        basis=basis,
        seizoenen=[Seizoen.ALLE],
        basis_porties=2,
        ingredienten=[
            Ingredient(naam="test", hoeveelheid=1, eenheid="stuk"),
        ],
    )


RECEPTEN = [
    _make_recipe("kip-curry", "Kip curry", Categorie.GEVOGELTE, Basis.RIJST),
    _make_recipe("bolognese", "Pasta bolognese", Categorie.VLEES, Basis.PASTA),
    _make_recipe("zalm", "Zalm teriyaki", Categorie.VIS, Basis.RIJST),
    _make_recipe("linzensoep", "Rode linzensoep", Categorie.VEGETARISCH, Basis.GEEN),
    _make_recipe("kip-pesto", "Kip pesto pasta", Categorie.GEVOGELTE, Basis.PASTA),
    _make_recipe("vissticks", "Vissticks", Categorie.VIS, Basis.AARDAPPEL),
    _make_recipe("chili", "Chili sin carne", Categorie.VEGETARISCH, Basis.RIJST),
]


# --- WeekMenu builders ---


def make_full_week_menu(personen: int = 2) -> WeekMenu:
    """Maak een weekmenu met 7 kookdagen."""
    dagen = [
        DagPlanning(dag=i, recept=RECEPTEN[i], personen=personen) for i in range(7)
    ]
    return WeekMenu(week_start=WEEK_START, dagen=dagen)


def make_week_menu_met_niet_thuis(niet_thuis_dag: int = 5) -> WeekMenu:
    """Maak een weekmenu met één niet-thuis dag."""
    dagen = []
    for i in range(7):
        if i == niet_thuis_dag:
            dagen.append(DagPlanning(dag=i, recept=None, personen=0))
        else:
            dagen.append(DagPlanning(dag=i, recept=RECEPTEN[i], personen=2))
    return WeekMenu(week_start=WEEK_START, dagen=dagen)


# --- TestClient helpers ---


def set_week_menu(
    client: TestClient,
    week_menu: WeekMenu,
    hellofresh_dagen: set | None = None,
):
    """Stel weekmenu en hellofresh_dagen in op app.state."""
    client.app.state.week_menu = week_menu
    client.app.state.hellofresh_dagen = hellofresh_dagen or set()


def soup(response) -> BeautifulSoup:
    """Parse HTML response naar BeautifulSoup."""
    return BeautifulSoup(response.text, "html.parser")


# --- Fixtures ---


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
    kalender = SeizoenKalender()
    return MenuPlanner(
        recipes=recipes,
        history=menu_history,
        kalender=kalender,
        random_seed=42,
    )


@pytest.fixture
def all_recipes(recipe_repository) -> list[Recipe]:
    """Alle recepten uit data/recipes/ + test recepten — voor receptkiezer tests."""
    recipes: list[Recipe] = []
    for subdir in RECIPE_DIRS:
        recipes.extend(recipe_repository.load_all(DATA_DIR / "recipes" / subdir))
    # Voeg test recepten toe zodat kies/bevestig routes werken met test data
    existing_ids = {r.id for r in recipes}
    for r in RECEPTEN:
        if r.id not in existing_ids:
            recipes.append(r)
    return recipes


@pytest.fixture
def app_with_overrides(menu_history, menu_planner, all_recipes) -> FastAPI:
    """App met dependency_overrides voor user-generated data en planner."""
    app = create_app()
    app.dependency_overrides[get_menu_history] = lambda: menu_history
    app.dependency_overrides[get_menu_planner] = lambda: menu_planner
    app.dependency_overrides[get_all_recipes] = lambda: all_recipes
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
