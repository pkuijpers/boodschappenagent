"""Playwright E2E test voor de volledige flow (feature 004).

Week → Ingredient-selectie → Voorraad → Match-review.
De 'Verder' knop op /week gaat naar /ingredient-selectie, niet meer naar /voorraad.
"""

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e


class TestVolledigeFlow:
    """E14: Volledige flow Week → Ingredient-selectie → Voorraad → Match-review."""

    @pytest.fixture(autouse=True)
    def reset_state(self, app, mock_ah_token_manager):
        """Reset app state en authenticatie voor elke test."""
        app.state.ingredient_selectie = None
        mock_ah_token_manager.is_authenticated.return_value = True
        mock_ah_token_manager.is_authenticated.side_effect = None

    def test_e14_week_naar_ingredient_selectie_via_verder_knop(self, week_page: Page):
        """E14: Klik 'Verder' op /week navigeert naar /ingredient-selectie."""
        verder = week_page.locator("[data-testid='verder-button']")
        expect(verder).to_be_visible()
        verder.click()
        week_page.wait_for_url("**/ingredient-selectie")
        expect(week_page.locator("h1")).to_contain_text("Ingrediënten selecteren")

    def test_e14_volledige_flow_week_ingredient_selectie_voorraad(
        self, week_page: Page
    ):
        """E14: /week → /ingredient-selectie → /voorraad → match-review."""
        # Stap 1: /week → /ingredient-selectie via 'Verder' knop
        week_page.locator("[data-testid='verder-button']").click()
        week_page.wait_for_url("**/ingredient-selectie")
        expect(week_page.locator("h1")).to_contain_text("Ingrediënten selecteren")

        # Stap 2: Ingrediënten zijn zichtbaar
        expect(
            week_page.locator("[data-testid='ingredient-item']").first
        ).to_be_visible()

        # Stap 3: /ingredient-selectie → /voorraad via 'Verder naar voorraadcheck'
        week_page.locator("button[type='submit']").click()
        week_page.wait_for_selector("[data-testid='sectie-voorraad']", timeout=10000)

        # Stap 4: /voorraad → /boodschappen/match-review via 'Naar boodschappenlijst'
        week_page.locator("[data-testid='naar-boodschappen-button']").click()
        week_page.wait_for_selector("[data-testid='match-review']", timeout=10000)
