"""Integratietests voor weekmenu laden (Repository → Planner → UI).

Tests de volledige keten van HTTP request → route → template rendering → HTML response
met BeautifulSoup asserties op data-testid attributen.
"""

from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from boodschappenagent.models import Basis, Categorie, Ingredient, Seizoen
from boodschappenagent.models.recipe import Recipe
from boodschappenagent.planner import DagPlanning, WeekMenu


def _make_recipe(id: str, naam: str, categorie: Categorie, basis: Basis) -> Recipe:
    """Helper om een minimaal Recipe object te maken."""
    return Recipe(
        id=id,
        naam=naam,
        categorie=categorie,
        basis=basis,
        seizoenen=[Seizoen.ALLE],
        basis_porties=2,
        ingredienten=[
            Ingredient(naam="test", hoeveelheid=1, eenheid="stuk"),
        ],
    )


RECEPTEN = [
    _make_recipe("kip-curry", "Kip curry", Categorie.GEVOGELTE, Basis.RIJST),
    _make_recipe("bolognese", "Pasta bolognese", Categorie.VLEES, Basis.PASTA),
    _make_recipe("zalm", "Zalm teriyaki", Categorie.VIS, Basis.RIJST),
    _make_recipe("linzensoep", "Rode linzensoep", Categorie.VEGETARISCH, Basis.GEEN),
    _make_recipe("kip-pesto", "Kip pesto pasta", Categorie.GEVOGELTE, Basis.PASTA),
    _make_recipe("vissticks", "Vissticks", Categorie.VIS, Basis.AARDAPPEL),
    _make_recipe("chili", "Chili sin carne", Categorie.VEGETARISCH, Basis.RIJST),
]

WEEK_START = "2026-02-16"  # Week 8


def _full_week_menu(personen: int = 2) -> WeekMenu:
    """Maak een weekmenu met 7 kookdagen."""
    dagen = [
        DagPlanning(dag=i, recept=RECEPTEN[i], personen=personen) for i in range(7)
    ]
    return WeekMenu(week_start=WEEK_START, dagen=dagen)


def _set_week_menu(
    client: TestClient,
    week_menu: WeekMenu,
    hellofresh_dagen: set | None = None,
):
    """Stel weekmenu en hellofresh_dagen in op app.state."""
    client.app.state.week_menu = week_menu
    client.app.state.hellofresh_dagen = hellofresh_dagen or set()


def _soup(response) -> BeautifulSoup:
    return BeautifulSoup(response.text, "html.parser")


class TestVolledigWeekmenuLaden:
    """GET /week met 7 dagen, alle thuis → 7 dagkaarten type recept."""

    def test_zeven_dagkaarten_aanwezig(self, client: TestClient):
        _set_week_menu(client, _full_week_menu())
        response = client.get("/week")
        soup = _soup(response)

        dagkaarten = soup.select('[data-testid="dagkaart"]')
        assert len(dagkaarten) == 7

    def test_alle_dagkaarten_type_recept(self, client: TestClient):
        _set_week_menu(client, _full_week_menu())
        soup = _soup(client.get("/week"))

        dagkaarten = soup.select('[data-testid="dagkaart"][data-type="recept"]')
        assert len(dagkaarten) == 7

    def test_elke_dagkaart_heeft_receptnaam(self, client: TestClient):
        _set_week_menu(client, _full_week_menu())
        soup = _soup(client.get("/week"))

        dagkaarten = soup.select('[data-testid="dagkaart"]')
        for i, kaart in enumerate(dagkaarten):
            assert RECEPTEN[i].naam in kaart.get_text()

    def test_elke_dagkaart_heeft_porties(self, client: TestClient):
        _set_week_menu(client, _full_week_menu(personen=3))
        soup = _soup(client.get("/week"))

        porties_elements = soup.select('[data-testid="porties"]')
        assert len(porties_elements) == 7
        for el in porties_elements:
            assert "3" in el.get_text()

    def test_elke_dagkaart_heeft_categorie_emoji(self, client: TestClient):
        _set_week_menu(client, _full_week_menu())
        soup = _soup(client.get("/week"))

        categorie_elements = soup.select('[data-testid="categorie"]')
        assert len(categorie_elements) == 7
        for el in categorie_elements:
            assert el.get_text().strip() != ""

    def test_dagkaarten_hebben_data_dag_attribuut(self, client: TestClient):
        _set_week_menu(client, _full_week_menu())
        soup = _soup(client.get("/week"))

        dagkaarten = soup.select('[data-testid="dagkaart"]')
        dag_nummers = [kaart["data-dag"] for kaart in dagkaarten]
        assert dag_nummers == ["0", "1", "2", "3", "4", "5", "6"]


