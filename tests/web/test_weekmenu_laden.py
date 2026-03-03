"""Integratietests voor weekmenu laden (Repository → Planner → UI).

S1 uit het testplan: de volledige keten van HTTP request → route →
template rendering → HTML response met BeautifulSoup asserties.
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


class TestVolledigWeekmenuLaden:
    """GET /week met 7 dagen, alle thuis → 7 dagkaarten type recept."""

    def test_zeven_dagkaarten_aanwezig(self, client: TestClient):
        set_week_menu(client, make_full_week_menu())
        s = soup(client.get("/week"))

        dagkaarten = s.select('[data-testid="dagkaart"]')
        assert len(dagkaarten) == 7

    def test_alle_dagkaarten_type_recept(self, client: TestClient):
        set_week_menu(client, make_full_week_menu())
        s = soup(client.get("/week"))

        dagkaarten = s.select('[data-testid="dagkaart"][data-type="recept"]')
        assert len(dagkaarten) == 7

    def test_elke_dagkaart_heeft_receptnaam(self, client: TestClient):
        set_week_menu(client, make_full_week_menu())
        s = soup(client.get("/week"))

        dagkaarten = s.select('[data-testid="dagkaart"]')
        for i, kaart in enumerate(dagkaarten):
            assert RECEPTEN[i].naam in kaart.get_text()

    def test_elke_dagkaart_heeft_porties(self, client: TestClient):
        set_week_menu(client, make_full_week_menu(personen=3))
        s = soup(client.get("/week"))

        porties_elements = s.select('[data-testid="porties"]')
        assert len(porties_elements) == 7
        for el in porties_elements:
            assert "3" in el.get_text()

    def test_elke_dagkaart_heeft_categorie_emoji(self, client: TestClient):
        set_week_menu(client, make_full_week_menu())
        s = soup(client.get("/week"))

        categorie_elements = s.select('[data-testid="categorie"]')
        assert len(categorie_elements) == 7
        for el in categorie_elements:
            assert el.get_text().strip() != ""

    def test_dagkaarten_hebben_data_dag_attribuut(self, client: TestClient):
        set_week_menu(client, make_full_week_menu())
        s = soup(client.get("/week"))

        dagkaarten = s.select('[data-testid="dagkaart"]')
        dag_nummers = [kaart["data-dag"] for kaart in dagkaarten]
        assert dag_nummers == ["0", "1", "2", "3", "4", "5", "6"]


class TestNietThuisDagen:
    """GET /week met dag personen=0 → dagkaart type niet-thuis."""

    def test_niet_thuis_dag_type(self, client: TestClient):
        set_week_menu(client, make_week_menu_met_niet_thuis(niet_thuis_dag=5))

        s = soup(client.get("/week"))
        niet_thuis = s.select('[data-testid="dagkaart"][data-type="niet-thuis"]')
        assert len(niet_thuis) == 1
        assert niet_thuis[0]["data-dag"] == "5"

    def test_niet_thuis_dag_zonder_receptnaam(self, client: TestClient):
        set_week_menu(client, make_week_menu_met_niet_thuis(niet_thuis_dag=5))

        s = soup(client.get("/week"))
        niet_thuis = s.select_one('[data-testid="dagkaart"][data-type="niet-thuis"]')
        for recept in RECEPTEN:
            assert recept.naam not in niet_thuis.get_text()

    def test_overige_dagen_zijn_recept(self, client: TestClient):
        set_week_menu(client, make_week_menu_met_niet_thuis(niet_thuis_dag=5))

        s = soup(client.get("/week"))
        recept_kaarten = s.select('[data-testid="dagkaart"][data-type="recept"]')
        assert len(recept_kaarten) == 6


class TestHelloFreshDag:
    """GET /week met dag in hellofresh_dagen → dagkaart type hellofresh."""

    def test_hellofresh_dag_type(self, client: TestClient):
        set_week_menu(client, make_full_week_menu(), hellofresh_dagen={2})

        s = soup(client.get("/week"))
        hf_kaarten = s.select('[data-testid="dagkaart"][data-type="hellofresh"]')
        assert len(hf_kaarten) == 1
        assert hf_kaarten[0]["data-dag"] == "2"

    def test_hellofresh_dag_toont_hellofresh_tekst(self, client: TestClient):
        set_week_menu(client, make_full_week_menu(), hellofresh_dagen={2})

        s = soup(client.get("/week"))
        hf_kaart = s.select_one('[data-testid="dagkaart"][data-type="hellofresh"]')
        assert "HelloFresh" in hf_kaart.get_text()

    def test_hellofresh_dag_heeft_hf_styling(self, client: TestClient):
        set_week_menu(client, make_full_week_menu(), hellofresh_dagen={2})

        s = soup(client.get("/week"))
        hf_kaart = s.select_one('[data-testid="dagkaart"][data-type="hellofresh"]')
        classes = hf_kaart.get("class", [])
        assert any("hf-" in cls for cls in classes)


class TestWeeknummer:
    """GET /week toont correct weeknummer op basis van week_start."""

    def test_weeknummer_zichtbaar(self, client: TestClient):
        set_week_menu(client, make_full_week_menu())
        s = soup(client.get("/week"))

        week_nummer = s.select_one('[data-testid="week-nummer"]')
        assert week_nummer is not None
        assert "8" in week_nummer.get_text()

    def test_weeknummer_tekst_format(self, client: TestClient):
        set_week_menu(client, make_full_week_menu())
        s = soup(client.get("/week"))

        week_nummer = s.select_one('[data-testid="week-nummer"]')
        assert "Week 8" in week_nummer.get_text()


class TestVariatieGeenDubbeleCategorieen:
    """Geen twee opeenvolgende dagen met dezelfde categorie."""

    def test_geen_opeenvolgende_dubbele_categorieen(
        self, client: TestClient, menu_planner
    ):
        """Echte planner genereert menu zonder opeenvolgende dubbele categorieën."""
        dag_inputs = [DagInput(dag=i, personen=2) for i in range(7)]
        week_menu = menu_planner.plan_week(
            week_input=dag_inputs,
            maand="feb",
            week_start=WEEK_START,
        )
        set_week_menu(client, week_menu)

        s = soup(client.get("/week"))
        categorie_elements = s.select('[data-testid="categorie"]')
        categorieen = [el.get_text().strip() for el in categorie_elements]

        for i in range(len(categorieen) - 1):
            assert categorieen[i] != categorieen[i + 1], (
                f"Dag {i} en {i + 1} hebben dezelfde categorie: {categorieen[i]}"
            )


class TestAutoGenereerMenu:
    """GET /week zonder week_menu → automatisch menu genereren."""

    def test_auto_genereer_bij_leeg_menu(self, client: TestClient):
        s = soup(client.get("/week"))

        dagkaarten = s.select('[data-testid="dagkaart"]')
        assert len(dagkaarten) == 7

    def test_auto_genereer_zet_app_state(self, client: TestClient):
        assert getattr(client.app.state, "week_menu", None) is None
        client.get("/week")
        assert client.app.state.week_menu is not None


class TestFullPageResponse:
    """Browser request retourneert volledige HTML pagina."""

    def test_full_page_heeft_html_wrapper(self, client: TestClient):
        set_week_menu(client, make_full_week_menu())
        response = client.get("/week")

        assert "<html" in response.text
        assert "</html>" in response.text

    def test_full_page_heeft_tailwind(self, client: TestClient):
        set_week_menu(client, make_full_week_menu())
        response = client.get("/week")

        assert "tailwindcss" in response.text.lower() or "tailwind" in response.text

    def test_full_page_heeft_htmx(self, client: TestClient):
        set_week_menu(client, make_full_week_menu())
        response = client.get("/week")

        assert "htmx.org" in response.text


class TestHtmxFragmentResponse:
    """HTMX request retourneert HTML-fragment zonder wrapper."""

    def test_fragment_geen_html_wrapper(self, htmx_client: TestClient):
        set_week_menu(htmx_client, make_full_week_menu())
        response = htmx_client.get("/week")

        assert "<html" not in response.text
        assert "</html>" not in response.text

    def test_fragment_geen_head(self, htmx_client: TestClient):
        set_week_menu(htmx_client, make_full_week_menu())
        response = htmx_client.get("/week")

        assert "<head>" not in response.text

    def test_fragment_bevat_dagkaarten(self, htmx_client: TestClient):
        set_week_menu(htmx_client, make_full_week_menu())
        s = soup(htmx_client.get("/week"))

        dagkaarten = s.select('[data-testid="dagkaart"]')
        assert len(dagkaarten) == 7
