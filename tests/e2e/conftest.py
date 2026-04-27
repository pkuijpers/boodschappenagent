"""Playwright E2E test fixtures.

Start een live FastAPI-server met test-data voor E2E tests.
Gebruikt pytest-playwright voor browser-fixtures (page, browser, context).
"""

import socket
import threading
import time
from unittest.mock import MagicMock

import pytest
import uvicorn
from playwright.sync_api import Playwright

from boodschappenagent.ah import ProductMatch, SyncResultaat
from boodschappenagent.ah.models import FavoriteList, Product
from boodschappenagent.models import Basis, Categorie, Ingredient, Recipe, Seizoen
from boodschappenagent.planner import (
    DagPlanning,
    MenuHistory,
    WeekMenu,
)
from boodschappenagent.voorraadbeheer import (
    BoodschappenlijstFilter,
    VoorraadChecker,
    VoorraadRepository,
)
from boodschappenagent.web.app import create_app
from boodschappenagent.web.dependencies import (
    get_ah_client,
    get_ah_integratie,
    get_ah_token_manager,
    get_boodschappenlijst_filter,
    get_menu_history,
    get_voorraad_checker,
    get_voorraad_repository,
)


def _find_free_port() -> int:
    """Vind een vrije TCP-poort."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def _make_recipe(
    id: str,
    naam: str,
    categorie: Categorie,
    basis: Basis,
) -> Recipe:
    """Maak een test-recept."""
    return Recipe(
        id=id,
        naam=naam,
        categorie=categorie,
        basis=basis,
        seizoenen=[Seizoen.ALLE],
        basis_porties=4,
        ingredienten=[Ingredient(naam="test", hoeveelheid=1.0, eenheid="stuk")],
    )


# Vaste test-recepten
TEST_RECIPES = [
    _make_recipe(
        "spaghetti-bolognese",
        "Spaghetti Bolognese",
        Categorie.VLEES,
        Basis.PASTA,
    ),
    _make_recipe(
        "kip-curry",
        "Kip Curry",
        Categorie.GEVOGELTE,
        Basis.RIJST,
    ),
    _make_recipe(
        "zalm-teriyaki",
        "Zalm Teriyaki",
        Categorie.VIS,
        Basis.RIJST,
    ),
    _make_recipe(
        "groente-risotto",
        "Groente Risotto",
        Categorie.VEGETARISCH,
        Basis.RIJST,
    ),
    _make_recipe(
        "biefstuk-friet",
        "Biefstuk met Friet",
        Categorie.VLEES,
        Basis.AARDAPPEL,
    ),
    _make_recipe(
        "pad-thai",
        "Pad Thai",
        Categorie.VEGETARISCH,
        Basis.BROOD,
    ),
]

# Test weekmenu: 5 recepten, 1 HelloFresh (woensdag), 1 niet thuis (zaterdag)
TEST_WEEK_MENU = WeekMenu(
    week_start="2026-02-16",
    dagen=[
        DagPlanning(dag=0, recept=TEST_RECIPES[0], personen=4),  # ma
        DagPlanning(dag=1, recept=TEST_RECIPES[1], personen=4),  # di
        DagPlanning(dag=2, recept=None, personen=0),  # wo (HelloFresh)
        DagPlanning(dag=3, recept=TEST_RECIPES[2], personen=4),  # do
        DagPlanning(dag=4, recept=TEST_RECIPES[3], personen=4),  # vr
        DagPlanning(dag=5, recept=None, personen=0),  # za (niet thuis)
        DagPlanning(dag=6, recept=TEST_RECIPES[4], personen=4),  # zo
    ],
)

# Woensdag (dag=2) is HelloFresh
TEST_HELLOFRESH_DAGEN: set[int] = {2}

# Voorraad testproducten voor de AH 'Voorraad' favorietenlijst mock
TEST_VOORRAAD_PRODUCTEN = [
    Product(id=1001, title="melk", brand="", size="1L", price=1.09, category="Zuivel", is_orderable=True),
    Product(id=1002, title="eieren", brand="", size="6 stuks", price=2.49, category="Zuivel", is_orderable=True),
    Product(id=1003, title="boter", brand="", size="250g", price=1.59, category="Zuivel", is_orderable=True),
    Product(id=1004, title="kaas", brand="", size="500g", price=3.99, category="Zuivel", is_orderable=True),
    Product(id=1005, title="optimel", brand="", size="1.5L", price=2.19, category="Zuivel", is_orderable=True),
]


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args, playwright: Playwright):
    """Emuleer iPhone 13 (390x844, touch, Safari user-agent)."""
    iphone_13 = playwright.devices["iPhone 13"]
    return {**browser_context_args, **iphone_13}


@pytest.fixture(scope="session")
def mock_ah_token_manager():
    """Gemockte AHTokenManager voor E2E tests (session-scoped)."""
    mock = MagicMock()
    mock.is_authenticated.return_value = True
    mock.login.return_value = None
    return mock


@pytest.fixture(scope="session")
def mock_ah_client():
    """Gemockte AHClient die test voorraadproducten retourneert (session-scoped)."""
    voorraad_lijst = FavoriteList(
        id="list-voorraad",
        name="Voorraad",
        total_items=len(TEST_VOORRAAD_PRODUCTEN),
        items=[],
        products=TEST_VOORRAAD_PRODUCTEN,
    )
    mock = MagicMock()
    mock.find_list_by_name.return_value = voorraad_lijst
    mock.get_list_with_products.return_value = voorraad_lijst
    return mock


@pytest.fixture(scope="session")
def mock_ah_integratie():
    """Gemockte AHIntegratie voor E2E tests (session-scoped)."""
    mock = MagicMock()
    # Default: 5 producten gevonden, 0 niet gevonden
    matches = [
        ProductMatch(
            regel=type("Regel", (), {"naam": f"product-{i}"})(),
            product=Product(
                id=i,
                title=f"AH Product {i}",
                brand="AH",
                size="1 stuk",
                price=2.99,
                category="",
                is_orderable=True,
            ),
            bron="zoekopdracht",
        )
        for i in range(5)
    ]
    mock.sync_naar_lijst.return_value = SyncResultaat(
        lijst_id="e2e-list-123",
        lijst_naam="Boodschappen 2026-02-16",
        matches=matches,
    )
    return mock


@pytest.fixture(scope="session")
def app(tmp_path_factory, mock_ah_token_manager, mock_ah_integratie, mock_ah_client):
    """FastAPI app met test-data op app.state en tijdelijke VoorraadRepository."""
    tmp_dir = tmp_path_factory.mktemp("voorraad_e2e")
    voorraad_path = tmp_dir / "voorraad.json"
    history_path = tmp_dir / "history.json"

    app = create_app()
    app.state.week_menu = TEST_WEEK_MENU
    app.state.hellofresh_dagen = TEST_HELLOFRESH_DAGEN
    app.state._voorraad_path = voorraad_path

    def _get_repo():
        return VoorraadRepository(voorraad_path)

    app.dependency_overrides[get_voorraad_repository] = _get_repo
    app.dependency_overrides[get_voorraad_checker] = lambda: VoorraadChecker(
        _get_repo()
    )
    app.dependency_overrides[get_boodschappenlijst_filter] = (
        lambda: BoodschappenlijstFilter(_get_repo())
    )
    app.dependency_overrides[get_ah_token_manager] = lambda: mock_ah_token_manager
    app.dependency_overrides[get_ah_integratie] = lambda: mock_ah_integratie
    app.dependency_overrides[get_ah_client] = lambda: mock_ah_client
    app.dependency_overrides[get_menu_history] = lambda: MenuHistory(history_path)

    from boodschappenagent.planner import MenuPlanner, SeizoenKalender
    from boodschappenagent.web.dependencies import get_menu_planner

    menu_history = MenuHistory(history_path)
    kalender = SeizoenKalender()
    app.dependency_overrides[get_menu_planner] = lambda: MenuPlanner(
        recipes=TEST_RECIPES, history=menu_history, kalender=kalender
    )

    return app


@pytest.fixture(scope="session")
def live_server_url(app):
    """Start de FastAPI-server op een vrije poort en geef de base URL terug."""
    port = _find_free_port()
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    # Wacht tot server luistert
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.1):
                break
        except OSError:
            time.sleep(0.05)
    else:
        msg = "Server niet gestart binnen 5 seconden"
        raise RuntimeError(msg)

    yield f"http://127.0.0.1:{port}"

    server.should_exit = True
    thread.join(timeout=5)


@pytest.fixture
def week_page(page, live_server_url, app):
    """Navigeer naar /week, herstel test-staat en geef de Playwright-pagina terug."""
    # Reset naar initiële test-staat voor isolatie tussen E2E tests
    app.state.week_menu = TEST_WEEK_MENU
    app.state.hellofresh_dagen = set(TEST_HELLOFRESH_DAGEN)
    page.goto(f"{live_server_url}/week")
    page.wait_for_selector("[data-testid='dagkaart']")
    return page


@pytest.fixture
def voorraad_page(page, live_server_url, app, mock_ah_token_manager):
    """Navigeer naar /voorraad, herstel test-staat."""
    mock_ah_token_manager.is_authenticated.return_value = True
    mock_ah_token_manager.is_authenticated.side_effect = None
    app.state.week_menu = TEST_WEEK_MENU
    app.state.hellofresh_dagen = set(TEST_HELLOFRESH_DAGEN)
    # Reset voorraad naar schone staat (alle items standaard "Nee")
    voorraad_path = app.state._voorraad_path
    if voorraad_path.exists():
        voorraad_path.unlink()
    page.goto(f"{live_server_url}/voorraad")
    page.wait_for_selector("[data-testid='sectie-voorraad']")
    return page


@pytest.fixture
def boodschappen_page(page, live_server_url, app):
    """Navigeer naar /boodschappen, herstel test-staat."""
    app.state.week_menu = TEST_WEEK_MENU
    app.state.hellofresh_dagen = set(TEST_HELLOFRESH_DAGEN)
    app.state.boodschappenlijst = None
    page.goto(f"{live_server_url}/boodschappen")
    page.wait_for_selector("[data-testid='boodschappen-header']")
    return page
