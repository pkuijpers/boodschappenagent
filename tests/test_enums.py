"""Tests voor Seizoen en Categorie enums."""

import pytest

from boodschappenagent.models.enums import Categorie, Seizoen


class TestSeizoen:
    """Tests voor de Seizoen enum."""

    def test_seizoen_has_all_expected_values(self):
        """Seizoen heeft alle verwachte waarden."""
        expected = {"lente", "zomer", "herfst", "winter", "alle"}
        actual = {s.value for s in Seizoen}
        assert actual == expected

    def test_seizoen_values(self):
        """Seizoen waarden zijn correct."""
        assert Seizoen.LENTE.value == "lente"
        assert Seizoen.ZOMER.value == "zomer"
        assert Seizoen.HERFST.value == "herfst"
        assert Seizoen.WINTER.value == "winter"
        assert Seizoen.ALLE.value == "alle"

    def test_seizoen_from_string(self):
        """Seizoen kan worden aangemaakt vanuit string."""
        assert Seizoen("lente") == Seizoen.LENTE
        assert Seizoen("zomer") == Seizoen.ZOMER
        assert Seizoen("herfst") == Seizoen.HERFST
        assert Seizoen("winter") == Seizoen.WINTER
        assert Seizoen("alle") == Seizoen.ALLE

    def test_seizoen_invalid_value_raises(self):
        """Ongeldige waarde geeft ValueError."""
        with pytest.raises(ValueError):
            Seizoen("ongeldig")

    def test_seizoen_count(self):
        """Er zijn precies 5 seizoenen."""
        assert len(Seizoen) == 5


class TestCategorie:
    """Tests voor de Categorie enum."""

    def test_categorie_has_all_expected_values(self):
        """Categorie heeft alle verwachte waarden."""
        expected = {
            "pasta",
            "ovenschotel",
            "soep",
            "stamppot",
            "roerbak",
            "salade",
            "overig",
        }
        actual = {c.value for c in Categorie}
        assert actual == expected

    def test_categorie_values(self):
        """Categorie waarden zijn correct."""
        assert Categorie.PASTA.value == "pasta"
        assert Categorie.OVENSCHOTEL.value == "ovenschotel"
        assert Categorie.SOEP.value == "soep"
        assert Categorie.STAMPPOT.value == "stamppot"
        assert Categorie.ROERBAK.value == "roerbak"
        assert Categorie.SALADE.value == "salade"
        assert Categorie.OVERIG.value == "overig"

    def test_categorie_from_string(self):
        """Categorie kan worden aangemaakt vanuit string."""
        assert Categorie("pasta") == Categorie.PASTA
        assert Categorie("ovenschotel") == Categorie.OVENSCHOTEL
        assert Categorie("soep") == Categorie.SOEP
        assert Categorie("stamppot") == Categorie.STAMPPOT
        assert Categorie("roerbak") == Categorie.ROERBAK
        assert Categorie("salade") == Categorie.SALADE
        assert Categorie("overig") == Categorie.OVERIG

    def test_categorie_invalid_value_raises(self):
        """Ongeldige waarde geeft ValueError."""
        with pytest.raises(ValueError):
            Categorie("ongeldig")

    def test_categorie_count(self):
        """Er zijn precies 7 categorieën."""
        assert len(Categorie) == 7
