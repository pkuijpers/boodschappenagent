"""Tests voor POST /week/bevestig — history sync bij 'verder naar boodschappen'."""

from fastapi.testclient import TestClient

from .conftest import (
    make_full_week_menu,
    make_week_menu_met_niet_thuis,
    set_week_menu,
)


class TestWeekBevestig:
    """POST /week/bevestig synct history en redirect naar /voorraad."""

    def test_bevestig_redirect_naar_voorraad(self, client: TestClient):
        """POST /week/bevestig redirect naar /ingredient-selectie."""
        set_week_menu(client, make_full_week_menu())
        response = client.post("/week/bevestig", follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"] == "/ingredient-selectie"

    def test_bevestig_schrijft_history(self, client: TestClient, menu_history):
        """POST /week/bevestig schrijft het weekmenu naar history."""
        set_week_menu(client, make_full_week_menu())
        client.post("/week/bevestig")
        entries = menu_history.load()
        assert len(entries) == 7

    def test_bevestig_history_bevat_juiste_recepten(
        self, client: TestClient, menu_history
    ):
        """History entries bevatten de recepten uit het weekmenu."""
        week_menu = make_full_week_menu()
        set_week_menu(client, week_menu)
        client.post("/week/bevestig")
        entries = menu_history.load()
        recipe_ids = {e["recept_id"] for e in entries}
        expected_ids = {d.recept.id for d in week_menu.geplande_dagen}
        assert recipe_ids == expected_ids

    def test_bevestig_skipt_niet_thuis_in_history(
        self, client: TestClient, menu_history
    ):
        """Niet-thuis dagen worden niet in history opgeslagen."""
        set_week_menu(client, make_week_menu_met_niet_thuis(niet_thuis_dag=5))
        client.post("/week/bevestig")
        entries = menu_history.load()
        assert len(entries) == 6

    def test_bevestig_vervangt_eerdere_week_entries(
        self, client: TestClient, menu_history
    ):
        """Twee keer bevestigen geeft geen duplicaten."""
        set_week_menu(client, make_full_week_menu())
        client.post("/week/bevestig")
        client.post("/week/bevestig")
        entries = menu_history.load()
        assert len(entries) == 7

    def test_bevestig_zonder_weekmenu_redirect_naar_week(self, client: TestClient):
        """Zonder weekmenu redirect naar /week."""
        response = client.post("/week/bevestig", follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"] == "/week"


class TestGenereerSchrijftGeenHistory:
    """POST /week/genereer schrijft NIET meer naar history."""

    def test_genereer_schrijft_geen_history(self, client: TestClient, menu_history):
        """Na genereer is history nog leeg — pas bij bevestig wordt geschreven."""
        set_week_menu(client, make_full_week_menu())
        client.post("/week/genereer")
        entries = menu_history.load()
        assert len(entries) == 0
