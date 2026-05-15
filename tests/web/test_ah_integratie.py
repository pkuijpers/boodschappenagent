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
    """S15: Verstuur naar AH redirectt naar match-review na matching."""

    def test_s15_1_verstuur_redirect_naar_match_review(
        self,
        app_with_ah,
        mock_token_manager,
        mock_ah_integratie,
        setup_boodschappenlijst,  # noqa: ARG002
    ):
        """S15.1: Succesvol matchen → 303 redirect naar /boodschappen/match-review."""
        from boodschappenagent.ah.integration import ProductMatch
        from boodschappenagent.ah.models import Product

        mock_token_manager.is_authenticated.return_value = True
        mock_ah_integratie.zoek_producten.return_value = [
            ProductMatch(
                regel=type(
                    "R",
                    (),
                    {"naam": f"product-{i}", "hoeveelheid": 1.0, "eenheid": "stuk"},
                )(),
                product=Product(
                    id=i,
                    title=f"Product {i}",
                    brand="",
                    size="",
                    price=1.0,
                    category="",
                    is_orderable=True,
                ),
                bron="zoekopdracht",
                aantal=1,
            )
            for i in range(15)
        ]

        client = TestClient(app_with_ah, follow_redirects=False)
        response = client.post("/boodschappen/verstuur-naar-ah")

        assert response.status_code == 303
        assert response.headers["location"] == "/boodschappen/match-review"

    def test_s15_2_match_review_items_aanwezig_in_state(
        self,
        app_with_ah,
        mock_token_manager,
        mock_ah_integratie,
        setup_boodschappenlijst,  # noqa: ARG002
    ):
        """S15.2: Match-review items worden opgeslagen in app.state."""
        from boodschappenagent.ah.integration import ProductMatch
        from boodschappenagent.ah.models import Product

        mock_token_manager.is_authenticated.return_value = True
        mock_ah_integratie.zoek_producten.return_value = [
            ProductMatch(
                regel=type(
                    "R", (), {"naam": "melk", "hoeveelheid": 1.0, "eenheid": "liter"}
                )(),
                product=Product(
                    id=1,
                    title="AH Melk",
                    brand="AH",
                    size="1L",
                    price=1.09,
                    category="Zuivel",
                    is_orderable=True,
                ),
                bron="zoekopdracht",
                aantal=1,
            )
        ]

        client = TestClient(app_with_ah, follow_redirects=False)
        client.post("/boodschappen/verstuur-naar-ah")

        items = getattr(app_with_ah.state, "match_review_items", None)
        assert items is not None and len(items) == 1

    def test_s15_3_zoek_producten_niet_sync_naar_lijst(
        self,
        app_with_ah,
        mock_token_manager,
        mock_ah_integratie,
        setup_boodschappenlijst,  # noqa: ARG002
    ):
        """S15.3: zoek_producten() wordt aangeroepen; sync_naar_lijst() niet meer."""

        mock_token_manager.is_authenticated.return_value = True
        mock_ah_integratie.zoek_producten.return_value = []

        app_with_ah.state.boodschappenlijst = []
        client = TestClient(app_with_ah, follow_redirects=False)
        client.post("/boodschappen/verstuur-naar-ah")

        mock_ah_integratie.sync_naar_lijst.assert_not_called()


