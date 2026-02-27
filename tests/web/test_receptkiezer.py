"""Tests voor receptkiezer (fase 1c) — vervang recept flow."""

from datetime import date

from fastapi.testclient import TestClient

from .conftest import (
    make_full_week_menu,
    make_week_menu_met_niet_thuis,
    set_week_menu,
    soup,
)

# --- Stap 1: Sheet-infrastructuur ---


class TestSheetInfrastructuur:
    """Base.html moet sheet en backdrop elementen bevatten."""

    def test_week_page_heeft_sheet_div(self, client: TestClient):
        response = client.get("/week")
        html = soup(response)
        sheet = html.find(id="sheet")
        assert sheet is not None

    def test_week_page_heeft_sheet_backdrop(self, client: TestClient):
        response = client.get("/week")
        html = soup(response)
        backdrop = html.find(id="sheet-backdrop")
        assert backdrop is not None


# --- Stap 4: Receptkiezer route ---


class TestReceptkiezerOpenen:
    """GET /week/dag/{dag}/receptkiezer moet receptkiezer renderen."""

    def test_get_receptkiezer_geeft_200(self, client: TestClient):
        set_week_menu(client, make_full_week_menu())
        response = client.get("/week/dag/0/receptkiezer")
        assert response.status_code == 200

    def test_get_receptkiezer_zonder_weekmenu_geeft_404(self, client: TestClient):
        client.app.state.week_menu = None
        response = client.get("/week/dag/0/receptkiezer")
        assert response.status_code == 404

    def test_get_receptkiezer_niet_thuis_dag_geeft_422(self, client: TestClient):
        set_week_menu(client, make_week_menu_met_niet_thuis(niet_thuis_dag=5))
        response = client.get("/week/dag/5/receptkiezer")
        assert response.status_code == 422

    def test_get_receptkiezer_hellofresh_dag_geeft_422(self, client: TestClient):
        set_week_menu(client, make_full_week_menu(), hellofresh_dagen={2})
        response = client.get("/week/dag/2/receptkiezer")
        assert response.status_code == 422

    def test_get_receptkiezer_bevat_zoekbalk(self, client: TestClient):
        set_week_menu(client, make_full_week_menu())
        response = client.get("/week/dag/0/receptkiezer")
        html = soup(response)
        zoekbalk = html.select_one('[data-testid="zoekbalk"]')
        assert zoekbalk is not None

    def test_get_receptkiezer_bevat_filter_chips(self, client: TestClient):
        set_week_menu(client, make_full_week_menu())
        response = client.get("/week/dag/0/receptkiezer")
        html = soup(response)
        chips = html.select_one('[data-testid="filter-chips"]')
        assert chips is not None

    def test_get_receptkiezer_bevat_recepten_lijst(self, client: TestClient):
        set_week_menu(client, make_full_week_menu())
        response = client.get("/week/dag/0/receptkiezer")
        html = soup(response)
        lijst = html.select_one("#recepten-lijst")
        assert lijst is not None

    def test_get_receptkiezer_bevat_recepten(self, client: TestClient):
        set_week_menu(client, make_full_week_menu())
        response = client.get("/week/dag/0/receptkiezer")
        html = soup(response)
        recepten = html.select('[data-testid="receptrij"]')
        assert len(recepten) > 0

    def test_get_receptkiezer_dag_in_context(self, client: TestClient):
        set_week_menu(client, make_full_week_menu())
        response = client.get("/week/dag/3/receptkiezer")
        html = soup(response)
        kiezer = html.select_one('[data-testid="receptkiezer"]')
        assert kiezer is not None
        assert kiezer.get("data-dag") == "3"

    def test_get_receptkiezer_ongeldige_dag_geeft_422(self, client: TestClient):
        set_week_menu(client, make_full_week_menu())
        response = client.get("/week/dag/7/receptkiezer")
        assert response.status_code == 422


class TestReceptkiezerZoeken:
    """Receptkiezer zoekfunctie filtert recepten live."""

    def test_zoek_filtert_op_naam(self, client: TestClient):
        set_week_menu(client, make_full_week_menu())
        response = client.get("/week/dag/0/receptkiezer?search=kip")
        html = soup(response)
        recepten = html.select('[data-testid="receptrij"]')
        namen = [
            r.select_one('[data-testid="recept-naam"]').text.strip() for r in recepten
        ]
        assert all("kip" in naam.lower() for naam in namen)
        assert len(namen) > 0

    def test_zoek_lege_query_geeft_alle_recepten(self, client: TestClient):
        set_week_menu(client, make_full_week_menu())
        response_all = client.get("/week/dag/0/receptkiezer")
        response_empty = client.get("/week/dag/0/receptkiezer?search=")
        recepten_all = soup(response_all).select('[data-testid="receptrij"]')
        recepten_empty = soup(response_empty).select('[data-testid="receptrij"]')
        assert len(recepten_all) == len(recepten_empty)

    def test_zoek_htmx_target_recepten_lijst_geeft_fragment(self, client: TestClient):
        set_week_menu(client, make_full_week_menu())
        response = client.get(
            "/week/dag/0/receptkiezer?search=kip",
            headers={"HX-Request": "true", "HX-Target": "recepten-lijst"},
        )
        html = response.text
        assert "<html" not in html.lower()
        assert 'data-testid="receptkiezer"' not in html

    def test_zoek_geen_resultaten_toont_melding(self, client: TestClient):
        set_week_menu(client, make_full_week_menu())
        response = client.get("/week/dag/0/receptkiezer?search=xyznonexistent")
        html = soup(response)
        melding = html.select_one('[data-testid="geen-recepten"]')
        assert melding is not None