class TestNietThuisDagen:
    """GET /week met dag personen=0 → dagkaart type niet-thuis."""

    def test_niet_thuis_dag_type(self, client: TestClient):
        dagen = [
            DagPlanning(dag=i, recept=RECEPTEN[i], personen=2)
            for i in range(7)
            if i != 5
        ]
        dagen.append(DagPlanning(dag=5, recept=None, personen=0))
        dagen.sort(key=lambda d: d.dag)
        menu = WeekMenu(week_start=WEEK_START, dagen=dagen)
        _set_week_menu(client, menu)

        soup = _soup(client.get("/week"))
        niet_thuis = soup.select('[data-testid="dagkaart"][data-type="niet-thuis"]')
        assert len(niet_thuis) == 1
        assert niet_thuis[0]["data-dag"] == "5"

    def test_niet_thuis_dag_zonder_receptnaam(self, client: TestClient):
        dagen = [
            DagPlanning(dag=i, recept=RECEPTEN[i], personen=2)
            for i in range(7)
            if i != 5
        ]
        dagen.append(DagPlanning(dag=5, recept=None, personen=0))
        dagen.sort(key=lambda d: d.dag)
        menu = WeekMenu(week_start=WEEK_START, dagen=dagen)
        _set_week_menu(client, menu)

        soup = _soup(client.get("/week"))
        niet_thuis = soup.select('[data-testid="dagkaart"][data-type="niet-thuis"]')[0]
        for recept in RECEPTEN:
            assert recept.naam not in niet_thuis.get_text()

    def test_overige_dagen_zijn_recept(self, client: TestClient):
        dagen = [
            DagPlanning(dag=i, recept=RECEPTEN[i], personen=2)
            for i in range(7)
            if i != 5
        ]
        dagen.append(DagPlanning(dag=5, recept=None, personen=0))
        dagen.sort(key=lambda d: d.dag)
        menu = WeekMenu(week_start=WEEK_START, dagen=dagen)
        _set_week_menu(client, menu)

        soup = _soup(client.get("/week"))
        recept_kaarten = soup.select('[data-testid="dagkaart"][data-type="recept"]')
        assert len(recept_kaarten) == 6


class TestHelloFreshDag:
    """GET /week met dag in hellofresh_dagen → dagkaart type hellofresh."""

    def test_hellofresh_dag_type(self, client: TestClient):
        menu = _full_week_menu()
        _set_week_menu(client, menu, hellofresh_dagen={2})

        soup = _soup(client.get("/week"))
        hf_kaarten = soup.select('[data-testid="dagkaart"][data-type="hellofresh"]')
        assert len(hf_kaarten) == 1
        assert hf_kaarten[0]["data-dag"] == "2"

    def test_hellofresh_dag_toont_hellofresh_tekst(self, client: TestClient):
        menu = _full_week_menu()
        _set_week_menu(client, menu, hellofresh_dagen={2})

        soup = _soup(client.get("/week"))
        hf_kaart = soup.select('[data-testid="dagkaart"][data-type="hellofresh"]')[0]
        assert "HelloFresh" in hf_kaart.get_text()

    def test_hellofresh_dag_heeft_hf_styling(self, client: TestClient):
        menu = _full_week_menu()
        _set_week_menu(client, menu, hellofresh_dagen={2})

        soup = _soup(client.get("/week"))
        hf_kaart = soup.select('[data-testid="dagkaart"][data-type="hellofresh"]')[0]
        classes = hf_kaart.get("class", [])
        assert any("hf-" in cls for cls in classes)


