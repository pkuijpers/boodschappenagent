"""Integratietests voor boodschappenlijst pagina (S9)."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from boodschappenagent.voorraadbeheer import VoorraadRepository
from boodschappenagent.voorraadbeheer.models import VoorraadItem, VoorraadType

from .conftest import make_full_week_menu, set_week_menu, soup


@pytest.fixture
def client_with_boodschappen(app_with_boodschappen: FastAPI) -> TestClient:
    """TestClient met BoodschappenlijstGenerator en BoodschappenlijstFilter override."""
    return TestClient(app_with_boodschappen)


class TestBoodschappenlijstLaden:
    """S9: Boodschappenlijst laden (WeekMenu → Generator → Filter → UI)."""

    def test_s9_1a_full_page_bevat_html(self, client_with_boodschappen: TestClient):
        """S9.1a: Browser request geeft volledige HTML pagina."""
        set_week_menu(client_with_boodschappen, make_full_week_menu())
        response = client_with_boodschappen.get("/boodschappen")
        assert response.status_code == 200
        assert "<html" in response.text

    def test_s9_1b_htmx_fragment_geen_html(self, client_with_boodschappen: TestClient):
        """S9.1b: HTMX request geeft fragment zonder <html>."""
        set_week_menu(client_with_boodschappen, make_full_week_menu())
        response = client_with_boodschappen.get(
            "/boodschappen", headers={"HX-Request": "true"}
        )
        assert response.status_code == 200
        assert "<html" not in response.text

    def test_s9_1a_full_page_bevat_header_boodschappenlijst(
        self, client_with_boodschappen: TestClient
    ):
        """S9.1a: Volledige pagina bevat header 'Boodschappenlijst'."""
        set_week_menu(client_with_boodschappen, make_full_week_menu())
        s = soup(client_with_boodschappen.get("/boodschappen"))
        assert "Boodschappenlijst" in s.get_text()

    def test_s9_1_sectie_aanwezig(self, client_with_boodschappen: TestClient):
        """S9.1: Boodschappenlijst toont minimaal één sectie."""
        set_week_menu(client_with_boodschappen, make_full_week_menu())
        s = soup(client_with_boodschappen.get("/boodschappen"))
        secties = s.select('[data-testid="boodschappen-sectie"]')
        assert len(secties) >= 1

    def test_s9_8_header_aanwezig(self, client_with_boodschappen: TestClient):
        """S9.8: Header met product telling is aanwezig."""
        set_week_menu(client_with_boodschappen, make_full_week_menu())
        s = soup(client_with_boodschappen.get("/boodschappen"))
        header = s.select_one('[data-testid="boodschappen-header"]')
        assert header is not None

    def test_s9_8_header_toont_weektelling(self, client_with_boodschappen: TestClient):
        """S9.8: Header toont weeknummer en producttelling."""
        set_week_menu(client_with_boodschappen, make_full_week_menu())
        s = soup(client_with_boodschappen.get("/boodschappen"))
        header = s.select_one('[data-testid="boodschappen-header"]')
        assert header is not None
        text = header.get_text()
        assert any(c.isdigit() for c in text)

    def test_s9_9_zonder_weekmenu_redirect(self, client_with_boodschappen: TestClient):
        """S9.9: Zonder weekmenu redirect naar /week."""
        client_with_boodschappen.app.state.week_menu = None
        response = client_with_boodschappen.get("/boodschappen", follow_redirects=False)
        assert response.status_code in (301, 302, 303, 307, 308)
        assert "/week" in response.headers["location"]


class TestBoodschappenlijstLeeg:
    """S9.10: Lege boodschappenlijst state."""

    @pytest.fixture
    def app_alles_op_voorraad(
        self, app_with_boodschappen: FastAPI, voorraad_repository: VoorraadRepository
    ) -> FastAPI:
        """App waarbij het 'test' ingredient op voorraad staat."""
        voorraad_repository.update_item(
            VoorraadItem(
                naam="test",
                type=VoorraadType.HOUDBAAR,
                op_voorraad=True,
                laatst_gecheckt="2026-03-03",
            )
        )
        return app_with_boodschappen

    def test_s9_10_lege_lijst_bericht(self, app_alles_op_voorraad: FastAPI):
        """S9.10: Lege lijst toont 'Niets te bestellen!' bericht."""
        client = TestClient(app_alles_op_voorraad)
        set_week_menu(client, make_full_week_menu())
        s = soup(client.get("/boodschappen"))
        lege_lijst = s.select_one('[data-testid="lege-lijst"]')
        assert lege_lijst is not None
        assert "bestellen" in lege_lijst.get_text().lower()


class TestBoodschappenlijstItems:
    """S9: Items op de boodschappenlijst."""

    def test_s9_items_aanwezig(self, client_with_boodschappen: TestClient):
        """S9: Boodschappenlijst toont items."""
        set_week_menu(client_with_boodschappen, make_full_week_menu())
        s = soup(client_with_boodschappen.get("/boodschappen"))
        items = s.select('[data-testid="boodschapitem"]')
        assert len(items) >= 1

    def test_s9_items_standaard_niet_gecheckt(
        self, client_with_boodschappen: TestClient
    ):
        """S9: Items zijn standaard niet afgevinkt."""
        set_week_menu(client_with_boodschappen, make_full_week_menu())
        s = soup(client_with_boodschappen.get("/boodschappen"))
        items = s.select('[data-testid="boodschapitem"]')
        assert len(items) >= 1
        for item in items:
            assert item.get("data-checked") == "false"

    def test_s9_items_hebben_hoeveelheid(self, client_with_boodschappen: TestClient):
        """S9: Items tonen hoeveelheid."""
        set_week_menu(client_with_boodschappen, make_full_week_menu())
        s = soup(client_with_boodschappen.get("/boodschappen"))
        items = s.select('[data-testid="boodschapitem"]')
        assert len(items) >= 1
        hoeveelheid = items[0].select_one('[data-testid="hoeveelheid"]')
        assert hoeveelheid is not None


class TestBoodschapToggle:
    """S10.1-S10.3, S10.8: Toggle checked status."""

    def test_s10_1_toggle_checked_true(self, client_with_boodschappen: TestClient):
        """S10.1: PATCH met checked=true zet item op afgevinkt."""
        set_week_menu(client_with_boodschappen, make_full_week_menu())
        client_with_boodschappen.get("/boodschappen")
        items = client_with_boodschappen.app.state.boodschappenlijst
        item_id = items[0]["id"]

        response = client_with_boodschappen.patch(
            f"/boodschappen/{item_id}", data={"checked": "true"}
        )
        assert response.status_code == 200
        s = soup(response)
        item = s.select_one('[data-testid="boodschapitem"]')
        assert item is not None
        assert item.get("data-checked") == "true"

    def test_s10_2_toggle_checked_false(self, client_with_boodschappen: TestClient):
        """S10.2: PATCH met checked=false zet item op niet-afgevinkt."""
        set_week_menu(client_with_boodschappen, make_full_week_menu())
        client_with_boodschappen.get("/boodschappen")
        items = client_with_boodschappen.app.state.boodschappenlijst
        item_id = items[0]["id"]

        client_with_boodschappen.patch(
            f"/boodschappen/{item_id}", data={"checked": "true"}
        )
        response = client_with_boodschappen.patch(
            f"/boodschappen/{item_id}", data={"checked": "false"}
        )
        assert response.status_code == 200
        s = soup(response)
        item = s.select_one('[data-testid="boodschapitem"]')
        assert item is not None
        assert item.get("data-checked") == "false"

    def test_s10_3_htmx_swap_enkel_item(self, client_with_boodschappen: TestClient):
        """S10.3: Response bevat precies 1 boodschapitem."""
        set_week_menu(client_with_boodschappen, make_full_week_menu())
        client_with_boodschappen.get("/boodschappen")
        items = client_with_boodschappen.app.state.boodschappenlijst
        item_id = items[0]["id"]

        response = client_with_boodschappen.patch(
            f"/boodschappen/{item_id}", data={"checked": "true"}
        )
        assert response.status_code == 200
        s = soup(response)
        boodschapitems = s.select('[data-testid="boodschapitem"]')
        assert len(boodschapitems) == 1

    def test_s10_8_onbekend_item_404(self, client_with_boodschappen: TestClient):
        """S10.8: PATCH op onbekend item geeft 404."""
        set_week_menu(client_with_boodschappen, make_full_week_menu())
        client_with_boodschappen.get("/boodschappen")

        response = client_with_boodschappen.patch(
            "/boodschappen/onbekend-id", data={"checked": "true"}
        )
        assert response.status_code == 404


class TestBoodschapVerwijderen:
    """S10.4, S10.9: Verwijder item."""

    def test_s10_4_verwijder_item_status_200(
        self, client_with_boodschappen: TestClient
    ):
        """S10.4: DELETE geeft 200."""
        set_week_menu(client_with_boodschappen, make_full_week_menu())
        client_with_boodschappen.get("/boodschappen")
        items = client_with_boodschappen.app.state.boodschappenlijst
        item_id = items[0]["id"]

        response = client_with_boodschappen.delete(f"/boodschappen/{item_id}")
        assert response.status_code == 200

    def test_s10_4_verwijder_item_uit_state(self, client_with_boodschappen: TestClient):
        """S10.4: Item wordt verwijderd uit app state."""
        set_week_menu(client_with_boodschappen, make_full_week_menu())
        client_with_boodschappen.get("/boodschappen")
        items = client_with_boodschappen.app.state.boodschappenlijst
        item_id = items[0]["id"]
        count_before = len(items)

        client_with_boodschappen.delete(f"/boodschappen/{item_id}")

        remaining = client_with_boodschappen.app.state.boodschappenlijst
        assert len(remaining) == count_before - 1

    def test_s10_4_onbekend_item_404(self, client_with_boodschappen: TestClient):
        """S10.8: DELETE op onbekend item geeft 404."""
        set_week_menu(client_with_boodschappen, make_full_week_menu())
        client_with_boodschappen.get("/boodschappen")

        response = client_with_boodschappen.delete("/boodschappen/onbekend-id")
        assert response.status_code == 404

    def test_s10_9_header_oob_na_verwijdering(
        self, client_with_boodschappen: TestClient
    ):
        """S10.9: DELETE response bevat OOB header met bijgewerkte producttelling."""
        set_week_menu(client_with_boodschappen, make_full_week_menu())
        client_with_boodschappen.get("/boodschappen")
        items = client_with_boodschappen.app.state.boodschappenlijst
        item_id = items[0]["id"]

        response = client_with_boodschappen.delete(f"/boodschappen/{item_id}")
        assert response.status_code == 200
        s = soup(response)
        header = s.select_one('[data-testid="boodschappen-header"]')
        assert header is not None


class TestBoodschapHandmatigToevoegen:
    """S10.5-S10.6, S10.10: Handmatig product toevoegen."""

    def test_s10_5_handmatig_toevoegen(self, client_with_boodschappen: TestClient):
        """S10.5: POST toevoegen voegt nieuw boodschapitem toe."""
        set_week_menu(client_with_boodschappen, make_full_week_menu())
        client_with_boodschappen.get("/boodschappen")

        response = client_with_boodschappen.post(
            "/boodschappen/toevoegen",
            data={"naam": "bananen", "hoeveelheid": "6", "eenheid": "stuks"},
        )
        assert response.status_code == 200
        s = soup(response)
        item = s.select_one('[data-testid="boodschapitem"][data-item="bananen"]')
        assert item is not None

    def test_s10_6_toevoegen_zonder_naam_422(
        self, client_with_boodschappen: TestClient
    ):
        """S10.6: POST toevoegen zonder naam geeft 422."""
        set_week_menu(client_with_boodschappen, make_full_week_menu())
        client_with_boodschappen.get("/boodschappen")

        response = client_with_boodschappen.post(
            "/boodschappen/toevoegen",
            data={"naam": "", "hoeveelheid": "6", "eenheid": "stuks"},
        )
        assert response.status_code == 422

    def test_s10_10_header_oob_na_toevoegen(self, client_with_boodschappen: TestClient):
        """S10.10: POST toevoegen response bevat OOB header met bijgewerkte count."""
        set_week_menu(client_with_boodschappen, make_full_week_menu())
        client_with_boodschappen.get("/boodschappen")

        response = client_with_boodschappen.post(
            "/boodschappen/toevoegen",
            data={"naam": "bananen", "hoeveelheid": "6", "eenheid": "stuks"},
        )
        assert response.status_code == 200
        s = soup(response)
        header = s.select_one('[data-testid="boodschappen-header"]')
        assert header is not None


class TestBoodschapHoeveelheidAanpassen:
    """S10.7: Hoeveelheid aanpassen."""

    def test_s10_7_hoeveelheid_aanpassen(self, client_with_boodschappen: TestClient):
        """S10.7: PATCH hoeveelheid past hoeveelheid aan en toont in response."""
        set_week_menu(client_with_boodschappen, make_full_week_menu())
        client_with_boodschappen.get("/boodschappen")
        items = client_with_boodschappen.app.state.boodschappenlijst
        item_id = items[0]["id"]

        response = client_with_boodschappen.patch(
            f"/boodschappen/{item_id}/hoeveelheid",
            data={"hoeveelheid": "8"},
        )
        assert response.status_code == 200
        s = soup(response)
        hoeveelheid = s.select_one('[data-testid="hoeveelheid"]')
        assert hoeveelheid is not None
        assert hoeveelheid.get("value") == "8"

    def test_s10_7_hoeveelheid_opgeslagen_in_state(
        self, client_with_boodschappen: TestClient
    ):
        """S10.7: Hoeveelheid wordt bijgewerkt in app state."""
        set_week_menu(client_with_boodschappen, make_full_week_menu())
        client_with_boodschappen.get("/boodschappen")
        items = client_with_boodschappen.app.state.boodschappenlijst
        item_id = items[0]["id"]

        client_with_boodschappen.patch(
            f"/boodschappen/{item_id}/hoeveelheid",
            data={"hoeveelheid": "8"},
        )
        updated = next(
            i
            for i in client_with_boodschappen.app.state.boodschappenlijst
            if i["id"] == item_id
        )
        assert updated["hoeveelheid"] == 8

    def test_s10_7_onbekend_item_404(self, client_with_boodschappen: TestClient):
        """S10.7: PATCH hoeveelheid op onbekend item geeft 404."""
        set_week_menu(client_with_boodschappen, make_full_week_menu())
        client_with_boodschappen.get("/boodschappen")

        response = client_with_boodschappen.patch(
            "/boodschappen/onbekend-id/hoeveelheid",
            data={"hoeveelheid": "8"},
        )
        assert response.status_code == 404


class TestRecepteContextItemDict:
    """Item-dict velden voor recept-context (eerste_recept + extra_aantal)."""

    def test_gegenereerd_item_heeft_eerste_recept(
        self, client_with_boodschappen: TestClient
    ):
        """Gegenereerd item heeft eerste_recept uit BoodschappenRegel.recepten."""
        set_week_menu(client_with_boodschappen, make_full_week_menu())
        client_with_boodschappen.get("/boodschappen")
        items = client_with_boodschappen.app.state.boodschappenlijst
        assert len(items) >= 1
        # 7 recepten met identieke ingredient "test" → 1 regel met 7 recepten,
        # eerste = "Kip curry" (RECEPTEN[0]), extra = 6
        item = items[0]
        assert item["eerste_recept"] == "Kip curry"
        assert item["extra_aantal"] == 6

    def test_handmatig_item_heeft_geen_eerste_recept(
        self, client_with_boodschappen: TestClient
    ):
        """Handmatig toegevoegd item heeft eerste_recept=None, extra_aantal=0."""
        set_week_menu(client_with_boodschappen, make_full_week_menu())
        client_with_boodschappen.get("/boodschappen")
        client_with_boodschappen.post(
            "/boodschappen/toevoegen",
            data={"naam": "bananen", "hoeveelheid": "6", "eenheid": "stuks"},
        )
        items = client_with_boodschappen.app.state.boodschappenlijst
        handmatig = next(i for i in items if i["naam"] == "bananen")
        assert handmatig["eerste_recept"] is None
        assert handmatig["extra_aantal"] == 0
