"""E2E tests voor AH integratie (E15-E21)."""

import pytest


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
