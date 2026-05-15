"""Tests voor match-review routes (US1, US2, US3)."""

from unittest.mock import MagicMock
from uuid import uuid4

from fastapi.testclient import TestClient

from .conftest import soup


def _make_product(
    article_id: int = 123456, naam: str = "AH Volle melk 1L", prijs: float = 1.09
):
    from boodschappenagent.ah.models import Product

    return Product(
        id=article_id,
        title=naam,
        brand="AH",
        size="1L",
        price=prijs,
        category="Zuivel",
        is_orderable=True,
    )


def _make_match_review_item(
    naam: str = "melk",
    product=None,
    bron: str = "zoekopdracht",
    gecorrigeerd: bool = False,
    aantal: int = 1,
):
    from boodschappenagent.ah.preferences import MatchReviewItem

    if product is None:
        product = _make_product()

    return MatchReviewItem(
        id=str(uuid4()),
        naam=naam,
        hoeveelheid=1.0,
        eenheid="liter",
        product=product,
        bron=bron,
        gecorrigeerd=gecorrigeerd,
        aantal=aantal,
    )


def _setup_match_review_state(app, items=None):
    """Zet match_review_items op app.state."""
    if items is None:
        items = [_make_match_review_item("melk"), _make_match_review_item("pasta")]
    app.state.match_review_items = items
    return items


# ── T007: POST /boodschappen/verstuur-naar-ah (gewijzigd gedrag) ───────────────


