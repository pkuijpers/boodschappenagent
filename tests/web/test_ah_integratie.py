"""Tests voor AH integratie web routes (S12-S19)."""

from fastapi.testclient import TestClient

from .conftest import soup


class TestAHLoginPagina:
    """S12: AH Login pagina."""

    def test_s12_1a_login_pagina_laadt_full_page(self, app_with_ah):
        """S12.1a: GET /ah/login zonder HTMX headers -> volledige HTML pagina."""
        client = TestClient(app_with_ah)
        response = client.get("/ah/login")

        assert response.status_code == 200
        html = soup(response)
        assert html.find("html") is not None
        assert html.select_one('[data-testid="ah-login-form"]') is not None

    def test_s12_1b_login_pagina_laadt_htmx_fragment(self, app_with_ah):
        """S12.1b: GET /ah/login met HX-Request header -> fragment zonder <html>."""
        client = TestClient(app_with_ah, headers={"HX-Request": "true"})
        response = client.get("/ah/login")

        assert response.status_code == 200
        html = soup(response)
        assert html.find("html") is None
        assert html.select_one('[data-testid="ah-login-form"]') is not None

    def test_s12_2_login_pagina_toont_login_url(self, app_with_ah):
        """S12.2: Login pagina toont login URL naar login.ah.nl."""
        client = TestClient(app_with_ah)
        response = client.get("/ah/login")

        html = soup(response)
        login_url_el = html.select_one('[data-testid="ah-login-url"]')
        assert login_url_el is not None
        # Moet verwijzen naar login.ah.nl
        href = login_url_el.get("href", login_url_el.get_text())
        assert "login.ah.nl" in href

    def test_s12_3_login_pagina_heeft_code_veld(self, app_with_ah):
        """S12.3: Login pagina heeft input veld voor authorization code."""
        client = TestClient(app_with_ah)
        response = client.get("/ah/login")

        html = soup(response)
        code_input = html.select_one('input[name="code"]')
        assert code_input is not None

    def test_s12_4_login_pagina_heeft_submit_knop(self, app_with_ah):
        """S12.4: Login pagina heeft "Inloggen" submit knop."""
        client = TestClient(app_with_ah)
        response = client.get("/ah/login")

        html = soup(response)
        submit = html.select_one('[data-testid="ah-login-submit"]')
        assert submit is not None
