"""Integratietests voor navigatie tussen fasen (S11)."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from .conftest import make_full_week_menu, set_week_menu, soup


@pytest.fixture
def client_with_boodschappen(app_with_boodschappen: FastAPI) -> TestClient:
    return TestClient(app_with_boodschappen)


class TestWeekNaarVoorraad:
    """S11.1: Week pagina heeft 'Verder naar boodschappen' link naar /voorraad."""

    def test_verder_button_aanwezig(self, client: TestClient):
        set_week_menu(client, make_full_week_menu())
        s = soup(client.get("/week"))
        verder = s.select_one('[data-testid="verder-button"]')
        assert verder is not None

    def test_verder_button_href_naar_voorraad(self, client: TestClient):
        set_week_menu(client, make_full_week_menu())
        s = soup(client.get("/week"))
        verder = s.select_one('[data-testid="verder-button"]')
        assert verder is not None
        assert verder.get("href") == "/voorraad"

    def test_verder_button_tekst_bevat_boodschappen(self, client: TestClient):
        set_week_menu(client, make_full_week_menu())
        s = soup(client.get("/week"))
        verder = s.select_one('[data-testid="verder-button"]')
        assert verder is not None
        assert "boodschappen" in verder.get_text().lower()

    def test_verder_button_niet_aanwezig_zonder_menu(self, client: TestClient):
        """Verder-button altijd zichtbaar (auto-genereer activeert bij lege state)."""
        # Auto-genereer zorgt voor weekmenu, dus de button is zichtbaar
        s = soup(client.get("/week"))
        verder = s.select_one('[data-testid="verder-button"]')
        assert verder is not None


class TestVoorraadNaarBoodschappen:
    """S11.2: Voorraad pagina heeft 'Naar boodschappenlijst' knop."""

    @pytest.fixture
    def client_with_voorraad(self, app_with_voorraad: FastAPI) -> TestClient:
        return TestClient(app_with_voorraad)

    def test_s11_2_naar_boodschappen_button_aanwezig(
        self, client_with_voorraad: TestClient
    ):
        """S11.2: GET /voorraad toont 'Naar boodschappenlijst' knop."""
        set_week_menu(client_with_voorraad, make_full_week_menu())
        s = soup(client_with_voorraad.get("/voorraad"))
        button = s.select_one('[data-testid="naar-boodschappen-button"]')
        assert button is not None

    def test_s11_5_terug_naar_week_link_aanwezig(
        self, client_with_voorraad: TestClient
    ):
        """S11.5: GET /voorraad heeft 'Terug' link naar /week."""
        set_week_menu(client_with_voorraad, make_full_week_menu())
        s = soup(client_with_voorraad.get("/voorraad"))
        terug = s.select_one('a[href="/week"]')
        assert terug is not None


class TestBoodschappenNaarAH:
    """S11.3 en S11.4: Boodschappenlijst navigatie."""

    def test_s11_3_verstuur_naar_ah_button_aanwezig(
        self, client_with_boodschappen: TestClient
    ):
        """S11.3: GET /boodschappen toont 'Verstuur naar AH' knop."""
        set_week_menu(client_with_boodschappen, make_full_week_menu())
        s = soup(client_with_boodschappen.get("/boodschappen"))
        button = s.select_one('[data-testid="verstuur-naar-ah-button"]')
        assert button is not None

    def test_s11_4_terug_naar_voorraad_link_aanwezig(
        self, client_with_boodschappen: TestClient
    ):
        """S11.4: GET /boodschappen heeft 'Terug' link naar /voorraad."""
        set_week_menu(client_with_boodschappen, make_full_week_menu())
        s = soup(client_with_boodschappen.get("/boodschappen"))
        terug = s.select_one('a[href="/voorraad"]')
        assert terug is not None
