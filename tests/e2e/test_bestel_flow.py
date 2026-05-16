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
        week_page.wait_for_selector("h1:has-text('Ingrediënten')", timeout=10000)

    def test_ingredient_selectie_toont_recepten(self, week_page: Page):
        """Ingredient-selectiescherm toont receptgroepen met ingrediënten."""
        week_page.locator("[data-testid='verder-button']").click()
        week_page.wait_for_selector("h1:has-text('Ingrediënten')", timeout=10000)
        expect(week_page.locator("h2").first).to_be_visible()
        expect(
            week_page.locator("[data-testid='ingredient-item']").first
        ).to_be_visible()

    def test_ingredient_toggle_deselecteert_item(self, week_page: Page):
        """Toggle-knop deselecteert een ingredient (item krijgt opacity-50 class)."""
        week_page.locator("[data-testid='verder-button']").click()
        week_page.wait_for_selector(
            "[data-testid='ingredient-item']", timeout=10000
        )
        # Klik toggle-knop van eerste item
        week_page.locator("[data-testid='ingredient-item']").first.locator(
            "button"
        ).first.click()
        # Wacht tot HTMX de DOM heeft bijgewerkt met opacity-50 class
        week_page.wait_for_selector(
            "[data-testid='ingredient-item'].opacity-50", timeout=5000
        )

    def test_ingredient_selectie_naar_voorraad(self, week_page: Page):
        """'Verder naar voorraadcheck' navigeert naar /voorraad."""
        week_page.locator("[data-testid='verder-button']").click()
        week_page.wait_for_selector("h1:has-text('Ingrediënten')", timeout=10000)
        week_page.locator("button[type='submit']").click()
        # Wacht op sectie-voorraad die alleen op /voorraad bestaat
        week_page.wait_for_selector("[data-testid='sectie-voorraad']", timeout=10000)

    def test_volledige_bestelflow(self, week_page: Page):
        """Volledige flow: /week → /ingredient-selectie → /voorraad → match-review."""
        # Stap 1: /week → /ingredient-selectie via 'Verder' knop
        week_page.locator("[data-testid='verder-button']").click()
        week_page.wait_for_selector("h1:has-text('Ingrediënten')", timeout=10000)
        expect(
            week_page.locator("[data-testid='ingredient-item']").first
        ).to_be_visible()

        # Stap 2: /ingredient-selectie → /voorraad via 'Verder naar voorraadcheck'
        week_page.locator("button[type='submit']").click()
        week_page.wait_for_selector("[data-testid='sectie-voorraad']", timeout=10000)

        # Stap 3: /voorraad → /boodschappen/match-review via 'Naar boodschappenlijst'
        week_page.locator("[data-testid='naar-boodschappen-button']").click()
        week_page.wait_for_selector("[data-testid='match-review']", timeout=10000)
