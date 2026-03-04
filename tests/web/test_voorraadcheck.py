"""Integratietests voor voorraadcheck pagina (S6, S7, S8)."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from boodschappenagent.models import Basis, Categorie, Ingredient, Seizoen
from boodschappenagent.models.recipe import Recipe
from boodschappenagent.planner import DagPlanning, WeekMenu
from boodschappenagent.voorraadbeheer import VoorraadRepository
from boodschappenagent.web.dependencies import get_voorraad_repository

from .conftest import WEEK_START, make_full_week_menu, set_week_menu, soup


def _make_pasta_recept() -> Recipe:
    """Recept met pasta als ingredient (in STANDAARD_HOUDBAAR)."""
    return Recipe(
        id="spaghetti-bolognese",
        naam="Spaghetti Bolognese",
        categorie=Categorie.VLEES,
        basis=Basis.PASTA,
        seizoenen=[Seizoen.ALLE],
        basis_porties=2,
        ingredienten=[
            Ingredient(naam="pasta", hoeveelheid=200, eenheid="gram"),
            Ingredient(naam="gehakt", hoeveelheid=300, eenheid="gram"),
        ],
    )


def _make_week_menu_met_pasta() -> WeekMenu:
    """WeekMenu met Spaghetti Bolognese op dag 0."""
    from .conftest import RECEPTEN

    pasta_recept = _make_pasta_recept()
    dagen = [DagPlanning(dag=0, recept=pasta_recept, personen=2)] + [
        DagPlanning(dag=i, recept=RECEPTEN[i], personen=2) for i in range(1, 7)
    ]
    return WeekMenu(week_start=WEEK_START, dagen=dagen)


@pytest.fixture
def client_with_voorraad(app_with_voorraad: FastAPI) -> TestClient:
    """TestClient met lege VoorraadRepository override."""
    return TestClient(app_with_voorraad)


@pytest.fixture
def client_met_pasta_op_voorraad(
    app_with_overrides: FastAPI, voorraad_met_pasta: VoorraadRepository
) -> TestClient:
    """TestClient met pasta op voorraad."""
    app_with_overrides.dependency_overrides[get_voorraad_repository] = (
        lambda: voorraad_met_pasta
    )
    return TestClient(app_with_overrides)


class TestVoorraadcheckLaden:
    """S6: Voorraadcheck laden (WeekMenu → UI)."""

    def test_s6_1a_full_page_bevat_html(self, client_with_voorraad: TestClient):
        """S6.1a: Browser request geeft volledige HTML pagina."""
        set_week_menu(client_with_voorraad, make_full_week_menu())
        response = client_with_voorraad.get("/voorraad")
        assert response.status_code == 200
        assert "<html" in response.text

    def test_s6_1a_full_page_bevat_header_voorraadcheck(
        self, client_with_voorraad: TestClient
    ):
        """S6.1a: Volledige pagina bevat header 'Voorraadcheck'."""
        set_week_menu(client_with_voorraad, make_full_week_menu())
        s = soup(client_with_voorraad.get("/voorraad"))
        assert "Voorraadcheck" in s.get_text()

    def test_s6_1b_htmx_fragment_geen_html(self, client_with_voorraad: TestClient):
        """S6.1b: HTMX request geeft fragment zonder <html>."""
        set_week_menu(client_with_voorraad, make_full_week_menu())
        response = client_with_voorraad.get(
            "/voorraad", headers={"HX-Request": "true"}
        )
        assert response.status_code == 200
        assert "<html" not in response.text

    def test_s6_1_twee_secties_aanwezig(self, client_with_voorraad: TestClient):
        """S6.1: Voorraadcheck toont twee secties: houdbaar en vers."""
        set_week_menu(client_with_voorraad, make_full_week_menu())
        s = soup(client_with_voorraad.get("/voorraad"))
        assert s.select_one('[data-testid="sectie-houdbaar"]') is not None
        assert s.select_one('[data-testid="sectie-vers"]') is not None

    def test_s6_3_verse_basics_altijd_zichtbaar(
        self, client_with_voorraad: TestClient
    ):
        """S6.3: Verse basics altijd getoond, ongeacht weekmenu."""
        set_week_menu(client_with_voorraad, make_full_week_menu())
        s = soup(client_with_voorraad.get("/voorraad"))
        vers_sectie = s.select_one('[data-testid="sectie-vers"]')
        assert vers_sectie is not None
        items = vers_sectie.select('[data-testid="voorraaditem"]')
        assert len(items) > 0

    def test_s6_4_standaard_nee_actief(self, client_with_voorraad: TestClient):
        """S6.4: Elk item heeft standaard 'Nee' actief (veilige default)."""
        set_week_menu(client_with_voorraad, make_full_week_menu())
        s = soup(client_with_voorraad.get("/voorraad"))
        nee_buttons = s.select('[data-testid="status-nee"][data-actief="true"]')
        assert len(nee_buttons) > 0

    def test_s6_6_zonder_weekmenu_redirect(self, client_with_voorraad: TestClient):
        """S6.6: Zonder weekmenu redirect naar /week."""
        client_with_voorraad.app.state.week_menu = None
        response = client_with_voorraad.get(
            "/voorraad", follow_redirects=False
        )
        assert response.status_code in (301, 302, 303, 307, 308)
        assert "/week" in response.headers["location"]

    def test_s6_7_lege_voorraad_toont_verse_basics(
        self, client_with_voorraad: TestClient
    ):
        """S6.7: Lege VoorraadRepository toont minimaal verse basics."""
        set_week_menu(client_with_voorraad, make_full_week_menu())
        s = soup(client_with_voorraad.get("/voorraad"))
        vers_sectie = s.select_one('[data-testid="sectie-vers"]')
        assert vers_sectie is not None
        items = vers_sectie.select('[data-testid="voorraaditem"]')
        assert len(items) > 0


class TestVoorraadcheckHoudbaar:
    """S6.2: Houdbare items uit weekmenu."""

    def test_s6_2_pasta_in_houdbaar_sectie(self, client_with_voorraad: TestClient):
        """S6.2: Weekmenu met pasta-recept → pasta verschijnt als houdbaar item."""
        set_week_menu(client_with_voorraad, _make_week_menu_met_pasta())
        s = soup(client_with_voorraad.get("/voorraad"))
        houdbaar_sectie = s.select_one('[data-testid="sectie-houdbaar"]')
        assert houdbaar_sectie is not None
        items = houdbaar_sectie.select('[data-testid="voorraaditem"]')
        item_namen = [item.get("data-item", "") for item in items]
        assert "pasta" in item_namen

    def test_s6_2_pasta_toont_recept_context(
        self, client_with_voorraad: TestClient
    ):
        """S6.2: pasta item toont context met receptnaam 'Spaghetti Bolognese'."""
        set_week_menu(client_with_voorraad, _make_week_menu_met_pasta())
        s = soup(client_with_voorraad.get("/voorraad"))
        houdbaar_sectie = s.select_one('[data-testid="sectie-houdbaar"]')
        pasta_item = houdbaar_sectie.select_one(
            '[data-testid="voorraaditem"][data-item="pasta"]'
        )
        assert pasta_item is not None
        assert "Spaghetti Bolognese" in pasta_item.get_text()


class TestVoorraadcheckOpVoorraad:
    """S6.5: Items met bestaande voorraad tonen 'Ja' actief."""

    def test_s6_5_pasta_op_voorraad_toont_ja(
        self, client_met_pasta_op_voorraad: TestClient
    ):
        """S6.5: pasta op voorraad → 'Ja' button actief."""
        set_week_menu(
            client_met_pasta_op_voorraad, _make_week_menu_met_pasta()
        )
        s = soup(client_met_pasta_op_voorraad.get("/voorraad"))
        pasta_item = s.select_one(
            '[data-testid="voorraaditem"][data-item="pasta"]'
        )
        assert pasta_item is not None
        ja_button = pasta_item.select_one(
            '[data-testid="status-ja"][data-actief="true"]'
        )
        assert ja_button is not None


class TestVoorraadToggle:
    """S7: Voorraad status toggle (UI → VoorraadRepository → UI)."""

    def test_s7_1_toggle_ja_actief(self, client_with_voorraad: TestClient):
        """S7.1: POST /voorraad/pasta/status met op_voorraad=true → Ja actief."""
        set_week_menu(client_with_voorraad, _make_week_menu_met_pasta())
        response = client_with_voorraad.post(
            "/voorraad/pasta/status",
            data={"op_voorraad": "true"},
        )
        assert response.status_code == 200
        s = soup(response)
        pasta_item = s.select_one('[data-testid="voorraaditem"][data-item="pasta"]')
        assert pasta_item is not None
        ja_button = pasta_item.select_one('[data-testid="status-ja"][data-actief="true"]')
        assert ja_button is not None

    def test_s7_2_toggle_nee_actief(
        self, client_met_pasta_op_voorraad: TestClient
    ):
        """S7.2: POST /voorraad/pasta/status met op_voorraad=false → Nee actief."""
        set_week_menu(client_met_pasta_op_voorraad, _make_week_menu_met_pasta())
        response = client_met_pasta_op_voorraad.post(
            "/voorraad/pasta/status",
            data={"op_voorraad": "false"},
        )
        assert response.status_code == 200
        s = soup(response)
        pasta_item = s.select_one('[data-testid="voorraaditem"][data-item="pasta"]')
        assert pasta_item is not None
        nee_button = pasta_item.select_one(
            '[data-testid="status-nee"][data-actief="true"]'
        )
        assert nee_button is not None

    def test_s7_3_htmx_swap_enkel_item(self, client_with_voorraad: TestClient):
        """S7.3: Response bevat precies 1 voorraaditem (niet hele pagina)."""
        set_week_menu(client_with_voorraad, _make_week_menu_met_pasta())
        response = client_with_voorraad.post(
            "/voorraad/pasta/status",
            data={"op_voorraad": "true"},
        )
        assert response.status_code == 200
        s = soup(response)
        items = s.select('[data-testid="voorraaditem"]')
        assert len(items) == 1

    def test_s7_4_onbekend_item_404(self, client_with_voorraad: TestClient):
        """S7.4: Onbekend item → HTTP 404."""
        set_week_menu(client_with_voorraad, make_full_week_menu())
        response = client_with_voorraad.post(
            "/voorraad/onbekend-item/status",
            data={"op_voorraad": "true"},
        )
        assert response.status_code == 404

    def test_s7_5_zonder_weekmenu_404(self, client_with_voorraad: TestClient):
        """S7.5: Zonder weekmenu → HTTP 404."""
        client_with_voorraad.app.state.week_menu = None
        response = client_with_voorraad.post(
            "/voorraad/pasta/status",
            data={"op_voorraad": "true"},
        )
        assert response.status_code == 404

    def test_s7_1_repository_opgeslagen(self, client_with_voorraad: TestClient):
        """S7.1: Na toggle Ja is pasta op_voorraad=True in repository."""
        set_week_menu(client_with_voorraad, _make_week_menu_met_pasta())
        client_with_voorraad.post(
            "/voorraad/pasta/status",
            data={"op_voorraad": "true"},
        )
        repo: VoorraadRepository = (
            client_with_voorraad.app.dependency_overrides[get_voorraad_repository]()
        )
        assert "pasta" in repo.op_voorraad_namen()


class TestVoorraadBevestig:
    """S8: Voorraad bevestigen (batch update → redirect)."""

    def test_s8_1_redirect_naar_boodschappen(
        self, client_with_voorraad: TestClient
    ):
        """S8.1: POST /voorraad/bevestig → 303 redirect naar /boodschappen."""
        set_week_menu(client_with_voorraad, make_full_week_menu())
        response = client_with_voorraad.post(
            "/voorraad/bevestig", follow_redirects=False
        )
        assert response.status_code in (301, 302, 303, 307, 308)
        assert "/boodschappen" in response.headers["location"]

    def test_s8_3_zonder_weekmenu_redirect_naar_week(
        self, client_with_voorraad: TestClient
    ):
        """S8.3: Zonder weekmenu → redirect naar /week."""
        client_with_voorraad.app.state.week_menu = None
        response = client_with_voorraad.post(
            "/voorraad/bevestig", follow_redirects=False
        )
        assert response.status_code in (301, 302, 303, 307, 308)
        assert "/week" in response.headers["location"]
