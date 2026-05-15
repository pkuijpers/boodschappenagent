"""E2E tests voor AH integratie (E15-E21)."""

import pytest

from boodschappenagent.ah.models import Product
from boodschappenagent.ah.preferences import MatchReviewItem


@pytest.mark.e2e
class TestE15LoginPaginaLaden:
    """E15: Login pagina laden — navigeer naar /ah/login en verifieer inhoud."""

    def test_login_pagina_instructies_zichtbaar(self, page, live_server_url):
        """Instructies, code-invoerveld, login URL en submit knop zichtbaar."""
        page.goto(f"{live_server_url}/ah/login")
        page.wait_for_selector("[data-testid='ah-login-form']")

        # Login formulier zichtbaar
        form = page.locator('[data-testid="ah-login-form"]')
        assert form.is_visible()

        # Login URL zichtbaar en verwijst naar login.ah.nl
        login_url = page.locator('[data-testid="ah-login-url"]')
        assert login_url.is_visible()
        href = login_url.get_attribute("href")
        assert "login.ah.nl" in href

        # Code invoerveld aanwezig
        code_input = page.locator('input[name="code"]')
        assert code_input.is_visible()

        # Submit knop aanwezig
        submit = page.locator('[data-testid="ah-login-submit"]')
        assert submit.is_visible()


@pytest.mark.e2e
class TestE16LoginFlowSucces:
    """E16: Login flow (succes) — vul code in, submit, redirect naar /boodschappen."""

    def test_login_succes_redirect(self, page, live_server_url, mock_ah_token_manager):
        """Vul geldige code in -> submit -> redirect naar /boodschappen."""
        mock_ah_token_manager.login.return_value = None
        mock_ah_token_manager.login.side_effect = None

        page.goto(f"{live_server_url}/ah/login")
        page.wait_for_selector("[data-testid='ah-login-form']")

        # Vul code in
        page.fill('input[name="code"]', "valid-test-code")

        # Submit formulier en wacht op redirect
        page.locator('[data-testid="ah-login-submit"]').click()
        page.wait_for_url("**/boodschappen**")

        # Moet redirect zijn naar /boodschappen
        assert "/boodschappen" in page.url
        # Geen foutmelding zichtbaar
        assert page.locator('[data-testid="ah-login-error"]').count() == 0


@pytest.mark.e2e
class TestE17LoginFlowFout:
    """E17: Login flow (fout) — ongeldige code -> foutmelding op login pagina."""

    def test_login_fout_toont_foutmelding(
        self, page, live_server_url, mock_ah_token_manager
    ):
        """Vul ongeldige code in -> submit -> foutmelding zichtbaar."""
        mock_ah_token_manager.login.side_effect = Exception("Invalid code")

        page.goto(f"{live_server_url}/ah/login")
        page.wait_for_selector("[data-testid='ah-login-form']")

        # Vul code in en submit
        page.fill('input[name="code"]', "invalid-code")
        page.click('[data-testid="ah-login-submit"]')
        page.wait_for_selector("[data-testid='ah-login-error']")

        # Foutmelding zichtbaar
        error = page.locator('[data-testid="ah-login-error"]')
        assert error.is_visible()

        # Login formulier nog steeds zichtbaar (kan opnieuw proberen)
        form = page.locator('[data-testid="ah-login-form"]')
        assert form.is_visible()

        # Code-veld nog steeds aanwezig
        code_input = page.locator('input[name="code"]')
        assert code_input.is_visible()


@pytest.mark.e2e
class TestE18VerstuurNaarAHSucces:
    """E18: Verstuur naar AH (succes) — via match-review flow."""

    def test_verstuur_naar_ah_toont_bevestiging(
        self,
        page,
        live_server_url,
        app,
        mock_ah_token_manager,
    ):
        """Verstuur -> match-review -> bevestig -> bevestigingsscherm."""
        mock_ah_token_manager.is_authenticated.return_value = True
        app.state.boodschappenlijst = None
        app.state.match_review_items = []

        page.goto(f"{live_server_url}/boodschappen")
        page.wait_for_selector("[data-testid='boodschappen-header']")

        page.click("[data-testid='verstuur-naar-ah-button']")
        page.wait_for_url("**/boodschappen/match-review")

        page.click("[data-testid='bevestig-btn']")
        page.wait_for_url("**/boodschappen/ah-bevestiging", timeout=5000)

        bevestiging = page.locator('[data-testid="ah-bevestiging"]')
        assert bevestiging.is_visible()

        ah_link = page.locator('[data-testid="ah-open-link"]')
        assert ah_link.is_visible()
        assert "ah.nl" in ah_link.get_attribute("href")


