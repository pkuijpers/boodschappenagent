"""Integratietests voor boodschappenlijst pagina (S9)."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from boodschappenagent.voorraadbeheer import VoorraadRepository
from boodschappenagent.voorraadbeheer.models import VoorraadItem, VoorraadType

from .conftest import make_full_week_menu, set_week_menu, soup


@pytest.fixture
def client_with_boodschappen(app_with_boodschappen: FastAPI) -> TestClient:
    """TestClient met BoodschappenlijstGenerator en BoodschappenlijstFilter override."""
    return TestClient(app_with_boodschappen)


class TestBoodschappenlijstLaden:
    """S9: Boodschappenlijst laden (WeekMenu → Generator → Filter → UI)."""

    def test_s9_1a_full_page_bevat_html(self, client_with_boodschappen: TestClient):
        """S9.1a: Browser request geeft volledige HTML pagina."""
        set_week_menu(client_with_boodschappen, make_full_week_menu())
        response = client_with_boodschappen.get("/boodschappen")
        assert response.status_code == 200
        assert "<html" in response.text

    def test_s9_1b_htmx_fragment_geen_html(self, client_with_boodschappen: TestClient):
        """S9.1b: HTMX request geeft fragment zonder <html>."""
        set_week_menu(client_with_boodschappen, make_full_week_menu())
        response = client_with_boodschappen.get(
            "/boodschappen", headers={"HX-Request": "true"}
        )
        assert response.status_code == 200
        assert "<html" not in response.text

    def test_s9_1a_full_page_bevat_header_boodschappenlijst(
        self, client_with_boodschappen: TestClient
    ):
        """S9.1a: Volledige pagina bevat header 'Boodschappenlijst'."""
        set_week_menu(client_with_boodschappen, make_full_week_menu())
        s = soup(client_with_boodschappen.get("/boodschappen"))
        assert "Boodschappenlijst" in s.get_text()

    def test_s9_1_sectie_aanwezig(self, client_with_boodschappen: TestClient):
        """S9.1: Boodschappenlijst toont minimaal één sectie."""
        set_week_menu(client_with_boodschappen, make_full_week_menu())
        s = soup(client_with_boodschappen.get("/boodschappen"))
        secties = s.select('[data-testid="boodschappen-sectie"]')
        assert len(secties) >= 1

    def test_s9_8_header_aanwezig(self, client_with_boodschappen: TestClient):
        """S9.8: Header met product telling is aanwezig."""
        set_week_menu(client_with_boodschappen, make_full_week_menu())
        s = soup(client_with_boodschappen.get("/boodschappen"))
        header = s.select_one('[data-testid="boodschappen-header"]')
        assert header is not None

    def test_s9_8_header_toont_weektelling(self, client_with_boodschappen: TestClient):
        """S9.8: Header toont weeknummer en producttelling."""
        set_week_menu(client_with_boodschappen, make_full_week_menu())
        s = soup(client_with_boodschappen.get("/boodschappen"))
        header = s.select_one('[data-testid="boodschappen-header"]')
        assert header is not None
        text = header.get_text()
        assert any(c.isdigit() for c in text)

    def test_s9_9_zonder_weekmenu_redirect(self, client_with_boodschappen: TestClient):
        """S9.9: Zonder weekmenu redirect naar /week."""
        client_with_boodschappen.app.state.week_menu = None
        response = client_with_boodschappen.get(
            "/boodschappen", follow_redirects=False
        )
        assert response.status_code in (301, 302, 303, 307, 308)
        assert "/week" in response.headers["location"]


class TestBoodschappenlijstLeeg:
    """S9.10: Lege boodschappenlijst state."""

    @pytest.fixture
    def app_alles_op_voorraad(
        self, app_with_boodschappen: FastAPI, voorraad_repository: VoorraadRepository
    ) -> FastAPI:
        """App waarbij het 'test' ingredient op voorraad staat."""
        voorraad_repository.update_item(
            VoorraadItem(
                naam="test",
                type=VoorraadType.HOUDBAAR,
                op_voorraad=True,
                laatst_gecheckt="2026-03-03",
            )
        )
        return app_with_boodschappen

    def test_s9_10_lege_lijst_bericht(self, app_alles_op_voorraad: FastAPI):
        """S9.10: Lege lijst toont 'Niets te bestellen!' bericht."""
        client = TestClient(app_alles_op_voorraad)
        set_week_menu(client, make_full_week_menu())
        s = soup(client.get("/boodschappen"))
        lege_lijst = s.select_one('[data-testid="lege-lijst"]')
        assert lege_lijst is not None
        assert "bestellen" in lege_lijst.get_text().lower()


class TestBoodschappenlijstItems:
    """S9: Items op de boodschappenlijst."""

    def test_s9_items_aanwezig(self, client_with_boodschappen: TestClient):
        """S9: Boodschappenlijst toont items."""
        set_week_menu(client_with_boodschappen, make_full_week_menu())
        s = soup(client_with_boodschappen.get("/boodschappen"))
        items = s.select('[data-testid="boodschapitem"]')
        assert len(items) >= 1

    def test_s9_items_standaard_niet_gecheckt(
        self, client_with_boodschappen: TestClient
    ):
        """S9: Items zijn standaard niet afgevinkt."""
        set_week_menu(client_with_boodschappen, make_full_week_menu())
        s = soup(client_with_boodschappen.get("/boodschappen"))
        items = s.select('[data-testid="boodschapitem"]')
        assert len(items) >= 1
        for item in items:
            assert item.get("data-checked") == "false"

    def test_s9_items_hebben_hoeveelheid(self, client_with_boodschappen: TestClient):
        """S9: Items tonen hoeveelheid."""
        set_week_menu(client_with_boodschappen, make_full_week_menu())
        s = soup(client_with_boodschappen.get("/boodschappen"))
        items = s.select('[data-testid="boodschapitem"]')
        assert len(items) >= 1
        hoeveelheid = items[0].select_one('[data-testid="hoeveelheid"]')
        assert hoeveelheid is not None
