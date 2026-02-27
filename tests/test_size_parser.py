"""Tests voor AH product size parser."""

import pytest

from boodschappenagent.ah.size_parser import ParsedSize, parse_size


class TestParseSize:
    """Tests voor parse_size functie."""

    def test_eenvoudig_liter(self):
        assert parse_size("1 l") == ParsedSize(1.0, "l")

    def test_eenvoudig_gram(self):
        assert parse_size("300 g") == ParsedSize(300.0, "g")

    def test_milliliter(self):
        assert parse_size("500 ml") == ParsedSize(500.0, "ml")

    def test_kilogram(self):
        assert parse_size("1 kg") == ParsedSize(1.0, "kg")

    def test_stuks(self):
        assert parse_size("2 stuks") == ParsedSize(2.0, "stuks")

    def test_gram_voluit(self):
        assert parse_size("100 gram") == ParsedSize(100.0, "gram")

    def test_liter_voluit(self):
        assert parse_size("1,5 liter") == ParsedSize(1.5, "liter")

    def test_nederlandse_komma(self):
        assert parse_size("1,5 l") == ParsedSize(1.5, "l")

    def test_nederlandse_komma_half(self):
        assert parse_size("0,5 l") == ParsedSize(0.5, "l")

    def test_ca_prefix(self):
        """AH gebruikt soms 'ca.' voor geschat gewicht."""
        assert parse_size("ca. 300 g") == ParsedSize(300.0, "g")

    def test_bereik_neemt_eerste_getal(self):
        """Bij bereik (2-3 stuks) neem het eerste getal (conservatief)."""
        assert parse_size("2-3 stuks") == ParsedSize(2.0, "stuks")

    def test_lege_string(self):
        assert parse_size("") is None

    def test_none_achtig(self):
        assert parse_size("   ") is None

    def test_alleen_tekst_zonder_getal(self):
        assert parse_size("stuk") is None

    def test_onparseerbaar(self):
        assert parse_size("div. formaten") is None

    def test_whitespace_wordt_gestript(self):
        assert parse_size("  1 l  ") == ParsedSize(1.0, "l")

    def test_groot_getal(self):
        assert parse_size("750 ml") == ParsedSize(750.0, "ml")

    def test_heel_getal_zonder_decimaal(self):
        assert parse_size("6 stuks") == ParsedSize(6.0, "stuks")

    def test_stuk_enkelvoud(self):
        assert parse_size("1 stuk") == ParsedSize(1.0, "stuk")

    def test_deciliter(self):
        assert parse_size("2 dl") == ParsedSize(2.0, "dl")


class TestParsedSize:
    """Tests voor ParsedSize dataclass."""

    def test_frozen(self):
        ps = ParsedSize(1.0, "l")
        with pytest.raises(AttributeError):
            ps.hoeveelheid = 2.0

    def test_equality(self):
        assert ParsedSize(1.0, "l") == ParsedSize(1.0, "l")

    def test_inequality(self):
        assert ParsedSize(1.0, "l") != ParsedSize(2.0, "l")
