"""Playwright E2E tests voor Fase 2: Voorraadcheck (E8, E9, E10)."""

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e


class TestVoorraadcheckLaadt:
    """E8: Voorraadcheck laden."""

    def test_e8_pagina_heeft_voorraadcheck_header(self, voorraad_page: Page):
        """E8: /voorraad toont header 'Voorraadcheck'."""
        expect(voorraad_page.locator("h1")).to_contain_text("Voorraadcheck")

    def test_e8_sectie_voorraad_zichtbaar(self, voorraad_page: Page):
        """E8: Sectie 'Voorraadlijst' is zichtbaar."""
        expect(voorraad_page.locator("[data-testid='sectie-voorraad']")).to_be_visible()

    def test_e8_items_zichtbaar(self, voorraad_page: Page):
        """E8: Voorraad sectie toont minimaal één item."""
        expect(
            voorraad_page.locator("[data-testid='voorraaditem']").first
        ).to_be_visible()

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
    """E10: Voorraad → Match-review navigatie (via POST /voorraad/bevestig)."""

    @pytest.fixture(autouse=True)
    def setup_ingredient_selectie(self, app):
        """Zet ingredient_selectie in app.state zodat POST /voorraad/bevestig werkt."""
        app.state.ingredient_selectie = [
            {
                "id": "e10-test-item",
                "recept_naam": "Test Recept",
                "naam": "test-ingredient",
                "hoeveelheid": 1.0,
                "eenheid": "stuk",
                "geselecteerd": True,
            }
        ]
        yield
        app.state.ingredient_selectie = None

    def test_e10_naar_boodschappen_button_navigeert(self, voorraad_page: Page):
        """E10: 'Naar boodschappenlijst' knop start AH-matching, navigeert naar match-review."""  # noqa: E501
        btn = voorraad_page.locator("[data-testid='naar-boodschappen-button']")
        expect(btn).to_be_visible()
        btn.click()
        voorraad_page.wait_for_selector("[data-testid='match-review']", timeout=10000)


class TestVoorraadSorteringE2E:
    """T010: Voorraadpagina toont secties in juiste volgorde."""

    def test_koelkast_sectieheader_zichtbaar(self, voorraad_page: Page):
        """T010: 'Koelkast' sectieheader is zichtbaar op de pagina."""
        koelkast_header = voorraad_page.locator("h3", has_text="Koelkast")
        expect(koelkast_header).to_be_visible()

    def test_diepvries_sectieheader_zichtbaar(self, voorraad_page: Page):
        """T010: 'Diepvries' sectieheader is zichtbaar op de pagina."""
        diepvries_header = voorraad_page.locator("h3", has_text="Diepvries")
        expect(diepvries_header).to_be_visible()

    def test_koelkast_sectie_voor_diepvries_sectie(self, voorraad_page: Page):
        """T010: Koelkast-sectieheader staat in DOM vóór Diepvries-sectieheader."""
        headers = voorraad_page.locator("h3").all_text_contents()
        assert "Koelkast" in headers, f"Koelkast ontbreekt; gevonden: {headers}"
        assert "Diepvries" in headers, f"Diepvries ontbreekt; gevonden: {headers}"
        koelkast_idx = headers.index("Koelkast")
        diepvries_idx = headers.index("Diepvries")
        assert koelkast_idx < diepvries_idx, (
            f"Koelkast (pos {koelkast_idx}) moet vóór "
            f"Diepvries (pos {diepvries_idx}) staan"
        )
