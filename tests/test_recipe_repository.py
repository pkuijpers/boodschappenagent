"""Tests voor de RecipeRepository."""

import json
from pathlib import Path

import pytest

from boodschappenagent.models import Categorie, Recipe, Seizoen
from boodschappenagent.repository import RecipeRepository


@pytest.fixture
def repo() -> RecipeRepository:
    """Repository instance voor tests."""
    return RecipeRepository()


class TestRecipeRepositoryLoad:
    """Tests voor het laden van recepten uit JSON."""

    def test_load_recipe_from_json_file(
        self, repo: RecipeRepository, sample_json_data: dict, tmp_path: Path
    ):
        """Laad een recept uit een JSON bestand."""
        json_file = tmp_path / "carbonara.json"
        json_file.write_text(json.dumps(sample_json_data), encoding="utf-8")

        recipe = repo.load(json_file)

        assert recipe.id == "pasta-carbonara"
        assert recipe.naam == "Pasta Carbonara"
        assert recipe.categorie == Categorie.PASTA
        assert recipe.seizoenen == [Seizoen.ALLE]
        assert recipe.basis_porties == 2
        assert len(recipe.ingredienten) == 2
        assert recipe.ingredienten[0].naam == "spaghetti"
        assert recipe.ingredienten[1].opmerking == "in blokjes"

    def test_load_recipe_with_multiple_seasons(
        self, repo: RecipeRepository, tmp_path: Path
    ):
        """Laad een recept met meerdere seizoenen."""
        data = {
            "id": "erwtensoep",
            "naam": "Erwtensoep",
            "categorie": "soep",
            "seizoenen": ["herfst", "winter"],
            "basis_porties": 4,
            "ingredienten": [
                {
                    "naam": "erwten",
                    "hoeveelheid": 500,
                    "eenheid": "gram",
                    "opmerking": None,
                }
            ],
            "tags": [],
            "bereidingstijd_min": 120,
        }
        json_file = tmp_path / "erwtensoep.json"
        json_file.write_text(json.dumps(data), encoding="utf-8")

        recipe = repo.load(json_file)

        assert recipe.seizoenen == [Seizoen.HERFST, Seizoen.WINTER]

    def test_load_nonexistent_file_raises(self, repo: RecipeRepository, tmp_path: Path):
        """Laden van niet-bestaand bestand geeft FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            repo.load(tmp_path / "niet-bestaand.json")

    def test_load_invalid_json_raises(self, repo: RecipeRepository, tmp_path: Path):
        """Laden van ongeldig JSON geeft ValueError."""
        json_file = tmp_path / "invalid.json"
        json_file.write_text("{ invalid json }", encoding="utf-8")

        with pytest.raises(ValueError, match="JSON"):
            repo.load(json_file)

    def test_load_recipe_without_optional_fields(
        self, repo: RecipeRepository, tmp_path: Path
    ):
        """Laad een recept zonder optionele velden."""
        data = {
            "id": "simpel",
            "naam": "Simpel Recept",
            "categorie": "overig",
            "seizoenen": ["alle"],
            "basis_porties": 2,
            "ingredienten": [{"naam": "water", "hoeveelheid": 1, "eenheid": "liter"}],
            "bereidingstijd_min": 5,
        }
        json_file = tmp_path / "simpel.json"
        json_file.write_text(json.dumps(data), encoding="utf-8")

        recipe = repo.load(json_file)

        assert recipe.tags == []
        assert recipe.bereidingswijze is None
        assert recipe.bron is None


class TestRecipeRepositoryLoadAll:
    """Tests voor het laden van alle recepten uit een directory."""

    def test_load_all_recipes_from_directory(
        self, repo: RecipeRepository, tmp_path: Path
    ):
        """Laad alle recepten uit een directory."""
        # Maak twee JSON bestanden
        recipe1 = {
            "id": "recept-1",
            "naam": "Recept 1",
            "categorie": "pasta",
            "seizoenen": ["alle"],
            "basis_porties": 2,
            "ingredienten": [],
            "bereidingstijd_min": 10,
        }
        recipe2 = {
            "id": "recept-2",
            "naam": "Recept 2",
            "categorie": "soep",
            "seizoenen": ["winter"],
            "basis_porties": 4,
            "ingredienten": [],
            "bereidingstijd_min": 30,
        }
        (tmp_path / "recept1.json").write_text(json.dumps(recipe1), encoding="utf-8")
        (tmp_path / "recept2.json").write_text(json.dumps(recipe2), encoding="utf-8")

        recipes = repo.load_all(tmp_path)

        assert len(recipes) == 2
        ids = {r.id for r in recipes}
        assert ids == {"recept-1", "recept-2"}

    def test_load_all_from_empty_directory(
        self, repo: RecipeRepository, tmp_path: Path
    ):
        """Laden uit lege directory geeft lege lijst."""
        recipes = repo.load_all(tmp_path)
        assert recipes == []

    def test_load_all_ignores_non_json_files(
        self, repo: RecipeRepository, tmp_path: Path
    ):
        """Alleen JSON bestanden worden geladen."""
        recipe = {
            "id": "test",
            "naam": "Test",
            "categorie": "pasta",
            "seizoenen": ["alle"],
            "basis_porties": 2,
            "ingredienten": [],
            "bereidingstijd_min": 10,
        }
        (tmp_path / "recept.json").write_text(json.dumps(recipe), encoding="utf-8")
        (tmp_path / "readme.txt").write_text("Dit is geen recept", encoding="utf-8")
        (tmp_path / "data.xml").write_text("<xml/>", encoding="utf-8")

        recipes = repo.load_all(tmp_path)

        assert len(recipes) == 1
        assert recipes[0].id == "test"

    def test_load_all_recursive_from_subdirectories(
        self, repo: RecipeRepository, tmp_path: Path
    ):
        """Laad recepten recursief uit subdirectories."""
        # Maak subdirectories volgens de structuur in het plan
        pasta_dir = tmp_path / "pasta"
        soep_dir = tmp_path / "soep"
        pasta_dir.mkdir()
        soep_dir.mkdir()

        recipe1 = {
            "id": "spaghetti",
            "naam": "Spaghetti",
            "categorie": "pasta",
            "seizoenen": ["alle"],
            "basis_porties": 2,
            "ingredienten": [],
            "bereidingstijd_min": 20,
        }
        recipe2 = {
            "id": "tomatensoep",
            "naam": "Tomatensoep",
            "categorie": "soep",
            "seizoenen": ["herfst"],
            "basis_porties": 4,
            "ingredienten": [],
            "bereidingstijd_min": 45,
        }
        (pasta_dir / "spaghetti.json").write_text(json.dumps(recipe1), encoding="utf-8")
        (soep_dir / "tomatensoep.json").write_text(
            json.dumps(recipe2), encoding="utf-8"
        )

        recipes = repo.load_all(tmp_path)

        assert len(recipes) == 2
        ids = {r.id for r in recipes}
        assert ids == {"spaghetti", "tomatensoep"}


class TestRecipeRepositorySave:
    """Tests voor het opslaan van recepten naar JSON."""

    def test_save_recipe_to_json_file(
        self, repo: RecipeRepository, sample_recipe: Recipe, tmp_path: Path
    ):
        """Sla een recept op als JSON bestand."""
        json_file = tmp_path / "bolognese.json"

        repo.save(sample_recipe, json_file)

        assert json_file.exists()
        data = json.loads(json_file.read_text(encoding="utf-8"))
        assert data["id"] == "spaghetti-bolognese"
        assert data["naam"] == "Spaghetti Bolognese"
        assert data["categorie"] == "pasta"
        assert data["seizoenen"] == ["alle"]
        assert data["basis_porties"] == 2
        assert len(data["ingredienten"]) == 4

    def test_save_creates_parent_directories(
        self, repo: RecipeRepository, sample_recipe: Recipe, tmp_path: Path
    ):
        """Save maakt parent directories aan indien nodig."""
        json_file = tmp_path / "pasta" / "italiaans" / "bolognese.json"

        repo.save(sample_recipe, json_file)

        assert json_file.exists()

    def test_save_overwrites_existing_file(
        self, repo: RecipeRepository, sample_recipe: Recipe, tmp_path: Path
    ):
        """Save overschrijft een bestaand bestand."""
        json_file = tmp_path / "recept.json"
        json_file.write_text('{"old": "data"}', encoding="utf-8")

        repo.save(sample_recipe, json_file)

        data = json.loads(json_file.read_text(encoding="utf-8"))
        assert data["id"] == "spaghetti-bolognese"

    def test_saved_recipe_can_be_loaded(
        self, repo: RecipeRepository, sample_recipe: Recipe, tmp_path: Path
    ):
        """Een opgeslagen recept kan weer worden geladen."""
        json_file = tmp_path / "bolognese.json"

        repo.save(sample_recipe, json_file)
        loaded = repo.load(json_file)

        assert loaded.id == sample_recipe.id
        assert loaded.naam == sample_recipe.naam
        assert loaded.categorie == sample_recipe.categorie
        assert loaded.seizoenen == sample_recipe.seizoenen
        assert loaded.basis_porties == sample_recipe.basis_porties
        assert len(loaded.ingredienten) == len(sample_recipe.ingredienten)
        assert loaded.bereidingswijze == sample_recipe.bereidingswijze
        assert loaded.bron == sample_recipe.bron

    def test_save_with_pretty_print(
        self, repo: RecipeRepository, sample_recipe: Recipe, tmp_path: Path
    ):
        """JSON wordt opgeslagen met indentatie voor leesbaarheid."""
        json_file = tmp_path / "bolognese.json"

        repo.save(sample_recipe, json_file)

        content = json_file.read_text(encoding="utf-8")
        # Pretty print heeft meerdere regels
        assert content.count("\n") > 5


class TestRecipeRepositoryDelete:
    """Tests voor het verwijderen van recepten."""

    def test_delete_existing_file(self, repo: RecipeRepository, tmp_path: Path):
        """Verwijder een bestaand recept bestand."""
        json_file = tmp_path / "recept.json"
        json_file.write_text('{"test": "data"}', encoding="utf-8")

        repo.delete(json_file)

        assert not json_file.exists()

    def test_delete_nonexistent_file_raises(
        self, repo: RecipeRepository, tmp_path: Path
    ):
        """Verwijderen van niet-bestaand bestand geeft FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            repo.delete(tmp_path / "niet-bestaand.json")
