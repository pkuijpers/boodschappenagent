"""Integratietests voor dag aanpassen flow (S5).

S5.1: Dagkaart is tappable — de volledige dagkaart is een tap-target
dat de dag-aanpassen sheet opent via HTMX.

S5.2: Dag-aanpassen sheet openen — GET /week/dag/{dag}/aanpassen retourneert
het dag-aanpassen formulier met dagtype-selector, personen-selector en
"Ander recept" knop (alleen voor recept-dagen).
"""

from fastapi.testclient import TestClient

from .conftest import (
    RECEPTEN,
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


class TestDagAanpassenOpenen:
    """S5.2: Dag-aanpassen sheet opent via GET /week/dag/{dag}/aanpassen."""

    def test_sheet_opent_voor_recept_dag(self, client: TestClient):
        """S5.2.1: Sheet voor recept-dag heeft dag-aanpassen, dagtype-selector,
        personen-selector en ander-recept knop."""
        set_week_menu(client, make_full_week_menu())
        response = client.get("/week/dag/0/aanpassen")
        assert response.status_code == 200
        s = soup(response)
        assert s.select_one('[data-testid="dag-aanpassen"]') is not None
        assert s.select_one('[data-testid="dagtype-selector"]') is not None
        assert s.select_one('[data-testid="personen-selector"]') is not None
        assert s.select_one('[data-testid="ander-recept-button"]') is not None

    def test_sheet_opent_voor_niet_thuis_dag(self, client: TestClient):
        """S5.2.2: Sheet voor niet-thuis dag heeft dagtype-selector,
        maar geen personen-selector en geen ander-recept knop."""
        set_week_menu(client, make_week_menu_met_niet_thuis(niet_thuis_dag=5))
        response = client.get("/week/dag/5/aanpassen")
        assert response.status_code == 200
        s = soup(response)
        assert s.select_one('[data-testid="dagtype-selector"]') is not None
        assert s.select_one('[data-testid="personen-selector"]') is None
        assert s.select_one('[data-testid="ander-recept-button"]') is None

    def test_sheet_opent_voor_hellofresh_dag(self, client: TestClient):
        """S5.2.3: Sheet voor HelloFresh dag heeft dagtype-selector,
        maar geen personen-selector en geen ander-recept knop."""
        set_week_menu(client, make_full_week_menu(), hellofresh_dagen={2})
        response = client.get("/week/dag/2/aanpassen")
        assert response.status_code == 200
        s = soup(response)
        assert s.select_one('[data-testid="dagtype-selector"]') is not None
        assert s.select_one('[data-testid="personen-selector"]') is None
        assert s.select_one('[data-testid="ander-recept-button"]') is None

    def test_huidig_dagtype_recept_is_actief(self, client: TestClient):
        """S5.2.4: Bij een recept-dag heeft de 'Recept' knop data-actief="true"."""
        set_week_menu(client, make_full_week_menu())
        s = soup(client.get("/week/dag/0/aanpassen"))
        actieve_knop = s.select_one(
            '[data-testid="dagtype-recept"][data-actief="true"]'
        )
        assert actieve_knop is not None

    def test_huidig_dagtype_niet_thuis_is_actief(self, client: TestClient):
        """S5.2.4 (variant): 'Geen menu' knop is actief bij niet-thuis dag."""
        set_week_menu(client, make_week_menu_met_niet_thuis(niet_thuis_dag=3))
        s = soup(client.get("/week/dag/3/aanpassen"))
        actieve_knop = s.select_one(
            '[data-testid="dagtype-geen-menu"][data-actief="true"]'
        )
        assert actieve_knop is not None

    def test_huidig_dagtype_hellofresh_is_actief(self, client: TestClient):
        """S5.2.4 (variant): 'HelloFresh' knop heeft data-actief="true" bij HF dag."""
        set_week_menu(client, make_full_week_menu(), hellofresh_dagen={2})
        s = soup(client.get("/week/dag/2/aanpassen"))
        actieve_knop = s.select_one(
            '[data-testid="dagtype-hellofresh"][data-actief="true"]'
        )
        assert actieve_knop is not None

    def test_huidige_receptnaam_zichtbaar(self, client: TestClient):
        """S5.2.5: De naam van het huidige recept staat in de sheet-header."""
        set_week_menu(client, make_full_week_menu())
        s = soup(client.get("/week/dag/0/aanpassen"))
        # Dag 0 heeft RECEPTEN[0] = "Kip curry"
        assert RECEPTEN[0].naam in s.get_text()

    def test_zonder_weekmenu_geeft_404(self, client: TestClient):
        """S5.2.6: Zonder weekmenu geeft de sheet 404."""
        client.app.state.week_menu = None
        response = client.get("/week/dag/0/aanpassen")
        assert response.status_code == 404

    def test_ongeldige_dag_geeft_422(self, client: TestClient):
        """S5.2.7: Dagnummer 7 (buiten 0–6) geeft 422."""
        set_week_menu(client, make_full_week_menu())
        response = client.get("/week/dag/7/aanpassen")
        assert response.status_code == 422
