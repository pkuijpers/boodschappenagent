"""Tests voor extract_houdbaar_kandidaten()."""

from __future__ import annotations

from boodschappenagent.boodschappenlijst.normalizer import IngredientNormalizer
from boodschappenagent.models import Basis, Categorie, Ingredient, Recipe
from boodschappenagent.voorraadbeheer.presets import extract_houdbaar_kandidaten


def _make_recipe(
    recipe_id: str,
    ingredienten: list[Ingredient],
) -> Recipe:
    return Recipe(
        id=recipe_id,
        naam=f"Recept {recipe_id}",
        categorie=Categorie.VEGETARISCH,
        basis=Basis.PASTA,
        basis_porties=2,
        ingredienten=ingredienten,
        bereidingstijd_min=20,
    )


class TestExtractHoudbaarKandidaten:
    def test_returns_ingredients_above_min_freq(self) -> None:
        recipes = [
            _make_recipe(
                "r1",
                [Ingredient(naam="pasta", hoeveelheid=250, eenheid="gram")],
            ),
            _make_recipe(
                "r2",
                [Ingredient(naam="pasta", hoeveelheid=300, eenheid="gram")],
            ),
        ]
        normalizer = IngredientNormalizer()
        result = extract_houdbaar_kandidaten(recipes, normalizer, min_freq=2)

        namen = [naam for naam, _ in result]
        assert "pasta" in namen

    def test_excludes_below_min_freq(self) -> None:
        recipes = [
            _make_recipe(
                "r1",
                [Ingredient(naam="pasta", hoeveelheid=250, eenheid="gram")],
            ),
        ]
        normalizer = IngredientNormalizer()
        result = extract_houdbaar_kandidaten(recipes, normalizer, min_freq=2)

        namen = [naam for naam, _ in result]
        assert "pasta" not in namen

    def test_excludes_naar_smaak(self) -> None:
        recipes = [
            _make_recipe(
                "r1",
                [Ingredient(naam="peper", hoeveelheid=1, eenheid="naar smaak")],
            ),
            _make_recipe(
                "r2",
                [Ingredient(naam="peper", hoeveelheid=1, eenheid="naar smaak")],
            ),
            _make_recipe(
                "r3",
                [Ingredient(naam="peper", hoeveelheid=1, eenheid="naar smaak")],
            ),
        ]
        normalizer = IngredientNormalizer()
        result = extract_houdbaar_kandidaten(recipes, normalizer, min_freq=2)

        namen = [naam for naam, _ in result]
        assert "peper" not in namen

    def test_excludes_existing_names(self) -> None:
        recipes = [
            _make_recipe(
                "r1",
                [Ingredient(naam="pasta", hoeveelheid=250, eenheid="gram")],
            ),
            _make_recipe(
                "r2",
                [Ingredient(naam="pasta", hoeveelheid=300, eenheid="gram")],
            ),
        ]
        normalizer = IngredientNormalizer()
        result = extract_houdbaar_kandidaten(
            recipes, normalizer, min_freq=2, bestaande_namen={"pasta"}
        )

        namen = [naam for naam, _ in result]
        assert "pasta" not in namen

    def test_normalizes_ingredient_names(self) -> None:
        recipes = [
            _make_recipe(
                "r1",
                [Ingredient(naam="Uien", hoeveelheid=2, eenheid="stuks")],
            ),
            _make_recipe(
                "r2",
                [Ingredient(naam="uien", hoeveelheid=1, eenheid="stuks")],
            ),
            _make_recipe(
                "r3",
                [Ingredient(naam="ui", hoeveelheid=1, eenheid="stuks")],
            ),
        ]
        normalizer = IngredientNormalizer()
        result = extract_houdbaar_kandidaten(recipes, normalizer, min_freq=2)

        namen = [naam for naam, _ in result]
        # "uien" normaliseert naar "ui", dus alle 3 tellen als "ui"
        assert "ui" in namen

    def test_returns_sorted_by_freq_desc(self) -> None:
        recipes = [
            _make_recipe(
                "r1",
                [
                    Ingredient(naam="pasta", hoeveelheid=250, eenheid="gram"),
                    Ingredient(naam="tomaat", hoeveelheid=3, eenheid="stuks"),
                ],
            ),
            _make_recipe(
                "r2",
                [
                    Ingredient(naam="pasta", hoeveelheid=300, eenheid="gram"),
                    Ingredient(naam="tomaat", hoeveelheid=2, eenheid="stuks"),
                ],
            ),
            _make_recipe(
                "r3",
                [Ingredient(naam="pasta", hoeveelheid=200, eenheid="gram")],
            ),
        ]
        normalizer = IngredientNormalizer()
        result = extract_houdbaar_kandidaten(recipes, normalizer, min_freq=2)

        # pasta=3x, tomaat=2x → pasta eerst
        assert result[0] == ("pasta", 3)
        assert result[1] == ("tomaat", 2)

    def test_returns_tuples_of_name_and_freq(self) -> None:
        recipes = [
            _make_recipe(
                "r1",
                [Ingredient(naam="pasta", hoeveelheid=250, eenheid="gram")],
            ),
            _make_recipe(
                "r2",
                [Ingredient(naam="pasta", hoeveelheid=300, eenheid="gram")],
            ),
        ]
        normalizer = IngredientNormalizer()
        result = extract_houdbaar_kandidaten(recipes, normalizer, min_freq=2)

        assert result == [("pasta", 2)]

    def test_empty_recipes_returns_empty(self) -> None:
        normalizer = IngredientNormalizer()
        result = extract_houdbaar_kandidaten([], normalizer, min_freq=2)
        assert result == []

    def test_counts_ingredient_once_per_recipe(self) -> None:
        """An ingredient appearing 2x in one recipe counts as 1."""
        recipes = [
            _make_recipe(
                "r1",
                [
                    Ingredient(naam="pasta", hoeveelheid=250, eenheid="gram"),
                    Ingredient(naam="pasta", hoeveelheid=100, eenheid="gram"),
                ],
            ),
        ]
        normalizer = IngredientNormalizer()
        result = extract_houdbaar_kandidaten(recipes, normalizer, min_freq=2)

        namen = [naam for naam, _ in result]
        assert "pasta" not in namen  # Only in 1 recipe, not 2
