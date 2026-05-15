"""Playwright E2E test voor de volledige bestelflow (E-bestel):
Weekmenu → Ingredient-selectie → Voorraadcheck → Match-review.
"""

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e


class TestBestelFlow:
    """Volledige bestelflow: Week → Ingredient-selectie → Voorraad → Match-review."""

    @pytest.fixture(autouse=True)
    def reset_state(self, app, mock_ah_token_manager):
        """Reset app state en authenticatie voor elke test."""
        app.state.ingredient_selectie = None
        mock_ah_token_manager.is_authenticated.return_value = True
        mock_ah_token_manager.is_authenticated.side_effect = None

    def test_week_naar_ingredient_selectie(self, week_page: Page):
        """'Verder' op /week navigeert naar /ingredient-selectie."""
        week_page.locator("[data-testid='verder-button']").click()
        week_page.wait_for_url("**/ingredient-selectie")
        expect(week_page.locator("h1")).to_contain_text("Ingrediënten selecteren")

    def test_ingredient_selectie_toont_recepten(self, week_page: Page):
        """Ingredient-selectiescherm toont receptgroepen met ingrediënten."""
        week_page.locator("[data-testid='verder-button']").click()
        week_page.wait_for_url("**/ingredient-selectie")
        expect(week_page.locator("h2").first).to_be_visible()
        expect(
            week_page.locator("[data-testid='ingredient-item']").first
        ).to_be_visible()

    def test_ingredient_toggle_deselecteert_item(self, week_page: Page):
        """Toggle-knop deselecteert een ingredient (item krijgt opacity-50)."""
        week_page.locator("[data-testid='verder-button']").click()
        week_page.wait_for_url("**/ingredient-selectie")

        eerste_item = week_page.locator("[data-testid='ingredient-item']").first
        expect(eerste_item).not_to_have_class("opacity-50")
        eerste_item.locator("button").first.click()
        week_page.wait_for_timeout(300)
        expect(
            week_page.locator("[data-testid='ingredient-item']").first
        ).to_have_class("opacity-50")

    def test_ingredient_selectie_naar_voorraad(self, week_page: Page):
        """'Verder naar voorraadcheck' navigeert naar /voorraad."""
        week_page.locator("[data-testid='verder-button']").click()
        week_page.wait_for_url("**/ingredient-selectie")
        week_page.locator("button[type='submit']").click()
        week_page.wait_for_url("**/voorraad")
        expect(week_page.locator("h1")).to_contain_text("Voorraadcheck")

    def test_volledige_bestelflow(self, week_page: Page):
        """Volledige flow: /week → /ingredient-selectie → /voorraad → match-review."""
        # Stap 1: /week → /ingredient-selectie via 'Verder' knop
        week_page.locator("[data-testid='verder-button']").click()
        week_page.wait_for_url("**/ingredient-selectie")
        expect(week_page.locator("h1")).to_contain_text("Ingrediënten selecteren")
        expect(
            week_page.locator("[data-testid='ingredient-item']").first
        ).to_be_visible()

        # Stap 2: /ingredient-selectie → /voorraad via 'Verder naar voorraadcheck'
        week_page.locator("button[type='submit']").click()
        week_page.wait_for_url("**/voorraad")
        expect(week_page.locator("h1")).to_contain_text("Voorraadcheck")
        expect(week_page.locator("[data-testid='sectie-voorraad']")).to_be_visible()

        # Stap 3: /voorraad → /boodschappen/match-review via 'Naar boodschappenlijst'
        week_page.locator("[data-testid='naar-boodschappen-button']").click()
        week_page.wait_for_url("**/boodschappen/match-review")
        expect(week_page.locator("[data-testid='match-review']")).to_be_visible()
