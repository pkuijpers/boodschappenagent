"""Tests voor de Recipe dataclass."""

import pytest

from boodschappenagent.models.enums import Basis, Categorie
from boodschappenagent.models.ingredient import Ingredient
from boodschappenagent.models.recipe import Recipe


class TestRecipeCreation:
    """Tests voor het aanmaken van Recipe objecten."""

    def test_create_recipe_with_required_fields(
        self, sample_ingredients: list[Ingredient]
    ):
        """Een recept kan worden aangemaakt met alle verplichte velden."""
        recipe = Recipe(
            id="pasta-carbonara",
            naam="Pasta Carbonara",
            categorie=Categorie.VLEES,
            basis=Basis.PASTA,
            basis_porties=2,
            ingredienten=sample_ingredients,
            tags=["italiaans"],
            bereidingstijd_min=25,
        )

        assert recipe.id == "pasta-carbonara"
        assert recipe.naam == "Pasta Carbonara"
        assert recipe.categorie == Categorie.VLEES
        assert recipe.basis == Basis.PASTA
        assert recipe.basis_porties == 2
        assert len(recipe.ingredienten) == 4
        assert recipe.tags == ["italiaans"]
        assert recipe.bereidingstijd_min == 25
        assert recipe.bereidingswijze is None
        assert recipe.bron is None

    def test_create_recipe_with_optional_fields(
        self, sample_ingredients: list[Ingredient]
    ):
        """Een recept kan worden aangemaakt met optionele velden."""
        recipe = Recipe(
            id="lasagne",
            naam="Lasagne",
            categorie=Categorie.VLEES,
            basis=Basis.PASTA,
            basis_porties=4,
            ingredienten=sample_ingredients,
            tags=["italiaans"],
            bereidingstijd_min=90,
            bereidingswijze="1. Maak de ragusaus...",
            bron="oma's kookboek",
        )

        assert recipe.bereidingswijze == "1. Maak de ragusaus..."
        assert recipe.bron == "oma's kookboek"


class TestRecipeIdValidation:
    """Tests voor validatie van het id veld (slug format)."""

    def test_id_must_be_lowercase(self, sample_ingredients: list[Ingredient]):
        """Id moet lowercase zijn."""
        with pytest.raises(ValueError, match="id"):
            Recipe(
                id="Spaghetti-Bolognese",
                naam="Spaghetti Bolognese",
                categorie=Categorie.VLEES,
                basis=Basis.PASTA,
                basis_porties=2,
                ingredienten=sample_ingredients,
                tags=[],
                bereidingstijd_min=30,
            )

    def test_id_cannot_contain_spaces(self, sample_ingredients: list[Ingredient]):
        """Id mag geen spaties bevatten."""
        with pytest.raises(ValueError, match="id"):
            Recipe(
                id="spaghetti bolognese",
                naam="Spaghetti Bolognese",
                categorie=Categorie.VLEES,
                basis=Basis.PASTA,
                basis_porties=2,
                ingredienten=sample_ingredients,
                tags=[],
                bereidingstijd_min=30,
            )

    def test_id_cannot_be_empty(self, sample_ingredients: list[Ingredient]):
        """Id mag niet leeg zijn."""
        with pytest.raises(ValueError, match="id"):
            Recipe(
                id="",
                naam="Spaghetti Bolognese",
                categorie=Categorie.VLEES,
                basis=Basis.PASTA,
                basis_porties=2,
                ingredienten=sample_ingredients,
                tags=[],
                bereidingstijd_min=30,
            )

    def test_id_can_contain_hyphens_and_numbers(
        self, sample_ingredients: list[Ingredient]
    ):
        """Id mag koppeltekens en cijfers bevatten."""
        recipe = Recipe(
            id="pasta-pesto-2",
            naam="Pasta Pesto",
            categorie=Categorie.VEGETARISCH,
            basis=Basis.PASTA,
            basis_porties=2,
            ingredienten=sample_ingredients,
            tags=[],
            bereidingstijd_min=20,
        )

        assert recipe.id == "pasta-pesto-2"


