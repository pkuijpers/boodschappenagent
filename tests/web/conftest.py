"""FastAPI TestClient fixtures voor web integratietests."""

from unittest.mock import MagicMock

import pytest
from bs4 import BeautifulSoup
from fastapi import FastAPI
from fastapi.testclient import TestClient

from boodschappenagent.ah import ProductMatch, SyncResultaat
from boodschappenagent.boodschappenlijst import (
    BoodschappenlijstGenerator,
    IngredientNormalizer,
)
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
from boodschappenagent.utils import PortionCalculator
from boodschappenagent.voorraadbeheer import BoodschappenlijstFilter, VoorraadRepository
from boodschappenagent.voorraadbeheer.models import VoorraadItem, VoorraadType
from boodschappenagent.web.app import create_app
from boodschappenagent.web.dependencies import (
    DATA_DIR,
    RECIPE_DIRS,
    get_ah_integratie,
    get_ah_token_manager,
    get_all_recipes,
    get_boodschappenlijst_filter,
    get_boodschappenlijst_generator,
    get_menu_history,
    get_menu_planner,
    get_voorraad_repository,
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


def make_week_menu_met_hellofresh(hellofresh_dag: int = 2) -> WeekMenu:
    """Maak een weekmenu met één hellofresh dag (recept=None, personen=0)."""
    dagen = []
    for i in range(7):
        if i == hellofresh_dag:
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


# --- Voorraad fixtures ---


@pytest.fixture
def voorraad_repository(tmp_path) -> VoorraadRepository:
    """VoorraadRepository op tmp_path (geen echte voorraad.json)."""
    return VoorraadRepository(tmp_path / "voorraad.json")


@pytest.fixture
def voorraad_met_pasta(voorraad_repository) -> VoorraadRepository:
    """VoorraadRepository met pasta op voorraad."""
    item = VoorraadItem(
        naam="pasta",
        type=VoorraadType.HOUDBAAR,
        op_voorraad=True,
        laatst_gecheckt="2026-03-03",
    )
    voorraad_repository.update_item(item)
    return voorraad_repository


@pytest.fixture
def boodschappenlijst_generator() -> BoodschappenlijstGenerator:
    """Echte BoodschappenlijstGenerator met IngredientNormalizer."""
    normalizer = IngredientNormalizer()
    calculator = PortionCalculator()
    return BoodschappenlijstGenerator(normalizer, calculator)


@pytest.fixture
def boodschappenlijst_filter(voorraad_repository) -> BoodschappenlijstFilter:
    """BoodschappenlijstFilter met gemockte voorraad."""
    return BoodschappenlijstFilter(voorraad_repository)


@pytest.fixture
def app_with_voorraad(app_with_overrides, voorraad_repository) -> FastAPI:
    """App met dependency_overrides voor VoorraadRepository."""
    app_with_overrides.dependency_overrides[get_voorraad_repository] = (
        lambda: voorraad_repository
    )
    return app_with_overrides


@pytest.fixture
def app_with_boodschappen(
    app_with_voorraad,
    boodschappenlijst_generator,
    boodschappenlijst_filter,
) -> FastAPI:
    """App met dependency_overrides voor BoodschappenlijstGenerator en -Filter."""
    app_with_voorraad.dependency_overrides[get_boodschappenlijst_generator] = (
        lambda: boodschappenlijst_generator
    )
    app_with_voorraad.dependency_overrides[get_boodschappenlijst_filter] = (
        lambda: boodschappenlijst_filter
    )
    return app_with_voorraad


# --- AH integratie fixtures ---


@pytest.fixture
def mock_token_manager() -> MagicMock:
    """Gemockte AHTokenManager (geen echte tokens/API calls)."""
    mock = MagicMock()
    mock.is_authenticated.return_value = False
    mock.login.return_value = None
    return mock


@pytest.fixture
def mock_token_manager_authenticated(mock_token_manager) -> MagicMock:
    """AHTokenManager die is_authenticated() = True retourneert."""
    mock_token_manager.is_authenticated.return_value = True
    return mock_token_manager


@pytest.fixture
def mock_token_manager_unauthenticated(mock_token_manager) -> MagicMock:
    """AHTokenManager die is_authenticated() = False retourneert."""
    mock_token_manager.is_authenticated.return_value = False
    return mock_token_manager


@pytest.fixture
def mock_ah_integratie() -> MagicMock:
    """Gemockte AHIntegratie (geen echte AH API calls)."""
    return MagicMock()


def _apply_ah_overrides(
    app: FastAPI, mock_token_manager: MagicMock, mock_ah_integratie: MagicMock
) -> FastAPI:
    """Installeer AH dependency overrides op een app."""
    app.dependency_overrides[get_ah_token_manager] = lambda: mock_token_manager
    app.dependency_overrides[get_ah_integratie] = lambda: mock_ah_integratie
    return app


@pytest.fixture
def app_with_ah(app_with_overrides, mock_token_manager, mock_ah_integratie) -> FastAPI:
    """App met dependency_overrides voor AH token manager en integratie."""
    return _apply_ah_overrides(
        app_with_overrides, mock_token_manager, mock_ah_integratie
    )


@pytest.fixture
def app_with_boodschappen_and_ah(
    app_with_boodschappen, mock_token_manager, mock_ah_integratie
) -> FastAPI:
    """App met boodschappen en AH dependencies."""
    return _apply_ah_overrides(
        app_with_boodschappen, mock_token_manager, mock_ah_integratie
    )


@pytest.fixture
def setup_boodschappenlijst(app_with_ah):
    """Zet een boodschappenlijst van 15 producten en weekmenu op app.state."""
    from boodschappenagent.boodschappenlijst.models import (
        Boodschappenlijst,
        BoodschappenRegel,
    )

    week_menu = make_full_week_menu()
    app_with_ah.state.week_menu = week_menu
    regels = [
        BoodschappenRegel(
            naam=f"product-{i}",
            hoeveelheid=1,
            eenheid="stuk",
            originele_namen=frozenset({f"product-{i}"}),
        )
        for i in range(15)
    ]
    app_with_ah.state.boodschappenlijst_model = Boodschappenlijst(
        week_start=week_menu.week_start, regels=regels,
    )
    app_with_ah.state.boodschappenlijst = [
        {
            "id": f"item-{i}",
            "naam": f"product-{i}",
            "hoeveelheid": 1,
            "eenheid": "stuk",
            "checked": False,
        }
        for i in range(15)
    ]


def _make_product_match(naam: str, gevonden: bool, product_id: int = 1) -> ProductMatch:
    """Helper om een ProductMatch te maken."""
    from boodschappenagent.ah.models import Product

    product = (
        Product(
            id=product_id, title=naam, brand="", size="", price=2.99,
            category="", is_orderable=True,
        )
        if gevonden
        else None
    )
    bron = "zoekopdracht" if gevonden else "niet_gevonden"
    regel = type("Regel", (), {"naam": naam})()
    return ProductMatch(regel=regel, product=product, bron=bron)


@pytest.fixture
def sync_resultaat_succes() -> SyncResultaat:
    """SyncResultaat met 15 gevonden producten, 0 niet gevonden."""
    matches = [
        _make_product_match(f"product-{i}", gevonden=True, product_id=i)
        for i in range(15)
    ]
    return SyncResultaat(
        lijst_id="list-123",
        lijst_naam="Boodschappen 2026-03-02",
        matches=matches,
    )


@pytest.fixture
def sync_resultaat_deels() -> SyncResultaat:
    """SyncResultaat met 13 gevonden producten, 2 niet gevonden."""
    matches = [
        _make_product_match(f"product-{i}", gevonden=True, product_id=i)
        for i in range(13)
    ]
    matches.append(_make_product_match("verse basilicum", gevonden=False))
    matches.append(_make_product_match("za'atar kruiden", gevonden=False))
    return SyncResultaat(
        lijst_id="list-456",
        lijst_naam="Boodschappen 2026-03-02",
        matches=matches,
    )
