"""Pytest configuration and fixtures."""

import pytest

from boodschappenagent.models import Categorie, Ingredient, Recipe, Seizoen


@pytest.fixture
def sample_ingredients() -> list[Ingredient]:
    """Voorbeeld ingrediënten voor tests."""
    return [
        Ingredient(naam="spaghetti", hoeveelheid=200, eenheid="gram"),
        Ingredient(naam="rundergehakt", hoeveelheid=250, eenheid="gram"),
        Ingredient(naam="ui", hoeveelheid=1, eenheid="stuks", opmerking="fijngesneden"),
        Ingredient(naam="passata", hoeveelheid=400, eenheid="gram"),
    ]


@pytest.fixture
def sample_recipe(sample_ingredients: list[Ingredient]) -> Recipe:
    """Voorbeeld recept voor tests."""
    return Recipe(
        id="spaghetti-bolognese",
        naam="Spaghetti Bolognese",
        categorie=Categorie.PASTA,
        seizoenen=[Seizoen.ALLE],
        basis_porties=2,
        ingredienten=sample_ingredients,
        tags=["vlees", "italiaans"],
        bereidingstijd_min=35,
        bereidingswijze="1. Kook de spaghetti...",
        bron="oma's kookboek",
    )


@pytest.fixture
def sample_json_data() -> dict:
    """Voorbeeld JSON data voor tests."""
    return {
        "id": "pasta-carbonara",
        "naam": "Pasta Carbonara",
        "categorie": "pasta",
        "seizoenen": ["alle"],
        "basis_porties": 2,
        "ingredienten": [
            {
                "naam": "spaghetti",
                "hoeveelheid": 200,
                "eenheid": "gram",
                "opmerking": None,
            },
            {
                "naam": "spek",
                "hoeveelheid": 150,
                "eenheid": "gram",
                "opmerking": "in blokjes",
            },
        ],
        "tags": ["vlees", "italiaans"],
        "bereidingstijd_min": 25,
        "bereidingswijze": "1. Kook de pasta...",
        "bron": None,
    }