class TestReceptkiezerFilterChips:
    """Filter chips filteren recepten op categorie."""

    def test_filter_categorie_vlees(self, client: TestClient):
        set_week_menu(client, make_full_week_menu())
        response = client.get("/week/dag/0/receptkiezer?categorie=vlees")
        html = soup(response)
        recepten = html.select('[data-testid="receptrij"]')
        assert len(recepten) > 0

    def test_filter_meerdere_categorieen(self, client: TestClient):
        set_week_menu(client, make_full_week_menu())
        response = client.get("/week/dag/0/receptkiezer?categorie=vlees&categorie=vis")
        html = soup(response)
        recepten = html.select('[data-testid="receptrij"]')
        assert len(recepten) > 0

    def test_filter_en_zoek_gecombineerd(self, client: TestClient):
        set_week_menu(client, make_full_week_menu())
        response = client.get("/week/dag/0/receptkiezer?search=kip&categorie=gevogelte")
        html = soup(response)
        recepten = html.select('[data-testid="receptrij"]')
        assert len(recepten) > 0


class TestReceptkiezerSortering:
    """Recepten gesorteerd op langst-niet-gegeten eerst."""

    def test_recepten_gesorteerd_op_oud_gegeten_eerst(
        self, client: TestClient, menu_history
    ):
        set_week_menu(client, make_full_week_menu())
        # Voeg history entries toe: bolognese recent, kip-curry lang geleden
        menu_history.save(
            [
                {"datum": "2026-02-01", "recept_id": "kip-curry", "personen": 2},
                {"datum": "2026-02-15", "recept_id": "bolognese", "personen": 2},
            ]
        )
        response = client.get("/week/dag/0/receptkiezer")
        html = soup(response)
        recepten = html.select('[data-testid="receptrij"]')
        ids = [r.get("data-recept-id") for r in recepten]
        # kip-curry (oud) moet voor bolognese (recent) staan
        if "kip-curry" in ids and "bolognese" in ids:
            assert ids.index("kip-curry") < ids.index("bolognese")


# --- Stap 5: Kies recept ---


class TestKiesRecept:
    """POST /week/dag/{dag}/kies/{recipe_id} toont portiescherm."""

    def test_post_kies_geeft_200(self, client: TestClient):
        set_week_menu(client, make_full_week_menu())
        response = client.post("/week/dag/0/kies/kip-curry")
        assert response.status_code == 200

    def test_post_kies_onbekend_recept_geeft_404(self, client: TestClient):
        set_week_menu(client, make_full_week_menu())
        response = client.post("/week/dag/0/kies/onbekend-recept")
        assert response.status_code == 404

    def test_post_kies_bevat_recept_naam(self, client: TestClient):
        set_week_menu(client, make_full_week_menu())
        response = client.post("/week/dag/0/kies/kip-curry")
        html = soup(response)
        assert "Kip curry" in html.text

    def test_post_kies_bevat_portie_opties(self, client: TestClient):
        set_week_menu(client, make_full_week_menu())
        response = client.post("/week/dag/0/kies/kip-curry")
        html = soup(response)
        portie_knoppen = html.select('[data-testid="portie-knoppen"] button')
        assert len(portie_knoppen) == 3

    def test_post_kies_bevat_bevestig_url_met_dag(self, client: TestClient):
        set_week_menu(client, make_full_week_menu())
        response = client.post("/week/dag/3/kies/kip-curry")
        html = soup(response)
        portie_scherm = html.select_one('[data-testid="portiescherm"]')
        assert portie_scherm is not None

    def test_post_kies_zonder_weekmenu_geeft_404(self, client: TestClient):
        client.app.state.week_menu = None
        response = client.post("/week/dag/0/kies/kip-curry")
        assert response.status_code == 404


# --- Stap 6: Bevestig recept ---


