"""Playwright E2E test: HelloFresh-dag genereert geen boodschappen.

Valideert de hele keten: dagtype instellen → domeinmodel → boodschappenlijst.
"""

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e


class TestHelloFreshGeenBoodschappen:
    """Bugfix: HelloFresh-dag mag geen boodschappen genereren."""

    def test_hellofresh_dag_uitgesloten_van_boodschappenlijst(
        self, week_page: Page, live_server_url: str, app
    ):
        """Dag op hellofresh → geplande_dagen -1 → boodschappenlijst OK.

        TEST_WEEK_MENU: 5 receptdagen, 1 hellofresh (dag 2), 1 niet-thuis (dag 5).
        Na dag 0 op hellofresh: 4 receptdagen, 2 hellofresh, 1 niet-thuis.
        """
        # Verifieer uitgangssituatie: 5 geplande dagen
        assert len(app.state.week_menu.geplande_dagen) == 5

        # Zet dag 0 (maandag, recept) op hellofresh via UI
        week_page.locator("[data-testid='dagkaart'][data-dag='0']").click()
        week_page.wait_for_selector("#sheet [data-testid='dag-aanpassen']")
        week_page.locator("[data-testid='dagtype-hellofresh']").click()
        week_page.wait_for_selector(
            "[data-testid='dagkaart'][data-dag='0'][data-type='hellofresh']"
        )

        # Verifieer domeinmodel: nu 4 geplande dagen
        assert len(app.state.week_menu.geplande_dagen) == 4

        # Navigeer naar boodschappenlijst — deze moet laden zonder error
        week_page.goto(f"{live_server_url}/boodschappen")
        week_page.wait_for_selector("[data-testid='boodschappen-header']")
        expect(week_page.locator("h1")).to_contain_text("Boodschappenlijst")

        # Boodschappenlijst heeft items (van de 4 receptdagen)
        expect(week_page.locator("[data-testid='boodschapitem']").first).to_be_visible()
