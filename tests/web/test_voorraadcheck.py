"""Integratietests voor voorraadcheck pagina (S6, S7, S8)."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from boodschappenagent.voorraadbeheer import VoorraadRepository
from boodschappenagent.web.dependencies import get_ah_client, get_voorraad_repository

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
    """TestClient met Melk op voorraad, mock AHClient en ingelogde token manager."""
    from boodschappenagent.web.dependencies import get_ah_token_manager

    app_with_overrides.dependency_overrides[get_voorraad_repository] = (
        lambda: voorraad_met_melk
    )
    app_with_overrides.dependency_overrides[get_ah_client] = lambda: mock_ah_client
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
        response = client_with_voorraad.get(
            "/voorraad", headers={"HX-Request": "true"}
        )
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
        response = client_with_voorraad.get(
            "/voorraad", follow_redirects=False
        )
        assert response.status_code in (301, 302, 303, 307, 308)
        assert "/week" in response.headers["location"]

    def test_s6_7_ah_fout_toont_melding(
        self, app_with_overrides: FastAPI, mock_token_manager_authenticated
    ):
        """S6.7: Als AH lijst leeg is, toont pagina foutmelding."""
        from unittest.mock import MagicMock

        from boodschappenagent.web.dependencies import get_ah_token_manager

        lege_client = MagicMock()
        lege_client.find_list_by_name.return_value = None
        app_with_overrides.dependency_overrides[get_ah_client] = lambda: lege_client
        app_with_overrides.dependency_overrides[get_ah_token_manager] = (
            lambda: mock_token_manager_authenticated
        )
        client = TestClient(app_with_overrides)
        set_week_menu(client, make_full_week_menu())
        s = soup(client.get("/voorraad"))
        assert "Albert Heijn" in s.get_text()

    def test_s6_8_niet_ingelogd_redirect_naar_login(
        self, app_with_overrides: FastAPI, mock_ah_client, mock_token_manager_unauthenticated
    ):
        """S6.8: Niet ingelogd bij AH → redirect naar /ah/login."""
        from boodschappenagent.web.dependencies import get_ah_token_manager

        app_with_overrides.dependency_overrides[get_ah_client] = lambda: mock_ah_client
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
        melk_item = s.select_one(
            '[data-testid="voorraaditem"][data-item="1001"]'
        )
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
        item = s.select_one('[data-testid="voorraaditem"][data-item="1001"]')
        assert item is not None
        ja_button = item.select_one('[data-testid="status-ja"][data-actief="true"]')
        assert ja_button is not None

    def test_s7_2_toggle_nee_actief(
        self, client_met_melk_op_voorraad: TestClient
    ):
        """S7.2: POST /voorraad/1001/status met op_voorraad=false → Nee actief."""
        set_week_menu(client_met_melk_op_voorraad, make_full_week_menu())
        response = client_met_melk_op_voorraad.post(
            "/voorraad/1001/status",
            data={"op_voorraad": "false", "naam": "Melk"},
        )
        assert response.status_code == 200
        s = soup(response)
        item = s.select_one('[data-testid="voorraaditem"][data-item="1001"]')
        assert item is not None
        nee_button = item.select_one(
            '[data-testid="status-nee"][data-actief="true"]'
        )
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
        repo: VoorraadRepository = (
            client_with_voorraad.app.dependency_overrides[get_voorraad_repository]()
        )
        assert "melk" in repo.op_voorraad_namen()


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
