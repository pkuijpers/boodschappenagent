"""Playwright E2E tests voor de match-review flow (003-ingredient-match-review).

Valideert:
- "Verstuur naar AH" opent match-review pagina (niet direct AH-lijst aanmaken)
- Match-review toont alle gematche items
- Bevestig-knop is actief als alle items een product hebben
- Bevestig-knop is uitgeschakeld als een item geen product heeft
- Corrigeer-knop opent de zoekbalk inline
- Kies-knop update de kaart naar gecorrigeerd-staat via HTMX OOB
- Bevestigen redirect naar de AH-bevestigingspagina
"""

import re

import pytest
from playwright.sync_api import Page, expect

from boodschappenagent.ah.models import Product
from boodschappenagent.ah.preferences import MatchReviewItem

pytestmark = pytest.mark.e2e


class TestMatchReviewVolledigeFlow:
    """Volledige match-review flow: van boodschappenlijst tot AH-bevestiging."""

    def test_verstuur_opent_match_review(self, boodschappen_page: Page):
        """Klikken op 'Verstuur naar AH' redirect naar de match-review pagina."""
        boodschappen_page.click("[data-testid='verstuur-naar-ah-button']")
        boodschappen_page.wait_for_url("**/boodschappen/match-review")
        expect(boodschappen_page.locator("[data-testid='match-review']")).to_be_visible()

    def test_match_review_toont_items(self, boodschappen_page: Page):
        """Match-review pagina toont alle gematche items."""
        boodschappen_page.click("[data-testid='verstuur-naar-ah-button']")
        boodschappen_page.wait_for_url("**/boodschappen/match-review")
        items = boodschappen_page.locator("[data-testid='match-review-item']")
        expect(items).to_have_count(5)

    def test_bevestig_btn_actief_als_alle_gevonden(self, boodschappen_page: Page):
        """Bevestig-knop is actief wanneer alle items een product hebben."""
        boodschappen_page.click("[data-testid='verstuur-naar-ah-button']")
        boodschappen_page.wait_for_url("**/boodschappen/match-review")
        btn = boodschappen_page.locator("[data-testid='bevestig-btn']")
        expect(btn).to_be_enabled()

    def test_bevestig_redirect_naar_ah_bevestiging(self, boodschappen_page: Page):
        """Bevestigen redirect naar de AH-bevestigingspagina."""
        boodschappen_page.click("[data-testid='verstuur-naar-ah-button']")
        boodschappen_page.wait_for_url("**/boodschappen/match-review")
        boodschappen_page.click("[data-testid='bevestig-btn']")
        boodschappen_page.wait_for_url("**/boodschappen/ah-bevestiging")
        expect(
            boodschappen_page.locator("[data-testid='ah-bevestiging']")
        ).to_be_visible()


class TestMatchReviewGeenMatch:
    """Tests voor de staat wanneer een of meer items geen match hebben."""

    def test_bevestig_btn_disabled_bij_geen_match(
        self, page: Page, live_server_url: str, app
    ):
        """Bevestig-knop is uitgeschakeld wanneer een item geen product heeft."""
        app.state.match_review_items = [
            MatchReviewItem(
                id="geen-match-item",
                naam="quinoa",
                hoeveelheid=200.0,
                eenheid="gram",
                product=None,
                bron="niet_gevonden",
                gecorrigeerd=False,
                aantal=1,
            ),
            MatchReviewItem(
                id="wel-match-item",
                naam="rijst",
                hoeveelheid=1.0,
                eenheid="kg",
                product=Product(
                    id=10,
                    title="AH Rijst 1kg",
                    brand="AH",
                    size="1 kg",
                    price=1.29,
                    category="",
                    is_orderable=True,
                ),
                bron="zoekopdracht",
                gecorrigeerd=False,
                aantal=1,
            ),
        ]
        page.goto(f"{live_server_url}/boodschappen/match-review")
        page.wait_for_selector("[data-testid='match-review']")
        btn = page.locator("[data-testid='bevestig-btn']")
        expect(btn).to_be_disabled()

    def test_geen_match_toont_amber_kaart(
        self, page: Page, live_server_url: str, app
    ):
        """Item zonder match heeft amber stijling."""
        app.state.match_review_items = [
            MatchReviewItem(
                id="geen-match-amber",
                naam="quinoa",
                hoeveelheid=200.0,
                eenheid="gram",
                product=None,
                bron="niet_gevonden",
                gecorrigeerd=False,
                aantal=1,
            ),
        ]
        page.goto(f"{live_server_url}/boodschappen/match-review")
        page.wait_for_selector("[data-testid='match-review']")
        kaart = page.locator("[data-testid='match-review-item']")
        expect(kaart).to_have_class(re.compile(r"amber"))


class TestMatchReviewCorrectie:
    """Tests voor de inline correctie flow."""

    def test_corrigeer_opent_zoekbalk(self, match_review_page: Page):
        """Klikken op 'Corrigeer ›' toont een zoekbalk in de kaart."""
        corrigeer = match_review_page.locator("button:has-text('Corrigeer')").first
        corrigeer.click()
        zoek_input = match_review_page.locator("[data-testid='zoek-input']").first
        expect(zoek_input).to_be_visible()

    def test_kies_product_update_kaart(
        self, match_review_page: Page, mock_ah_integratie  # noqa: ARG002
    ):
        """Na het kiezen van een product wordt de kaart bijgewerkt naar gecorrigeerd."""
        corrigeer = match_review_page.locator("button:has-text('Corrigeer')").first
        corrigeer.click()

        zoek_input = match_review_page.locator("[data-testid='zoek-input']").first
        expect(zoek_input).to_be_visible()

        zoek_input.fill("test product")
        # Wacht op resultaten na debounce (300ms + marge)
        kies_btn = match_review_page.locator("[data-testid='kies-btn']").first
        expect(kies_btn).to_be_visible(timeout=2000)

        kies_btn.click()
        # Na het klikken verschijnt het gecorrigeerd-badge
        gecorrigeerd = match_review_page.locator("text=gecorrigeerd").first
        expect(gecorrigeerd).to_be_visible(timeout=2000)
