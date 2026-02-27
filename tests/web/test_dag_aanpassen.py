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


class TestDagTypeSelector:
    """S5.3: POST /week/dag/{dag}/stel-type-in wijzigt het dagtype."""

    def test_stel_geen_menu_in_dagkaart_type(self, client: TestClient):
        """S5.3.1: Dagkaart na stel geen_menu in heeft type niet-thuis."""
        set_week_menu(client, make_full_week_menu())
        response = client.post("/week/dag/0/stel-type-in", data={"type": "geen_menu"})
        assert response.status_code == 200
        assert soup(response).select_one('[data-type="niet-thuis"]') is not None

    def test_stel_geen_menu_in_app_state(self, client: TestClient):
        """S5.3.1: Na stel geen_menu in is dag 0 personen=0 in app.state."""
        set_week_menu(client, make_full_week_menu())
        client.post("/week/dag/0/stel-type-in", data={"type": "geen_menu"})
        assert client.app.state.week_menu.dagen[0].personen == 0

    def test_stel_hellofresh_in_dagkaart_type(self, client: TestClient):
        """S5.3.2: Dagkaart na stel hellofresh in heeft type hellofresh."""
        set_week_menu(client, make_full_week_menu())
        response = client.post("/week/dag/0/stel-type-in", data={"type": "hellofresh"})
        assert response.status_code == 200
        assert soup(response).select_one('[data-type="hellofresh"]') is not None

    def test_stel_hellofresh_in_app_state(self, client: TestClient):
        """S5.3.2: Na stel hellofresh in is dag 0 in app.state.hellofresh_dagen."""
        set_week_menu(client, make_full_week_menu())
        client.post("/week/dag/0/stel-type-in", data={"type": "hellofresh"})
        assert 0 in client.app.state.hellofresh_dagen

    def test_zet_hellofresh_uit_dagkaart_type(self, client: TestClient):
        """S5.3.3: Dagkaart na stel recept in (dag 2 was HF) heeft type recept."""
        set_week_menu(client, make_full_week_menu(), hellofresh_dagen={2})
        response = client.post("/week/dag/2/stel-type-in", data={"type": "recept"})
        assert response.status_code == 200
        assert soup(response).select_one('[data-type="recept"]') is not None

    def test_zet_hellofresh_uit_app_state(self, client: TestClient):
        """S5.3.3: Na recept instellen staat dag 2 niet meer in hellofresh_dagen."""
        set_week_menu(client, make_full_week_menu(), hellofresh_dagen={2})
        client.post("/week/dag/2/stel-type-in", data={"type": "recept"})
        assert 2 not in client.app.state.hellofresh_dagen

    def test_wijzigt_alleen_gevraagde_dag(self, client: TestClient):
        """S5.3.4: Alleen dag 0 wordt gewijzigd; overige 6 dagen ongewijzigd."""
        set_week_menu(client, make_full_week_menu())
        client.post("/week/dag/0/stel-type-in", data={"type": "geen_menu"})
        updated = client.app.state.week_menu
        for i in range(1, 7):
            assert updated.dagen[i].recept.id == RECEPTEN[i].id
            assert updated.dagen[i].personen == 2

    def test_ongeldig_type_geeft_422(self, client: TestClient):
        """S5.3.5: Ongeldig dagtype geeft 422."""
        set_week_menu(client, make_full_week_menu())
        response = client.post(
            "/week/dag/0/stel-type-in", data={"type": "onbekend"}
        )
        assert response.status_code == 422

    def test_zonder_weekmenu_geeft_404(self, client: TestClient):
        """S5.3.6: Zonder weekmenu geeft 404."""
        client.app.state.week_menu = None
        response = client.post(
            "/week/dag/0/stel-type-in", data={"type": "geen_menu"}
        )
        assert response.status_code == 404

    def test_niet_thuis_terug_naar_recept_dagkaart_type(self, client: TestClient):
        """S5.3.7: Na geen_menu → recept heeft dagkaart type recept."""
        set_week_menu(client, make_full_week_menu())
        client.post("/week/dag/0/stel-type-in", data={"type": "geen_menu"})
        response = client.post("/week/dag/0/stel-type-in", data={"type": "recept"})
        assert response.status_code == 200
        assert soup(response).select_one('[data-type="recept"]') is not None

    def test_niet_thuis_terug_naar_recept_app_state(self, client: TestClient):
        """S5.3.7: Na geen_menu → recept is dag 0 personen > 0 in app.state."""
        set_week_menu(client, make_full_week_menu())
        client.post("/week/dag/0/stel-type-in", data={"type": "geen_menu"})
        client.post("/week/dag/0/stel-type-in", data={"type": "recept"})
        assert client.app.state.week_menu.dagen[0].personen > 0

    def test_niet_thuis_terug_naar_recept_heeft_recept(self, client: TestClient):
        """S5.3.7: Na geen_menu → recept bevat dag 0 het originele recept."""
        set_week_menu(client, make_full_week_menu())
        client.post("/week/dag/0/stel-type-in", data={"type": "geen_menu"})
        client.post("/week/dag/0/stel-type-in", data={"type": "recept"})
        assert client.app.state.week_menu.dagen[0].recept is not None
        assert client.app.state.week_menu.dagen[0].recept.id == RECEPTEN[0].id


class TestGenereerBewaartDagtype:
    """Genereer nieuw weekmenu behoudt niet-thuis en hellofresh configuratie."""

    def test_genereer_bewaart_niet_thuis_dag(self, client: TestClient):
        """Na genereer blijft een niet-thuis dag niet-thuis."""
        set_week_menu(client, make_full_week_menu())
        client.post("/week/dag/0/stel-type-in", data={"type": "geen_menu"})
        client.post("/week/genereer")
        assert client.app.state.week_menu.dagen[0].personen == 0

    def test_genereer_bewaart_meerdere_niet_thuis_dagen(self, client: TestClient):
        """Na genereer blijven meerdere niet-thuis dagen niet-thuis."""
        set_week_menu(client, make_full_week_menu())
        client.post("/week/dag/1/stel-type-in", data={"type": "geen_menu"})
        client.post("/week/dag/3/stel-type-in", data={"type": "geen_menu"})
        client.post("/week/genereer")
        assert client.app.state.week_menu.dagen[1].personen == 0
        assert client.app.state.week_menu.dagen[3].personen == 0

    def test_genereer_overige_dagen_krijgen_nieuw_recept(self, client: TestClient):
        """Na genereer hebben niet-niet-thuis dagen recepten."""
        set_week_menu(client, make_full_week_menu())
        client.post("/week/dag/0/stel-type-in", data={"type": "geen_menu"})
        client.post("/week/genereer")
        for i in range(1, 7):
            assert client.app.state.week_menu.dagen[i].personen > 0
            assert client.app.state.week_menu.dagen[i].recept is not None

    def test_genereer_bewaart_hellofresh_dag(self, client: TestClient):
        """Na genereer blijft een hellofresh dag hellofresh (via hellofresh_dagen)."""
        set_week_menu(client, make_full_week_menu(), hellofresh_dagen={2})
        client.post("/week/genereer")
        assert 2 in client.app.state.hellofresh_dagen
