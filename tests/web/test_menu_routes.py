"""Tests voor menu routes (fase 0)."""

from fastapi.testclient import TestClient


class TestRootRedirect:
    """GET / moet redirecten naar /week."""

    def test_root_redirects_to_week(self, client: TestClient):
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/week"

    def test_root_follow_redirect_lands_on_week(self, client: TestClient):
        response = client.get("/")
        assert response.status_code == 200


class TestWeekRoute:
    """GET /week moet een 200 teruggeven met correcte HTML-structuur."""

    def test_week_returns_200(self, client: TestClient):
        response = client.get("/week")
        assert response.status_code == 200

    def test_week_returns_html(self, client: TestClient):
        response = client.get("/week")
        assert "text/html" in response.headers["content-type"]

    def test_week_has_base_layout(self, client: TestClient):
        response = client.get("/week")
        html = response.text
        assert "<!doctype html>" in html.lower() or "<!DOCTYPE html>" in html
        assert "<html" in html
        assert "</html>" in html

    def test_week_includes_tailwind(self, client: TestClient):
        response = client.get("/week")
        assert "tailwindcss" in response.text.lower() or "tailwind" in response.text

    def test_week_includes_htmx(self, client: TestClient):
        response = client.get("/week")
        assert "htmx" in response.text.lower()

    def test_week_has_tab_bar(self, client: TestClient):
        """Tab-bar moet Week, Vandaag en Instellingen bevatten."""
        response = client.get("/week")
        html = response.text
        assert "Week" in html
        assert "Vandaag" in html
        assert "Instellingen" in html

    def test_week_has_tab_bar_links(self, client: TestClient):
        """Tab-bar links moeten naar de juiste routes verwijzen."""
        response = client.get("/week")
        html = response.text
        assert 'href="/week"' in html
        assert 'href="/vandaag"' in html
        assert 'href="/instellingen"' in html

    def test_week_has_ah_colors(self, client: TestClient):
        """AH-kleurenpalet moet als CSS custom properties aanwezig zijn."""
        response = client.get("/week")
        html = response.text
        assert "#00A0E2" in html or "--ah-blue" in html

    def test_week_has_page_title(self, client: TestClient):
        response = client.get("/week")
        assert "<title>" in response.text
        assert "Albert" in response.text
