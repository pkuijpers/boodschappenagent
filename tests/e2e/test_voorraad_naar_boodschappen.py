"""E2E test: voorraad 'Nee' items verschijnen op boodschappenlijst.

Reproduceert de bug waarbij items die op de voorraadcheck als 'Nee' (niet op
voorraad) gemarkeerd worden, niet op de boodschappenlijst verschijnen.
"""

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e


class TestVoorraadNaarBoodschappen:
    """Voorraad 'Nee' items moeten op de boodschappenlijst komen."""

    def test_vers_item_nee_verschijnt_op_boodschappenlijst(
        self, voorraad_page: Page
    ):
        """Vers basic als 'Nee' markeren → verschijnt op boodschappenlijst."""
        # Zoek het voorraaditem voor 'optimel'
        optimel_item = voorraad_page.locator(
            "[data-testid='voorraaditem'][data-item='optimel']"
        )
        expect(optimel_item).to_be_visible()

        # Default staat is 'Nee' (niet op voorraad). Klik 'Nee' om te bevestigen.
        nee_btn = optimel_item.locator("[data-testid='status-nee']")
        nee_btn.click()

        # Wacht op HTMX swap — Nee moet actief blijven
        voorraad_page.wait_for_timeout(500)
        optimel_item = voorraad_page.locator(
            "[data-testid='voorraaditem'][data-item='optimel']"
        )
        nee_btn = optimel_item.locator("[data-testid='status-nee']")
        expect(nee_btn).to_have_attribute("data-actief", "true")

        # Navigeer naar boodschappenlijst
        voorraad_page.locator("[data-testid='naar-boodschappen-button']").click()
        voorraad_page.wait_for_url("**/boodschappen")

        # Optimel moet op de boodschappenlijst staan
        boodschap_items = voorraad_page.locator("[data-testid='boodschapitem']")
        item_namen = boodschap_items.all_text_contents()
        assert any(
            "optimel" in naam.lower() for naam in item_namen
        ), f"'optimel' niet gevonden op boodschappenlijst: {item_namen}"
