"""Integratietests voor voorraadcheck pagina (S6, S7, S8)."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from boodschappenagent.ah import AHIntegratie
from boodschappenagent.voorraadbeheer import VoorraadRepository
from boodschappenagent.web.dependencies import (
    get_ah_integratie,
    get_ah_token_manager,
    get_match_voorkeuren_repository,
    get_voorraad_repository,
)

from .conftest import TEST_VOORRAAD_PRODUCTEN, make_full_week_menu, set_week_menu, soup


@pytest.fixture
def client_with_voorraad(app_with_voorraad: FastAPI) -> TestClient:
    """TestClient met lege VoorraadRepository en mock AHClient."""
    return TestClient(app_with_voorraad)


@pytest.fixture
def client_met_melk_op_voorraad(
    app_with_overrides: FastAPI,
    voorraad_met_melk: VoorraadRepository,
    mock_ah_client,
    mock_token_manager_authenticated,
) -> TestClient:
    """TestClient met Melk op voorraad, mock AHIntegratie en ingelogde token manager."""
    from boodschappenagent.web.dependencies import get_ah_token_manager

    app_with_overrides.dependency_overrides[get_voorraad_repository] = (
        lambda: voorraad_met_melk
    )
    app_with_overrides.dependency_overrides[get_ah_integratie] = lambda: AHIntegratie(
        mock_ah_client
    )
    app_with_overrides.dependency_overrides[get_ah_token_manager] = (
        lambda: mock_token_manager_authenticated
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
        response = client_with_voorraad.get("/voorraad", headers={"HX-Request": "true"})
        assert response.status_code == 200
        assert "<html" not in response.text

    def test_s6_1_sectie_voorraad_aanwezig(self, client_with_voorraad: TestClient):
        """S6.1: Voorraadcheck toont sectie 'sectie-voorraad'."""
        set_week_menu(client_with_voorraad, make_full_week_menu())
        s = soup(client_with_voorraad.get("/voorraad"))
        assert s.select_one('[data-testid="sectie-voorraad"]') is not None

    def test_s6_2_ah_producten_zichtbaar(self, client_with_voorraad: TestClient):
        """S6.2: Producten uit AH 'Voorraad' lijst worden getoond."""
        set_week_menu(client_with_voorraad, make_full_week_menu())
        s = soup(client_with_voorraad.get("/voorraad"))
        sectie = s.select_one('[data-testid="sectie-voorraad"]')
        items = sectie.select('[data-testid="voorraaditem"]')
        assert len(items) == len(TEST_VOORRAAD_PRODUCTEN)

    def test_s6_3_productnamen_getoond(self, client_with_voorraad: TestClient):
        """S6.3: Productnamen uit AH lijst zijn zichtbaar op de pagina."""
        set_week_menu(client_with_voorraad, make_full_week_menu())
        s = soup(client_with_voorraad.get("/voorraad"))
        tekst = s.get_text()
        for p in TEST_VOORRAAD_PRODUCTEN:
            assert p["title"] in tekst

    def test_s6_4_standaard_nee_actief(self, client_with_voorraad: TestClient):
        """S6.4: Elk item heeft standaard 'Nee' actief (veilige default)."""
        set_week_menu(client_with_voorraad, make_full_week_menu())
        s = soup(client_with_voorraad.get("/voorraad"))
        nee_buttons = s.select('[data-testid="status-nee"][data-actief="true"]')
        assert len(nee_buttons) == len(TEST_VOORRAAD_PRODUCTEN)

    def test_s6_6_zonder_weekmenu_redirect(self, client_with_voorraad: TestClient):
        """S6.6: Zonder weekmenu redirect naar /week."""
        client_with_voorraad.app.state.week_menu = None
        response = client_with_voorraad.get("/voorraad", follow_redirects=False)
        assert response.status_code in (301, 302, 303, 307, 308)
        assert "/week" in response.headers["location"]

    def test_s6_7_ah_fout_toont_melding(
        self, app_with_overrides: FastAPI, mock_token_manager_authenticated
    ):
        """S6.7: Als AH lijst leeg is, toont pagina foutmelding."""
        from unittest.mock import MagicMock

        lege_client = MagicMock()
        lege_client.find_list_by_name.return_value = None
        app_with_overrides.dependency_overrides[get_ah_integratie] = (
            lambda: AHIntegratie(lege_client)
        )
        app_with_overrides.dependency_overrides[get_ah_token_manager] = (
            lambda: mock_token_manager_authenticated
        )
        client = TestClient(app_with_overrides)
        set_week_menu(client, make_full_week_menu())
        s = soup(client.get("/voorraad"))
        assert "Albert Heijn" in s.get_text()

    def test_s6_8_niet_ingelogd_redirect_naar_login(
        self,
        app_with_overrides: FastAPI,
        mock_ah_client,
        mock_token_manager_unauthenticated,
    ):
        """S6.8: Niet ingelogd bij AH → redirect naar /ah/login."""

        app_with_overrides.dependency_overrides[get_ah_integratie] = (
            lambda: AHIntegratie(mock_ah_client)
        )
        app_with_overrides.dependency_overrides[get_ah_token_manager] = (
            lambda: mock_token_manager_unauthenticated
        )
        client = TestClient(app_with_overrides)
        set_week_menu(client, make_full_week_menu())
        response = client.get("/voorraad", follow_redirects=False)
        assert response.status_code in (301, 302, 303, 307, 308)
        location = response.headers["location"]
        assert "/ah/login" in location
        assert "terug=/week" in location
        assert "next=/voorraad" in location


class TestVoorraadcheckOpVoorraad:
    """S6.5: Items met bestaande voorraad tonen 'Ja' actief."""

    def test_s6_5_melk_op_voorraad_toont_ja(
        self, client_met_melk_op_voorraad: TestClient
    ):
        """S6.5: Melk op voorraad → 'Ja' button actief voor Melk item."""
        set_week_menu(client_met_melk_op_voorraad, make_full_week_menu())
        s = soup(client_met_melk_op_voorraad.get("/voorraad"))
        melk_item = s.select_one('[data-testid="voorraaditem"][data-item="Melk"]')
        assert melk_item is not None
        ja_button = melk_item.select_one(
            '[data-testid="status-ja"][data-actief="true"]'
        )
        assert ja_button is not None


class TestVoorraadToggle:
    """S7: Voorraad status toggle (UI → VoorraadRepository → UI)."""

    def test_s7_1_toggle_ja_actief(self, client_with_voorraad: TestClient):
        """S7.1: POST /voorraad/1001/status met op_voorraad=true → Ja actief."""
        set_week_menu(client_with_voorraad, make_full_week_menu())
        response = client_with_voorraad.post(
            "/voorraad/1001/status",
            data={"op_voorraad": "true", "naam": "Melk"},
        )
        assert response.status_code == 200
        s = soup(response)
        item = s.select_one('[data-testid="voorraaditem"][data-item="Melk"]')
        assert item is not None
        ja_button = item.select_one('[data-testid="status-ja"][data-actief="true"]')
        assert ja_button is not None

    def test_s7_2_toggle_nee_actief(self, client_met_melk_op_voorraad: TestClient):
        """S7.2: POST /voorraad/1001/status met op_voorraad=false → Nee actief."""
        set_week_menu(client_met_melk_op_voorraad, make_full_week_menu())
        response = client_met_melk_op_voorraad.post(
            "/voorraad/1001/status",
            data={"op_voorraad": "false", "naam": "Melk"},
        )
        assert response.status_code == 200
        s = soup(response)
        item = s.select_one('[data-testid="voorraaditem"][data-item="Melk"]')
        assert item is not None
        nee_button = item.select_one('[data-testid="status-nee"][data-actief="true"]')
        assert nee_button is not None

    def test_s7_3_htmx_swap_enkel_item(self, client_with_voorraad: TestClient):
        """S7.3: Response bevat precies 1 voorraaditem (niet hele pagina)."""
        set_week_menu(client_with_voorraad, make_full_week_menu())
        response = client_with_voorraad.post(
            "/voorraad/1001/status",
            data={"op_voorraad": "true", "naam": "Melk"},
        )
        assert response.status_code == 200
        s = soup(response)
        items = s.select('[data-testid="voorraaditem"]')
        assert len(items) == 1

    def test_s7_4_onbekend_product_404(self, client_with_voorraad: TestClient):
        """S7.4: Onbekend product ID → HTTP 404."""
        set_week_menu(client_with_voorraad, make_full_week_menu())
        response = client_with_voorraad.post(
            "/voorraad/9999/status",
            data={"op_voorraad": "true", "naam": "Onbekend"},
        )
        assert response.status_code == 404

    def test_s7_5_zonder_weekmenu_404(self, client_with_voorraad: TestClient):
        """S7.5: Zonder weekmenu → HTTP 404."""
        client_with_voorraad.app.state.week_menu = None
        response = client_with_voorraad.post(
            "/voorraad/1001/status",
            data={"op_voorraad": "true", "naam": "Melk"},
        )
        assert response.status_code == 404

    def test_s7_1_repository_opgeslagen(self, client_with_voorraad: TestClient):
        """S7.1: Na toggle Ja is Melk (lowercase) op_voorraad=True in repository."""
        set_week_menu(client_with_voorraad, make_full_week_menu())
        client_with_voorraad.post(
            "/voorraad/1001/status",
            data={"op_voorraad": "true", "naam": "Melk"},
        )
        repo: VoorraadRepository = client_with_voorraad.app.dependency_overrides[
            get_voorraad_repository
        ]()
        assert "melk" in repo.op_voorraad_namen()


class TestVoorraadSyncMetAHLijst:
    """Voorraad wordt gesynchroniseerd met AH 'Voorraad' lijst bij laden."""

    def test_nieuw_ah_product_wordt_toegevoegd_aan_repository(
        self, client_with_voorraad: TestClient
    ):
        """Nieuw AH product (niet in repository) → toegevoegd na GET /voorraad."""
        set_week_menu(client_with_voorraad, make_full_week_menu())
        client_with_voorraad.get("/voorraad")
        repo: VoorraadRepository = client_with_voorraad.app.dependency_overrides[
            get_voorraad_repository
        ]()
        namen = {i.naam for i in repo.load()}
        for p in TEST_VOORRAAD_PRODUCTEN:
            assert p["title"].lower() in namen

    def test_verouderd_item_verwijderd_uit_repository(self, app_with_voorraad: FastAPI):
        """Item niet meer op AH lijst → verwijderd uit repository na GET /voorraad."""
        from boodschappenagent.voorraadbeheer.models import VoorraadItem, VoorraadType

        repo: VoorraadRepository = app_with_voorraad.dependency_overrides[
            get_voorraad_repository
        ]()
        repo.save(
            [
                VoorraadItem(
                    naam="oud-product",
                    type=VoorraadType.HOUDBAAR,
                    op_voorraad=True,
                    laatst_gecheckt="2026-01-01",
                )
            ]
        )
        client = TestClient(app_with_voorraad)
        set_week_menu(client, make_full_week_menu())
        client.get("/voorraad")
        namen = {i.naam for i in repo.load()}
        assert "oud-product" not in namen

    def test_bestaand_item_behoudt_status_bij_sync(self, app_with_voorraad: FastAPI):
        """Item dat al in repository staat behoudt op_voorraad=False na sync."""
        from boodschappenagent.voorraadbeheer.models import VoorraadItem, VoorraadType

        repo: VoorraadRepository = app_with_voorraad.dependency_overrides[
            get_voorraad_repository
        ]()
        # Melk staat in TEST_VOORRAAD_PRODUCTEN, maar al als niet-op-voorraad opgeslagen
        repo.save(
            [
                VoorraadItem(
                    naam="melk",
                    type=VoorraadType.HOUDBAAR,
                    op_voorraad=False,
                    laatst_gecheckt="2026-01-01",
                )
            ]
        )
        client = TestClient(app_with_voorraad)
        set_week_menu(client, make_full_week_menu())
        client.get("/voorraad")
        items = repo.load()
        melk = next(i for i in items if i.naam == "melk")
        assert melk.op_voorraad is False


class TestVoorraadBevestig:
    """S8: Voorraad bevestigen (batch update → redirect)."""

    def test_s8_1_redirect_naar_boodschappen(
        self,
        app_with_boodschappen_and_ah: FastAPI,
        mock_token_manager_authenticated,
        mock_ah_integratie,
    ):
        """S8.1: POST /voorraad/bevestig → 303 redirect naar /boodschappen/match-review."""  # noqa: E501
        app_with_boodschappen_and_ah.dependency_overrides[get_ah_token_manager] = (
            lambda: mock_token_manager_authenticated
        )
        app_with_boodschappen_and_ah.dependency_overrides[get_ah_integratie] = (
            lambda: mock_ah_integratie
        )
        mock_ah_integratie.zoek_producten.return_value = []
        client = TestClient(app_with_boodschappen_and_ah)
        set_week_menu(client, make_full_week_menu())
        client.app.state.ingredient_selectie = [
            {
                "id": "item-s8",
                "recept_naam": "Kip curry",
                "naam": "kip",
                "hoeveelheid": 300.0,
                "eenheid": "g",
                "geselecteerd": True,
            }
        ]
        response = client.post("/voorraad/bevestig", follow_redirects=False)
        assert response.status_code in (301, 302, 303, 307, 308)
        assert response.headers["location"] == "/boodschappen/match-review"

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


class TestVoorraadBevestigAggregatie:
    """T017: POST /voorraad/bevestig aggregeert geselecteerde recept-ingrediënten."""

    @pytest.fixture
    def client_met_selectie(self, app_with_boodschappen: FastAPI) -> TestClient:
        """Client met boodschappenlijst dependencies en ingredient_selectie in state."""
        client = TestClient(app_with_boodschappen)
        set_week_menu(client, make_full_week_menu())
        client.app.state.ingredient_selectie = [
            {
                "id": "item-1",
                "recept_naam": "Kip curry",
                "naam": "kip",
                "hoeveelheid": 300.0,
                "eenheid": "g",
                "geselecteerd": True,
            },
            {
                "id": "item-2",
                "recept_naam": "Kip wok",
                "naam": "kip",
                "hoeveelheid": 200.0,
                "eenheid": "g",
                "geselecteerd": True,
            },
            {
                "id": "item-3",
                "recept_naam": "Kip curry",
                "naam": "rijst",
                "hoeveelheid": 150.0,
                "eenheid": "g",
                "geselecteerd": True,
            },
            {
                "id": "item-4",
                "recept_naam": "Kip curry",
                "naam": "ui",
                "hoeveelheid": 1.0,
                "eenheid": "stuks",
                "geselecteerd": False,
            },
        ]
        return client

    def test_aggregeert_gelijke_ingredienten(self, client_met_selectie: TestClient):
        """Kip uit twee recepten worden samengevoegd in één regel."""
        client_met_selectie.post("/voorraad/bevestig", follow_redirects=False)
        boodschappenlijst = client_met_selectie.app.state.boodschappenlijst
        kip_items = [i for i in boodschappenlijst if i["naam"] == "kip"]
        assert len(kip_items) == 1
        assert kip_items[0]["hoeveelheid"] == pytest.approx(500.0, abs=1)

    def test_laat_niet_geselecteerde_items_weg(self, client_met_selectie: TestClient):
        """Niet-geselecteerde items komen niet in de boodschappenlijst."""
        client_met_selectie.post("/voorraad/bevestig", follow_redirects=False)
        boodschappenlijst = client_met_selectie.app.state.boodschappenlijst
        namen = {i["naam"] for i in boodschappenlijst}
        assert "ui" not in namen

    def test_slaat_boodschappenlijst_op_in_state(self, client_met_selectie: TestClient):
        """Na POST is app.state.boodschappenlijst gevuld."""
        client_met_selectie.post("/voorraad/bevestig", follow_redirects=False)
        assert hasattr(client_met_selectie.app.state, "boodschappenlijst")
        assert client_met_selectie.app.state.boodschappenlijst is not None

    def test_rijst_aanwezig_in_resultaat(self, client_met_selectie: TestClient):
        """Geselecteerde rijst-ingredient is aanwezig in boodschappenlijst."""
        client_met_selectie.post("/voorraad/bevestig", follow_redirects=False)
        boodschappenlijst = client_met_selectie.app.state.boodschappenlijst
        namen = {i["naam"] for i in boodschappenlijst}
        assert "rijst" in namen


class TestVoorraadBevestigMatching:
    """T020, T021: POST /voorraad/bevestig → matching redirect en lege-lijst fout."""

    @pytest.fixture
    def app_met_matching(
        self,
        app_with_boodschappen: FastAPI,
        mock_token_manager_authenticated,
        mock_ah_integratie,
        mock_match_voorkeuren_repository,
    ) -> FastAPI:
        """App met boodschappen, authenticated AH token en mock AH integratie."""
        app_with_boodschappen.dependency_overrides[get_ah_token_manager] = (
            lambda: mock_token_manager_authenticated
        )
        app_with_boodschappen.dependency_overrides[get_ah_integratie] = (
            lambda: mock_ah_integratie
        )
        app_with_boodschappen.dependency_overrides[get_match_voorkeuren_repository] = (
            lambda: mock_match_voorkeuren_repository
        )
        return app_with_boodschappen

    def test_t020_redirectt_naar_match_review(
        self, app_met_matching: FastAPI, mock_ah_integratie
    ):
        """T020: Gevulde lijst → 303 redirect naar /boodschappen/match-review."""
        mock_ah_integratie.zoek_producten.return_value = []
        client = TestClient(app_met_matching)
        set_week_menu(client, make_full_week_menu())
        client.app.state.ingredient_selectie = [
            {
                "id": "item-t020",
                "recept_naam": "Kip curry",
                "naam": "kip",
                "hoeveelheid": 300.0,
                "eenheid": "g",
                "geselecteerd": True,
            }
        ]
        response = client.post("/voorraad/bevestig", follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"] == "/boodschappen/match-review"

    def test_t020_slaat_match_review_items_op(
        self, app_met_matching: FastAPI, mock_ah_integratie
    ):
        """T020: Na succesvolle bevestiging staan match_review_items in app.state."""
        mock_ah_integratie.zoek_producten.return_value = []
        client = TestClient(app_met_matching)
        set_week_menu(client, make_full_week_menu())
        client.app.state.ingredient_selectie = [
            {
                "id": "item-t020b",
                "recept_naam": "Kip curry",
                "naam": "kip",
                "hoeveelheid": 300.0,
                "eenheid": "g",
                "geselecteerd": True,
            }
        ]
        client.post("/voorraad/bevestig", follow_redirects=False)
        assert hasattr(client.app.state, "match_review_items")

    def test_t021_lege_lijst_geeft_foutpagina(self, app_met_matching: FastAPI):
        """T021: Lege ingredient_selectie + geen pantry → ah_error.html lege_lijst."""
        client = TestClient(app_met_matching)
        set_week_menu(client, make_full_week_menu())
        client.app.state.ingredient_selectie = []
        response = client.post("/voorraad/bevestig", follow_redirects=False)
        assert response.status_code == 200
        s = soup(response)
        assert s.select_one('[data-testid="ah-lege-lijst"]') is not None