class TestVerstuurNaarAHNietGevonden:
    """S16: Niet-gevonden producten zijn zichtbaar in de match-review pagina."""

    def test_s16_1_niet_gevonden_in_match_review_state(
        self,
        app_with_ah,
        mock_token_manager,
        mock_ah_integratie,
        setup_boodschappenlijst,  # noqa: ARG002
    ):
        """S16.1: Niet-gevonden items (product=None) landen in match_review_items."""
        from boodschappenagent.ah.integration import ProductMatch

        mock_token_manager.is_authenticated.return_value = True
        mock_ah_integratie.zoek_producten.return_value = [
            ProductMatch(
                regel=type(
                    "R",
                    (),
                    {"naam": "verse basilicum", "hoeveelheid": 1.0, "eenheid": "bos"},
                )(),
                product=None,
                bron="niet_gevonden",
                aantal=1,
            )
        ]

        client = TestClient(app_with_ah, follow_redirects=False)
        client.post("/boodschappen/verstuur-naar-ah")

        items = getattr(app_with_ah.state, "match_review_items", None)
        assert items is not None
        assert items[0].product is None
        assert items[0].bron == "niet_gevonden"

    def test_s16_2_niet_gevonden_redirect_naar_match_review(
        self,
        app_with_ah,
        mock_token_manager,
        mock_ah_integratie,
        setup_boodschappenlijst,  # noqa: ARG002
    ):
        """S16.2: Niet-gevonden producten → redirect naar match-review."""
        from boodschappenagent.ah.integration import ProductMatch

        mock_token_manager.is_authenticated.return_value = True
        mock_ah_integratie.zoek_producten.return_value = [
            ProductMatch(
                regel=type(
                    "R", (), {"naam": "quinoa", "hoeveelheid": 200.0, "eenheid": "gram"}
                )(),
                product=None,
                bron="niet_gevonden",
                aantal=1,
            )
        ]

        client = TestClient(app_with_ah, follow_redirects=False)
        response = client.post("/boodschappen/verstuur-naar-ah")

        assert response.status_code == 303
        assert response.headers["location"] == "/boodschappen/match-review"


class TestVerstuurNaarAHErrors:
    """S17: Verstuur naar AH (error scenarios)."""

    def test_s17_1_niet_ingelogd_redirect_login(self, app_with_ah, mock_token_manager):
        """S17.1: Niet ingelogd -> redirect (303) naar /ah/login."""
        mock_token_manager.is_authenticated.return_value = False
        client = TestClient(app_with_ah, follow_redirects=False)
        response = client.post("/boodschappen/verstuur-naar-ah")

        assert response.status_code == 303
        assert response.headers["location"] == "/ah/login"

    def test_s17_2_geen_boodschappenlijst_redirect_week(
        self, app_with_ah, mock_token_manager
    ):
        """S17.2: Geen boodschappenlijst in state -> redirect (303) naar /week."""
        mock_token_manager.is_authenticated.return_value = True
        app_with_ah.state.boodschappenlijst_model = None
        client = TestClient(app_with_ah, follow_redirects=False)
        response = client.post("/boodschappen/verstuur-naar-ah")

        assert response.status_code == 303
        assert response.headers["location"] == "/week"

    def test_s17_3_lege_boodschappenlijst_foutmelding(
        self, app_with_ah, mock_token_manager
    ):
        """S17.3: Lege boodschappenlijst -> foutmelding."""
        from boodschappenagent.boodschappenlijst.models import Boodschappenlijst

        mock_token_manager.is_authenticated.return_value = True
        app_with_ah.state.boodschappenlijst_model = Boodschappenlijst(
            week_start="2026-02-16", regels=[]
        )
        client = TestClient(app_with_ah)
        response = client.post("/boodschappen/verstuur-naar-ah")

        assert response.status_code == 200
        html = soup(response)
        assert html.select_one('[data-testid="ah-lege-lijst"]') is not None

    def test_s17_4_ah_api_fout_foutmelding(
        self,
        app_with_ah,
        mock_token_manager,
        mock_ah_integratie,
        setup_boodschappenlijst,  # noqa: ARG002
    ):
        """S17.4: AH API fout (zoek_producten) -> foutmelding."""
        mock_token_manager.is_authenticated.return_value = True
        mock_ah_integratie.zoek_producten.side_effect = Exception("AH API error")
        client = TestClient(app_with_ah)
        response = client.post("/boodschappen/verstuur-naar-ah")

        assert response.status_code == 200
        html = soup(response)
        assert html.select_one('[data-testid="ah-api-error"]') is not None

    def test_s17_5_token_verlopen_redirect_login(self, app_with_ah, mock_token_manager):
        """S17.5: Token verlopen bij versturen -> redirect (303) naar /ah/login."""
        mock_token_manager.is_authenticated.side_effect = Exception("Token expired")
        client = TestClient(app_with_ah, follow_redirects=False)
        response = client.post("/boodschappen/verstuur-naar-ah")

        assert response.status_code == 303
        assert response.headers["location"] == "/ah/login"


