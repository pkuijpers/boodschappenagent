"""Playwright E2E test fixtures.

Start een live FastAPI-server met test-data voor E2E tests.
Gebruikt pytest-playwright voor browser-fixtures (page, browser, context).
"""

import socket
import threading
import time

import pytest
import uvicorn
from playwright.sync_api import Playwright

from boodschappenagent.models import Basis, Categorie, Ingredient, Recipe, Seizoen
from boodschappenagent.planner import DagPlanning, WeekMenu
from boodschappenagent.web.app import create_app


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


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args, playwright: Playwright):
    """Emuleer iPhone 13 (390x844, touch, Safari user-agent)."""
    iphone_13 = playwright.devices["iPhone 13"]
    return {**browser_context_args, **iphone_13}


@pytest.fixture(scope="session")
def app():
    """FastAPI app met test-data op app.state."""
    app = create_app()
    app.state.week_menu = TEST_WEEK_MENU
    app.state.hellofresh_dagen = TEST_HELLOFRESH_DAGEN
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
    app.state.recept_backup = {}
    page.goto(f"{live_server_url}/week")
    page.wait_for_load_state("networkidle")
    return page
