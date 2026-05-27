"""E2E test: Voorraad items en de bestelflow.

In feature 004 is de flow gewijzigd: de 'Naar boodschappenlijst' knop op /voorraad
doet nu een POST naar /voorraad/bevestig die AH-matching start en redirect naar
/boodschappen/match-review. De boodschappenlijst wordt samengesteld uit
ingredient_selectie (recept-ingrediënten), niet meer uit de AH 'Voorraad' lijst.
"""

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e


class TestVoorraadNaarMatchReview:
    """Voorraad bevestig start AH-matching en navigeert naar match-review."""

    @pytest.fixture(autouse=True)
    def reset_state(self, app, mock_ah_token_manager):
        """Reset app state en authenticatie."""
        app.state.ingredient_selectie = None
        mock_ah_token_manager.is_authenticated.return_value = True
        mock_ah_token_manager.is_authenticated.side_effect = None

    def test_voorraad_naar_match_review(self, week_page: Page):
        """'Naar boodschappenlijst' op /voorraad redirect naar /boodschappen/match-review."""  # noqa: E501
        # Navigeer via de volledige flow zodat ingredient_selectie gevuld is
        week_page.locator("[data-testid='verder-button']").click()
        week_page.wait_for_url("**/ingredient-selectie")
        week_page.locator("button[type='submit']").click()
        week_page.wait_for_url("**/voorraad")

        # Klik op 'Naar boodschappenlijst' → match-review
        week_page.locator("[data-testid='naar-boodschappen-button']").click()
        week_page.wait_for_url("**/boodschappen/match-review")
        expect(week_page.locator("[data-testid='match-review']")).to_be_visible()

    def test_voorraad_toggle_voor_bevestig(self, voorraad_page: Page):
        """Voorraad toggle werkt nog steeds via HTMX."""
        melk_item = voorraad_page.locator(
            "[data-testid='voorraaditem'][data-item='melk']"
        )
        expect(melk_item).to_be_visible()
        nee_btn = melk_item.locator("[data-testid='status-nee']")
        nee_btn.click()
        voorraad_page.wait_for_timeout(300)
        melk_item = voorraad_page.locator(
            "[data-testid='voorraaditem'][data-item='melk']"
        )
        nee_btn = melk_item.locator("[data-testid='status-nee']")
        expect(nee_btn).to_have_attribute("data-actief", "true")
