"""Tests voor SeizoenKalender — CO2-gebaseerde groente-seizoensfiltering."""

import json

import pytest

from boodschappenagent.models import Basis, Categorie, Ingredient, Recipe
from boodschappenagent.planner.seizoen_kalender import SeizoenKalender

ALLE_MAANDEN = [
    "jan",
    "feb",
    "mrt",
    "apr",
    "mei",
    "jun",
    "jul",
    "aug",
    "sep",
    "okt",
    "nov",
    "dec",
]
ZOMER = ["jun", "jul", "aug", "sep", "okt"]


def _groente(nr, naam, maanden):
    return {"nr": nr, "groente": naam, "lage_co2_maanden": maanden}


@pytest.fixture
def kalender_data(tmp_path):
    """Minimale seizoenskalender voor tests."""
    data = [
        _groente(1, "Tomaat", ZOMER),
        _groente(2, "Ui", ALLE_MAANDEN),
        _groente(3, "Paprika", ZOMER),
        _groente(4, "Champignon", ALLE_MAANDEN),
        _groente(5, "Boerenkool", ["nov", "dec", "jan", "feb"]),
        _groente(6, "Broccoli", ZOMER + ["nov"]),
        _groente(7, "Rucola", ["mei"] + ZOMER),
        _groente(8, "Bloemkool", ["mei"] + ZOMER + ["nov"]),
        _groente(9, "Aubergine", ZOMER),
        _groente(10, "Sperziebonen", ZOMER[:4]),
    ]
    path = tmp_path / "kalender.json"
    path.write_text(json.dumps(data))
    return path


@pytest.fixture
def kalender(kalender_data):
    """SeizoenKalender met testdata."""
    return SeizoenKalender(kalender_data)


def _make_recipe(id: str, ingredienten: list[Ingredient]) -> Recipe:
    """Helper om een test-recept te maken."""
    return Recipe(
        id=id,
        naam=id.replace("-", " ").title(),
        categorie=Categorie.VEGETARISCH,
        basis=Basis.GEEN,
        basis_porties=2,
        ingredienten=ingredienten,
    )


