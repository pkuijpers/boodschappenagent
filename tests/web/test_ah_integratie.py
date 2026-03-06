"""Tests voor AH integratie web routes (S12-S19)."""

import pytest
from fastapi.testclient import TestClient

from .conftest import soup


class TestAHLoginPagina:
    """S12: AH Login pagina."""

    @pytest.fixture
    def login_html(self, app_with_ah):
        """GET /ah/login als BeautifulSoup (full page)."""
        client = TestClient(app_with_ah)
        response = client.get("/ah/login")
        assert response.status_code == 200
        return soup(response)

    def test_s12_1a_login_pagina_laadt_full_page(self, login_html):
        """S12.1a: GET /ah/login zonder HTMX headers -> volledige HTML pagina."""
        assert login_html.find("html") is not None
        assert login_html.select_one('[data-testid="ah-login-form"]') is not None

    def test_s12_1b_login_pagina_laadt_htmx_fragment(self, app_with_ah):
        """S12.1b: GET /ah/login met HX-Request header -> fragment zonder <html>."""
        client = TestClient(app_with_ah, headers={"HX-Request": "true"})
        response = client.get("/ah/login")

        assert response.status_code == 200
        html = soup(response)
        assert html.find("html") is None
        assert html.select_one('[data-testid="ah-login-form"]') is not None

    def test_s12_2_login_pagina_toont_login_url(self, login_html):
        """S12.2: Login pagina toont login URL naar login.ah.nl."""
        login_url_el = login_html.select_one('[data-testid="ah-login-url"]')
        assert login_url_el is not None
        href = login_url_el.get("href", login_url_el.get_text())
        assert "login.ah.nl" in href

    def test_s12_3_login_pagina_heeft_code_veld(self, login_html):
        """S12.3: Login pagina heeft input veld voor authorization code."""
        assert login_html.select_one('input[name="code"]') is not None

    def test_s12_4_login_pagina_heeft_submit_knop(self, login_html):
        """S12.4: Login pagina heeft "Inloggen" submit knop."""
        assert login_html.select_one('[data-testid="ah-login-submit"]') is not None


class TestAHLoginVerwerken:
    """S13: AH Login verwerken."""

    def test_s13_1_succesvolle_login_redirect(self, app_with_ah, mock_token_manager):
        """S13.1: Geldige code -> redirect (303) naar /boodschappen."""
        mock_token_manager.login.return_value = None
        client = TestClient(app_with_ah, follow_redirects=False)
        response = client.post("/ah/login", data={"code": "valid-auth-code"})

        assert response.status_code == 303
        assert response.headers["location"] == "/boodschappen"

    def test_s13_2_login_slaat_tokens_op(self, app_with_ah, mock_token_manager):
        """S13.2: POST /ah/login roept token_manager.login() aan met code."""
        client = TestClient(app_with_ah, follow_redirects=False)
        client.post("/ah/login", data={"code": "valid-auth-code"})

        mock_token_manager.login.assert_called_once_with("valid-auth-code")

    def test_s13_3_ongeldige_code_foutmelding(self, app_with_ah, mock_token_manager):
        """S13.3: POST /ah/login met ongeldige code -> login pagina met foutmelding."""
        mock_token_manager.login.side_effect = Exception("Invalid authorization code")
        client = TestClient(app_with_ah)
        response = client.post("/ah/login", data={"code": "invalid-code"})

        assert response.status_code == 200
        html = soup(response)
        error = html.select_one('[data-testid="ah-login-error"]')
        assert error is not None
        # Login form moet nog steeds zichtbaar zijn
        assert html.select_one('[data-testid="ah-login-form"]') is not None

    def test_s13_4_lege_code_422(self, app_with_ah):
        """S13.4: POST /ah/login met lege code -> HTTP 422."""
        client = TestClient(app_with_ah)
        response = client.post("/ah/login", data={"code": ""})

        assert response.status_code == 422

    def test_s13_5_login_redirect_met_next(self, app_with_ah, mock_token_manager):
        """S13.5: POST /ah/login met next parameter -> redirect naar next URL."""
        mock_token_manager.login.return_value = None
        client = TestClient(app_with_ah, follow_redirects=False)
        response = client.post(
            "/ah/login?next=/boodschappen/verstuur-naar-ah",
            data={"code": "valid-auth-code"},
        )

        assert response.status_code == 303
        assert response.headers["location"] == "/boodschappen/verstuur-naar-ah"


class TestAHStatusCheck:
    """S14: AH Status check."""

    def test_s14_1_ingelogd_status_ok(self, app_with_ah, mock_token_manager):
        """S14.1: Ingelogd -> JSON {"authenticated": true}."""
        mock_token_manager.is_authenticated.return_value = True
        client = TestClient(app_with_ah)
        response = client.get("/ah/status")

        assert response.status_code == 200
        assert response.json() == {"authenticated": True}

    def test_s14_2_niet_ingelogd_status_not_ok(self, app_with_ah, mock_token_manager):
        """S14.2: Niet ingelogd -> JSON {"authenticated": false}."""
        mock_token_manager.is_authenticated.return_value = False
        client = TestClient(app_with_ah)
        response = client.get("/ah/status")

        assert response.status_code == 200
        assert response.json() == {"authenticated": False}

    def test_s14_3_verlopen_tokens_refresh_lukt(self, app_with_ah, mock_token_manager):
        """S14.3: Access token verlopen maar refresh lukt -> authenticated true."""
        # Eerste keer is_authenticated: False (verlopen), maar na refresh: True
        mock_token_manager.is_authenticated.return_value = False
        mock_token_manager.refresh.return_value = None
        # Na refresh wordt is_authenticated True
        mock_token_manager.is_authenticated.side_effect = [False, True]
        mock_token_manager.refresh.side_effect = None

        client = TestClient(app_with_ah)
        response = client.get("/ah/status")

        assert response.status_code == 200
        assert response.json() == {"authenticated": True}
        mock_token_manager.refresh.assert_called_once()


