"""Playwright E2E tests voor S5.1 en S5.2: Dagkaart tappable + sheet openen.

Valideert de visuele en interactieve staat van dagkaarten als tap-targets,
én de dag-aanpassen sheet die opent na een tap:
- Dagkaarten tonen cursor pointer (visueel klikbaar)
- Correcte HTMX-attributen in de browser
- Geen losse ↻ knop
- Sheet is initieel verborgen, backdrop ook
- Tap op dagkaart opent sheet met dag-aanpassen inhoud
"""

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e


class TestDagkaartTappableUI:
    """S5.1: Dagkaarten zijn visueel tappable en hebben correcte HTMX-attributen."""

    def test_alle_dagkaarten_hebben_hx_get_aanpassen(self, week_page: Page):
        """Alle 7 dagkaarten hebben hx-get="/week/dag/{N}/aanpassen"."""
        dagkaarten = week_page.locator("[data-testid='dagkaart']")
        expect(dagkaarten).to_have_count(7)
        for i in range(7):
            kaart = dagkaarten.nth(i)
            dag = kaart.get_attribute("data-dag")
            expect(kaart).to_have_attribute("hx-get", f"/week/dag/{dag}/aanpassen")

    def test_alle_dagkaarten_hebben_hx_target_sheet(self, week_page: Page):
        """Alle 7 dagkaarten hebben hx-target="#sheet"."""
        dagkaarten = week_page.locator("[data-testid='dagkaart']")
        for i in range(7):
            expect(dagkaarten.nth(i)).to_have_attribute("hx-target", "#sheet")

    def test_dagkaarten_hebben_cursor_pointer(self, week_page: Page):
        """Alle dagkaarten tonen cursor: pointer (visueel klikbaar)."""
        dagkaarten = week_page.locator("[data-testid='dagkaart']")
        for i in range(7):
            cursor = dagkaarten.nth(i).evaluate(
                "el => window.getComputedStyle(el).cursor"
            )
            assert cursor == "pointer", (
                f"Dagkaart {i} heeft cursor '{cursor}', verwacht 'pointer'"
            )

    def test_hellofresh_kaart_is_tappable(self, week_page: Page):
        """HelloFresh-dagkaart (woensdag, dag 2) heeft hx-get aanpassen."""
        hf_kaart = week_page.locator("[data-testid='dagkaart'][data-type='hellofresh']")
        expect(hf_kaart).to_have_count(1)
        expect(hf_kaart).to_have_attribute("hx-get", "/week/dag/2/aanpassen")

    def test_niet_thuis_kaart_is_tappable(self, week_page: Page):
        """Niet-thuis-dagkaart (zaterdag, dag 5) heeft hx-get aanpassen."""
        niet_thuis = week_page.locator(
            "[data-testid='dagkaart'][data-type='niet-thuis']"
        )
        expect(niet_thuis).to_have_count(1)
        expect(niet_thuis).to_have_attribute("hx-get", "/week/dag/5/aanpassen")

    def test_geen_vervang_dag_button(self, week_page: Page):
        """Er zijn geen losse ↻ knoppen (data-testid='vervang-dag-button')."""
        vervang_knoppen = week_page.locator("[data-testid='vervang-dag-button']")
        expect(vervang_knoppen).to_have_count(0)


class TestSheetInfrastructuurUI:
    """Sheet-infrastructuur is aanwezig maar initieel verborgen."""

    def test_sheet_element_aanwezig(self, week_page: Page):
        """Sheet div (#sheet) bestaat in de DOM."""
        sheet = week_page.locator("#sheet")
        expect(sheet).to_be_attached()

    def test_backdrop_element_aanwezig(self, week_page: Page):
        """Backdrop div (#sheet-backdrop) bestaat in de DOM."""
        backdrop = week_page.locator("#sheet-backdrop")
        expect(backdrop).to_be_attached()

    def test_sheet_is_initieel_niet_zichtbaar(self, week_page: Page):
        """Sheet is initieel buiten het scherm en niet zichtbaar voor de gebruiker."""
        # Sheet heeft translate-y-full: schuift van onderaf het scherm in
        is_off_screen = week_page.evaluate("""
            () => {
                const sheet = document.getElementById('sheet');
                const rect = sheet.getBoundingClientRect();
                return rect.top >= window.innerHeight;
            }
        """)
        assert is_off_screen, "Sheet is initieel zichtbaar; verwacht buiten het scherm"

    def test_backdrop_is_initieel_verborgen(self, week_page: Page):
        """Backdrop is initieel niet zichtbaar (hidden class)."""
        backdrop = week_page.locator("#sheet-backdrop")
        expect(backdrop).to_be_hidden()

    def test_sheet_is_initieel_leeg(self, week_page: Page):
        """Sheet bevat initieel geen inhoud."""
        inhoud = week_page.evaluate(
            "() => document.getElementById('sheet').innerHTML.trim()"
        )
        assert inhoud == "", f"Sheet bevat initieel inhoud: '{inhoud}'"