class TestVerstuurNaarAHCheckedItems:
    """Gecheckte items worden niet verstuurd naar AH (gefilterde lijst)."""

    def test_gecheckt_item_wordt_niet_verstuurd(
        self,
        app_with_ah,
        mock_token_manager,
        mock_ah_integratie,
        setup_boodschappenlijst,  # noqa: ARG002
    ):
        """Item met checked=True: zoek_producten krijgt 14 regels."""
        mock_token_manager.is_authenticated.return_value = True
        mock_ah_integratie.zoek_producten.return_value = []

        app_with_ah.state.boodschappenlijst[0]["checked"] = True

        client = TestClient(app_with_ah, follow_redirects=False)
        client.post("/boodschappen/verstuur-naar-ah")

        mock_ah_integratie.zoek_producten.assert_called_once()
        lijst_arg = mock_ah_integratie.zoek_producten.call_args[0][0]
        namen = [r.naam for r in lijst_arg.regels]
        assert "product-0" not in namen
        assert len(namen) == 14

    def test_meerdere_gecheckte_items_worden_niet_verstuurd(
        self,
        app_with_ah,
        mock_token_manager,
        mock_ah_integratie,
        setup_boodschappenlijst,  # noqa: ARG002
    ):
        """Meerdere gecheckte items worden allemaal uitgefilterd."""
        mock_token_manager.is_authenticated.return_value = True
        mock_ah_integratie.zoek_producten.return_value = []

        app_with_ah.state.boodschappenlijst[0]["checked"] = True
        app_with_ah.state.boodschappenlijst[3]["checked"] = True

        client = TestClient(app_with_ah, follow_redirects=False)
        client.post("/boodschappen/verstuur-naar-ah")

        mock_ah_integratie.zoek_producten.assert_called_once()
        lijst_arg = mock_ah_integratie.zoek_producten.call_args[0][0]
        namen = [r.naam for r in lijst_arg.regels]
        assert "product-0" not in namen
        assert "product-3" not in namen
        assert len(namen) == 13

    def test_geen_gecheckte_items_stuurt_volledige_lijst(
        self,
        app_with_ah,
        mock_token_manager,
        mock_ah_integratie,
        setup_boodschappenlijst,  # noqa: ARG002
    ):
        """Zonder gecheckte items krijgt zoek_producten de volledige lijst."""
        mock_token_manager.is_authenticated.return_value = True
        mock_ah_integratie.zoek_producten.return_value = []

        client = TestClient(app_with_ah, follow_redirects=False)
        client.post("/boodschappen/verstuur-naar-ah")

        mock_ah_integratie.zoek_producten.assert_called_once()
        lijst_arg = mock_ah_integratie.zoek_producten.call_args[0][0]
        assert len(lijst_arg.regels) == 15