class TestVerstuurNaarAHNieuwGedrag:
    """T007: POST /boodschappen/verstuur-naar-ah converteert naar MatchReviewItems en redirectt."""  # noqa: E501

    def test_redirect_naar_match_review_na_matching(
        self,
        app_with_ah,
        mock_token_manager,
        mock_ah_integratie,
        setup_boodschappenlijst,  # noqa: ARG002
    ):
        """Succesvolle matching → 303 redirect naar /boodschappen/match-review."""
        from boodschappenagent.ah.integration import ProductMatch

        mock_token_manager.is_authenticated.return_value = True
        mock_ah_integratie.zoek_producten.return_value = [
            ProductMatch(
                regel=type(
                    "R",
                    (),
                    {"naam": f"product-{i}", "hoeveelheid": 1.0, "eenheid": "stuk"},
                )(),
                product=_make_product(article_id=i + 1, naam=f"Product {i}"),
                bron="zoekopdracht",
                aantal=1,
            )
            for i in range(3)
        ]

        client = TestClient(app_with_ah, follow_redirects=False)
        response = client.post("/boodschappen/verstuur-naar-ah")

        assert response.status_code == 303
        assert response.headers["location"] == "/boodschappen/match-review"

    def test_match_review_items_opgeslagen_in_state(
        self,
        app_with_ah,
        mock_token_manager,
        mock_ah_integratie,
        setup_boodschappenlijst,  # noqa: ARG002
    ):
        """Na matching zijn MatchReviewItems aanwezig in app.state."""
        from boodschappenagent.ah.integration import ProductMatch

        mock_token_manager.is_authenticated.return_value = True
        mock_ah_integratie.zoek_producten.return_value = [
            ProductMatch(
                regel=type(
                    "R", (), {"naam": "melk", "hoeveelheid": 1.0, "eenheid": "liter"}
                )(),
                product=_make_product(),
                bron="zoekopdracht",
                aantal=1,
            )
        ]

        client = TestClient(app_with_ah, follow_redirects=False)
        client.post("/boodschappen/verstuur-naar-ah")

        items = getattr(app_with_ah.state, "match_review_items", None)
        assert items is not None
        assert len(items) == 1
        assert items[0].naam == "melk"

    def test_match_review_items_bevatten_uuid(
        self,
        app_with_ah,
        mock_token_manager,
        mock_ah_integratie,
        setup_boodschappenlijst,  # noqa: ARG002
    ):
        """Elk MatchReviewItem heeft een unieke UUID als id."""
        from boodschappenagent.ah.integration import ProductMatch

        mock_token_manager.is_authenticated.return_value = True
        mock_ah_integratie.zoek_producten.return_value = [
            ProductMatch(
                regel=type(
                    "R", (), {"naam": "melk", "hoeveelheid": 1.0, "eenheid": "liter"}
                )(),
                product=_make_product(),
                bron="zoekopdracht",
                aantal=1,
            ),
            ProductMatch(
                regel=type(
                    "R", (), {"naam": "pasta", "hoeveelheid": 500.0, "eenheid": "gram"}
                )(),
                product=_make_product(article_id=999),
                bron="zoekopdracht",
                aantal=1,
            ),
        ]

        client = TestClient(app_with_ah, follow_redirects=False)
        client.post("/boodschappen/verstuur-naar-ah")

        items = app_with_ah.state.match_review_items
        ids = [item.id for item in items]
        assert len(set(ids)) == 2  # Alle UUIDs zijn uniek

    def test_niet_ingelogd_redirect_login(self, app_with_ah, mock_token_manager):
        """Niet ingelogd → 303 redirect naar /ah/login."""
        mock_token_manager.is_authenticated.return_value = False
        client = TestClient(app_with_ah, follow_redirects=False)
        response = client.post("/boodschappen/verstuur-naar-ah")

        assert response.status_code == 303
        assert response.headers["location"] == "/ah/login"

    def test_geen_boodschappenlijst_redirect_week(
        self, app_with_ah, mock_token_manager
    ):
        """Geen boodschappenlijst in state → 303 redirect naar /week."""
        mock_token_manager.is_authenticated.return_value = True
        app_with_ah.state.boodschappenlijst_model = None
        client = TestClient(app_with_ah, follow_redirects=False)
        response = client.post("/boodschappen/verstuur-naar-ah")

        assert response.status_code == 303
        assert response.headers["location"] == "/week"

    def test_api_fout_toont_foutpagina(
        self,
        app_with_ah,
        mock_token_manager,
        mock_ah_integratie,
        setup_boodschappenlijst,  # noqa: ARG002
    ):
        """AH API fout → foutpagina (geen redirect naar match-review)."""
        mock_token_manager.is_authenticated.return_value = True
        mock_ah_integratie.zoek_producten.side_effect = Exception("AH API error")

        client = TestClient(app_with_ah)
        response = client.post("/boodschappen/verstuur-naar-ah")

        assert response.status_code == 200
        html = soup(response)
        assert html.select_one('[data-testid="ah-api-error"]') is not None

    def test_zoek_producten_aangeroepen_niet_sync_naar_lijst(
        self,
        app_with_ah,
        mock_token_manager,
        mock_ah_integratie,
        setup_boodschappenlijst,  # noqa: ARG002
    ):
        """zoek_producten() wordt aangeroepen; sync_naar_lijst() niet meer."""
        from boodschappenagent.ah.integration import ProductMatch

        mock_token_manager.is_authenticated.return_value = True
        mock_ah_integratie.zoek_producten.return_value = [
            ProductMatch(
                regel=type(
                    "R", (), {"naam": "melk", "hoeveelheid": 1.0, "eenheid": "liter"}
                )(),
                product=_make_product(),
                bron="zoekopdracht",
                aantal=1,
            )
        ]

        client = TestClient(app_with_ah, follow_redirects=False)
        client.post("/boodschappen/verstuur-naar-ah")

        mock_ah_integratie.zoek_producten.assert_called_once()
        mock_ah_integratie.sync_naar_lijst.assert_not_called()


# ── T008: GET /boodschappen/match-review ──────────────────────────────────────


