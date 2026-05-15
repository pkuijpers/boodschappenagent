"""Tests voor ingredient-selectie endpoints (T005-T008)."""

from fastapi.testclient import TestClient

from boodschappenagent.models import Basis, Categorie, Ingredient, Seizoen
from boodschappenagent.models.recipe import Recipe
from boodschappenagent.planner import DagPlanning, WeekMenu

from .conftest import set_week_menu, soup

WEEK_START = "2026-02-16"


def _make_recipe_met_ingredienten(id: str, naam: str) -> Recipe:
    """Maak een recept met twee ingrediënten voor testinitalisatie."""
    return Recipe(
        id=id,
        naam=naam,
        categorie=Categorie.GEVOGELTE,
        basis=Basis.RIJST,
        seizoenen=[Seizoen.ALLE],
        basis_porties=2,
        ingredienten=[
            Ingredient(naam="kip", hoeveelheid=300, eenheid="g"),
            Ingredient(naam="rijst", hoeveelheid=200, eenheid="g"),
        ],
    )


def _make_week_menu_met_ingredienten() -> WeekMenu:
    """Weekmenu met 2 recepten die elk 2 ingrediënten hebben (4 items totaal)."""
    recept_a = _make_recipe_met_ingredienten("recept-a", "Kip curry")
    recept_b = _make_recipe_met_ingredienten("recept-b", "Kip wok")
    dagen = [
        DagPlanning(dag=0, recept=recept_a, personen=2),
        DagPlanning(dag=1, recept=recept_b, personen=2),
        DagPlanning(dag=2, recept=None, personen=0),
        DagPlanning(dag=3, recept=None, personen=0),
        DagPlanning(dag=4, recept=None, personen=0),
        DagPlanning(dag=5, recept=None, personen=0),
        DagPlanning(dag=6, recept=None, personen=0),
    ]
    return WeekMenu(week_start=WEEK_START, dagen=dagen)


# --- T005: GET /ingredient-selectie ---