@pytest.mark.e2e
class TestE19NietGevondenProducten:
    """E19: Niet-gevonden producten — match-review toont amber kaart, knop disabled."""

    def test_geen_match_toont_uitgeschakelde_knop(
        self,
        page,
        live_server_url,
        app,
    ):
        """Items zonder match tonen amber stijl en bevestig-knop is uitgeschakeld."""
        app.state.match_review_items = [
            MatchReviewItem(
                id="niet-gevonden-e19",
                naam="verse basilicum",
                hoeveelheid=1.0,
                eenheid="bos",
                product=None,
                bron="niet_gevonden",
                gecorrigeerd=False,
                aantal=1,
            ),
            MatchReviewItem(
                id="gevonden-e19",
                naam="rijst",
                hoeveelheid=1.0,
                eenheid="kg",
                product=Product(
                    id=10,
                    title="AH Rijst 1kg",
                    brand="AH",
                    size="1 kg",
                    price=1.29,
                    category="",
                    is_orderable=True,
                ),
                bron="zoekopdracht",
                gecorrigeerd=False,
                aantal=1,
            ),
        ]

        page.goto(f"{live_server_url}/boodschappen/match-review")
        page.wait_for_selector("[data-testid='match-review']")

        btn = page.locator('[data-testid="bevestig-btn"]')
        assert btn.is_disabled()


@pytest.mark.e2e
class TestE20VerstuurZonderLogin:
    """E20: Verstuur zonder login -> redirect naar /ah/login."""

    def test_verstuur_zonder_login_redirect(
        self, page, live_server_url, mock_ah_token_manager
    ):
        """Verstuur naar AH zonder login -> login pagina verschijnt."""
        mock_ah_token_manager.is_authenticated.return_value = False

        page.goto(f"{live_server_url}/boodschappen")
        page.wait_for_selector("[data-testid='boodschappen-header']")

        # Verstuur via JS form submit
        page.evaluate("""() => {
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = '/boodschappen/verstuur-naar-ah';
            document.body.appendChild(form);
            form.submit();
        }""")

        # Wacht tot de login pagina verschijnt (HTMX swap of volledige redirect)
        login_form = page.locator('[data-testid="ah-login-form"]')
        login_form.wait_for(state="visible", timeout=5000)
        assert login_form.is_visible()


@pytest.mark.e2e
class TestE21VolleFlow:
    """E21: Volledige flow: Boodschappen -> AH -> Bevestiging -> Terug naar home."""

    def test_volledige_flow_boodschappen_naar_week(
        self,
        page,
        live_server_url,
        app,
        mock_ah_token_manager,
    ):
        """Hele flow: boodschappen -> verstuur -> match-review -> bevestig -> /week."""
        mock_ah_token_manager.is_authenticated.return_value = True
        mock_ah_token_manager.is_authenticated.side_effect = None

        app.state.boodschappenlijst = None
        app.state.match_review_items = []

        page.goto(f"{live_server_url}/boodschappen")
        page.wait_for_selector("[data-testid='boodschappen-header']")

        page.click("[data-testid='verstuur-naar-ah-button']")
        page.wait_for_url("**/boodschappen/match-review")

        page.click("[data-testid='bevestig-btn']")
        page.wait_for_url("**/boodschappen/ah-bevestiging", timeout=5000)

        assert page.locator('[data-testid="ah-bevestiging"]').is_visible()

        terug_link = page.get_by_role("link", name="Terug naar home")
        terug_link.wait_for(state="visible")
        terug_link.click()
        page.wait_for_url("**/week**", timeout=5000)

        assert "/week" in page.url
