"""Playwright E2E tests voor Fase 1a: Menu genereren en tonen.

Valideert:
- GET /week toont weekoverzicht met 7 dagkaarten
- Dagkaarten tonen receptnamen, porties, categorie, basis
- HelloFresh-dagen hebben oranje styling
- Niet-thuis-dagen hebben grijze styling
- Shuffle-knop en "Verder naar boodschappen" knop zijn aanwezig
- Header toont weeknummer
"""

import re

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e

DAG_NAMEN = [
    "Maandag",
    "Dinsdag",
    "Woensdag",
    "Donderdag",
    "Vrijdag",
    "Zaterdag",
    "Zondag",
]


class TestWeekPaginaLaadt:
    """Basis: weekoverzicht pagina laadt correct."""

    def test_pagina_heeft_titel_met_week(self, week_page: Page):
        """Paginatitel bevat 'Week' en 'Albert'."""
        expect(week_page).to_have_title(re.compile(r"Week.*Albert"))

    def test_header_toont_weeknummer(self, week_page: Page):
        """Header toont 'Week' gevolgd door een weeknummer."""
        header = week_page.locator("h1")
        expect(header).to_contain_text(re.compile(r"Week \d+"))


class TestDagkaarten:
    """Weekoverzicht toont 7 dagkaarten met correcte inhoud."""

    def test_toont_zeven_dagkaarten(self, week_page: Page):
        """Er worden exact 7 dagkaarten getoond."""
        dagkaarten = week_page.locator("[data-testid='dagkaart']")
        expect(dagkaarten).to_have_count(7)

    def test_dagkaarten_tonen_dagnamen(self, week_page: Page):
        """Alle 7 dagnamen zijn zichtbaar in het weekoverzicht."""
        for dag_naam in DAG_NAMEN:
            expect(week_page.get_by_text(dag_naam, exact=True)).to_be_visible()

    def test_dagkaarten_tonen_receptnamen(self, week_page: Page):
        """Dagkaarten met recepten tonen de juiste receptnaam."""
        receptnamen = [
            "Spaghetti Bolognese",
            "Kip Curry",
            "Zalm Teriyaki",
            "Groente Risotto",
            "Biefstuk met Friet",
        ]
        for naam in receptnamen:
            expect(week_page.get_by_text(naam)).to_be_visible()

    def test_receptkaarten_tonen_porties(self, week_page: Page):
        """Dagkaarten met recepten tonen het aantal porties."""
        recept_kaarten = week_page.locator(
            "[data-testid='dagkaart'][data-type='recept']"
        )
        expect(recept_kaarten).to_have_count(5)
        for i in range(5):
            porties = recept_kaarten.nth(i).locator("[data-testid='porties']")
            expect(porties).to_be_visible()
            expect(porties).to_contain_text("4")

    def test_receptkaarten_tonen_categorie(self, week_page: Page):
        """Dagkaarten met recepten tonen een categorie-indicator."""
        recept_kaarten = week_page.locator(
            "[data-testid='dagkaart'][data-type='recept']"
        )
        for i in range(5):
            categorie = recept_kaarten.nth(i).locator("[data-testid='categorie']")
            expect(categorie).to_be_visible()

    def test_receptkaarten_tonen_basis(self, week_page: Page):
        """Dagkaarten met recepten tonen de basis (pasta, rijst, etc.)."""
        recept_kaarten = week_page.locator(
            "[data-testid='dagkaart'][data-type='recept']"
        )
        for i in range(5):
            basis = recept_kaarten.nth(i).locator("[data-testid='basis']")
            expect(basis).to_be_visible()