class TestRecipeNaamValidation:
    """Tests voor validatie van het naam veld."""

    def test_naam_cannot_be_empty(self, sample_ingredients: list[Ingredient]):
        """Naam mag niet leeg zijn."""
        with pytest.raises(ValueError, match="naam"):
            Recipe(
                id="test",
                naam="",
                categorie=Categorie.VLEES,
                basis=Basis.PASTA,
                basis_porties=2,
                ingredienten=sample_ingredients,
                tags=[],
                bereidingstijd_min=30,
            )

    def test_naam_cannot_exceed_100_characters(
        self, sample_ingredients: list[Ingredient]
    ):
        """Naam mag niet langer dan 100 karakters zijn."""
        with pytest.raises(ValueError, match="naam"):
            Recipe(
                id="test",
                naam="A" * 101,
                categorie=Categorie.VLEES,
                basis=Basis.PASTA,
                basis_porties=2,
                ingredienten=sample_ingredients,
                tags=[],
                bereidingstijd_min=30,
            )

    def test_naam_of_100_characters_is_valid(
        self, sample_ingredients: list[Ingredient]
    ):
        """Naam van precies 100 karakters is geldig."""
        recipe = Recipe(
            id="test",
            naam="A" * 100,
            categorie=Categorie.VLEES,
            basis=Basis.PASTA,
            basis_porties=2,
            ingredienten=sample_ingredients,
            tags=[],
            bereidingstijd_min=30,
        )

        assert len(recipe.naam) == 100


class TestRecipeBasisPortiesValidation:
    """Tests voor validatie van basis_porties."""

    def test_basis_porties_must_be_at_least_one(
        self, sample_ingredients: list[Ingredient]
    ):
        """Basis porties moet minimaal 1 zijn."""
        with pytest.raises(ValueError, match="basis_porties"):
            Recipe(
                id="test",
                naam="Test",
                categorie=Categorie.VLEES,
                basis=Basis.PASTA,
                basis_porties=0,
                ingredienten=sample_ingredients,
                tags=[],
                bereidingstijd_min=30,
            )

    def test_basis_porties_cannot_be_negative(
        self, sample_ingredients: list[Ingredient]
    ):
        """Basis porties mag niet negatief zijn."""
        with pytest.raises(ValueError, match="basis_porties"):
            Recipe(
                id="test",
                naam="Test",
                categorie=Categorie.VLEES,
                basis=Basis.PASTA,
                basis_porties=-1,
                ingredienten=sample_ingredients,
                tags=[],
                bereidingstijd_min=30,
            )


class TestRecipeBereidingstijdValidation:
    """Tests voor validatie van bereidingstijd_min."""

    def test_bereidingstijd_must_be_positive(
        self, sample_ingredients: list[Ingredient]
    ):
        """Bereidingstijd moet groter dan 0 zijn."""
        with pytest.raises(ValueError, match="bereidingstijd"):
            Recipe(
                id="test",
                naam="Test",
                categorie=Categorie.VLEES,
                basis=Basis.PASTA,
                basis_porties=2,
                ingredienten=sample_ingredients,
                tags=[],
                bereidingstijd_min=0,
            )

    def test_bereidingstijd_cannot_be_negative(
        self, sample_ingredients: list[Ingredient]
    ):
        """Bereidingstijd mag niet negatief zijn."""
        with pytest.raises(ValueError, match="bereidingstijd"):
            Recipe(
                id="test",
                naam="Test",
                categorie=Categorie.VLEES,
                basis=Basis.PASTA,
                basis_porties=2,
                ingredienten=sample_ingredients,
                tags=[],
                bereidingstijd_min=-10,
            )