class TestDagAanpassenSheetOpenen:
    """S5.2 E2E: Tap op dagkaart opent dag-aanpassen sheet."""

    def test_tap_recept_dagkaart_opent_sheet(self, week_page: Page):
        """Tap op een recept-dagkaart opent de dag-aanpassen sheet."""
        week_page.locator("[data-testid='dagkaart'][data-dag='0']").click()
        week_page.wait_for_selector("#sheet [data-testid='dag-aanpassen']")
        expect(
            week_page.locator("#sheet [data-testid='dag-aanpassen']")
        ).to_be_visible()

    def test_tap_dagkaart_toont_backdrop(self, week_page: Page):
        """Na tap op dagkaart is de backdrop zichtbaar."""
        week_page.locator("[data-testid='dagkaart'][data-dag='1']").click()
        week_page.wait_for_selector("#sheet [data-testid='dag-aanpassen']")
        expect(week_page.locator("#sheet-backdrop")).to_be_visible()

    def test_tap_recept_dagkaart_toont_dagtype_selector(self, week_page: Page):
        """Sheet voor recept-dag bevat een dagtype-selector."""
        week_page.locator("[data-testid='dagkaart'][data-dag='0']").click()
        week_page.wait_for_selector("#sheet [data-testid='dagtype-selector']")
        expect(
            week_page.locator("#sheet [data-testid='dagtype-selector']")
        ).to_be_visible()

    def test_tap_recept_dagkaart_toont_personen_selector(self, week_page: Page):
        """Sheet voor recept-dag bevat een personen-selector."""
        week_page.locator("[data-testid='dagkaart'][data-dag='0']").click()
        week_page.wait_for_selector("#sheet [data-testid='personen-selector']")
        expect(
            week_page.locator("#sheet [data-testid='personen-selector']")
        ).to_be_visible()

    def test_tap_recept_dagkaart_toont_ander_recept_button(self, week_page: Page):
        """Sheet voor recept-dag bevat 'Ander recept' knop."""
        week_page.locator("[data-testid='dagkaart'][data-dag='0']").click()
        week_page.wait_for_selector("#sheet [data-testid='ander-recept-button']")
        expect(
            week_page.locator("#sheet [data-testid='ander-recept-button']")
        ).to_be_visible()

    def test_tap_hellofresh_dagkaart_opent_sheet(self, week_page: Page):
        """Tap op HelloFresh-dagkaart (dag 2) opent sheet zonder personen-selector."""
        week_page.locator("[data-testid='dagkaart'][data-dag='2']").click()
        week_page.wait_for_selector("#sheet [data-testid='dag-aanpassen']")
        expect(
            week_page.locator("#sheet [data-testid='dag-aanpassen']")
        ).to_be_visible()
        expect(
            week_page.locator("#sheet [data-testid='personen-selector']")
        ).to_have_count(0)

    def test_tap_niet_thuis_dagkaart_opent_sheet(self, week_page: Page):
        """Tap op niet-thuis-dagkaart (dag 5) opent sheet zonder personen-selector."""
        week_page.locator("[data-testid='dagkaart'][data-dag='5']").click()
        week_page.wait_for_selector("#sheet [data-testid='dag-aanpassen']")
        expect(
            week_page.locator("#sheet [data-testid='dag-aanpassen']")
        ).to_be_visible()
        expect(
            week_page.locator("#sheet [data-testid='personen-selector']")
        ).to_have_count(0)