class TestHelloFreshDag:
    """HelloFresh-dagen worden correct weergegeven."""

    def test_hellofresh_kaart_aanwezig(self, week_page: Page):
        """Er is exact één HelloFresh-dagkaart (woensdag)."""
        hellofresh = week_page.locator(
            "[data-testid='dagkaart'][data-type='hellofresh']"
        )
        expect(hellofresh).to_have_count(1)

    def test_hellofresh_toont_label(self, week_page: Page):
        """HelloFresh-dagkaart toont 'HelloFresh' tekst."""
        hellofresh = week_page.locator(
            "[data-testid='dagkaart'][data-type='hellofresh']"
        )
        expect(hellofresh).to_contain_text("HelloFresh")

    def test_hellofresh_toont_dagnaam(self, week_page: Page):
        """HelloFresh-dagkaart toont 'Woensdag'."""
        hellofresh = week_page.locator(
            "[data-testid='dagkaart'][data-type='hellofresh']"
        )
        expect(hellofresh).to_contain_text("Woensdag")

    def test_hellofresh_heeft_oranje_achtergrond(self, week_page: Page):
        """HelloFresh-dagkaart heeft een lichtoranje achtergrondkleur."""
        hellofresh = week_page.locator(
            "[data-testid='dagkaart'][data-type='hellofresh']"
        )
        # Lichtoranje #FFF7F0 = rgb(255, 247, 240)
        expect(hellofresh).to_have_css(
            "background-color", re.compile(r"rgb\(255,\s*247,\s*240\)")
        )


class TestNietThuisDag:
    """Niet-thuis-dagen worden correct weergegeven."""

    def test_niet_thuis_kaart_aanwezig(self, week_page: Page):
        """Er is exact één niet-thuis-dagkaart (zaterdag)."""
        niet_thuis = week_page.locator(
            "[data-testid='dagkaart'][data-type='niet-thuis']"
        )
        expect(niet_thuis).to_have_count(1)

    def test_niet_thuis_toont_label(self, week_page: Page):
        """Niet-thuis-dagkaart toont 'Niet thuis' tekst."""
        niet_thuis = week_page.locator(
            "[data-testid='dagkaart'][data-type='niet-thuis']"
        )
        expect(niet_thuis).to_contain_text("Niet thuis")

    def test_niet_thuis_toont_dagnaam(self, week_page: Page):
        """Niet-thuis-dagkaart toont 'Zaterdag'."""
        niet_thuis = week_page.locator(
            "[data-testid='dagkaart'][data-type='niet-thuis']"
        )
        expect(niet_thuis).to_contain_text("Zaterdag")

    def test_niet_thuis_heeft_grijze_achtergrond(self, week_page: Page):
        """Niet-thuis-dagkaart heeft een grijze achtergrondkleur."""
        niet_thuis = week_page.locator(
            "[data-testid='dagkaart'][data-type='niet-thuis']"
        )
        # Grijs #F5F5F5 = rgb(245, 245, 245)
        expect(niet_thuis).to_have_css(
            "background-color", re.compile(r"rgb\(245,\s*245,\s*245\)")
        )


class TestNavigatieElementen:
    """Shuffle-knop en 'Verder naar boodschappen' knop zijn aanwezig."""

    def test_shuffle_knop_zichtbaar(self, week_page: Page):
        """Shuffle-knop is zichtbaar in de header."""
        shuffle = week_page.locator("[data-testid='shuffle-button']")
        expect(shuffle).to_be_visible()

    def test_shuffle_knop_heeft_htmx_post(self, week_page: Page):
        """Shuffle-knop heeft een hx-post attribuut naar /week/shuffle."""
        shuffle = week_page.locator("[data-testid='shuffle-button']")
        expect(shuffle).to_have_attribute("hx-post", "/week/shuffle")

    def test_verder_naar_boodschappen_knop(self, week_page: Page):
        """'Verder naar boodschappen' knop is zichtbaar onderaan."""
        btn = week_page.get_by_role(
            "link", name=re.compile(r"verder naar boodschappen", re.IGNORECASE)
        )
        expect(btn).to_be_visible()

    def test_verder_naar_boodschappen_linkt_naar_voorraad(self, week_page: Page):
        """'Verder naar boodschappen' knop linkt naar /voorraad."""
        btn = week_page.get_by_role(
            "link", name=re.compile(r"verder naar boodschappen", re.IGNORECASE)
        )
        expect(btn).to_have_attribute("href", "/voorraad")

    def test_tab_bar_week_is_actief(self, week_page: Page):
        """Tab bar markeert 'Week' als actieve tab (AH-blauw)."""
        week_tab = week_page.locator("nav a[href='/week']")
        # AH blauw #00A0E2 = rgb(0, 160, 226)
        expect(week_tab).to_have_css("color", re.compile(r"rgb\(0,\s*160,\s*226\)"))
