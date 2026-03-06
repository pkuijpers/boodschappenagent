"""Playwright E2E tests voor Fase 3: Boodschappenlijst (E11, E12, E13)."""

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e


class TestBoodschappenlijstLaadt:
    """E11: Boodschappenlijst laden."""

    def test_e11_pagina_heeft_boodschappenlijst_header(self, boodschappen_page: Page):
        """E11: /boodschappen toont header 'Boodschappenlijst'."""
        expect(boodschappen_page.locator("h1")).to_contain_text("Boodschappenlijst")

    def test_e11_sectie_zichtbaar(self, boodschappen_page: Page):
        """E11: Boodschappenlijst toont minimaal één sectie."""
        expect(
            boodschappen_page.locator("[data-testid='boodschappen-sectie']").first
        ).to_be_visible()

    def test_e11_items_aanwezig(self, boodschappen_page: Page):
        """E11: Boodschappenlijst toont items."""
        expect(
            boodschappen_page.locator("[data-testid='boodschapitem']").first
        ).to_be_visible()

    def test_e11_items_tonen_hoeveelheid(self, boodschappen_page: Page):
        """E11: Items tonen hoeveelheid."""
        expect(
            boodschappen_page.locator("[data-testid='hoeveelheid']").first
        ).to_be_visible()


class TestBoodschapAfvinken:
    """E12: Boodschap afvinken via HTMX."""

    def test_e12_tap_checkbox_zet_checked(self, boodschappen_page: Page):
        """E12: Tap op checkbox zet item op afgevinkt (data-checked='true')."""
        item = boodschappen_page.locator("[data-testid='boodschapitem']").first
        expect(item).to_have_attribute("data-checked", "false")

        # De checkbox is een button met hx-patch (niet de stepper buttons)
        checkbox = item.locator("button[hx-patch]:not([hx-vals*='hoeveelheid'])").first
        checkbox.click()

        boodschappen_page.wait_for_selector(
            "[data-testid='boodschapitem'][data-checked='true']", timeout=3000
        )
        expect(
            boodschappen_page.locator(
                "[data-testid='boodschapitem'][data-checked='true']"
            ).first
        ).to_be_visible()

    def test_e12_afvinken_geen_page_reload(self, boodschappen_page: Page):
        """E12: Afvinken werkt via HTMX, geen volledige page reload."""
        navigated = []
        boodschappen_page.on("domcontentloaded", lambda: navigated.append(1))

        item = boodschappen_page.locator("[data-testid='boodschapitem']").first
        checkbox = item.locator("button[hx-patch]:not([hx-vals*='hoeveelheid'])").first
        checkbox.click()

        boodschappen_page.wait_for_selector(
            "[data-testid='boodschapitem'][data-checked='true']", timeout=3000
        )
        assert len(navigated) == 0


class TestHandmatigToevoegen:
    """E13: Product handmatig toevoegen via HTMX."""

    def test_e13_voeg_toe_button_aanwezig(self, boodschappen_page: Page):
        """E13: '+ Voeg product toe' knop is aanwezig."""
        expect(
            boodschappen_page.locator("[data-testid='voeg-toe-button']")
        ).to_be_visible()

    def test_e13_nieuw_item_verschijnt_na_toevoegen(self, boodschappen_page: Page):
        """E13: Na invullen en bevestigen verschijnt het nieuwe item in de lijst."""
        # Open het formulier
        boodschappen_page.locator("[data-testid='voeg-toe-button']").click()

        # Wacht tot formulier zichtbaar is
        naam_input = boodschappen_page.locator("[data-testid='voeg-toe-naam']")
        expect(naam_input).to_be_visible()

        # Vul naam in en bevestig
        naam_input.fill("bananen")
        boodschappen_page.locator("[data-testid='voeg-toe-submit']").click()

        # Wacht op nieuw item in de DOM
        boodschappen_page.wait_for_selector(
            "[data-testid='boodschapitem'][data-item='bananen']", timeout=3000
        )
        expect(
            boodschappen_page.locator(
                "[data-testid='boodschapitem'][data-item='bananen']"
            )
        ).to_be_visible()