class TestSeizoenKalenderLaden:
    """Tests voor het laden van de seizoenskalender."""

    def test_laadt_kalender_uit_json(self, kalender):
        assert len(kalender._groenten) == 10

    def test_default_pad_laadt_productie_kalender(self):
        kalender = SeizoenKalender()
        assert len(kalender._groenten) > 0

    def test_ongeldig_pad_geeft_fout(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            SeizoenKalender(tmp_path / "niet-bestaand.json")


class TestGroentenInSeizoen:
    """Tests voor het ophalen van seizoensgroenten per maand."""

    def test_februari_bevat_boerenkool(self, kalender):
        groenten = kalender.groenten_in_seizoen("feb")
        assert "tomaat" not in groenten
        assert "boerenkool" in groenten
        assert "ui" in groenten
        assert "champignon" in groenten

    def test_juli_bevat_zomergroenten(self, kalender):
        groenten = kalender.groenten_in_seizoen("jul")
        assert "tomaat" in groenten
        assert "paprika" in groenten
        assert "broccoli" in groenten
        assert "boerenkool" not in groenten

    def test_ongeldige_maand_geeft_fout(self, kalender):
        with pytest.raises(ValueError, match="ongeldige maand"):
            kalender.groenten_in_seizoen("januari")


class TestMatchIngredient:
    """Tests voor fuzzy/substring matching van ingrediëntnamen."""

    def test_exacte_match(self, kalender):
        assert kalender.match_ingredient("tomaat") == "tomaat"

    def test_substring_match(self, kalender):
        assert kalender.match_ingredient("rode paprika") == "paprika"

    def test_samengesteld_woord(self, kalender):
        assert kalender.match_ingredient("kastanjechampignons") == "champignon"

    def test_cherrytomaten(self, kalender):
        assert kalender.match_ingredient("cherrytomaten") == "tomaat"

    def test_geen_match_voor_vlees(self, kalender):
        assert kalender.match_ingredient("rundergehakt") is None

    def test_geen_match_voor_kruiden(self, kalender):
        assert kalender.match_ingredient("olijfolie") is None

    def test_case_insensitive(self, kalender):
        assert kalender.match_ingredient("Rode Paprika") == "paprika"

    def test_ui_matcht_niet_op_aubergine(self, kalender):
        """Langste match wint — 'aubergine' matcht op 'aubergine', niet op 'ui'."""
        assert kalender.match_ingredient("aubergine") == "aubergine"

    def test_bloemkoolpizzabodem_matcht_bloemkool(self, kalender):
        assert kalender.match_ingredient("bloemkoolpizzabodem") == "bloemkool"

    def test_sperziebonen_matcht(self, kalender):
        assert kalender.match_ingredient("sperziebonen") == "sperziebonen"

    def test_biologische_rode_ui(self, kalender):
        assert kalender.match_ingredient("biologische rode ui") == "ui"


class TestReceptIsSeizoengeschikt:
    """Tests voor de meerderheidsregel (>50% groenten lage CO2)."""

    def test_alle_groenten_in_seizoen(self, kalender):
        """Stampot boerenkool in februari: boerenkool + ui = 2/2 = 100%."""
        recept = _make_recipe(
            "stampot",
            [
                Ingredient(naam="boerenkool", hoeveelheid=500, eenheid="gram"),
                Ingredient(naam="ui", hoeveelheid=1, eenheid="stuks"),
                Ingredient(naam="rookworst", hoeveelheid=1, eenheid="stuks"),
            ],
        )
        assert kalender.recept_is_seizoensgeschikt(recept, "feb") is True

    def test_meerderheid_in_seizoen(self, kalender):
        """Recept met 3 groenten, 2 in seizoen: 2/3 > 50%."""
        recept = _make_recipe(
            "gemengd",
            [
                Ingredient(naam="ui", hoeveelheid=1, eenheid="stuks"),
                Ingredient(naam="champignon", hoeveelheid=200, eenheid="gram"),
                Ingredient(
                    naam="tomaat", hoeveelheid=2, eenheid="stuks"
                ),  # niet in feb
            ],
        )
        assert kalender.recept_is_seizoensgeschikt(recept, "feb") is True

    def test_minderheid_in_seizoen(self, kalender):
        """Recept met 5 groenten, 2 in seizoen: 2/5 = 40% < 50%."""
        recept = _make_recipe(
            "pizza",
            [
                Ingredient(naam="bloemkoolpizzabodem", hoeveelheid=4, eenheid="stuks"),
                Ingredient(naam="rode paprika", hoeveelheid=1, eenheid="stuks"),
                Ingredient(naam="kastanjechampignons", hoeveelheid=250, eenheid="gram"),
                Ingredient(naam="cherrytomaten", hoeveelheid=250, eenheid="gram"),
                Ingredient(naam="rucola", hoeveelheid=75, eenheid="gram"),
                Ingredient(naam="mozzarella", hoeveelheid=2, eenheid="stuks"),
            ],
        )
        # feb: bloemkool ❌ (mei-nov), paprika ❌, champignon ✅, tomaat ❌, rucola ❌
        # = 1/5 = 20%
        assert kalender.recept_is_seizoensgeschikt(recept, "feb") is False

    def test_zelfde_recept_in_zomer_wel_geschikt(self, kalender):
        """Hetzelfde pizza-recept in juli: alles in seizoen."""
        recept = _make_recipe(
            "pizza",
            [
                Ingredient(naam="bloemkoolpizzabodem", hoeveelheid=4, eenheid="stuks"),
                Ingredient(naam="rode paprika", hoeveelheid=1, eenheid="stuks"),
                Ingredient(naam="kastanjechampignons", hoeveelheid=250, eenheid="gram"),
                Ingredient(naam="cherrytomaten", hoeveelheid=250, eenheid="gram"),
                Ingredient(naam="rucola", hoeveelheid=75, eenheid="gram"),
            ],
        )
        # jul: bloemkool ✅, paprika ✅, champignon ✅, tomaat ✅, rucola ✅ = 5/5
        assert kalender.recept_is_seizoensgeschikt(recept, "jul") is True

    def test_geen_herkenbare_groenten_is_geschikt(self, kalender):
        """Recept zonder herkenbare groenten is altijd geschikt."""
        recept = _make_recipe(
            "pasta",
            [
                Ingredient(naam="spaghetti", hoeveelheid=200, eenheid="gram"),
                Ingredient(naam="spek", hoeveelheid=150, eenheid="gram"),
                Ingredient(naam="ei", hoeveelheid=2, eenheid="stuks"),
            ],
        )
        assert kalender.recept_is_seizoensgeschikt(recept, "feb") is True

    def test_precies_50_procent_is_niet_geschikt(self, kalender):
        """>50% vereist, niet >=50%."""
        recept = _make_recipe(
            "mix",
            [
                Ingredient(
                    naam="tomaat", hoeveelheid=2, eenheid="stuks"
                ),  # niet in feb
                Ingredient(naam="ui", hoeveelheid=1, eenheid="stuks"),  # wel in feb
            ],
        )
        assert kalender.recept_is_seizoensgeschikt(recept, "feb") is False