class TestRecipeCategorieValidation:
    """Tests voor validatie van categorie."""

    def test_all_valid_categories(self, sample_ingredients: list[Ingredient]):
        """Alle geldige categorieën worden geaccepteerd."""
        for categorie in Categorie:
            recipe = Recipe(
                id="test",
                naam="Test",
                categorie=categorie,
                basis=Basis.PASTA,
                basis_porties=2,
                ingredienten=sample_ingredients,
                tags=[],
                bereidingstijd_min=30,
            )
            assert recipe.categorie == categorie


class TestRecipeBasisValidation:
    """Tests voor validatie van basis."""

    def test_all_valid_basis_values(self, sample_ingredients: list[Ingredient]):
        """Alle geldige basis waarden worden geaccepteerd."""
        for basis in Basis:
            recipe = Recipe(
                id="test",
                naam="Test",
                categorie=Categorie.VLEES,
                basis=basis,
                basis_porties=2,
                ingredienten=sample_ingredients,
                tags=[],
                bereidingstijd_min=30,
            )
            assert recipe.basis == basis


class TestRecipeScaleToPortions:
    """Tests voor de scale_to_portions methode."""

    def test_scale_doubles_ingredients(self, sample_recipe: Recipe):
        """Scale naar dubbele porties verdubbelt ingrediënten."""
        # basis_porties = 2, scale naar 4 = factor 2
        scaled = sample_recipe.scale_to_portions(4)

        assert scaled.basis_porties == 4
        # Originele hoeveelheden: 200, 250, 1, 400
        assert scaled.ingredienten[0].hoeveelheid == 400  # spaghetti
        assert scaled.ingredienten[1].hoeveelheid == 500  # gehakt
        assert scaled.ingredienten[2].hoeveelheid == 2  # ui
        assert scaled.ingredienten[3].hoeveelheid == 800  # passata

    def test_scale_halves_ingredients(self, sample_recipe: Recipe):
        """Scale naar helft van porties halveert ingrediënten."""
        # basis_porties = 2, scale naar 1 = factor 0.5
        scaled = sample_recipe.scale_to_portions(1)

        assert scaled.basis_porties == 1
        assert scaled.ingredienten[0].hoeveelheid == 100  # spaghetti
        assert scaled.ingredienten[1].hoeveelheid == 125  # gehakt

    def test_scale_returns_new_instance(self, sample_recipe: Recipe):
        """Scale retourneert een nieuw object, muteert niet het origineel."""
        scaled = sample_recipe.scale_to_portions(4)

        assert sample_recipe.basis_porties == 2  # Origineel ongewijzigd
        assert scaled.basis_porties == 4
        assert sample_recipe is not scaled

    def test_scale_preserves_other_fields(self, sample_recipe: Recipe):
        """Scale behoudt alle andere velden."""
        scaled = sample_recipe.scale_to_portions(4)

        assert scaled.id == sample_recipe.id
        assert scaled.naam == sample_recipe.naam
        assert scaled.categorie == sample_recipe.categorie
        assert scaled.tags == sample_recipe.tags
        assert scaled.bereidingstijd_min == sample_recipe.bereidingstijd_min

    def test_scale_to_same_portions_returns_copy(self, sample_recipe: Recipe):
        """Scale naar dezelfde porties retourneert een kopie."""
        scaled = sample_recipe.scale_to_portions(2)

        assert scaled.basis_porties == 2
        assert scaled.ingredienten[0].hoeveelheid == 200
        assert scaled is not sample_recipe

    def test_scale_portions_must_be_positive(self, sample_recipe: Recipe):
        """Porties moeten positief zijn."""
        with pytest.raises(ValueError, match="porties"):
            sample_recipe.scale_to_portions(0)

        with pytest.raises(ValueError, match="porties"):
            sample_recipe.scale_to_portions(-1)

    def test_scale_to_three_portions(self, sample_recipe: Recipe):
        """Scale naar 3 porties (factor 1.5)."""
        scaled = sample_recipe.scale_to_portions(3)

        assert scaled.basis_porties == 3
        assert scaled.ingredienten[0].hoeveelheid == 300  # 200 * 1.5
        assert scaled.ingredienten[1].hoeveelheid == 375  # 250 * 1.5
