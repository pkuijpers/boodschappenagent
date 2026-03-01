"""Tests voor de PortionCalculator."""

import pytest

from boodschappenagent.models import Basis, Categorie, Ingredient, Recipe
from boodschappenagent.utils import PortionCalculator


@pytest.fixture
def calculator() -> PortionCalculator:
    """PortionCalculator instance voor tests."""
    return PortionCalculator()


@pytest.fixture
def sample_recipe() -> Recipe:
    """Voorbeeld recept voor tests."""
    return Recipe(
        id="test-recept",
        naam="Test Recept",
        categorie=Categorie.VLEES,
        basis=Basis.PASTA,
        basis_porties=2,
        ingredienten=[
            Ingredient(naam="spaghetti", hoeveelheid=200, eenheid="gram"),
            Ingredient(naam="ei", hoeveelheid=2, eenheid="stuks"),
            Ingredient(naam="knoflook", hoeveelheid=2, eenheid="teen"),
            Ingredient(naam="olijfolie", hoeveelheid=2, eenheid="eetlepel"),
            Ingredient(naam="zout", hoeveelheid=1, eenheid="snuf"),
            Ingredient(naam="melk", hoeveelheid=100, eenheid="ml"),
        ],
        tags=[],
        bereidingstijd_min=20,
    )


class TestRoundQuantity:
    """Tests voor het afronden van individuele hoeveelheden."""

    def test_round_gram_to_nearest_5(self, calculator: PortionCalculator):
        """Gram wordt afgerond naar dichtstbijzijnde 5."""
        assert calculator.round_quantity(123, "gram") == 125
        assert calculator.round_quantity(122, "gram") == 120
        assert calculator.round_quantity(100, "gram") == 100
        assert calculator.round_quantity(1, "gram") == 5  # minimum 5

    def test_round_ml_to_nearest_5(self, calculator: PortionCalculator):
        """Milliliter wordt afgerond naar dichtstbijzijnde 5."""
        assert calculator.round_quantity(123, "ml") == 125
        assert calculator.round_quantity(122, "ml") == 120
        assert calculator.round_quantity(1, "ml") == 5

    def test_round_stuks_up(self, calculator: PortionCalculator):
        """Stuks worden naar boven afgerond."""
        assert calculator.round_quantity(1.5, "stuks") == 2
        assert calculator.round_quantity(1.1, "stuks") == 2
        assert calculator.round_quantity(2.0, "stuks") == 2
        assert calculator.round_quantity(0.5, "stuks") == 1

    def test_round_teen_up(self, calculator: PortionCalculator):
        """Teentjes (knoflook) worden naar boven afgerond."""
        assert calculator.round_quantity(1.5, "teen") == 2
        assert calculator.round_quantity(2.3, "teen") == 3
        assert calculator.round_quantity(3.0, "teen") == 3

    def test_round_eetlepel_to_half(self, calculator: PortionCalculator):
        """Eetlepels worden afgerond naar 0.5."""
        assert calculator.round_quantity(1.3, "eetlepel") == 1.5
        assert calculator.round_quantity(1.7, "eetlepel") == 1.5
        assert calculator.round_quantity(1.8, "eetlepel") == 2.0
        assert calculator.round_quantity(2.0, "eetlepel") == 2.0

    def test_round_theelepel_to_half(self, calculator: PortionCalculator):
        """Theelepels worden afgerond naar 0.5."""
        assert calculator.round_quantity(0.3, "theelepel") == 0.5
        assert calculator.round_quantity(0.7, "theelepel") == 0.5
        assert calculator.round_quantity(0.8, "theelepel") == 1.0

    def test_round_snuf_unchanged(self, calculator: PortionCalculator):
        """Snuf blijft ongewijzigd (altijd 1)."""
        assert calculator.round_quantity(1.5, "snuf") == 1.5
        assert calculator.round_quantity(2.0, "snuf") == 2.0

    def test_round_naar_smaak_unchanged(self, calculator: PortionCalculator):
        """'Naar smaak' blijft ongewijzigd."""
        assert calculator.round_quantity(1.5, "naar smaak") == 1.5

    def test_round_liter_to_nearest_tenth(self, calculator: PortionCalculator):
        """Liters worden afgerond naar 0.1."""
        assert calculator.round_quantity(0.33, "liter") == 0.3
        assert calculator.round_quantity(0.37, "liter") == 0.4
        assert calculator.round_quantity(1.25, "liter") == 1.3

    def test_round_unknown_unit_unchanged(self, calculator: PortionCalculator):
        """Onbekende eenheden blijven ongewijzigd."""
        assert calculator.round_quantity(1.234, "onbekend") == 1.234


class TestRoundIngredient:
    """Tests voor het afronden van een Ingredient."""

    def test_round_ingredient_returns_new_instance(self, calculator: PortionCalculator):
        """Round retourneert een nieuw Ingredient object."""
        original = Ingredient(naam="bloem", hoeveelheid=123, eenheid="gram")

        rounded = calculator.round_ingredient(original)

        assert rounded is not original
        assert original.hoeveelheid == 123  # ongewijzigd
        assert rounded.hoeveelheid == 125

    def test_round_ingredient_preserves_other_fields(
        self, calculator: PortionCalculator
    ):
        """Round behoudt naam, eenheid en opmerking."""
        original = Ingredient(
            naam="ui", hoeveelheid=1.5, eenheid="stuks", opmerking="fijngesneden"
        )

        rounded = calculator.round_ingredient(original)

        assert rounded.naam == "ui"
        assert rounded.eenheid == "stuks"
        assert rounded.opmerking == "fijngesneden"
        assert rounded.hoeveelheid == 2


