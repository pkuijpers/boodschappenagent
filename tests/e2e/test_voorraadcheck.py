"""Playwright E2E tests voor Fase 2: Voorraadcheck (E8, E9, E10)."""

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e


class TestVoorraadcheckLaadt:
    """E8: Voorraadcheck laden."""

    def test_e8_pagina_heeft_voorraadcheck_header(self, voorraad_page: Page):
        """E8: /voorraad toont header 'Voorraadcheck'."""
        expect(voorraad_page.locator("h1")).to_contain_text("Voorraadcheck")

    def test_e8_sectie_houdbaar_zichtbaar(self, voorraad_page: Page):
        """E8: Sectie 'Houdbare producten' is zichtbaar."""
        expect(voorraad_page.locator("[data-testid='sectie-houdbaar']")).to_be_visible()

    def test_e8_sectie_vers_zichtbaar(self, voorraad_page: Page):
        """E8: Sectie 'Verse basics' is zichtbaar."""
        expect(voorraad_page.locator("[data-testid='sectie-vers']")).to_be_visible()

    def test_e8_items_hebben_ja_nee_toggles(self, voorraad_page: Page):
        """E8: Voorraaditem heeft 'Ja' en 'Nee' toggles."""
        item = voorraad_page.locator("[data-testid='voorraaditem']").first
        expect(item.locator("[data-testid='status-ja']")).to_be_visible()
        expect(item.locator("[data-testid='status-nee']")).to_be_visible()


class TestVoorraadToggle:
    """E9: Voorraad toggle via HTMX (geen page reload)."""

    def test_e9_tap_ja_activeert_ja_toggle(self, voorraad_page: Page):
        """E9: Tap 'Ja' wisselt highlight naar Ja."""
        # Zoek item met 'Nee' actief (default staat)
        nee_item = voorraad_page.locator(
            "[data-testid='voorraaditem']:has([data-testid='status-nee'][data-actief='true'])"
        ).first
        expect(nee_item).to_be_visible()

        ja_btn = nee_item.locator("[data-testid='status-ja']")
        ja_btn.click()

        # Wacht op HTMX DOM-update: 'Ja' wordt actief
        voorraad_page.wait_for_selector(
            "[data-testid='status-ja'][data-actief='true']", timeout=3000
        )

    def test_e9_toggle_geen_page_reload(self, voorraad_page: Page):
        """E9: Toggle werkt via HTMX, geen volledige page reload."""
        navigated = []
        voorraad_page.on("domcontentloaded", lambda: navigated.append(1))

        nee_item = voorraad_page.locator(
            "[data-testid='voorraaditem']:has([data-testid='status-nee'][data-actief='true'])"
        ).first
        nee_item.locator("[data-testid='status-ja']").click()

        voorraad_page.wait_for_selector(
            "[data-testid='status-ja'][data-actief='true']", timeout=3000
        )
        assert len(navigated) == 0


class TestVoorraadNaarBoodschappenFlow:
    """E10: Voorraad → Boodschappen navigatie."""

    def test_e10_naar_boodschappen_button_navigeert(self, voorraad_page: Page):
        """E10: 'Naar boodschappenlijst' knop navigeert naar /boodschappen."""
        btn = voorraad_page.locator("[data-testid='naar-boodschappen-button']")
        expect(btn).to_be_visible()
        btn.click()
        voorraad_page.wait_for_url("**/boodschappen")
        expect(voorraad_page.locator("h1")).to_contain_text("Boodschappenlijst")