class TestMatchReviewPagina:
    """T008: GET /boodschappen/match-review toont overzicht van gematche items."""

    def test_pagina_laadt_met_items(self, app_with_ah, mock_token_manager):
        """GET /boodschappen/match-review → 200 met gematche items."""
        mock_token_manager.is_authenticated.return_value = True
        _setup_match_review_state(app_with_ah)

        client = TestClient(app_with_ah)
        response = client.get("/boodschappen/match-review")

        assert response.status_code == 200

    def test_pagina_toont_alle_items(self, app_with_ah, mock_token_manager):
        """Match-review pagina toont alle MatchReviewItems."""
        mock_token_manager.is_authenticated.return_value = True
        items = [
            _make_match_review_item("melk"),
            _make_match_review_item("pasta"),
            _make_match_review_item("oregano"),
        ]
        _setup_match_review_state(app_with_ah, items)

        client = TestClient(app_with_ah)
        response = client.get("/boodschappen/match-review")

        html = soup(response)
        assert html.select_one('[data-testid="match-review"]') is not None

    def test_redirect_naar_boodschappen_als_state_leeg(
        self, app_with_ah, mock_token_manager
    ):
        """Geen items in state → 303 redirect naar /boodschappen."""
        mock_token_manager.is_authenticated.return_value = True
        app_with_ah.state.match_review_items = []

        client = TestClient(app_with_ah, follow_redirects=False)
        response = client.get("/boodschappen/match-review")

        assert response.status_code == 303
        assert response.headers["location"] == "/boodschappen"

    def test_redirect_naar_boodschappen_als_state_none(
        self, app_with_ah, mock_token_manager
    ):
        """State.match_review_items = None → 303 redirect naar /boodschappen."""
        mock_token_manager.is_authenticated.return_value = True
        app_with_ah.state.match_review_items = None

        client = TestClient(app_with_ah, follow_redirects=False)
        response = client.get("/boodschappen/match-review")

        assert response.status_code == 303
        assert response.headers["location"] == "/boodschappen"

    def test_confirm_button_aanwezig(self, app_with_ah, mock_token_manager):
        """Pagina bevat bevestig-knop (#bevestig-btn)."""
        mock_token_manager.is_authenticated.return_value = True
        _setup_match_review_state(app_with_ah)

        client = TestClient(app_with_ah)
        response = client.get("/boodschappen/match-review")

        html = soup(response)
        assert html.select_one("#bevestig-btn") is not None

    def test_confirm_button_disabled_bij_geen_match(
        self, app_with_ah, mock_token_manager
    ):
        """Bevestig-knop is disabled als een item geen product heeft."""
        from boodschappenagent.ah.preferences import MatchReviewItem

        mock_token_manager.is_authenticated.return_value = True
        items = [
            _make_match_review_item("melk"),
            MatchReviewItem(
                id=str(uuid4()),
                naam="quinoa",
                hoeveelheid=200.0,
                eenheid="gram",
                product=None,
                bron="niet_gevonden",
                gecorrigeerd=False,
                aantal=1,
            ),
        ]
        _setup_match_review_state(app_with_ah, items)

        client = TestClient(app_with_ah)
        response = client.get("/boodschappen/match-review")

        html = soup(response)
        btn = html.select_one("#bevestig-btn")
        assert btn is not None
        assert btn.has_attr("disabled")

    def test_confirm_button_actief_als_alles_gevonden(
        self, app_with_ah, mock_token_manager
    ):
        """Bevestig-knop is actief (niet disabled) als alle items een product hebben."""
        mock_token_manager.is_authenticated.return_value = True
        items = [_make_match_review_item("melk"), _make_match_review_item("pasta")]
        _setup_match_review_state(app_with_ah, items)

        client = TestClient(app_with_ah)
        response = client.get("/boodschappen/match-review")

        html = soup(response)
        btn = html.select_one("#bevestig-btn")
        assert btn is not None
        assert not btn.has_attr("disabled")


# ── T009: POST /boodschappen/bevestig-matches ──────────────────────────────────


