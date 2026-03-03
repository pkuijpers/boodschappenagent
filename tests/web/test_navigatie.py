"""Integratietests voor navigatie tussen fasen (S11)."""

from fastapi.testclient import TestClient

from .conftest import make_full_week_menu, set_week_menu, soup


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