class TestWeeknummer:
    """GET /week toont correct weeknummer op basis van week_start."""

    def test_weeknummer_zichtbaar(self, client: TestClient):
        _set_week_menu(client, _full_week_menu())
        soup = _soup(client.get("/week"))

        week_nummer = soup.select_one('[data-testid="week-nummer"]')
        assert week_nummer is not None
        assert "8" in week_nummer.get_text()

    def test_weeknummer_tekst_format(self, client: TestClient):
        _set_week_menu(client, _full_week_menu())
        soup = _soup(client.get("/week"))

        week_nummer = soup.select_one('[data-testid="week-nummer"]')
        assert "Week 8" in week_nummer.get_text()


class TestVariatieGeenDubbeleCategorieen:
    """Geen twee opeenvolgende dagen met dezelfde categorie."""

    def test_geen_opeenvolgende_dubbele_categorieen(
        self, client: TestClient, menu_planner
    ):
        """Echte planner genereert menu zonder opeenvolgende dubbele categorieën."""
        from boodschappenagent.models import Seizoen
        from boodschappenagent.planner import DagInput

        dag_inputs = [DagInput(dag=i, personen=2) for i in range(7)]
        week_menu = menu_planner.plan_week(
            week_input=dag_inputs,
            seizoen=Seizoen.ALLE,
            week_start=WEEK_START,
        )
        _set_week_menu(client, week_menu)

        soup = _soup(client.get("/week"))
        categorie_elements = soup.select('[data-testid="categorie"]')
        categorieen = [el.get_text().strip() for el in categorie_elements]

        for i in range(len(categorieen) - 1):
            assert categorieen[i] != categorieen[i + 1], (
                f"Dag {i} en {i + 1} hebben dezelfde categorie: {categorieen[i]}"
            )


class TestLeegMenu:
    """GET /week zonder week_menu → lege staat."""

    def test_geen_dagkaarten_bij_leeg_menu(self, client: TestClient):
        soup = _soup(client.get("/week"))

        dagkaarten = soup.select('[data-testid="dagkaart"]')
        assert len(dagkaarten) == 0

    def test_lege_staat_bericht(self, client: TestClient):
        soup = _soup(client.get("/week"))

        week_content = soup.select_one('[data-testid="week-content"]')
        assert week_content is not None
        assert week_content.get_text().strip() != ""


class TestFullPageResponse:
    """Browser request retourneert volledige HTML pagina."""

    def test_full_page_heeft_html_wrapper(self, client: TestClient):
        _set_week_menu(client, _full_week_menu())
        response = client.get("/week")

        assert "<html" in response.text
        assert "</html>" in response.text

    def test_full_page_heeft_tailwind(self, client: TestClient):
        _set_week_menu(client, _full_week_menu())
        response = client.get("/week")

        assert "tailwindcss" in response.text.lower() or "tailwind" in response.text

    def test_full_page_heeft_htmx(self, client: TestClient):
        _set_week_menu(client, _full_week_menu())
        response = client.get("/week")

        assert "htmx.org" in response.text


class TestHtmxFragmentResponse:
    """HTMX request retourneert HTML-fragment zonder wrapper."""

    def test_fragment_geen_html_wrapper(self, htmx_client: TestClient):
        _set_week_menu(htmx_client, _full_week_menu())
        response = htmx_client.get("/week")

        assert "<html" not in response.text
        assert "</html>" not in response.text

    def test_fragment_geen_head(self, htmx_client: TestClient):
        _set_week_menu(htmx_client, _full_week_menu())
        response = htmx_client.get("/week")

        assert "<head>" not in response.text

    def test_fragment_bevat_dagkaarten(self, htmx_client: TestClient):
        _set_week_menu(htmx_client, _full_week_menu())
        soup = _soup(htmx_client.get("/week"))

        dagkaarten = soup.select('[data-testid="dagkaart"]')
        assert len(dagkaarten) == 7