class TestBevestigMatches:
    """T009: POST /boodschappen/bevestig-matches maakt AH-lijst en slaat voorkeuren op."""  # noqa: E501

    def test_redirect_naar_ah_bevestiging(
        self,
        app_with_ah,
        mock_token_manager,
        mock_ah_integratie,
    ):
        """Succes → 303 redirect (naar ah-bevestiging of gerelateerde pagina)."""
        mock_token_manager.is_authenticated.return_value = True
        mock_ah_integratie.create_list = MagicMock(return_value="list-123")
        mock_ah_integratie.add_products_to_list = MagicMock()
        _setup_match_review_state(app_with_ah)

        client = TestClient(app_with_ah, follow_redirects=False)
        response = client.post("/boodschappen/bevestig-matches")

        assert response.status_code == 303

    def test_state_gewist_na_bevestiging(
        self,
        app_with_ah,
        mock_token_manager,
        mock_ah_integratie,
    ):
        """match_review_items wordt geleegd na succesvolle bevestiging."""
        mock_token_manager.is_authenticated.return_value = True
        mock_ah_integratie.create_list = MagicMock(return_value="list-123")
        mock_ah_integratie.add_products_to_list = MagicMock()
        _setup_match_review_state(app_with_ah)

        client = TestClient(app_with_ah, follow_redirects=False)
        client.post("/boodschappen/bevestig-matches")

        items = getattr(app_with_ah.state, "match_review_items", None)
        assert not items  # Leeg of None

    def test_400_als_item_zonder_product(
        self,
        app_with_ah,
        mock_token_manager,
    ):
        """400 als een MatchReviewItem product=None heeft."""
        from boodschappenagent.ah.preferences import MatchReviewItem

        mock_token_manager.is_authenticated.return_value = True
        items = [
            _make_match_review_item("melk"),
            MatchReviewItem(
                id=str(uuid4()),
                naam="quinoa",
                hoeveelheid=200.0,
                eenheid="gram",
                product=None,
                bron="niet_gevonden",
                gecorrigeerd=False,
                aantal=1,
            ),
        ]
        _setup_match_review_state(app_with_ah, items)

        client = TestClient(app_with_ah)
        response = client.post("/boodschappen/bevestig-matches")

        assert response.status_code == 400

    def test_redirect_naar_login_als_niet_ingelogd(
        self,
        app_with_ah,
        mock_token_manager,
    ):
        """Niet ingelogd → 303 redirect naar /ah/login."""
        mock_token_manager.is_authenticated.return_value = False
        _setup_match_review_state(app_with_ah)

        client = TestClient(app_with_ah, follow_redirects=False)
        response = client.post("/boodschappen/bevestig-matches")

        assert response.status_code == 303
        assert response.headers["location"] == "/ah/login"

    def test_create_list_aangeroepen(
        self,
        app_with_ah,
        mock_token_manager,
        mock_ah_integratie,
    ):
        """create_list() wordt aangeroepen bij bevestiging."""
        mock_token_manager.is_authenticated.return_value = True
        mock_ah_integratie.create_list = MagicMock(return_value="list-123")
        mock_ah_integratie.add_products_to_list = MagicMock()
        _setup_match_review_state(app_with_ah)

        client = TestClient(app_with_ah, follow_redirects=False)
        client.post("/boodschappen/bevestig-matches")

        mock_ah_integratie.create_list.assert_called_once()

    def test_add_products_to_list_aangeroepen(
        self,
        app_with_ah,
        mock_token_manager,
        mock_ah_integratie,
    ):
        """add_products_to_list() wordt aangeroepen met de juiste article-id's."""
        mock_token_manager.is_authenticated.return_value = True
        mock_ah_integratie.create_list = MagicMock(return_value="list-123")
        mock_ah_integratie.add_products_to_list = MagicMock()

        product = _make_product(article_id=555)
        from boodschappenagent.ah.preferences import MatchReviewItem

        items = [
            MatchReviewItem(
                id=str(uuid4()),
                naam="melk",
                hoeveelheid=1.0,
                eenheid="liter",
                product=product,
                bron="zoekopdracht",
                gecorrigeerd=False,
                aantal=2,
            )
        ]
        _setup_match_review_state(app_with_ah, items)

        client = TestClient(app_with_ah, follow_redirects=False)
        client.post("/boodschappen/bevestig-matches")

        mock_ah_integratie.add_products_to_list.assert_called_once_with(
            "list-123", [(555, 2)]
        )


# ── T015: GET /boodschappen/zoek-product (US2) ────────────────────────────────


