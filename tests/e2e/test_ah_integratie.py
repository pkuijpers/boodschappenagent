"""E2E tests voor AH integratie (E15-E21)."""

import pytest

from boodschappenagent.ah import ProductMatch, SyncResultaat
from boodschappenagent.ah.models import Product


@pytest.mark.e2e
class TestE15LoginPaginaLaden:
    """E15: Login pagina laden — navigeer naar /ah/login en verifieer inhoud."""

    def test_login_pagina_instructies_zichtbaar(self, page, live_server_url):
        """Instructies, code-invoerveld, login URL en submit knop zichtbaar."""
        page.goto(f"{live_server_url}/ah/login")
        page.wait_for_load_state("networkidle")

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
        page.wait_for_load_state("networkidle")

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
        page.wait_for_load_state("networkidle")

        # Vul code in en submit
        page.fill('input[name="code"]', "invalid-code")
        page.click('[data-testid="ah-login-submit"]')
        page.wait_for_load_state("networkidle")

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
    """E18: Verstuur naar AH (succes)."""

    def test_verstuur_naar_ah_toont_bevestiging(
        self,
        page,
        live_server_url,
        app,
        mock_ah_token_manager,
        mock_ah_integratie,
    ):
        """Verstuur -> bevestigingsscherm."""
        # Setup: authenticeer en zet sync resultaat
        mock_ah_token_manager.is_authenticated.return_value = True

        matches = [
            ProductMatch(
                regel=type("Regel", (), {"naam": f"product-{i}"})(),
                product=Product(
                    id=i, title=f"AH Product {i}", brand="AH",
                    size="1 stuk", price=2.99, category="", is_orderable=True,
                ),
                bron="zoekopdracht",
            )
            for i in range(5)
        ]
        mock_ah_integratie.sync_naar_lijst.return_value = SyncResultaat(
            lijst_id="e2e-list-123",
            lijst_naam="Boodschappen 2026-02-16",
            matches=matches,
        )

        # Reset app state voor boodschappenlijst
        app.state.boodschappenlijst = None

        page.goto(f"{live_server_url}/boodschappen")
        page.wait_for_load_state("networkidle")

        # Verstuur naar AH via formulier POST (de knop komt in stap 7)
        page.evaluate("""() => {
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = '/boodschappen/verstuur-naar-ah';
            document.body.appendChild(form);
            form.submit();
        }""")
        page.wait_for_load_state("networkidle")

        # Bevestigingsscherm zichtbaar
        bevestiging = page.locator('[data-testid="ah-bevestiging"]')
        bevestiging.wait_for(state="visible", timeout=5000)

        # Aantal producten
        aantal = page.locator('[data-testid="ah-aantal-producten"]')
        assert aantal.is_visible()
        assert "5" in aantal.text_content()

        # "Open Albert Heijn" link
        ah_link = page.locator('[data-testid="ah-open-link"]')
        assert ah_link.is_visible()
        assert "ah.nl" in ah_link.get_attribute("href")