class TestScaleRecipe:
    """Tests voor het schalen van een recept met afronding."""

    def test_scale_recipe_with_rounding(
        self, calculator: PortionCalculator, sample_recipe: Recipe
    ):
        """Schaal recept naar 3 porties met praktische afrondingen."""
        # basis_porties = 2, scale naar 3 = factor 1.5
        scaled = calculator.scale_recipe(sample_recipe, 3)

        assert scaled.basis_porties == 3

        # spaghetti: 200 * 1.5 = 300 gram (al rond)
        assert scaled.ingredienten[0].hoeveelheid == 300

        # ei: 2 * 1.5 = 3 stuks (al rond)
        assert scaled.ingredienten[1].hoeveelheid == 3

        # knoflook: 2 * 1.5 = 3 teen (al rond)
        assert scaled.ingredienten[2].hoeveelheid == 3

        # olijfolie: 2 * 1.5 = 3 eetlepel (al rond)
        assert scaled.ingredienten[3].hoeveelheid == 3

        # zout: 1 * 1.5 = 1.5 snuf (niet afgerond)
        assert scaled.ingredienten[4].hoeveelheid == 1.5

        # melk: 100 * 1.5 = 150 ml (al rond)
        assert scaled.ingredienten[5].hoeveelheid == 150

    def test_scale_recipe_awkward_portions(
        self, calculator: PortionCalculator, sample_recipe: Recipe
    ):
        """Schaal recept naar 5 porties (factor 2.5) met afrondingen."""
        scaled = calculator.scale_recipe(sample_recipe, 5)

        # spaghetti: 200 * 2.5 = 500 gram
        assert scaled.ingredienten[0].hoeveelheid == 500

        # ei: 2 * 2.5 = 5 stuks
        assert scaled.ingredienten[1].hoeveelheid == 5

        # knoflook: 2 * 2.5 = 5 teen
        assert scaled.ingredienten[2].hoeveelheid == 5

        # olijfolie: 2 * 2.5 = 5 eetlepel
        assert scaled.ingredienten[3].hoeveelheid == 5

        # melk: 100 * 2.5 = 250 ml
        assert scaled.ingredienten[5].hoeveelheid == 250

    def test_scale_recipe_to_one_portion(
        self, calculator: PortionCalculator, sample_recipe: Recipe
    ):
        """Schaal recept naar 1 portie (factor 0.5)."""
        scaled = calculator.scale_recipe(sample_recipe, 1)

        # spaghetti: 200 * 0.5 = 100 gram
        assert scaled.ingredienten[0].hoeveelheid == 100

        # ei: 2 * 0.5 = 1 stuks
        assert scaled.ingredienten[1].hoeveelheid == 1

        # knoflook: 2 * 0.5 = 1 teen
        assert scaled.ingredienten[2].hoeveelheid == 1

        # olijfolie: 2 * 0.5 = 1 eetlepel
        assert scaled.ingredienten[3].hoeveelheid == 1

        # melk: 100 * 0.5 = 50 ml
        assert scaled.ingredienten[5].hoeveelheid == 50

    def test_scale_recipe_preserves_metadata(
        self, calculator: PortionCalculator, sample_recipe: Recipe
    ):
        """Schalen behoudt alle metadata van het recept."""
        scaled = calculator.scale_recipe(sample_recipe, 4)

        assert scaled.id == sample_recipe.id
        assert scaled.naam == sample_recipe.naam
        assert scaled.categorie == sample_recipe.categorie
        assert scaled.tags == sample_recipe.tags
        assert scaled.bereidingstijd_min == sample_recipe.bereidingstijd_min

    def test_scale_recipe_returns_new_instance(
        self, calculator: PortionCalculator, sample_recipe: Recipe
    ):
        """Schalen retourneert een nieuw Recipe object."""
        scaled = calculator.scale_recipe(sample_recipe, 4)

        assert scaled is not sample_recipe
        assert sample_recipe.basis_porties == 2  # ongewijzigd

    def test_scale_recipe_invalid_portions_raises(
        self, calculator: PortionCalculator, sample_recipe: Recipe
    ):
        """Ongeldige porties geeft ValueError."""
        with pytest.raises(ValueError, match="porties"):
            calculator.scale_recipe(sample_recipe, 0)

        with pytest.raises(ValueError, match="porties"):
            calculator.scale_recipe(sample_recipe, -1)


class TestEdgeCases:
    """Tests voor edge cases."""

    def test_very_small_quantities_gram(self, calculator: PortionCalculator):
        """Zeer kleine gram hoeveelheden worden minimum 5."""
        assert calculator.round_quantity(0.1, "gram") == 5
        assert calculator.round_quantity(2, "gram") == 5
        assert calculator.round_quantity(3, "gram") == 5

    def test_scale_with_rounding_three_portions_from_four(
        self, calculator: PortionCalculator
    ):
        """Schaal van 4 naar 3 porties met onhandige getallen."""
        recipe = Recipe(
            id="test",
            naam="Test",
            categorie=Categorie.VEGETARISCH,
            basis=Basis.GEEN,
            basis_porties=4,
            ingredienten=[
                Ingredient(naam="bloem", hoeveelheid=500, eenheid="gram"),
                Ingredient(naam="ei", hoeveelheid=3, eenheid="stuks"),
            ],
            tags=[],
            bereidingstijd_min=10,
        )

        scaled = calculator.scale_recipe(recipe, 3)

        # bloem: 500 * 0.75 = 375 gram
        assert scaled.ingredienten[0].hoeveelheid == 375

        # ei: 3 * 0.75 = 2.25 → 3 stuks (naar boven)
        assert scaled.ingredienten[1].hoeveelheid == 3
