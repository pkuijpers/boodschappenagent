"""Integratietests voor dag aanpassen flow (S5).

S5.1: Dagkaart is tappable — de volledige dagkaart is een tap-target
dat de dag-aanpassen sheet opent via HTMX.
"""

from fastapi.testclient import TestClient

from .conftest import (
    make_full_week_menu,
    make_week_menu_met_niet_thuis,
    set_week_menu,
    soup,
)


class TestDagkaartTappable:
    """S5.1: Elke dagkaart is tappable en opent de dag-aanpassen sheet."""

    def test_alle_dagkaarten_hebben_hx_get(self, client: TestClient):
        """S5.1.1: Elke dagkaart heeft hx-get="/week/dag/{N}/aanpassen"."""
        set_week_menu(client, make_full_week_menu())
        s = soup(client.get("/week"))

        dagkaarten = s.select('[data-testid="dagkaart"]')
        assert len(dagkaarten) == 7
        for kaart in dagkaarten:
            dag = kaart["data-dag"]
            assert kaart.get("hx-get") == f"/week/dag/{dag}/aanpassen", (
                f"Dagkaart {dag} mist hx-get='/week/dag/{dag}/aanpassen'"
            )

    def test_alle_dagkaarten_hebben_hx_target_sheet(self, client: TestClient):
        """S5.1.1: Elke dagkaart heeft hx-target="#sheet"."""
        set_week_menu(client, make_full_week_menu())
        s = soup(client.get("/week"))

        dagkaarten = s.select('[data-testid="dagkaart"]')
        for kaart in dagkaarten:
            dag = kaart["data-dag"]
            assert kaart.get("hx-target") == "#sheet", (
                f"Dagkaart {dag} mist hx-target='#sheet'"
            )

    def test_hellofresh_kaart_is_tappable(self, client: TestClient):
        """S5.1.2: HelloFresh-kaart heeft hx-get="/week/dag/2/aanpassen"."""
        set_week_menu(client, make_full_week_menu(), hellofresh_dagen={2})
        s = soup(client.get("/week"))

        hf_kaart = s.select_one('[data-testid="dagkaart"][data-type="hellofresh"]')
        assert hf_kaart is not None
        assert hf_kaart.get("hx-get") == "/week/dag/2/aanpassen"

    def test_niet_thuis_kaart_is_tappable(self, client: TestClient):
        """S5.1.1: Niet-thuis-kaart heeft ook hx-get="/week/dag/{N}/aanpassen"."""
        set_week_menu(client, make_week_menu_met_niet_thuis(niet_thuis_dag=5))
        s = soup(client.get("/week"))

        niet_thuis = s.select_one('[data-testid="dagkaart"][data-type="niet-thuis"]')
        assert niet_thuis is not None
        assert niet_thuis.get("hx-get") == "/week/dag/5/aanpassen"

    def test_geen_vervang_dag_button(self, client: TestClient):
        """S5.1.3: Er is geen losse ↻ knop (vervang-dag-button)."""
        set_week_menu(client, make_full_week_menu())
        s = soup(client.get("/week"))

        vervang_knoppen = s.select('[data-testid="vervang-dag-button"]')
        assert len(vervang_knoppen) == 0, (
            f"Gevonden {len(vervang_knoppen)} vervang-dag-button(s), verwacht 0"
        )

    def test_geen_vervang_dag_button_met_hellofresh(self, client: TestClient):
        """S5.1.3: Ook bij HelloFresh-dag geen losse ↻ knop."""
        set_week_menu(client, make_full_week_menu(), hellofresh_dagen={2})
        s = soup(client.get("/week"))

        vervang_knoppen = s.select('[data-testid="vervang-dag-button"]')
        assert len(vervang_knoppen) == 0