class TestZoekProduct:
    """T015: GET /boodschappen/zoek-product retourneert zoekresultaten fragment."""

    def test_geeft_fragment_terug_bij_valide_item_id(
        self, app_with_ah, mock_token_manager, mock_ah_integratie
    ):
        """Valide item_id en zoekterm → 200 met HTML fragment."""
        mock_token_manager.is_authenticated.return_value = True
        mock_ah_integratie._client.search_products.return_value = [
            _make_product(article_id=1, naam="AH Melk 1L"),
        ]
        items = [_make_match_review_item("melk")]
        item_id = items[0].id
        _setup_match_review_state(app_with_ah, items)

        client = TestClient(app_with_ah)
        response = client.get(f"/boodschappen/zoek-product?q=melk&item_id={item_id}")

        assert response.status_code == 200

    def test_404_voor_onbekende_item_id(self, app_with_ah, mock_token_manager):
        """Onbekende item_id → 404."""
        mock_token_manager.is_authenticated.return_value = True
        _setup_match_review_state(app_with_ah)

        client = TestClient(app_with_ah)
        response = client.get("/boodschappen/zoek-product?q=melk&item_id=niet-bestaand")

        assert response.status_code == 404

    def test_lege_resultaten_bij_geen_resultaten(
        self, app_with_ah, mock_token_manager, mock_ah_integratie
    ):
        """Geen zoekresultaten → fragment met lege-staat bericht."""
        mock_token_manager.is_authenticated.return_value = True
        mock_ah_integratie._client.search_products.return_value = []
        items = [_make_match_review_item("quinoa")]
        item_id = items[0].id
        _setup_match_review_state(app_with_ah, items)

        client = TestClient(app_with_ah)
        response = client.get(f"/boodschappen/zoek-product?q=xyzabc&item_id={item_id}")

        assert response.status_code == 200
        html = soup(response)
        assert html.select_one('[data-testid="geen-resultaten"]') is not None

    def test_maximaal_10_resultaten(
        self, app_with_ah, mock_token_manager, mock_ah_integratie
    ):
        """Maximaal 10 producten worden teruggegeven."""
        mock_token_manager.is_authenticated.return_value = True
        mock_ah_integratie._client.search_products.return_value = [
            _make_product(article_id=i, naam=f"Product {i}") for i in range(15)
        ]
        items = [_make_match_review_item("melk")]
        item_id = items[0].id
        _setup_match_review_state(app_with_ah, items)

        client = TestClient(app_with_ah)
        response = client.get(f"/boodschappen/zoek-product?q=melk&item_id={item_id}")

        assert response.status_code == 200
        html = soup(response)
        kies_buttons = html.find_all("button", string=lambda t: t and "Kies" in t)
        assert len(kies_buttons) <= 10


# ── T016: POST /boodschappen/kies-product (US2) ───────────────────────────────


class TestKiesProduct:
    """T016: POST /boodschappen/kies-product werkt item bij en retourneert OOB fragment."""  # noqa: E501

    def test_werkt_item_bij_met_gekozen_product(self, app_with_ah, mock_token_manager):
        """Geldig item_id + article_id + product-velden → item bijgewerkt in state."""
        mock_token_manager.is_authenticated.return_value = True

        items = [_make_match_review_item("melk")]
        item_id = items[0].id
        _setup_match_review_state(app_with_ah, items)

        client = TestClient(app_with_ah)
        response = client.post(
            "/boodschappen/kies-product",
            data={
                "item_id": item_id,
                "article_id": 999,
                "title": "AH Halfvolle melk 1L",
                "brand": "AH",
                "size": "1L",
                "price": "0.99",
                "category": "Zuivel",
            },
        )

        assert response.status_code == 200
        updated = next(
            i for i in app_with_ah.state.match_review_items if i.id == item_id
        )
        assert updated.product.id == 999
        assert updated.gecorrigeerd is True
        assert updated.bron == "zoekopdracht"

    def test_404_voor_onbekende_item_id(self, app_with_ah, mock_token_manager):
        """Onbekende item_id → 404."""
        mock_token_manager.is_authenticated.return_value = True
        _setup_match_review_state(app_with_ah)

        client = TestClient(app_with_ah)
        response = client.post(
            "/boodschappen/kies-product",
            data={"item_id": "niet-bestaand", "article_id": 123, "title": "Test"},
        )

        assert response.status_code == 404

    def test_400_voor_ongeldig_article_id(self, app_with_ah, mock_token_manager):
        """article_id <= 0 → 400."""
        mock_token_manager.is_authenticated.return_value = True
        items = [_make_match_review_item("melk")]
        item_id = items[0].id
        _setup_match_review_state(app_with_ah, items)

        client = TestClient(app_with_ah)
        response = client.post(
            "/boodschappen/kies-product",
            data={"item_id": item_id, "article_id": 0, "title": "Test"},
        )

        assert response.status_code == 400

    def test_retourneert_oob_card_update(self, app_with_ah, mock_token_manager):
        """Respons bevat bijgewerkte card HTML voor HTMX OOB swap."""
        mock_token_manager.is_authenticated.return_value = True

        items = [_make_match_review_item("pasta")]
        item_id = items[0].id
        _setup_match_review_state(app_with_ah, items)

        client = TestClient(app_with_ah)
        response = client.post(
            "/boodschappen/kies-product",
            data={
                "item_id": item_id,
                "article_id": 777,
                "title": "AH Pasta 500g",
                "brand": "AH",
                "size": "500g",
                "price": "1.49",
                "category": "Pasta",
            },
        )

        assert response.status_code == 200
        assert f"item-{item_id}" in response.text

    def test_product_gekozen_via_form_data_zonder_api_call(
        self, app_with_ah, mock_token_manager, mock_ah_integratie
    ):
        """Reproduceert productie-bug: search_products("999") geeft in productie
        nooit een product met id 999 terug. Product data moet uit form komen,
        niet via een nieuwe AH API-call."""
        mock_token_manager.is_authenticated.return_value = True
        mock_ah_integratie._client.search_products.return_value = []

        items = [_make_match_review_item("melk")]
        item_id = items[0].id
        _setup_match_review_state(app_with_ah, items)

        client = TestClient(app_with_ah)
        response = client.post(
            "/boodschappen/kies-product",
            data={
                "item_id": item_id,
                "article_id": 999,
                "title": "AH Halfvolle melk 1L",
                "brand": "AH",
                "size": "1 liter",
                "price": "0.99",
                "category": "Zuivel",
            },
        )

        assert response.status_code == 200
        updated = next(
            i for i in app_with_ah.state.match_review_items if i.id == item_id
        )
        assert updated.product.id == 999
        assert updated.product.title == "AH Halfvolle melk 1L"
        assert updated.gecorrigeerd is True
        mock_ah_integratie._client.search_products.assert_not_called()