class TestBevestigRecept:
    """POST /week/dag/{dag}/bevestig plaatst recept en swapt dagkaart."""

    def test_post_bevestig_geeft_200(self, client: TestClient):
        set_week_menu(client, make_full_week_menu())
        response = client.post(
            "/week/dag/0/bevestig",
            data={"recipe_id": "zalm", "personen": "3"},
        )
        assert response.status_code == 200

    def test_post_bevestig_update_app_state_recept(self, client: TestClient):
        set_week_menu(client, make_full_week_menu())
        client.post(
            "/week/dag/0/bevestig",
            data={"recipe_id": "zalm", "personen": "3"},
        )
        week_menu = client.app.state.week_menu
        dag_0 = next(d for d in week_menu.dagen if d.dag == 0)
        assert dag_0.recept.id == "zalm"

    def test_post_bevestig_update_app_state_personen(self, client: TestClient):
        set_week_menu(client, make_full_week_menu())
        client.post(
            "/week/dag/0/bevestig",
            data={"recipe_id": "zalm", "personen": "3"},
        )
        week_menu = client.app.state.week_menu
        dag_0 = next(d for d in week_menu.dagen if d.dag == 0)
        assert dag_0.personen == 3

    def test_post_bevestig_overige_dagen_ongewijzigd(self, client: TestClient):
        original = make_full_week_menu()
        set_week_menu(client, original)
        client.post(
            "/week/dag/0/bevestig",
            data={"recipe_id": "zalm", "personen": "3"},
        )
        week_menu = client.app.state.week_menu
        for dag_planning in week_menu.dagen:
            if dag_planning.dag != 0:
                orig = next(d for d in original.dagen if d.dag == dag_planning.dag)
                assert dag_planning.recept.id == orig.recept.id
                assert dag_planning.personen == orig.personen

    def test_post_bevestig_retourneert_dagkaart_fragment(self, client: TestClient):
        set_week_menu(client, make_full_week_menu())
        response = client.post(
            "/week/dag/0/bevestig",
            data={"recipe_id": "zalm", "personen": "3"},
        )
        html = soup(response)
        dagkaart = html.select_one('[data-testid="dagkaart"]')
        assert dagkaart is not None

    def test_post_bevestig_dagkaart_bevat_nieuw_recept(self, client: TestClient):
        set_week_menu(client, make_full_week_menu())
        response = client.post(
            "/week/dag/0/bevestig",
            data={"recipe_id": "zalm", "personen": "3"},
        )
        html = soup(response)
        assert "Zalm teriyaki" in html.text

    def test_post_bevestig_dagkaart_correcte_dag_id(self, client: TestClient):
        set_week_menu(client, make_full_week_menu())
        response = client.post(
            "/week/dag/2/bevestig",
            data={"recipe_id": "zalm", "personen": "3"},
        )
        html = soup(response)
        dagkaart = html.select_one('[data-testid="dagkaart"]')
        assert dagkaart is not None
        assert dagkaart.get("id") == "dag-2"

    def test_post_bevestig_heeft_close_sheet_trigger(self, client: TestClient):
        set_week_menu(client, make_full_week_menu())
        response = client.post(
            "/week/dag/0/bevestig",
            data={"recipe_id": "zalm", "personen": "3"},
        )
        assert "closeSheet" in response.headers.get("HX-Trigger", "")

    def test_post_bevestig_onbekend_recept_geeft_404(self, client: TestClient):
        set_week_menu(client, make_full_week_menu())
        response = client.post(
            "/week/dag/0/bevestig",
            data={"recipe_id": "onbekend", "personen": "3"},
        )
        assert response.status_code == 404

    def test_post_bevestig_zonder_weekmenu_geeft_404(self, client: TestClient):
        client.app.state.week_menu = None
        response = client.post(
            "/week/dag/0/bevestig",
            data={"recipe_id": "zalm", "personen": "3"},
        )
        assert response.status_code == 404


# --- Stap 7: Helper _format_tijd_geleden ---


class TestFormatTijdGeleden:
    """_format_tijd_geleden formatteert tijdsverschil leesbaar."""

    def test_none_geeft_nog_nooit(self):
        from boodschappenagent.web.routers.menu import _format_tijd_geleden

        assert _format_tijd_geleden(None) == "Nog nooit"

    def test_vandaag_geeft_0_d_geleden(self):
        from boodschappenagent.web.routers.menu import _format_tijd_geleden

        vandaag = date(2026, 2, 21)
        assert _format_tijd_geleden(vandaag, vandaag=vandaag) == "Vandaag"

    def test_3_dagen_geleden(self):
        from boodschappenagent.web.routers.menu import _format_tijd_geleden

        vandaag = date(2026, 2, 21)
        assert _format_tijd_geleden(date(2026, 2, 18), vandaag=vandaag) == "3 d geleden"

    def test_2_weken_geleden(self):
        from boodschappenagent.web.routers.menu import _format_tijd_geleden

        vandaag = date(2026, 2, 21)
        assert _format_tijd_geleden(date(2026, 2, 7), vandaag=vandaag) == "2 wk geleden"

    def test_2_maanden_geleden(self):
        from boodschappenagent.web.routers.menu import _format_tijd_geleden

        vandaag = date(2026, 2, 21)
        result = _format_tijd_geleden(date(2025, 12, 21), vandaag=vandaag)
        assert result == "2 mnd geleden"
