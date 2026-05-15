"""
Unit tests for AH Integration.

Run with: uv run pytest tests/test_ah_integration.py -v
"""

from unittest.mock import Mock

import pytest

from boodschappenagent.ah.auth import AHTokenManager
from boodschappenagent.ah.client import AHClient
from boodschappenagent.ah.integration import AHIntegratie, ProductMatch, SyncResultaat
from boodschappenagent.ah.models import FavoriteList, Product
from boodschappenagent.boodschappenlijst.models import (
    Boodschappenlijst,
    BoodschappenRegel,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def melk_regel():
    """BoodschappenRegel voor melk."""
    return BoodschappenRegel(
        naam="melk",
        hoeveelheid=1.0,
        eenheid="liter",
        originele_namen=frozenset({"melk"}),
    )


@pytest.fixture
def ui_regel():
    """BoodschappenRegel voor ui."""
    return BoodschappenRegel(
        naam="ui",
        hoeveelheid=2.0,
        eenheid="stuks",
        originele_namen=frozenset({"ui", "uien"}),
    )


@pytest.fixture
def knoflook_regel():
    """BoodschappenRegel voor knoflook."""
    return BoodschappenRegel(
        naam="knoflook",
        hoeveelheid=3.0,
        eenheid="teen",
        originele_namen=frozenset({"knoflook"}),
    )


@pytest.fixture
def melk_product():
    """AH Product voor melk."""
    return Product(
        id=100,
        title="AH Halfvolle melk",
        brand="AH",
        size="1 l",
        price=1.29,
        category="Zuivel",
        is_orderable=True,
    )


@pytest.fixture
def ui_product():
    """AH Product voor ui."""
    return Product(
        id=200,
        title="AH Uien",
        brand="AH",
        size="1 kg",
        price=1.49,
        category="Groenten",
        is_orderable=True,
    )


@pytest.fixture
def knoflook_product():
    """AH Product voor knoflook."""
    return Product(
        id=300,
        title="AH Knoflook",
        brand="AH",
        size="2 stuks",
        price=1.39,
        category="Groenten",
        is_orderable=True,
    )


@pytest.fixture
def boodschappenlijst(melk_regel, ui_regel, knoflook_regel):
    """Boodschappenlijst met 3 regels."""
    return Boodschappenlijst(
        week_start="2026-02-16",
        regels=[knoflook_regel, melk_regel, ui_regel],
    )


@pytest.fixture
def lege_boodschappenlijst():
    """Lege boodschappenlijst."""
    return Boodschappenlijst(week_start="2026-02-16", regels=[])


@pytest.fixture
def mock_client():
    """AHClient met gemockte token manager."""
    mock_token_manager = Mock(spec=AHTokenManager)
    mock_token_manager.get_access_token.return_value = "test-token"
    client = AHClient(mock_token_manager)
    client.session = Mock()
    # Default: geen auto-detect referentielijst
    client.find_list_by_name = Mock(return_value=None)
    return client


# =============================================================================
# ProductMatch Tests
# =============================================================================


class TestProductMatch:
    """Tests voor ProductMatch dataclass."""

    def test_gevonden_match(self, melk_regel, melk_product):
        """Test ProductMatch met gevonden product."""
        match = ProductMatch(
            regel=melk_regel,
            product=melk_product,
            bron="zoekopdracht",
        )

        assert match.regel is melk_regel
        assert match.product is melk_product
        assert match.bron == "zoekopdracht"
        assert match.gevonden is True

    def test_niet_gevonden_match(self, melk_regel):
        """Test ProductMatch zonder gevonden product."""
        match = ProductMatch(
            regel=melk_regel,
            product=None,
            bron="niet_gevonden",
        )

        assert match.product is None
        assert match.bron == "niet_gevonden"
        assert match.gevonden is False

    def test_referentie_bron(self, melk_regel, melk_product):
        """Test ProductMatch met referentielijst als bron."""
        match = ProductMatch(
            regel=melk_regel,
            product=melk_product,
            bron="referentie",
        )

        assert match.bron == "referentie"
        assert match.gevonden is True

    def test_aantal_default_is_1(self, melk_regel, melk_product):
        """Test dat ProductMatch.aantal standaard 1 is."""
        match = ProductMatch(
            regel=melk_regel,
            product=melk_product,
            bron="zoekopdracht",
        )
        assert match.aantal == 1

    def test_aantal_kan_gezet_worden(self, melk_regel, melk_product):
        """Test dat ProductMatch.aantal meegegeven kan worden."""
        match = ProductMatch(
            regel=melk_regel,
            product=melk_product,
            bron="zoekopdracht",
            aantal=3,
        )
        assert match.aantal == 3

    def test_is_frozen(self, melk_regel, melk_product):
        """Test dat ProductMatch immutable is."""
        match = ProductMatch(
            regel=melk_regel,
            product=melk_product,
            bron="zoekopdracht",
        )

        with pytest.raises(AttributeError):
            match.product = None


# =============================================================================
# SyncResultaat Tests
# =============================================================================


class TestSyncResultaat:
    """Tests voor SyncResultaat dataclass."""

    def test_alle_gevonden(self, melk_regel, ui_regel, melk_product, ui_product):
        """Test SyncResultaat wanneer alle producten gevonden zijn."""
        matches = [
            ProductMatch(regel=melk_regel, product=melk_product, bron="zoekopdracht"),
            ProductMatch(regel=ui_regel, product=ui_product, bron="referentie"),
        ]
        resultaat = SyncResultaat(
            lijst_id="list-123",
            lijst_naam="Boodschappen 2026-02-16",
            matches=matches,
        )

        assert resultaat.lijst_id == "list-123"
        assert resultaat.lijst_naam == "Boodschappen 2026-02-16"
        assert len(resultaat.gevonden) == 2
        assert len(resultaat.niet_gevonden) == 0

    def test_gedeeltelijk_gevonden(self, melk_regel, ui_regel, melk_product):
        """Test SyncResultaat met gedeeltelijke matches."""
        matches = [
            ProductMatch(regel=melk_regel, product=melk_product, bron="zoekopdracht"),
            ProductMatch(regel=ui_regel, product=None, bron="niet_gevonden"),
        ]
        resultaat = SyncResultaat(
            lijst_id="list-123",
            lijst_naam="Boodschappen 2026-02-16",
            matches=matches,
        )

        assert len(resultaat.gevonden) == 1
        assert len(resultaat.niet_gevonden) == 1
        assert resultaat.gevonden[0].regel is melk_regel
        assert resultaat.niet_gevonden[0].regel is ui_regel

    def test_geen_gevonden(self, melk_regel, ui_regel):
        """Test SyncResultaat wanneer niets gevonden is."""
        matches = [
            ProductMatch(regel=melk_regel, product=None, bron="niet_gevonden"),
            ProductMatch(regel=ui_regel, product=None, bron="niet_gevonden"),
        ]
        resultaat = SyncResultaat(
            lijst_id="list-123",
            lijst_naam="Test",
            matches=matches,
        )

        assert len(resultaat.gevonden) == 0
        assert len(resultaat.niet_gevonden) == 2

    def test_samenvatting(
        self, melk_regel, ui_regel, knoflook_regel, melk_product, ui_product
    ):
        """Test samenvatting property."""
        matches = [
            ProductMatch(regel=melk_regel, product=melk_product, bron="zoekopdracht"),
            ProductMatch(regel=ui_regel, product=ui_product, bron="referentie"),
            ProductMatch(regel=knoflook_regel, product=None, bron="niet_gevonden"),
        ]
        resultaat = SyncResultaat(
            lijst_id="list-123",
            lijst_naam="Test",
            matches=matches,
        )

        samenvatting = resultaat.samenvatting
        assert samenvatting["totaal"] == 3
        assert samenvatting["gevonden"] == 2
        assert samenvatting["niet_gevonden"] == 1

    def test_lege_matches(self):
        """Test SyncResultaat met lege matches."""
        resultaat = SyncResultaat(
            lijst_id="list-123",
            lijst_naam="Test",
            matches=[],
        )

        assert len(resultaat.gevonden) == 0
        assert len(resultaat.niet_gevonden) == 0
        assert resultaat.samenvatting["totaal"] == 0

    def test_is_frozen(self, melk_regel, melk_product):
        """Test dat SyncResultaat immutable is."""
        resultaat = SyncResultaat(
            lijst_id="list-123",
            lijst_naam="Test",
            matches=[
                ProductMatch(
                    regel=melk_regel, product=melk_product, bron="zoekopdracht"
                ),
            ],
        )

        with pytest.raises(AttributeError):
            resultaat.lijst_id = "other"


# =============================================================================
# AHIntegratie.zoek_producten Tests
# =============================================================================


class TestZoekProducten:
    """Tests voor AHIntegratie.zoek_producten method."""

    def test_zoekt_alle_regels(
        self, mock_client, boodschappenlijst, melk_product, ui_product, knoflook_product
    ):
        """Test dat alle regels gezocht worden via smart_search."""
        mock_client.smart_search = Mock(
            side_effect=[
                (knoflook_product, "search"),
                (melk_product, "search"),
                (ui_product, "search"),
            ]
        )

        integratie = AHIntegratie(mock_client)
        matches = integratie.zoek_producten(boodschappenlijst)

        assert len(matches) == 3
        assert mock_client.smart_search.call_count == 3

    def test_gebruikt_regelnaam_als_zoekterm(self, mock_client, boodschappenlijst):
        """Test dat de naam van de regel als zoekterm gebruikt wordt."""
        mock_client.smart_search = Mock(return_value=(None, "niet_gevonden"))

        integratie = AHIntegratie(mock_client)
        integratie.zoek_producten(boodschappenlijst)

        zoektermen = [c.args[0] for c in mock_client.smart_search.call_args_list]
        assert "knoflook" in zoektermen
        assert "melk" in zoektermen
        assert "ui" in zoektermen

    def test_geeft_referentie_producten_mee(
        self, mock_client, boodschappenlijst, melk_product
    ):
        """Test dat referentie-producten eenmalig geladen en meegegeven worden."""
        ref_products = [melk_product]
        mock_list = FavoriteList(
            id="ref-id",
            name="Referentie",
            total_items=1,
            items=[],
            products=ref_products,
        )
        mock_client.get_list_with_products = Mock(return_value=mock_list)
        mock_client.smart_search = Mock(return_value=(None, "niet_gevonden"))

        integratie = AHIntegratie(mock_client)
        integratie.zoek_producten(boodschappenlijst, referentie_lijst_id="ref-id")

        # Referentielijst wordt eenmalig geladen
        mock_client.get_list_with_products.assert_called_once_with("ref-id")

        # Alle smart_search calls krijgen reference_products mee
        for c in mock_client.smart_search.call_args_list:
            assert c.kwargs["reference_products"] is ref_products

    def test_zonder_referentielijst(self, mock_client, boodschappenlijst):
        """Test zoeken zonder referentielijst en zonder auto-detect match."""
        mock_client.find_list_by_name = Mock(return_value=None)
        mock_client.smart_search = Mock(return_value=(None, "niet_gevonden"))

        integratie = AHIntegratie(mock_client)
        integratie.zoek_producten(boodschappenlijst)

        for c in mock_client.smart_search.call_args_list:
            assert c.kwargs.get("reference_products") is None

    def test_auto_detect_referentielijst(
        self, mock_client, boodschappenlijst, melk_product
    ):
        """Test dat 'boodschappen' lijst automatisch gevonden wordt."""
        ref_products = [melk_product]
        found_list = FavoriteList(
            id="auto-id",
            name="boodschappen",
            total_items=1,
            items=[],
        )
        mock_list_with_products = FavoriteList(
            id="auto-id",
            name="boodschappen",
            total_items=1,
            items=[],
            products=ref_products,
        )
        mock_client.find_list_by_name = Mock(return_value=found_list)
        mock_client.get_list_with_products = Mock(return_value=mock_list_with_products)
        mock_client.smart_search = Mock(return_value=(None, "not_found"))

        integratie = AHIntegratie(mock_client)
        integratie.zoek_producten(boodschappenlijst)

        mock_client.find_list_by_name.assert_called_once_with("boodschappen")
        mock_client.get_list_with_products.assert_called_once_with("auto-id")
        for c in mock_client.smart_search.call_args_list:
            assert c.kwargs["reference_products"] is ref_products

    def test_auto_detect_niet_gevonden(self, mock_client, boodschappenlijst):
        """Test dat zonder 'boodschappen' lijst gewoon doorgegaan wordt."""
        mock_client.find_list_by_name = Mock(return_value=None)
        mock_client.get_list_with_products = Mock()
        mock_client.smart_search = Mock(return_value=(None, "not_found"))

        integratie = AHIntegratie(mock_client)
        integratie.zoek_producten(boodschappenlijst)

        mock_client.find_list_by_name.assert_called_once_with("boodschappen")
        mock_client.get_list_with_products.assert_not_called()
        for c in mock_client.smart_search.call_args_list:
            assert c.kwargs.get("reference_products") is None

    def test_expliciet_ref_id_heeft_voorrang(
        self, mock_client, boodschappenlijst, melk_product
    ):
        """Test dat expliciet ref-ID voorrang heeft boven auto-detect."""
        ref_products = [melk_product]
        mock_list = FavoriteList(
            id="explicit-id",
            name="Mijn Lijst",
            total_items=1,
            items=[],
            products=ref_products,
        )
        mock_client.get_list_with_products = Mock(return_value=mock_list)
        mock_client.find_list_by_name = Mock()
        mock_client.smart_search = Mock(return_value=(None, "not_found"))

        integratie = AHIntegratie(mock_client)
        integratie.zoek_producten(boodschappenlijst, referentie_lijst_id="explicit-id")

        mock_client.find_list_by_name.assert_not_called()
        mock_client.get_list_with_products.assert_called_once_with("explicit-id")

    def test_lege_boodschappenlijst(self, mock_client, lege_boodschappenlijst):
        """Test met lege boodschappenlijst."""
        mock_client.smart_search = Mock()

        integratie = AHIntegratie(mock_client)
        matches = integratie.zoek_producten(lege_boodschappenlijst)

        assert matches == []
        mock_client.smart_search.assert_not_called()

    def test_match_resultaten_correct(self, mock_client, melk_regel, melk_product):
        """Test dat ProductMatch correct opgebouwd wordt."""
        lijst = Boodschappenlijst(week_start="2026-02-16", regels=[melk_regel])
        mock_client.smart_search = Mock(return_value=(melk_product, "search"))

        integratie = AHIntegratie(mock_client)
        matches = integratie.zoek_producten(lijst)

        assert len(matches) == 1
        match = matches[0]
        assert match.regel is melk_regel
        assert match.product is melk_product
        assert match.bron == "zoekopdracht"

    def test_bron_mapping_reference(self, mock_client, melk_regel, melk_product):
        """Test dat 'reference' bron vertaald wordt naar 'referentie'."""
        lijst = Boodschappenlijst(week_start="2026-02-16", regels=[melk_regel])
        mock_client.smart_search = Mock(return_value=(melk_product, "reference"))

        integratie = AHIntegratie(mock_client)
        matches = integratie.zoek_producten(lijst)

        assert matches[0].bron == "referentie"

    def test_bron_mapping_search(self, mock_client, melk_regel, melk_product):
        """Test dat 'search' bron vertaald wordt naar 'zoekopdracht'."""
        lijst = Boodschappenlijst(week_start="2026-02-16", regels=[melk_regel])
        mock_client.smart_search = Mock(return_value=(melk_product, "search"))

        integratie = AHIntegratie(mock_client)
        matches = integratie.zoek_producten(lijst)

        assert matches[0].bron == "zoekopdracht"

    def test_berekent_aantal_voor_match(self, mock_client, melk_product):
        """Test dat zoek_producten het berekende aantal meezet in ProductMatch."""
        regel = BoodschappenRegel(
            naam="melk",
            hoeveelheid=2.0,
            eenheid="liter",
            originele_namen=frozenset({"melk"}),
        )
        lijst = Boodschappenlijst(week_start="2026-02-16", regels=[regel])
        mock_client.smart_search = Mock(return_value=(melk_product, "search"))

        integratie = AHIntegratie(mock_client)
        matches = integratie.zoek_producten(lijst)

        # 2 liter nodig, product is "1 l" → aantal=2
        assert matches[0].aantal == 2

    def test_aantal_1_bij_niet_gevonden(self, mock_client, melk_regel):
        """Test dat aantal 1 is als product niet gevonden is."""
        lijst = Boodschappenlijst(week_start="2026-02-16", regels=[melk_regel])
        mock_client.smart_search = Mock(return_value=(None, "not_found"))

        integratie = AHIntegratie(mock_client)
        matches = integratie.zoek_producten(lijst)

        assert matches[0].aantal == 1

    def test_bron_mapping_not_found(self, mock_client, melk_regel):
        """Test dat 'not_found' bron vertaald wordt naar 'niet_gevonden'."""
        lijst = Boodschappenlijst(week_start="2026-02-16", regels=[melk_regel])
        mock_client.smart_search = Mock(return_value=(None, "not_found"))

        integratie = AHIntegratie(mock_client)
        matches = integratie.zoek_producten(lijst)

        assert matches[0].bron == "niet_gevonden"


# =============================================================================
# T022: AHIntegratie.zoek_producten — met MatchVoorkeurenRepository
# =============================================================================


class TestZoekProductenMetVoorkeuren:
    """T022: zoek_producten() past opgeslagen voorkeuren toe vóór smart_search."""

    @pytest.fixture
    def melk_voorkeur_product(self):
        """AH product als opgeslagen voorkeur voor melk."""
        return Product(
            id=123456,
            title="AH Volle melk 1L",
            brand="AH",
            size="1L",
            price=1.09,
            category="Zuivel",
            is_orderable=True,
        )

    @pytest.fixture
    def niet_besteldbaar_product(self):
        """AH product dat niet besteld kan worden."""
        return Product(
            id=999999,
            title="Uitverkocht product",
            brand="X",
            size="1L",
            price=0.99,
            category="Zuivel",
            is_orderable=False,
        )

    @pytest.fixture
    def mock_voorkeuren_repo(self):
        from unittest.mock import MagicMock

        return MagicMock()

    def test_voorkeur_gevonden_bron_is_voorkeur(
        self, mock_client, melk_regel, melk_voorkeur_product, mock_voorkeuren_repo
    ):
        """Voorkeur gevonden en product beschikbaar → bron='voorkeur'."""
        from boodschappenagent.ah.preferences import MatchVoorkeur

        mock_voorkeuren_repo.get.return_value = MatchVoorkeur(
            ingredient_naam="melk",
            article_id=123456,
            product_naam="AH Volle melk 1L",
            updated_at="2026-05-14T10:00:00",
        )
        mock_client.search_products = Mock(return_value=[melk_voorkeur_product])
        mock_client.smart_search = Mock(return_value=(None, "not_found"))

        lijst = Boodschappenlijst(week_start="2026-02-16", regels=[melk_regel])
        integratie = AHIntegratie(mock_client)
        matches = integratie.zoek_producten(lijst, voorkeuren_repo=mock_voorkeuren_repo)

        assert len(matches) == 1
        assert matches[0].bron == "voorkeur"
        assert matches[0].product is not None
        assert matches[0].product.id == 123456
        mock_client.smart_search.assert_not_called()

    def test_voorkeur_niet_beschikbaar_valt_terug_op_smart_search(
        self,
        mock_client,
        melk_regel,
        niet_besteldbaar_product,
        melk_voorkeur_product,
        mock_voorkeuren_repo,
    ):
        """Voorkeur niet besteldbaar → fallback naar smart_search."""
        from boodschappenagent.ah.preferences import MatchVoorkeur

        mock_voorkeuren_repo.get.return_value = MatchVoorkeur(
            ingredient_naam="melk",
            article_id=999999,
            product_naam="Uitverkocht product",
            updated_at="2026-05-14T10:00:00",
        )
        mock_client.search_products = Mock(return_value=[niet_besteldbaar_product])
        mock_client.smart_search = Mock(return_value=(melk_voorkeur_product, "search"))

        lijst = Boodschappenlijst(week_start="2026-02-16", regels=[melk_regel])
        integratie = AHIntegratie(mock_client)
        matches = integratie.zoek_producten(lijst, voorkeuren_repo=mock_voorkeuren_repo)

        assert len(matches) == 1
        assert matches[0].bron == "voorkeur_niet_beschikbaar"
        mock_client.smart_search.assert_called_once()

    def test_geen_voorkeur_gebruikt_smart_search(
        self, mock_client, melk_regel, melk_voorkeur_product, mock_voorkeuren_repo
    ):
        """Geen voorkeur opgeslagen → smart_search zoals gewoonlijk."""
        mock_voorkeuren_repo.get.return_value = None
        mock_client.smart_search = Mock(return_value=(melk_voorkeur_product, "search"))
        mock_client.find_list_by_name = Mock(return_value=None)

        lijst = Boodschappenlijst(week_start="2026-02-16", regels=[melk_regel])
        integratie = AHIntegratie(mock_client)
        matches = integratie.zoek_producten(lijst, voorkeuren_repo=mock_voorkeuren_repo)

        assert len(matches) == 1
        assert matches[0].bron == "zoekopdracht"
        mock_client.smart_search.assert_called_once()

    def test_zonder_repo_gedrag_ongewijzigd(
        self, mock_client, melk_regel, melk_voorkeur_product
    ):
        """Zonder voorkeuren_repo (None) → gedrag identiek aan voor US3."""
        mock_client.find_list_by_name = Mock(return_value=None)
        mock_client.smart_search = Mock(return_value=(melk_voorkeur_product, "search"))

        lijst = Boodschappenlijst(week_start="2026-02-16", regels=[melk_regel])
        integratie = AHIntegratie(mock_client)
        matches = integratie.zoek_producten(lijst)  # Geen voorkeuren_repo

        assert len(matches) == 1
        assert matches[0].bron == "zoekopdracht"


# =============================================================================
# AHIntegratie.sync_naar_lijst Tests
# =============================================================================


class TestSyncNaarLijst:
    """Tests voor AHIntegratie.sync_naar_lijst method."""

    def test_maakt_lijst_aan_met_default_naam(self, mock_client, boodschappenlijst):
        """Test dat een AH lijst aangemaakt wordt met default naam."""
        mock_client.create_list = Mock(return_value="new-list-id")
        mock_client.smart_search = Mock(return_value=(None, "not_found"))
        mock_client.add_products_to_list = Mock()

        integratie = AHIntegratie(mock_client)
        resultaat = integratie.sync_naar_lijst(boodschappenlijst)

        mock_client.create_list.assert_called_once_with("Boodschappen 2026-02-16")
        assert resultaat.lijst_naam == "Boodschappen 2026-02-16"

    def test_maakt_lijst_aan_met_custom_naam(self, mock_client, boodschappenlijst):
        """Test dat een AH lijst aangemaakt wordt met custom naam."""
        mock_client.create_list = Mock(return_value="new-list-id")
        mock_client.smart_search = Mock(return_value=(None, "not_found"))
        mock_client.add_products_to_list = Mock()

        integratie = AHIntegratie(mock_client)
        resultaat = integratie.sync_naar_lijst(
            boodschappenlijst, lijst_naam="Mijn Weekboodschappen"
        )

        mock_client.create_list.assert_called_once_with("Mijn Weekboodschappen")
        assert resultaat.lijst_naam == "Mijn Weekboodschappen"

    def test_voegt_gevonden_producten_toe(
        self, mock_client, boodschappenlijst, melk_product, ui_product, knoflook_product
    ):
        """Test dat gevonden producten aan de lijst toegevoegd worden."""
        mock_client.create_list = Mock(return_value="new-list-id")
        mock_client.smart_search = Mock(
            side_effect=[
                (knoflook_product, "search"),
                (melk_product, "search"),
                (ui_product, "search"),
            ]
        )
        mock_client.add_products_to_list = Mock(return_value={"totalSize": 3})

        integratie = AHIntegratie(mock_client)
        integratie.sync_naar_lijst(boodschappenlijst)

        mock_client.add_products_to_list.assert_called_once()
        call_args = mock_client.add_products_to_list.call_args
        assert call_args.args[0] == "new-list-id"
        # Check dat alle product IDs meegegeven worden
        product_ids = {pid for pid, _ in call_args.args[1]}
        assert product_ids == {100, 200, 300}

    def test_voegt_alleen_gevonden_producten_toe(
        self, mock_client, boodschappenlijst, melk_product
    ):
        """Test dat alleen gevonden producten toegevoegd worden."""
        mock_client.create_list = Mock(return_value="new-list-id")
        # Alleen melk gevonden, rest niet
        mock_client.smart_search = Mock(
            side_effect=[
                (None, "not_found"),  # knoflook
                (melk_product, "search"),  # melk
                (None, "not_found"),  # ui
            ]
        )
        mock_client.add_products_to_list = Mock(return_value={"totalSize": 1})

        integratie = AHIntegratie(mock_client)
        resultaat = integratie.sync_naar_lijst(boodschappenlijst)

        call_args = mock_client.add_products_to_list.call_args
        product_ids = [pid for pid, _ in call_args.args[1]]
        assert product_ids == [100]
        assert len(resultaat.gevonden) == 1
        assert len(resultaat.niet_gevonden) == 2

    def test_geen_producten_gevonden(self, mock_client, boodschappenlijst):
        """Test wanneer geen enkel product gevonden wordt."""
        mock_client.create_list = Mock(return_value="new-list-id")
        mock_client.smart_search = Mock(return_value=(None, "not_found"))
        mock_client.add_products_to_list = Mock()

        integratie = AHIntegratie(mock_client)
        resultaat = integratie.sync_naar_lijst(boodschappenlijst)

        # Lijst wordt wel aangemaakt, maar add wordt niet aangeroepen
        mock_client.create_list.assert_called_once()
        mock_client.add_products_to_list.assert_not_called()
        assert resultaat.lijst_id == "new-list-id"
        assert len(resultaat.niet_gevonden) == 3

    def test_lege_boodschappenlijst(self, mock_client, lege_boodschappenlijst):
        """Test met lege boodschappenlijst."""
        mock_client.create_list = Mock(return_value="new-list-id")
        mock_client.add_products_to_list = Mock()

        integratie = AHIntegratie(mock_client)
        resultaat = integratie.sync_naar_lijst(lege_boodschappenlijst)

        mock_client.create_list.assert_called_once()
        mock_client.add_products_to_list.assert_not_called()
        assert len(resultaat.matches) == 0

    def test_resultaat_bevat_lijst_id(self, mock_client, boodschappenlijst):
        """Test dat het resultaat de lijst ID bevat."""
        mock_client.create_list = Mock(return_value="abc-456")
        mock_client.smart_search = Mock(return_value=(None, "not_found"))

        integratie = AHIntegratie(mock_client)
        resultaat = integratie.sync_naar_lijst(boodschappenlijst)

        assert resultaat.lijst_id == "abc-456"

    def test_quantiteit_berekend_uit_hoeveelheid(self, mock_client, melk_product):
        """Test dat quantity berekend wordt op basis van hoeveelheid en product size."""
        regel = BoodschappenRegel(
            naam="melk",
            hoeveelheid=2.0,
            eenheid="liter",
            originele_namen=frozenset({"melk"}),
        )
        lijst = Boodschappenlijst(week_start="2026-02-16", regels=[regel])
        mock_client.create_list = Mock(return_value="new-list-id")
        mock_client.smart_search = Mock(return_value=(melk_product, "search"))
        mock_client.add_products_to_list = Mock(return_value={"totalSize": 1})

        integratie = AHIntegratie(mock_client)
        integratie.sync_naar_lijst(lijst)

        call_args = mock_client.add_products_to_list.call_args
        products = call_args.args[1]
        # 2 liter nodig, product is 1 l → quantity=2
        assert products == [(100, 2)]

    def test_quantiteit_1_bij_exact_match(self, mock_client, melk_regel, melk_product):
        """Test dat quantity 1 is als hoeveelheid exact matcht."""
        lijst = Boodschappenlijst(week_start="2026-02-16", regels=[melk_regel])
        mock_client.create_list = Mock(return_value="new-list-id")
        mock_client.smart_search = Mock(return_value=(melk_product, "search"))
        mock_client.add_products_to_list = Mock(return_value={"totalSize": 1})

        integratie = AHIntegratie(mock_client)
        integratie.sync_naar_lijst(lijst)

        call_args = mock_client.add_products_to_list.call_args
        products = call_args.args[1]
        # 1 liter nodig, product is 1 l → quantity=1
        assert products == [(100, 1)]

    def test_quantiteit_1_bij_niet_berekenbare_eenheid(
        self, mock_client, knoflook_regel, knoflook_product
    ):
        """Test dat quantity 1 is voor niet-berekenbare eenheden (teen)."""
        lijst = Boodschappenlijst(week_start="2026-02-16", regels=[knoflook_regel])
        mock_client.create_list = Mock(return_value="new-list-id")
        mock_client.smart_search = Mock(return_value=(knoflook_product, "search"))
        mock_client.add_products_to_list = Mock(return_value={"totalSize": 1})

        integratie = AHIntegratie(mock_client)
        integratie.sync_naar_lijst(lijst)

        call_args = mock_client.add_products_to_list.call_args
        products = call_args.args[1]
        # teen is niet-berekenbaar → quantity=1
        assert products == [(300, 1)]

    def test_dedupliceert_producten(self, mock_client, melk_product):
        """Test dat duplicate product IDs samengevoegd worden met opgetelde quantity."""
        regel1 = BoodschappenRegel(
            naam="melk",
            hoeveelheid=1.0,
            eenheid="liter",
            originele_namen=frozenset({"melk"}),
        )
        regel2 = BoodschappenRegel(
            naam="volle melk",
            hoeveelheid=1.0,
            eenheid="liter",
            originele_namen=frozenset({"volle melk"}),
        )
        lijst = Boodschappenlijst(week_start="2026-02-16", regels=[regel1, regel2])
        mock_client.create_list = Mock(return_value="new-list-id")
        # Beide regels matchen hetzelfde product
        mock_client.smart_search = Mock(return_value=(melk_product, "search"))
        mock_client.add_products_to_list = Mock(return_value={"totalSize": 1})

        integratie = AHIntegratie(mock_client)
        integratie.sync_naar_lijst(lijst)

        call_args = mock_client.add_products_to_list.call_args
        products = call_args.args[1]
        # Moet 1 product zijn met quantity 2
        assert len(products) == 1
        assert products[0] == (100, 2)

    def test_geeft_referentie_door_aan_zoek_producten(
        self, mock_client, boodschappenlijst, melk_product
    ):
        """Test dat referentie_lijst_id doorgegeven wordt."""
        ref_products = [melk_product]
        mock_list = FavoriteList(
            id="ref-id",
            name="Referentie",
            total_items=1,
            items=[],
            products=ref_products,
        )
        mock_client.get_list_with_products = Mock(return_value=mock_list)
        mock_client.create_list = Mock(return_value="new-list-id")
        mock_client.smart_search = Mock(return_value=(None, "not_found"))

        integratie = AHIntegratie(mock_client)
        integratie.sync_naar_lijst(boodschappenlijst, referentie_lijst_id="ref-id")

        mock_client.get_list_with_products.assert_called_once_with("ref-id")


# =============================================================================
# AHIntegratie.zoek_producten_voor_correctie Tests
# =============================================================================


class TestZoekProductenVoorCorrectie:
    """Tests voor AHIntegratie.zoek_producten_voor_correctie method."""

    def test_geeft_resultaten_terug_via_facade(self, mock_client, melk_product):
        """Zoekresultaten worden teruggegeven via de facade, niet via _client direct."""
        mock_client.search_products = Mock(return_value=[melk_product])

        integratie = AHIntegratie(mock_client)
        resultaten = integratie.zoek_producten_voor_correctie("melk")

        assert resultaten == [melk_product]
        mock_client.search_products.assert_called_once_with("melk")

    def test_beperkt_resultaten_tot_limit(self, mock_client):
        """Resultaten worden beperkt tot het opgegeven limit."""
        producten = [
            Product(id=i, title=f"Product {i}", brand="AH", size="1x", price=1.0,
                    category="", is_orderable=True)
            for i in range(15)
        ]
        mock_client.search_products = Mock(return_value=producten)

        integratie = AHIntegratie(mock_client)
        resultaten = integratie.zoek_producten_voor_correctie("melk", limit=10)

        assert len(resultaten) == 10

    def test_standaard_limit_is_10(self, mock_client):
        """Standaard limit is 10."""
        producten = [
            Product(id=i, title=f"Product {i}", brand="AH", size="1x", price=1.0,
                    category="", is_orderable=True)
            for i in range(15)
        ]
        mock_client.search_products = Mock(return_value=producten)

        integratie = AHIntegratie(mock_client)
        resultaten = integratie.zoek_producten_voor_correctie("melk")

        assert len(resultaten) == 10

    def test_lege_resultaten_bij_geen_matches(self, mock_client):
        """Lege lijst bij geen zoekresultaten."""
        mock_client.search_products = Mock(return_value=[])

        integratie = AHIntegratie(mock_client)
        resultaten = integratie.zoek_producten_voor_correctie("xyzabc")

        assert resultaten == []
