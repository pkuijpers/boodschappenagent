"""Tests voor IngredientNormalizer."""

from boodschappenagent.boodschappenlijst.normalizer import IngredientNormalizer


class TestNormaliseerNaam:
    """Tests voor naam-normalisatie."""

    def setup_method(self) -> None:
        self.normalizer = IngredientNormalizer()

    def test_identiek_doorlaten(self) -> None:
        naam, eenheid = self.normalizer.normaliseer("ui", "stuks")
        assert naam == "ui"

    def test_case_insensitive(self) -> None:
        naam, _ = self.normalizer.normaliseer("Uien", "stuks")
        assert naam == "ui"

    def test_synoniem_uien(self) -> None:
        naam, _ = self.normalizer.normaliseer("uien", "stuks")
        assert naam == "ui"

    def test_synoniem_biologische_ui(self) -> None:
        naam, _ = self.normalizer.normaliseer("biologische ui", "stuks")
        assert naam == "ui"

    def test_synoniem_biologische_rode_ui(self) -> None:
        naam, _ = self.normalizer.normaliseer("biologische rode ui", "stuks")
        assert naam == "rode ui"

    def test_synoniem_knoflookteen(self) -> None:
        naam, eenheid = self.normalizer.normaliseer("knoflookteen", "stuks")
        assert naam == "knoflook"
        assert eenheid == "teen"

    def test_synoniem_passata(self) -> None:
        naam, _ = self.normalizer.normaliseer("passata di pomodoro", "gram")
        assert naam == "passata"

    def test_synoniem_peterselie(self) -> None:
        naam, _ = self.normalizer.normaliseer("platte peterselie", "eetlepel")
        assert naam == "peterselie"

    def test_synoniem_bladerdeeg(self) -> None:
        naam, _ = self.normalizer.normaliseer("vers bladerdeeg", "stuks")
        assert naam == "bladerdeeg"

    def test_synoniem_tuinkers(self) -> None:
        naam, _ = self.normalizer.normaliseer("biologische tuinkers", "stuks")
        assert naam == "tuinkers"

    def test_synoniem_sjalotten(self) -> None:
        naam, _ = self.normalizer.normaliseer("sjalotten", "stuks")
        assert naam == "sjalot"

    def test_onbekend_doorlaten(self) -> None:
        naam, _ = self.normalizer.normaliseer("quinoa", "gram")
        assert naam == "quinoa"

    def test_extra_synoniemen(self) -> None:
        normalizer = IngredientNormalizer(
            extra_synoniemen={"rode paprika": "paprika"}
        )
        naam, _ = normalizer.normaliseer("rode paprika", "stuks")
        assert naam == "paprika"

    def test_extra_synoniemen_overschrijven_niet(self) -> None:
        normalizer = IngredientNormalizer(
            extra_synoniemen={"quinoa": "graan"}
        )
        naam, _ = normalizer.normaliseer("uien", "stuks")
        assert naam == "ui"


class TestNormaliseerEenheid:
    """Tests voor eenheid-normalisatie."""

    def setup_method(self) -> None:
        self.normalizer = IngredientNormalizer()

    def test_snuf_naar_smaak(self) -> None:
        _, eenheid = self.normalizer.normaliseer("peper", "snuf")
        assert eenheid == "naar smaak"

    def test_el_naar_eetlepel(self) -> None:
        _, eenheid = self.normalizer.normaliseer("olie", "el")
        assert eenheid == "eetlepel"

    def test_tl_naar_theelepel(self) -> None:
        _, eenheid = self.normalizer.normaliseer("komijn", "tl")
        assert eenheid == "theelepel"

    def test_g_naar_gram(self) -> None:
        _, eenheid = self.normalizer.normaliseer("bloem", "g")
        assert eenheid == "gram"

    def test_l_naar_liter(self) -> None:
        _, eenheid = self.normalizer.normaliseer("water", "l")
        assert eenheid == "liter"

    def test_onbekende_eenheid_doorlaten(self) -> None:
        _, eenheid = self.normalizer.normaliseer("ei", "stuks")
        assert eenheid == "stuks"

    def test_case_insensitive_eenheid(self) -> None:
        _, eenheid = self.normalizer.normaliseer("bloem", "G")
        assert eenheid == "gram"


class TestIsNietAggregeerbaar:
    """Tests voor is_niet_aggregeerbaar."""

    def setup_method(self) -> None:
        self.normalizer = IngredientNormalizer()

    def test_naar_smaak(self) -> None:
        assert self.normalizer.is_niet_aggregeerbaar("naar smaak") is True

    def test_snuf(self) -> None:
        assert self.normalizer.is_niet_aggregeerbaar("snuf") is True

    def test_mespunt(self) -> None:
        assert self.normalizer.is_niet_aggregeerbaar("mespunt") is True

    def test_gram_wel_aggregeerbaar(self) -> None:
        assert self.normalizer.is_niet_aggregeerbaar("gram") is False

    def test_stuks_wel_aggregeerbaar(self) -> None:
        assert self.normalizer.is_niet_aggregeerbaar("stuks") is False