# ── T023: Voorkeur opslaan bij bevestiging (US3) ──────────────────────────────


class TestBevestigMatchesVoorkeuren:
    """T023: Gecorrigeerde items worden opgeslagen als voorkeur bij bevestiging."""

    def test_gecorrigeerd_item_wordt_opgeslagen(
        self,
        app_with_ah,
        mock_token_manager,
        mock_ah_integratie,
        mock_match_voorkeuren_repository,
    ):
        """Item met gecorrigeerd=True → MatchVoorkeurenRepository.save() aangeroepen."""
        mock_token_manager.is_authenticated.return_value = True
        mock_ah_integratie.create_list.return_value = "list-123"

        product = _make_product(article_id=555)
        from boodschappenagent.ah.preferences import MatchReviewItem

        items = [
            MatchReviewItem(
                id=str(uuid4()),
                naam="melk",
                hoeveelheid=1.0,
                eenheid="liter",
                product=product,
                bron="zoekopdracht",
                gecorrigeerd=True,
                aantal=1,
            )
        ]
        _setup_match_review_state(app_with_ah, items)

        client = TestClient(app_with_ah, follow_redirects=False)
        client.post("/boodschappen/bevestig-matches")

        mock_match_voorkeuren_repository.save.assert_called_once()

    def test_niet_gecorrigeerd_item_wordt_niet_opgeslagen(
        self,
        app_with_ah,
        mock_token_manager,
        mock_ah_integratie,
        mock_match_voorkeuren_repository,
    ):
        """Item met gecorrigeerd=False → MatchVoorkeurenRepository.save() NIET aangeroepen."""  # noqa: E501
        mock_token_manager.is_authenticated.return_value = True
        mock_ah_integratie.create_list.return_value = "list-123"

        product = _make_product(article_id=555)
        from boodschappenagent.ah.preferences import MatchReviewItem

        items = [
            MatchReviewItem(
                id=str(uuid4()),
                naam="melk",
                hoeveelheid=1.0,
                eenheid="liter",
                product=product,
                bron="voorkeur",
                gecorrigeerd=False,
                aantal=1,
            )
        ]
        _setup_match_review_state(app_with_ah, items)

        client = TestClient(app_with_ah, follow_redirects=False)
        client.post("/boodschappen/bevestig-matches")

        mock_match_voorkeuren_repository.save.assert_not_called()
