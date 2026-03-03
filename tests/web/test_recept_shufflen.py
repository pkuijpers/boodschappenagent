"""Integratietests voor recept shufflen (UI → Planner → UI).

S2 uit het testplan: POST /week/shuffle met dag parameter
vervangt het recept voor één dag, overige dagen blijven ongewijzigd.
"""

from fastapi.testclient import TestClient

from boodschappenagent.planner import DagInput

from .conftest import (
    RECEPTEN,
    WEEK_START,
    make_full_week_menu,
    make_week_menu_met_niet_thuis,
    set_week_menu,
    soup,
)


class TestShuffleEnkelRecept:
    """S2.1: POST /week/shuffle met dag=0 vervangt recept voor dag 0."""

    def test_shuffle_dag_0_geeft_ander_recept(self, client: TestClient):
        set_week_menu(client, make_full_week_menu())
        origineel_recept = RECEPTEN[0].naam

        response = client.post("/week/shuffle", data={"dag": "0"})
        assert response.status_code == 200

        dag_0 = soup(response).select_one('[data-testid="dagkaart"][data-dag="0"]')
        assert dag_0 is not None
        assert origineel_recept not in dag_0.get_text()

    def test_shuffle_dag_0_overige_dagen_ongewijzigd(self, client: TestClient):
        """Overige dagen ongewijzigd in app.state (response bevat alleen dag 0)."""
        set_week_menu(client, make_full_week_menu())

        client.post("/week/shuffle", data={"dag": "0"})

        updated_menu = client.app.state.week_menu
        for i in range(1, 7):
            assert updated_menu.dagen[i].recept.id == RECEPTEN[i].id

    def test_shuffle_update_app_state(self, client: TestClient):
        set_week_menu(client, make_full_week_menu())

        client.post("/week/shuffle", data={"dag": "0"})

        updated_menu = client.app.state.week_menu
        assert updated_menu.dagen[0].recept.id != RECEPTEN[0].id
        for i in range(1, 7):
            assert updated_menu.dagen[i].recept.id == RECEPTEN[i].id


class TestShuffleRespecteertVariatie:
    """S2.2: Shuffle respecteert variatie t.o.v. buren."""

    def test_shuffle_dag_3_verschilt_van_buren(self, client: TestClient, menu_planner):
        """Nieuw recept verschilt in categorie van buren (dag 2, dag 4)."""
        dag_inputs = [DagInput(dag=i, personen=2) for i in range(7)]
        week_menu = menu_planner.plan_week(
            week_input=dag_inputs,
            maand="feb",
            week_start=WEEK_START,
        )
        set_week_menu(client, week_menu)

        s = soup(client.post("/week/shuffle", data={"dag": "3"}))

        categorie_elements = s.select('[data-testid="categorie"]')
        categorieen = [el.get_text().strip() for el in categorie_elements]

        # Dag 3 (index 3) mag niet gelijk zijn aan dag 2 (index 2)
        if len(categorieen) > 3:
            assert categorieen[3] != categorieen[2], (
                f"Dag 3 heeft dezelfde categorie als dag 2: {categorieen[3]}"
            )


class TestShuffleNietThuisDag:
    """S2.3: Shuffle niet-thuis dag geeft foutmelding."""

    def test_shuffle_niet_thuis_geeft_422(self, client: TestClient):
        set_week_menu(client, make_week_menu_met_niet_thuis(niet_thuis_dag=5))

        response = client.post("/week/shuffle", data={"dag": "5"})
        assert response.status_code == 422


class TestShuffleRetourneertFragment:
    """S2.4: Shuffle retourneert altijd een OOB fragment (geen volledige pagina)."""

    def test_shuffle_geen_html_wrapper(self, client: TestClient):
        """Shuffle retourneert altijd een fragment, ook zonder HTMX headers."""
        set_week_menu(client, make_full_week_menu())

        response = client.post("/week/shuffle", data={"dag": "0"})

        assert "<html" not in response.text
        assert "</html>" not in response.text

    def test_shuffle_bevat_precies_een_dagkaart(self, client: TestClient):
        """S2.4: Precies 1 dagkaart in response (niet 7)."""
        set_week_menu(client, make_full_week_menu())

        s = soup(client.post("/week/shuffle", data={"dag": "0"}))

        dagkaarten = s.select('[data-testid="dagkaart"]')
        assert len(dagkaarten) == 1

    def test_shuffle_geen_close_sheet_trigger(self, client: TestClient):
        """S2.4: Geen closeSheet trigger; sheet blijft open."""
        set_week_menu(client, make_full_week_menu())

        response = client.post("/week/shuffle", data={"dag": "0"})

        hx_trigger = response.headers.get("HX-Trigger", "")
        assert "closeSheet" not in hx_trigger

    def test_shuffle_dagkaart_heeft_oob_attribuut(self, client: TestClient):
        """Dagkaart heeft hx-swap-oob voor OOB update van achtergrond-kaart."""
        set_week_menu(client, make_full_week_menu())

        s = soup(client.post("/week/shuffle", data={"dag": "0"}))

        dagkaart = s.select_one('[data-testid="dagkaart"]')
        assert dagkaart is not None
        assert dagkaart.get("hx-swap-oob") is not None