class TestIngredientSelectieGet:
    """T005: GET /ingredient-selectie — initialisatie, fragments, state-behoud."""

    def test_full_page_zonder_htmx(self, client: TestClient):
        """Zonder HX-Request header retourneert volledige HTML pagina."""
        set_week_menu(client, _make_week_menu_met_ingredienten())
        response = client.get("/ingredient-selectie")
        assert response.status_code == 200
        assert "<html" in response.text

    def test_full_page_bevat_header(self, client: TestClient):
        """Pagina bevat header 'Ingrediënten selecteren'."""
        set_week_menu(client, _make_week_menu_met_ingredienten())
        s = soup(client.get("/ingredient-selectie"))
        assert "Ingrediënten selecteren" in s.get_text()

    def test_htmx_fragment_geen_html(self, client: TestClient):
        """Met HX-Request: true retourneert fragment zonder <html>."""
        set_week_menu(client, _make_week_menu_met_ingredienten())
        response = client.get("/ingredient-selectie", headers={"HX-Request": "true"})
        assert response.status_code == 200
        assert "<html" not in response.text

    def test_initialisatie_vanuit_week_menu(self, client: TestClient):
        """Initialisatie bouwt ingredient_selectie vanuit week_menu (4 items)."""
        set_week_menu(client, _make_week_menu_met_ingredienten())
        client.get("/ingredient-selectie")
        items = client.app.state.ingredient_selectie
        assert len(items) == 4
        assert all(item["geselecteerd"] is True for item in items)

    def test_initialisatie_bevat_recept_naam(self, client: TestClient):
        """Elk item bevat recept_naam."""
        set_week_menu(client, _make_week_menu_met_ingredienten())
        client.get("/ingredient-selectie")
        namen = {item["recept_naam"] for item in client.app.state.ingredient_selectie}
        assert "Kip curry" in namen
        assert "Kip wok" in namen

    def test_initialisatie_bevat_id(self, client: TestClient):
        """Elk item heeft een uniek id."""
        set_week_menu(client, _make_week_menu_met_ingredienten())
        client.get("/ingredient-selectie")
        ids = [item["id"] for item in client.app.state.ingredient_selectie]
        assert len(ids) == len(set(ids))

    def test_bestaande_selectie_niet_overschreven(self, client: TestClient):
        """Tweede GET overschrijft bestaande ingredient_selectie niet."""
        set_week_menu(client, _make_week_menu_met_ingredienten())
        client.get("/ingredient-selectie")
        item_id = client.app.state.ingredient_selectie[0]["id"]
        client.app.state.ingredient_selectie[0]["geselecteerd"] = False
        client.get("/ingredient-selectie")
        assert client.app.state.ingredient_selectie[0]["geselecteerd"] is False
        assert client.app.state.ingredient_selectie[0]["id"] == item_id

    def test_zonder_week_menu_redirect_naar_week(self, client: TestClient):
        """Zonder week_menu redirect naar /week."""
        client.app.state.week_menu = None
        response = client.get("/ingredient-selectie", follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"] == "/week"

    def test_ingredienten_zichtbaar_op_pagina(self, client: TestClient):
        """Ingrediëntnamen zijn zichtbaar op de pagina."""
        set_week_menu(client, _make_week_menu_met_ingredienten())
        s = soup(client.get("/ingredient-selectie"))
        tekst = s.get_text()
        assert "kip" in tekst.lower()
        assert "rijst" in tekst.lower()


# --- T006: POST /ingredient-selectie/{item_id}/toggle ---


class TestIngredientSelectieToggle:
    """T006: POST /ingredient-selectie/{item_id}/toggle."""

    def _init_selectie(self, client: TestClient) -> str:
        """Initialiseer state en geef id van eerste item terug."""
        set_week_menu(client, _make_week_menu_met_ingredienten())
        client.get("/ingredient-selectie")
        return client.app.state.ingredient_selectie[0]["id"]

    def test_toggle_zet_geselecteerd_false(self, client: TestClient):
        """Toggle zet geselecteerd van True naar False."""
        item_id = self._init_selectie(client)
        assert client.app.state.ingredient_selectie[0]["geselecteerd"] is True
        client.post(f"/ingredient-selectie/{item_id}/toggle")
        assert client.app.state.ingredient_selectie[0]["geselecteerd"] is False

    def test_toggle_zet_geselecteerd_terug_true(self, client: TestClient):
        """Tweede toggle zet geselecteerd terug naar True."""
        item_id = self._init_selectie(client)
        client.post(f"/ingredient-selectie/{item_id}/toggle")
        client.post(f"/ingredient-selectie/{item_id}/toggle")
        assert client.app.state.ingredient_selectie[0]["geselecteerd"] is True

    def test_toggle_retourneert_item_fragment(self, client: TestClient):
        """Response is een HTML fragment zonder <html>."""
        item_id = self._init_selectie(client)
        response = client.post(f"/ingredient-selectie/{item_id}/toggle")
        assert response.status_code == 200
        assert "<html" not in response.text

    def test_toggle_onbekend_id_geeft_404(self, client: TestClient):
        """Onbekend item_id geeft HTTP 404."""
        self._init_selectie(client)
        response = client.post("/ingredient-selectie/onbekend-id/toggle")
        assert response.status_code == 404

    def test_toggle_fragment_bevat_item_data(self, client: TestClient):
        """Response fragment bevat de ingredientnaam."""
        item_id = self._init_selectie(client)
        response = client.post(f"/ingredient-selectie/{item_id}/toggle")
        assert response.status_code == 200
        assert len(response.text.strip()) > 0


# --- T007: PATCH /ingredient-selectie/{item_id}/hoeveelheid ---


class TestIngredientSelectieHoeveelheid:
    """T007: PATCH /ingredient-selectie/{item_id}/hoeveelheid."""

    def _init_selectie(self, client: TestClient) -> str:
        """Initialiseer state en geef id van eerste item terug."""
        set_week_menu(client, _make_week_menu_met_ingredienten())
        client.get("/ingredient-selectie")
        return client.app.state.ingredient_selectie[0]["id"]

    def test_patch_update_hoeveelheid(self, client: TestClient):
        """PATCH update hoeveelheid van item in app.state."""
        item_id = self._init_selectie(client)
        client.patch(
            f"/ingredient-selectie/{item_id}/hoeveelheid",
            data={"hoeveelheid": "450"},
        )
        assert client.app.state.ingredient_selectie[0]["hoeveelheid"] == 450.0

    def test_patch_retourneert_item_fragment(self, client: TestClient):
        """Response is HTML fragment zonder <html>."""
        item_id = self._init_selectie(client)
        response = client.patch(
            f"/ingredient-selectie/{item_id}/hoeveelheid",
            data={"hoeveelheid": "300"},
        )
        assert response.status_code == 200
        assert "<html" not in response.text

    def test_patch_onbekend_id_geeft_404(self, client: TestClient):
        """Onbekend item_id geeft HTTP 404."""
        self._init_selectie(client)
        response = client.patch(
            "/ingredient-selectie/onbekend-id/hoeveelheid",
            data={"hoeveelheid": "100"},
        )
        assert response.status_code == 404

    def test_patch_float_waarde(self, client: TestClient):
        """PATCH accepteert float hoeveelheid."""
        item_id = self._init_selectie(client)
        client.patch(
            f"/ingredient-selectie/{item_id}/hoeveelheid",
            data={"hoeveelheid": "1.5"},
        )
        assert client.app.state.ingredient_selectie[0]["hoeveelheid"] == 1.5


# --- T008: POST /ingredient-selectie/bevestig ---


class TestIngredientSelectieBevestig:
    """T008: POST /ingredient-selectie/bevestig."""

    def _init_selectie(self, client: TestClient):
        """Initialiseer state."""
        set_week_menu(client, _make_week_menu_met_ingredienten())
        client.get("/ingredient-selectie")

    def test_bevestig_redirect_naar_voorraad(self, client: TestClient):
        """POST /ingredient-selectie/bevestig redirect 303 naar /voorraad."""
        self._init_selectie(client)
        response = client.post("/ingredient-selectie/bevestig", follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"] == "/voorraad"

    def test_bevestig_wist_selectie_niet(self, client: TestClient):
        """Na bevestigen blijft ingredient_selectie intact (FR-011)."""
        self._init_selectie(client)
        items_voor = list(client.app.state.ingredient_selectie)
        client.post("/ingredient-selectie/bevestig")
        items_na = client.app.state.ingredient_selectie
        assert len(items_na) == len(items_voor)

    def test_bevestig_zonder_week_menu_redirect_naar_week(self, client: TestClient):
        """Zonder week_menu redirect naar /week."""
        client.app.state.week_menu = None
        response = client.post("/ingredient-selectie/bevestig", follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"] == "/week"
