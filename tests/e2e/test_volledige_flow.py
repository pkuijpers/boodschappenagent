"""Playwright E2E test voor de volledige flow: Week → Voorraad → Boodschappen (E14)."""

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e


class TestVolledigeFlow:
    """E14: Volledige flow Week → Voorraad → Boodschappen."""

    @pytest.fixture(autouse=True)
    def set_auth(self, mock_ah_token_manager):
        """Zet AH authenticatie aan voor voorraad-flow tests."""
        mock_ah_token_manager.is_authenticated.return_value = True
        mock_ah_token_manager.is_authenticated.side_effect = None

    def test_e14_week_naar_voorraad_via_verder_knop(self, week_page: Page):
        """E14: Klik 'Verder' op /week navigeert naar /voorraad."""
        verder = week_page.locator("[data-testid='verder-button']")
        expect(verder).to_be_visible()
        verder.click()
        week_page.wait_for_url("**/voorraad")
        expect(week_page.locator("h1")).to_contain_text("Voorraadcheck")

    def test_e14_volledige_flow_week_voorraad_boodschappen(self, week_page: Page):
        """E14: Volledige flow: /week → /voorraad → /boodschappen → lijst gevuld."""
        # Stap 1: /week → /voorraad via 'Verder' knop
        week_page.locator("[data-testid='verder-button']").click()
        week_page.wait_for_url("**/voorraad")
        expect(week_page.locator("h1")).to_contain_text("Voorraadcheck")

        # Stap 2: Voorraad sectie is zichtbaar
        expect(week_page.locator("[data-testid='sectie-voorraad']")).to_be_visible()

        # Stap 3: /voorraad → /boodschappen via 'Naar boodschappenlijst'
        week_page.locator("[data-testid='naar-boodschappen-button']").click()
        week_page.wait_for_url("**/boodschappen")
        expect(week_page.locator("h1")).to_contain_text("Boodschappenlijst")

        # Stap 4: Boodschappenlijst bevat items
        expect(
            week_page.locator("[data-testid='boodschappen-sectie']").first
        ).to_be_visible()
        expect(
            week_page.locator("[data-testid='boodschapitem']").first
        ).to_be_visible()
