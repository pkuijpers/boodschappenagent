"""Tests voor Seizoen, Categorie en Basis enums."""

import pytest

from boodschappenagent.models.enums import Basis, Categorie, Seizoen


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
    """Tests voor de Categorie enum (proteïnebron)."""

    def test_categorie_has_all_expected_values(self):
        """Categorie heeft alle verwachte waarden."""
        expected = {
            "vlees",
            "gevogelte",
            "vis",
            "vegetarisch",
            "veganistisch",
        }
        actual = {c.value for c in Categorie}
        assert actual == expected

    def test_categorie_values(self):
        """Categorie waarden zijn correct."""
        assert Categorie.VLEES.value == "vlees"
        assert Categorie.GEVOGELTE.value == "gevogelte"
        assert Categorie.VIS.value == "vis"
        assert Categorie.VEGETARISCH.value == "vegetarisch"
        assert Categorie.VEGANISTISCH.value == "veganistisch"

    def test_categorie_from_string(self):
        """Categorie kan worden aangemaakt vanuit string."""
        assert Categorie("vlees") == Categorie.VLEES
        assert Categorie("gevogelte") == Categorie.GEVOGELTE
        assert Categorie("vis") == Categorie.VIS
        assert Categorie("vegetarisch") == Categorie.VEGETARISCH
        assert Categorie("veganistisch") == Categorie.VEGANISTISCH

    def test_categorie_invalid_value_raises(self):
        """Ongeldige waarde geeft ValueError."""
        with pytest.raises(ValueError):
            Categorie("ongeldig")

    def test_categorie_count(self):
        """Er zijn precies 5 categorieën."""
        assert len(Categorie) == 5


class TestBasis:
    """Tests voor de Basis enum (koolhydraatbasis)."""

    def test_basis_has_all_expected_values(self):
        """Basis heeft alle verwachte waarden."""
        expected = {
            "pasta",
            "rijst",
            "aardappel",
            "brood",
            "geen",
        }
        actual = {b.value for b in Basis}
        assert actual == expected

    def test_basis_values(self):
        """Basis waarden zijn correct."""
        assert Basis.PASTA.value == "pasta"
        assert Basis.RIJST.value == "rijst"
        assert Basis.AARDAPPEL.value == "aardappel"
        assert Basis.BROOD.value == "brood"
        assert Basis.GEEN.value == "geen"

    def test_basis_from_string(self):
        """Basis kan worden aangemaakt vanuit string."""
        assert Basis("pasta") == Basis.PASTA
        assert Basis("rijst") == Basis.RIJST
        assert Basis("aardappel") == Basis.AARDAPPEL
        assert Basis("brood") == Basis.BROOD
        assert Basis("geen") == Basis.GEEN

    def test_basis_invalid_value_raises(self):
        """Ongeldige waarde geeft ValueError."""
        with pytest.raises(ValueError):
            Basis("ongeldig")

    def test_basis_count(self):
        """Er zijn precies 5 basis types."""
        assert len(Basis) == 5