class TestVerstuurNaarAHHandmatig:
    """S20: Handmatig toegevoegde artikelen worden meegestuurd naar zoek_producten."""

    def test_s20_1_handmatig_item_wordt_meegestuurd(
        self,
        app_with_ah,
        mock_token_manager,
        mock_ah_integratie,
        setup_boodschappenlijst_met_handmatig,  # noqa: ARG002
    ):
        """S20.1: Handmatig artikel "zeep" zit in de lijst voor zoek_producten."""
        mock_token_manager.is_authenticated.return_value = True
        mock_ah_integratie.zoek_producten.return_value = []

        client = TestClient(app_with_ah, follow_redirects=False)
        client.post("/boodschappen/verstuur-naar-ah")

        mock_ah_integratie.zoek_producten.assert_called_once()
        namen = [
            r.naam for r in mock_ah_integratie.zoek_producten.call_args[0][0].regels
        ]
        assert "zeep" in namen
        assert "pasta" in namen

    def test_s20_2_gemengde_lijst_alle_items_meegestuurd(
        self,
        app_with_ah,
        mock_token_manager,
        mock_ah_integratie,
        setup_boodschappenlijst_met_handmatig,  # noqa: ARG002
    ):
        """S20.2: Gemengde lijst (3 menu + 2 handmatig) → 5 regels."""
        mock_token_manager.is_authenticated.return_value = True
        mock_ah_integratie.zoek_producten.return_value = []

        app_with_ah.state.boodschappenlijst = [
            {
                "id": f"menu-{i}",
                "naam": f"menu-item-{i}",
                "hoeveelheid": 1,
                "eenheid": "stuk",
                "checked": False,
                "handmatig": False,
                "eerste_recept": "Recept",
                "extra_aantal": 0,
            }
            for i in range(3)
        ] + [
            {
                "id": f"handmatig-{i}",
                "naam": f"handmatig-item-{i}",
                "hoeveelheid": 1,
                "eenheid": "stuks",
                "checked": False,
                "handmatig": True,
                "eerste_recept": None,
                "extra_aantal": 0,
            }
            for i in range(2)
        ]

        client = TestClient(app_with_ah, follow_redirects=False)
        client.post("/boodschappen/verstuur-naar-ah")

        mock_ah_integratie.zoek_producten.assert_called_once()
        assert len(mock_ah_integratie.zoek_producten.call_args[0][0].regels) == 5

    def test_s20_3_alleen_handmatige_items_worden_verstuurd(
        self,
        app_with_ah,
        mock_token_manager,
        mock_ah_integratie,
        setup_boodschappenlijst_met_handmatig,  # noqa: ARG002
    ):
        """S20.3: Alleen handmatige items → volledig doorgegeven aan zoek_producten."""
        mock_token_manager.is_authenticated.return_value = True
        mock_ah_integratie.zoek_producten.return_value = []

        from boodschappenagent.boodschappenlijst.models import Boodschappenlijst

        app_with_ah.state.boodschappenlijst_model = Boodschappenlijst(
            week_start="2026-02-16",
            regels=[],
        )
        app_with_ah.state.boodschappenlijst = [
            {
                "id": f"handmatig-{i}",
                "naam": f"handmatig-item-{i}",
                "hoeveelheid": 1,
                "eenheid": "stuks",
                "checked": False,
                "handmatig": True,
                "eerste_recept": None,
                "extra_aantal": 0,
            }
            for i in range(2)
        ]

        client = TestClient(app_with_ah, follow_redirects=False)
        client.post("/boodschappen/verstuur-naar-ah")

        mock_ah_integratie.zoek_producten.assert_called_once()
        assert len(mock_ah_integratie.zoek_producten.call_args[0][0].regels) == 2

    def test_s20_4_gemengde_lijst_redirect_naar_match_review(
        self,
        app_with_ah,
        mock_token_manager,
        mock_ah_integratie,
        setup_boodschappenlijst_met_handmatig,  # noqa: ARG002
    ):
        """S20.4: Gemengde lijst → 303 redirect naar match-review."""
        mock_token_manager.is_authenticated.return_value = True
        mock_ah_integratie.zoek_producten.return_value = []

        client = TestClient(app_with_ah, follow_redirects=False)
        response = client.post("/boodschappen/verstuur-naar-ah")

        assert response.status_code == 303
        assert response.headers["location"] == "/boodschappen/match-review"

    def test_s20_5_fout_bij_versturen_toont_foutmelding(
        self,
        app_with_ah,
        mock_token_manager,
        mock_ah_integratie,
        setup_boodschappenlijst_met_handmatig,  # noqa: ARG002
    ):
        """S20.5: AH API fout toont foutmelding, lijst blijft ongewijzigd."""
        mock_token_manager.is_authenticated.return_value = True
        mock_ah_integratie.zoek_producten.side_effect = Exception("AH API error")

        client = TestClient(app_with_ah)
        response = client.post("/boodschappen/verstuur-naar-ah")

        assert response.status_code == 200
        assert soup(response).select_one('[data-testid="ah-api-error"]') is not None
        assert len(app_with_ah.state.boodschappenlijst) == 2

    def test_s20_6_lege_boodschappenlijst_toont_melding(
        self,
        app_with_ah,
        mock_token_manager,
        mock_ah_integratie,
        setup_boodschappenlijst_met_handmatig,  # noqa: ARG002
    ):
        """S20.6: Lege lijst toont melding; zoek_producten niet aangeroepen."""
        mock_token_manager.is_authenticated.return_value = True

        from boodschappenagent.boodschappenlijst.models import Boodschappenlijst

        app_with_ah.state.boodschappenlijst_model = Boodschappenlijst(
            week_start="2026-02-16",
            regels=[],
        )
        app_with_ah.state.boodschappenlijst = []

        client = TestClient(app_with_ah)
        response = client.post("/boodschappen/verstuur-naar-ah")

        assert response.status_code == 200
        assert soup(response).select_one('[data-testid="ah-lege-lijst"]') is not None
        mock_ah_integratie.zoek_producten.assert_not_called()
