"""Integratietests voor weekmenu genereren (S3).

S3 uit het testplan: POST /week/genereer genereert een volledig nieuw weekmenu
en behoudt de ingestelde personen-aantallen per dag.
"""

from fastapi.testclient import TestClient

from .conftest import (
    make_full_week_menu,
    set_week_menu,
    soup,
)


class TestGenereerVolledigWeek:
    """S3.1: POST /week/genereer retourneert volledig weekmenu."""

    def test_genereer_retourneert_zeven_dagkaarten(self, client: TestClient):
        """S3.1: Volledige pagina bevat 7 dagkaarten."""
        set_week_menu(client, make_full_week_menu())

        s = soup(client.post("/week/genereer"))

        dagkaarten = s.select('[data-testid="dagkaart"]')
        assert len(dagkaarten) == 7

    def test_genereer_htmx_fragment_geen_html_wrapper(self, htmx_client: TestClient):
        """S3.1 HTMX: Fragment zonder <html> wrapper."""
        set_week_menu(htmx_client, make_full_week_menu())

        response = htmx_client.post("/week/genereer")

        assert "<html" not in response.text
        assert "</html>" not in response.text

    def test_genereer_htmx_fragment_bevat_zeven_dagkaarten(
        self, htmx_client: TestClient
    ):
        """S3.1 HTMX: Fragment bevat 7 dagkaarten."""
        set_week_menu(htmx_client, make_full_week_menu())

        s = soup(htmx_client.post("/week/genereer"))

        dagkaarten = s.select('[data-testid="dagkaart"]')
        assert len(dagkaarten) == 7

    def test_genereer_dagkaarten_hebben_type_recept(self, client: TestClient):
        """S3.1: Alle dagkaarten zijn van type recept (geen niet-thuis/HF)."""
        set_week_menu(client, make_full_week_menu())

        s = soup(client.post("/week/genereer"))

        recept_kaarten = s.select('[data-testid="dagkaart"][data-type="recept"]')
        assert len(recept_kaarten) == 7


class TestGenereerBewaartPersonen:
    """S3.4: Genereer behoudt aangepast aantal personen per dag."""

    def test_genereer_bewaart_vier_personen(self, client: TestClient):
        """S3.4: Na stel-personen-in dag 1 = 4, behoudt genereer 4 personen."""
        set_week_menu(client, make_full_week_menu())
        client.post("/week/dag/1/stel-personen-in", data={"personen": "4"})

        client.post("/week/genereer")

        assert client.app.state.week_menu.dagen[1].personen == 4

    def test_genereer_dag_met_vier_personen_toont_porties(self, client: TestClient):
        """S3.4: Dagkaart dag 1 toont 4 porties na genereer."""
        set_week_menu(client, make_full_week_menu())
        client.post("/week/dag/1/stel-personen-in", data={"personen": "4"})

        s = soup(client.post("/week/genereer"))

        porties = s.select_one(
            '[data-testid="dagkaart"][data-dag="1"] [data-testid="porties"]'
        )
        assert porties is not None
        assert "4" in porties.get_text()

    def test_genereer_bewaart_drie_personen(self, client: TestClient):
        """S3.4: Genereer behoudt ook 3 personen."""
        set_week_menu(client, make_full_week_menu())
        client.post("/week/dag/3/stel-personen-in", data={"personen": "3"})

        client.post("/week/genereer")

        assert client.app.state.week_menu.dagen[3].personen == 3

    def test_genereer_dag_met_aangepaste_personen_heeft_recept(
        self, client: TestClient
    ):
        """S3.4: Dag met 4 personen heeft na genereer nog steeds een recept."""
        set_week_menu(client, make_full_week_menu())
        client.post("/week/dag/1/stel-personen-in", data={"personen": "4"})

        client.post("/week/genereer")

        assert client.app.state.week_menu.dagen[1].recept is not None


class TestHellofreshDefaultDagen:
    """S3.5: Fresh generatie stelt di/wo/do standaard in als HelloFresh."""

    def test_fresh_genereer_zet_hellofresh_op_dinsdag_woensdag_donderdag(
        self, client: TestClient
    ):
        """S3.5.1: Zonder bestaand menu worden dag 1, 2, 3 standaard HF."""
        # Geen set_week_menu — simuleert verse week
        client.post("/week/genereer")

        assert client.app.state.hellofresh_dagen == {1, 2, 3}

    def test_reshuffle_behoudt_bestaande_hellofresh_dagen(self, client: TestClient):
        """S3.5.2: Genereer met bestaand menu behoudt huidige HF-keuzes."""
        set_week_menu(client, make_full_week_menu(), hellofresh_dagen={0, 4})

        client.post("/week/genereer")

        assert client.app.state.hellofresh_dagen == {0, 4}
