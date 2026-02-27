"""Tests voor hoeveelheid-berekening op basis van boodschappenregel en AH product."""


from boodschappenagent.ah.models import Product
from boodschappenagent.ah.quantity_calculator import bereken_aantal
from boodschappenagent.boodschappenlijst.models import BoodschappenRegel


def _regel(naam: str, hoeveelheid: float, eenheid: str) -> BoodschappenRegel:
    """Helper om snel een BoodschappenRegel te maken."""
    return BoodschappenRegel(
        naam=naam,
        hoeveelheid=hoeveelheid,
        eenheid=eenheid,
        originele_namen=frozenset({naam}),
    )


def _product(size: str, title: str = "AH Product") -> Product:
    """Helper om snel een Product te maken."""
    return Product(
        id=1,
        title=title,
        brand="AH",
        size=size,
        price=1.00,
        category="",
        is_orderable=True,
    )


class TestBerekenAantalBasisgevallen:
    """Basisberekeningen: nodig / verpakkingsgrootte, naar boven afgerond."""

    def test_exact_match_liter(self):
        """2 liter nodig, product is 1 l → 2 stuks."""
        assert bereken_aantal(_regel("melk", 2.0, "liter"), _product("1 l")) == 2

    def test_exact_match_gram(self):
        """300 gram nodig, product is 300 g → 1 stuk."""
        assert bereken_aantal(_regel("gehakt", 300.0, "gram"), _product("300 g")) == 1

    def test_afronden_naar_boven(self):
        """1.5 liter nodig, product is 1 l → 2 (nooit minder)."""
        assert bereken_aantal(_regel("melk", 1.5, "liter"), _product("1 l")) == 2

    def test_product_groter_dan_nodig(self):
        """0.5 liter nodig, product is 1 l → 1 (product is al genoeg)."""
        assert bereken_aantal(_regel("melk", 0.5, "liter"), _product("1 l")) == 1

    def test_gehakt_meer_dan_verpakking(self):
        """500 gram nodig, product is 300 g → 2."""
        assert bereken_aantal(_regel("gehakt", 500.0, "gram"), _product("300 g")) == 2

    def test_gehakt_minder_dan_kilo(self):
        """600 gram nodig, product is 1 kg → 1."""
        assert bereken_aantal(_regel("gehakt", 600.0, "gram"), _product("1 kg")) == 1

    def test_eieren_doosje_genoeg(self):
        """2 eieren nodig, doosje van 6 → 1."""
        assert bereken_aantal(_regel("eieren", 2.0, "stuks"), _product("6 stuks")) == 1

    def test_eieren_twee_doosjes(self):
        """8 eieren nodig, doosje van 6 → 2."""
        assert bereken_aantal(_regel("eieren", 8.0, "stuks"), _product("6 stuks")) == 2

    def test_eieren_exact_doosje(self):
        """6 eieren nodig, doosje van 6 → 1."""
        assert bereken_aantal(_regel("eieren", 6.0, "stuks"), _product("6 stuks")) == 1


class TestBerekenAantalEenheidConversie:
    """Conversie tussen compatibele eenheden (ml↔l, g↔kg)."""

    def test_ml_naar_liter_product(self):
        """150 ml nodig, product is 1 l → 1."""
        assert bereken_aantal(_regel("melk", 150.0, "ml"), _product("1 l")) == 1

    def test_ml_naar_liter_product_meer(self):
        """1500 ml nodig, product is 1 l → 2."""
        assert bereken_aantal(_regel("melk", 1500.0, "ml"), _product("1 l")) == 2

    def test_liter_naar_ml_product(self):
        """2 liter nodig, product is 500 ml → 4."""
        assert bereken_aantal(_regel("melk", 2.0, "liter"), _product("500 ml")) == 4

    def test_gram_naar_kg_product(self):
        """600 gram nodig, product is 1 kg → 1."""
        assert bereken_aantal(_regel("gehakt", 600.0, "gram"), _product("1 kg")) == 1

    def test_kg_naar_gram_product(self):
        """1.5 kg nodig, product is 300 g → 5."""
        assert (
            bereken_aantal(_regel("gehakt", 1.5, "kilogram"), _product("300 g")) == 5
        )

    def test_nederlandse_komma_in_product_size(self):
        """2 liter nodig, product is 1,5 l → 2 (ceil(2.0/1.5))."""
        assert bereken_aantal(_regel("melk", 2.0, "liter"), _product("1,5 l")) == 2

    def test_3_liter_met_anderhalve_liter_product(self):
        """3 liter nodig, product is 1,5 l → 2."""
        assert bereken_aantal(_regel("melk", 3.0, "liter"), _product("1,5 l")) == 2


class TestBerekenAantalNietBerekenbaar:
    """Eenheden die niet berekenbaar zijn → altijd 1."""

    def test_naar_smaak(self):
        assert (
            bereken_aantal(_regel("peper", 1.0, "naar smaak"), _product("40 g")) == 1
        )

    def test_snuf(self):
        assert bereken_aantal(_regel("zout", 1.0, "snuf"), _product("1 kg")) == 1

    def test_mespunt(self):
        assert (
            bereken_aantal(_regel("kaneel", 1.0, "mespunt"), _product("40 g")) == 1
        )

    def test_eetlepel(self):
        assert (
            bereken_aantal(_regel("olie", 2.0, "eetlepel"), _product("500 ml")) == 1
        )

    def test_theelepel(self):
        assert (
            bereken_aantal(_regel("komijn", 1.0, "theelepel"), _product("30 g")) == 1
        )

    def test_teen(self):
        assert (
            bereken_aantal(_regel("knoflook", 3.0, "teen"), _product("2 stuks")) == 1
        )


class TestBerekenAantalEdgeCases:
    """Randgevallen en fallback-gedrag."""

    def test_incompatibele_eenheden(self):
        """stuks vs kg → incompatibel, fallback 1."""
        assert bereken_aantal(_regel("ui", 2.0, "stuks"), _product("1 kg")) == 1

    def test_lege_product_size(self):
        """Lege size → fallback 1."""
        assert bereken_aantal(_regel("tomaten", 400.0, "gram"), _product("")) == 1

    def test_onparseerbare_product_size(self):
        """Onparseerbare size → fallback 1."""
        assert (
            bereken_aantal(
                _regel("tomaten", 400.0, "gram"), _product("div. formaten")
            )
            == 1
        )

    def test_nooit_nul(self):
        """Zelfs bij heel kleine hoeveelheid, minimaal 1."""
        assert bereken_aantal(_regel("melk", 0.01, "liter"), _product("1 l")) == 1

    def test_onbekende_eenheid_op_boodschappenregel(self):
        """Onbekende eenheid op regel → fallback 1."""
        assert bereken_aantal(_regel("iets", 5.0, "bos"), _product("1 stuks")) == 1

    def test_stuk_vs_stuks(self):
        """Enkelvoud 'stuk' op product, meervoud 'stuks' op regel."""
        assert bereken_aantal(_regel("avocado", 3.0, "stuks"), _product("1 stuk")) == 3