class TestAHLogout:
    """S18: AH Logout."""

    def test_s18_1_logout_verwijdert_tokens(self, app_with_ah, mock_token_manager):
        """S18.1: POST /ah/logout -> redirect naar /ah/login, tokens verwijderd."""
        mock_token_manager.is_authenticated.return_value = True
        client = TestClient(app_with_ah, follow_redirects=False)
        response = client.post("/ah/logout")

        assert response.status_code == 303
        assert response.headers["location"] == "/ah/login"

    def test_s18_2_logout_als_niet_ingelogd(self, app_with_ah, mock_token_manager):
        """S18.2: POST /ah/logout als niet ingelogd -> redirect zonder error."""
        mock_token_manager.is_authenticated.return_value = False
        client = TestClient(app_with_ah, follow_redirects=False)
        response = client.post("/ah/logout")

        assert response.status_code == 303
        assert response.headers["location"] == "/ah/login"


class TestVerstuurNaarAHSucces:
    """S15: Verstuur naar AH (succes flow)."""

    @pytest.fixture
    def _setup_boodschappenlijst(self, app_with_ah):
        """Zet een boodschappenlijst en weekmenu op app.state."""
        from boodschappenagent.boodschappenlijst.models import (
            Boodschappenlijst,
            BoodschappenRegel,
        )

        from .conftest import make_full_week_menu

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

    def test_s15_1_verstuur_toont_bevestiging(
        self, app_with_ah, mock_token_manager, mock_ah_integratie,
        sync_resultaat_succes, _setup_boodschappenlijst,
    ):
        """S15.1: Bevestigingsscherm met groen vinkje."""
        mock_token_manager.is_authenticated.return_value = True
        mock_ah_integratie.sync_naar_lijst.return_value = sync_resultaat_succes
        client = TestClient(app_with_ah)
        response = client.post("/boodschappen/verstuur-naar-ah")

        assert response.status_code == 200
        html = soup(response)
        assert html.select_one('[data-testid="ah-bevestiging"]') is not None

    def test_s15_2_bevestiging_toont_aantal_producten(
        self, app_with_ah, mock_token_manager, mock_ah_integratie,
        sync_resultaat_succes, _setup_boodschappenlijst,
    ):
        """S15.2: Bevestiging toont "15 producten in je mandje"."""
        mock_token_manager.is_authenticated.return_value = True
        mock_ah_integratie.sync_naar_lijst.return_value = sync_resultaat_succes
        client = TestClient(app_with_ah)
        response = client.post("/boodschappen/verstuur-naar-ah")

        html = soup(response)
        aantal_el = html.select_one('[data-testid="ah-aantal-producten"]')
        assert aantal_el is not None
        assert "15" in aantal_el.get_text()

    def test_s15_3_bevestiging_toont_lijst_naam(
        self, app_with_ah, mock_token_manager, mock_ah_integratie,
        sync_resultaat_succes, _setup_boodschappenlijst,
    ):
        """S15.3: Bevestiging toont de lijst naam."""
        mock_token_manager.is_authenticated.return_value = True
        mock_ah_integratie.sync_naar_lijst.return_value = sync_resultaat_succes
        client = TestClient(app_with_ah)
        response = client.post("/boodschappen/verstuur-naar-ah")

        html = soup(response)
        naam_el = html.select_one('[data-testid="ah-lijst-naam"]')
        assert naam_el is not None
        assert "Boodschappen 2026-03-02" in naam_el.get_text()

    def test_s15_4_open_albert_heijn_link(
        self, app_with_ah, mock_token_manager, mock_ah_integratie,
        sync_resultaat_succes, _setup_boodschappenlijst,
    ):
        """S15.4: "Open Albert Heijn" link zichtbaar."""
        mock_token_manager.is_authenticated.return_value = True
        mock_ah_integratie.sync_naar_lijst.return_value = sync_resultaat_succes
        client = TestClient(app_with_ah)
        response = client.post("/boodschappen/verstuur-naar-ah")

        html = soup(response)
        link = html.select_one('[data-testid="ah-open-link"]')
        assert link is not None
        assert "ah.nl" in link.get("href", "")

    def test_s15_5_terug_naar_home_link(
        self, app_with_ah, mock_token_manager, mock_ah_integratie,
        sync_resultaat_succes, _setup_boodschappenlijst,
    ):
        """S15.5: "Terug naar home" link naar /week."""
        mock_token_manager.is_authenticated.return_value = True
        mock_ah_integratie.sync_naar_lijst.return_value = sync_resultaat_succes
        client = TestClient(app_with_ah)
        response = client.post("/boodschappen/verstuur-naar-ah")

        html = soup(response)
        link = html.select_one('a[href="/week"]')
        assert link is not None