class TestDagTypeWijzigenUI:
    """E4/E5/E6/E7: Dagtype wijzigen via de sheet met HTMX-interactie."""

    def test_dag_markeren_als_niet_thuis(self, week_page: Page):
        """E4: Tap dagkaart → 'Geen menu' → dagkaart niet-thuis, sheet bijgewerkt."""
        # Open sheet voor dag 4 (vrijdag, recept)
        week_page.locator("[data-testid='dagkaart'][data-dag='4']").click()
        week_page.wait_for_selector("#sheet [data-testid='dag-aanpassen']")

        # Tap "Geen menu" knop in de sheet
        week_page.locator("[data-testid='dagtype-geen-menu']").click()

        # Wacht op dagkaart-update in achtergrond
        week_page.wait_for_selector(
            "[data-testid='dagkaart'][data-dag='4'][data-type='niet-thuis']"
        )

        # Dagkaart is nu niet-thuis
        expect(
            week_page.locator("[data-testid='dagkaart'][data-dag='4']")
        ).to_have_attribute("data-type", "niet-thuis")

        # Sheet toont geen personen-selector meer
        expect(
            week_page.locator("#sheet [data-testid='personen-selector']")
        ).to_have_count(0)

    def test_dag_markeren_als_hellofresh(self, week_page: Page):
        """E5: Tap dagkaart → 'HelloFresh' → dagkaart hellofresh, sheet bijgewerkt."""
        # Open sheet voor dag 6 (zondag, recept)
        week_page.locator("[data-testid='dagkaart'][data-dag='6']").click()
        week_page.wait_for_selector("#sheet [data-testid='dag-aanpassen']")

        # Tap "HelloFresh" knop in de sheet
        week_page.locator("[data-testid='dagtype-hellofresh']").click()

        # Wacht op dagkaart-update in achtergrond
        week_page.wait_for_selector(
            "[data-testid='dagkaart'][data-dag='6'][data-type='hellofresh']"
        )

        # Dagkaart is nu hellofresh
        expect(
            week_page.locator("[data-testid='dagkaart'][data-dag='6']")
        ).to_have_attribute("data-type", "hellofresh")

        # Sheet toont geen "Ander recept" knop meer
        expect(
            week_page.locator("#sheet [data-testid='ander-recept-button']")
        ).to_have_count(0)

    def test_niet_thuis_terug_naar_recept(self, week_page: Page):
        """E6: Niet-thuis → Recept → dagkaart type recept."""
        # Zet dag 4 op niet-thuis
        week_page.locator("[data-testid='dagkaart'][data-dag='4']").click()
        week_page.wait_for_selector("#sheet [data-testid='dag-aanpassen']")
        week_page.locator("[data-testid='dagtype-geen-menu']").click()
        week_page.wait_for_selector(
            "[data-testid='dagkaart'][data-dag='4'][data-type='niet-thuis']"
        )

        # Zet dag 4 terug op recept
        week_page.locator("[data-testid='dagtype-recept']").click()
        week_page.wait_for_selector(
            "[data-testid='dagkaart'][data-dag='4'][data-type='recept']"
        )

        expect(
            week_page.locator("[data-testid='dagkaart'][data-dag='4']")
        ).to_have_attribute("data-type", "recept")
        expect(
            week_page.locator("#sheet [data-testid='personen-selector']")
        ).to_be_visible()

    def test_personen_aanpassen_via_sheet(self, week_page: Page):
        """E7: Tap dagkaart → tap '2' in personen-selector → dagkaart toont '2 porties';
        sheet blijft open."""
        # TEST_WEEK_MENU dag 0 start met personen=4; we passen aan naar 2
        week_page.locator("[data-testid='dagkaart'][data-dag='0']").click()
        week_page.wait_for_selector("#sheet [data-testid='personen-selector']")

        # Tap "2" in personen-selector
        week_page.locator("[data-testid='personen-selector'] button").filter(
            has_text="2"
        ).click()

        # Dagkaart toont nu "2 porties" — expect() wacht automatisch op HTMX update
        porties = week_page.locator(
            "[data-testid='dagkaart'][data-dag='0'] [data-testid='porties']"
        )
        expect(porties).to_contain_text("2")

        # Sheet blijft open (personen-selector is nog zichtbaar)
        expect(
            week_page.locator("#sheet [data-testid='personen-selector']")
        ).to_be_visible()

        # Actieve staat in personen-selector is bijgewerkt naar "2"
        actieve_knop = week_page.locator(
            "#sheet [data-testid='personen-selector'] button[data-actief='true']"
        )
        expect(actieve_knop).to_contain_text("2")

    def test_genereer_bewaart_niet_thuis(self, week_page: Page):
        """E7: Na genereer nieuw weekmenu blijft niet-thuis dag niet-thuis."""
        # Zet dag 4 op niet-thuis
        week_page.locator("[data-testid='dagkaart'][data-dag='4']").click()
        week_page.wait_for_selector("#sheet [data-testid='dag-aanpassen']")
        week_page.locator("[data-testid='dagtype-geen-menu']").click()
        week_page.wait_for_selector(
            "[data-testid='dagkaart'][data-dag='4'][data-type='niet-thuis']"
        )

        # Sluit sheet via backdrop klik bovenaan (buiten het sheet-gebied)
        week_page.locator("#sheet-backdrop").click(position={"x": 10, "y": 10})
        week_page.wait_for_selector("#sheet-backdrop", state="hidden")
        week_page.locator("[data-testid='genereer-button']").click()
        week_page.wait_for_load_state("networkidle")

        # Dag 4 moet nog steeds niet-thuis zijn
        expect(
            week_page.locator("[data-testid='dagkaart'][data-dag='4']")
        ).to_have_attribute("data-type", "niet-thuis")
