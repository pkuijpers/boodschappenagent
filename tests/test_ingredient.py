"""Tests voor de Ingredient dataclass."""

import pytest

from boodschappenagent.models.ingredient import Ingredient


class TestIngredientCreation:
    """Tests voor het aanmaken van Ingredient objecten."""

    def test_create_ingredient_with_all_fields(self):
        """Een ingredient kan worden aangemaakt met alle velden."""
        ingredient = Ingredient(
            naam="ui",
            hoeveelheid=2.0,
            eenheid="stuks",
            opmerking="fijngesneden",
        )

        assert ingredient.naam == "ui"
        assert ingredient.hoeveelheid == 2.0
        assert ingredient.eenheid == "stuks"
        assert ingredient.opmerking == "fijngesneden"

    def test_create_ingredient_without_opmerking(self):
        """Een ingredient kan worden aangemaakt zonder opmerking."""
        ingredient = Ingredient(
            naam="knoflook",
            hoeveelheid=3.0,
            eenheid="teen",
        )

        assert ingredient.naam == "knoflook"
        assert ingredient.hoeveelheid == 3.0
        assert ingredient.eenheid == "teen"
        assert ingredient.opmerking is None

    def test_create_ingredient_with_float_hoeveelheid(self):
        """Hoeveelheid kan een float zijn (bijv. 0.5 voor een half)."""
        ingredient = Ingredient(
            naam="citroen",
            hoeveelheid=0.5,
            eenheid="stuks",
        )

        assert ingredient.hoeveelheid == 0.5


class TestIngredientValidation:
    """Tests voor validatie van Ingredient velden."""

    def test_hoeveelheid_must_be_positive(self):
        """Hoeveelheid moet groter dan 0 zijn."""
        with pytest.raises(ValueError, match="hoeveelheid"):
            Ingredient(
                naam="ui",
                hoeveelheid=0,
                eenheid="stuks",
            )

    def test_hoeveelheid_cannot_be_negative(self):
        """Hoeveelheid mag niet negatief zijn."""
        with pytest.raises(ValueError, match="hoeveelheid"):
            Ingredient(
                naam="ui",
                hoeveelheid=-1,
                eenheid="stuks",
            )

    def test_naam_cannot_be_empty(self):
        """Naam mag niet leeg zijn."""
        with pytest.raises(ValueError, match="naam"):
            Ingredient(
                naam="",
                hoeveelheid=1,
                eenheid="stuks",
            )

    def test_naam_cannot_be_whitespace_only(self):
        """Naam mag niet alleen whitespace zijn."""
        with pytest.raises(ValueError, match="naam"):
            Ingredient(
                naam="   ",
                hoeveelheid=1,
                eenheid="stuks",
            )


class TestIngredientScale:
    """Tests voor de scale methode."""

    def test_scale_doubles_hoeveelheid(self):
        """Scale met factor 2 verdubbelt de hoeveelheid."""
        ingredient = Ingredient(
            naam="gehakt",
            hoeveelheid=250,
            eenheid="gram",
        )

        scaled = ingredient.scale(2.0)

        assert scaled.hoeveelheid == 500
        assert scaled.naam == "gehakt"
        assert scaled.eenheid == "gram"

    def test_scale_halves_hoeveelheid(self):
        """Scale met factor 0.5 halveert de hoeveelheid."""
        ingredient = Ingredient(
            naam="melk",
            hoeveelheid=200,
            eenheid="ml",
        )

        scaled = ingredient.scale(0.5)

        assert scaled.hoeveelheid == 100

    def test_scale_returns_new_instance(self):
        """Scale retourneert een nieuw object, muteert niet het origineel."""
        original = Ingredient(
            naam="bloem",
            hoeveelheid=100,
            eenheid="gram",
        )

        scaled = original.scale(2.0)

        assert original.hoeveelheid == 100  # Origineel ongewijzigd
        assert scaled.hoeveelheid == 200
        assert original is not scaled

    def test_scale_preserves_opmerking(self):
        """Scale behoudt de opmerking."""
        ingredient = Ingredient(
            naam="ui",
            hoeveelheid=1,
            eenheid="stuks",
            opmerking="fijngesneden",
        )

        scaled = ingredient.scale(3.0)

        assert scaled.opmerking == "fijngesneden"

    def test_scale_with_factor_one_returns_copy(self):
        """Scale met factor 1 retourneert een kopie met dezelfde waardes."""
        ingredient = Ingredient(
            naam="zout",
            hoeveelheid=1,
            eenheid="snuf",
        )

        scaled = ingredient.scale(1.0)

        assert scaled.hoeveelheid == 1
        assert scaled is not ingredient

    def test_scale_factor_must_be_positive(self):
        """Scale factor moet positief zijn."""
        ingredient = Ingredient(
            naam="peper",
            hoeveelheid=1,
            eenheid="snuf",
        )

        with pytest.raises(ValueError, match="factor"):
            ingredient.scale(0)

        with pytest.raises(ValueError, match="factor"):
            ingredient.scale(-1)
