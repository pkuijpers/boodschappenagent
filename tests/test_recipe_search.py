"""Tests voor RecipeSearch zoek- en filterfunctionaliteit."""

import json

import pytest

from boodschappenagent.models import Basis, Categorie, Ingredient, Recipe, Seizoen
from boodschappenagent.planner.seizoen_kalender import SeizoenKalender
from boodschappenagent.repository.recipe_search import RecipeSearch


@pytest.fixture
def sample_recipes() -> list[Recipe]:
    """Verzameling recepten voor tests."""
    return [
        Recipe(
            id="spaghetti-bolognese",
            naam="Spaghetti Bolognese",
            categorie=Categorie.VLEES,
            basis=Basis.PASTA,
            seizoenen=[Seizoen.ALLE],
            basis_porties=2,
            ingredienten=[
                Ingredient(naam="spaghetti", hoeveelheid=200, eenheid="gram"),
                Ingredient(naam="gehakt", hoeveelheid=250, eenheid="gram"),
            ],
            tags=["italiaans", "budget"],
            bereidingstijd_min=35,
        ),
        Recipe(
            id="pasta-pesto",
            naam="Pasta met Pesto",
            categorie=Categorie.VEGETARISCH,
            basis=Basis.PASTA,
            seizoenen=[Seizoen.LENTE, Seizoen.ZOMER],
            basis_porties=2,
            ingredienten=[
                Ingredient(naam="pasta", hoeveelheid=200, eenheid="gram"),
            ],
            tags=["italiaans", "snel"],
            bereidingstijd_min=15,
        ),
        Recipe(
            id="erwtensoep",
            naam="Erwtensoep",
            categorie=Categorie.VLEES,
            basis=Basis.GEEN,
            seizoenen=[Seizoen.HERFST, Seizoen.WINTER],
            basis_porties=4,
            ingredienten=[
                Ingredient(naam="erwten", hoeveelheid=500, eenheid="gram"),
            ],
            tags=["hollands", "budget"],
            bereidingstijd_min=120,
        ),
        Recipe(
            id="tomatensoep",
            naam="Tomatensoep",
            categorie=Categorie.VEGETARISCH,
            basis=Basis.GEEN,
            seizoenen=[Seizoen.ALLE],
            basis_porties=4,
            ingredienten=[
                Ingredient(naam="tomaten", hoeveelheid=500, eenheid="gram"),
            ],
            tags=["budget"],
            bereidingstijd_min=45,
        ),
        Recipe(
            id="stamppot-boerenkool",
            naam="Stamppot Boerenkool",
            categorie=Categorie.VLEES,
            basis=Basis.AARDAPPEL,
            seizoenen=[Seizoen.WINTER],
            basis_porties=4,
            ingredienten=[
                Ingredient(naam="boerenkool", hoeveelheid=500, eenheid="gram"),
            ],
            tags=["hollands"],
            bereidingstijd_min=45,
        ),
    ]


@pytest.fixture
def search(sample_recipes: list[Recipe]) -> RecipeSearch:
    """RecipeSearch instance met sample recepten."""
    return RecipeSearch(sample_recipes)


class TestFilterBySeizoen:
    """Tests voor filteren op seizoen."""

    def test_filter_by_single_seizoen(self, search: RecipeSearch):
        """Filter recepten voor één seizoen."""
        winter_recipes = search.filter_by_seizoen(Seizoen.WINTER).results

        ids = {r.id for r in winter_recipes}
        # Erwtensoep, Stamppot, Bolognese (alle), Tomatensoep (alle)
        assert "erwtensoep" in ids
        assert "stamppot-boerenkool" in ids
        assert "spaghetti-bolognese" in ids  # "alle" past bij elk seizoen
        assert "tomatensoep" in ids  # "alle" past bij elk seizoen
        assert "pasta-pesto" not in ids  # alleen lente/zomer

    def test_filter_by_seizoen_alle_includes_all(self, search: RecipeSearch):
        """Recepten met 'alle' worden altijd meegenomen."""
        lente_recipes = search.filter_by_seizoen(Seizoen.LENTE).results

        ids = {r.id for r in lente_recipes}
        assert "pasta-pesto" in ids  # lente/zomer
        assert "spaghetti-bolognese" in ids  # alle
        assert "tomatensoep" in ids  # alle
        assert "erwtensoep" not in ids  # herfst/winter

    def test_filter_by_seizoen_returns_empty_for_no_matches(
        self, sample_recipes: list[Recipe]
    ):
        """Leeg resultaat als geen recepten matchen."""
        # Maak search met alleen winter recepten
        winter_only = [r for r in sample_recipes if Seizoen.WINTER in r.seizoenen]
        search = RecipeSearch(winter_only)

        # Filter op zomer - alleen "alle" zou matchen, maar die hebben we niet
        # In dit geval hebben we stamppot die alleen winter is
        zomer_recipes = search.filter_by_seizoen(Seizoen.ZOMER).results

        # Stamppot is alleen winter, dus geen match
        ids = {r.id for r in zomer_recipes}
        assert "stamppot-boerenkool" not in ids


class TestFilterByCategorie:
    """Tests voor filteren op categorie (proteïnebron)."""

    def test_filter_by_single_categorie(self, search: RecipeSearch):
        """Filter recepten voor één categorie."""
        vlees_recipes = search.filter_by_categorie(Categorie.VLEES).results

        assert len(vlees_recipes) == 3
        ids = {r.id for r in vlees_recipes}
        assert ids == {"spaghetti-bolognese", "erwtensoep", "stamppot-boerenkool"}

    def test_filter_by_categorie_vegetarisch(self, search: RecipeSearch):
        """Filter recepten voor vegetarische categorie."""
        veg_recipes = search.filter_by_categorie(Categorie.VEGETARISCH).results

        assert len(veg_recipes) == 2
        ids = {r.id for r in veg_recipes}
        assert ids == {"pasta-pesto", "tomatensoep"}

    def test_filter_by_categorie_returns_empty_for_no_matches(
        self, search: RecipeSearch
    ):
        """Leeg resultaat als geen recepten matchen."""
        vis_recipes = search.filter_by_categorie(Categorie.VIS).results
        assert vis_recipes == []


class TestFilterByTags:
    """Tests voor filteren op tags."""

    def test_filter_by_single_tag(self, search: RecipeSearch):
        """Filter recepten met één tag."""
        italiaans = search.filter_by_tags(["italiaans"]).results

        ids = {r.id for r in italiaans}
        assert ids == {"spaghetti-bolognese", "pasta-pesto"}

    def test_filter_by_multiple_tags_and(self, search: RecipeSearch):
        """Filter recepten die ALLE opgegeven tags hebben (AND)."""
        # Recepten met zowel "italiaans" als "budget"
        results = search.filter_by_tags(["italiaans", "budget"], match_all=True).results

        ids = {r.id for r in results}
        assert ids == {"spaghetti-bolognese"}

    def test_filter_by_multiple_tags_or(self, search: RecipeSearch):
        """Filter recepten die MINSTENS ÉÉN tag hebben (OR)."""
        # Recepten met "hollands" of "snel"
        results = search.filter_by_tags(["hollands", "snel"], match_all=False).results

        ids = {r.id for r in results}
        assert ids == {"erwtensoep", "stamppot-boerenkool", "pasta-pesto"}

    def test_filter_by_tags_returns_empty_for_no_matches(self, search: RecipeSearch):
        """Leeg resultaat als geen recepten matchen."""
        results = search.filter_by_tags(["aziatisch"]).results
        assert results == []

    def test_filter_by_empty_tags_returns_all(self, search: RecipeSearch):
        """Lege tag lijst retourneert alle recepten."""
        results = search.filter_by_tags([]).results
        assert len(results) == 5


class TestSearchByNaam:
    """Tests voor zoeken op naam."""

    def test_search_exact_match(self, search: RecipeSearch):
        """Zoeken met exacte naam match."""
        results = search.search_by_naam("Spaghetti Bolognese").results

        assert len(results) == 1
        assert results[0].id == "spaghetti-bolognese"

    def test_search_partial_match(self, search: RecipeSearch):
        """Zoeken met gedeeltelijke naam match."""
        results = search.search_by_naam("soep").results

        ids = {r.id for r in results}
        assert ids == {"erwtensoep", "tomatensoep"}

    def test_search_case_insensitive(self, search: RecipeSearch):
        """Zoeken is niet hoofdlettergevoelig."""
        results = search.search_by_naam("PASTA").results

        ids = {r.id for r in results}
        assert "pasta-pesto" in ids

    def test_search_returns_empty_for_no_matches(self, search: RecipeSearch):
        """Leeg resultaat als geen recepten matchen."""
        results = search.search_by_naam("sushi").results
        assert results == []

    def test_search_fuzzy_match(self, search: RecipeSearch):
        """Zoeken met kleine typfouten (fuzzy matching)."""
        # "bolognese" met kleine typfout
        results = search.search_by_naam("bolonese").results

        # Zou spaghetti bolognese moeten vinden
        ids = {r.id for r in results}
        assert "spaghetti-bolognese" in ids

    def test_search_fuzzy_match_stamppot(self, search: RecipeSearch):
        """Zoeken met typfout in stamppot."""
        results = search.search_by_naam("stampot").results  # één p te weinig

        ids = {r.id for r in results}
        assert "stamppot-boerenkool" in ids


class TestCombinedFilters:
    """Tests voor gecombineerde filters (fluent interface)."""

    def test_filter_seizoen_and_categorie(self, search: RecipeSearch):
        """Combineer seizoen en categorie filter met fluent interface."""
        # Winter vlees recepten - nu met fluent chaining
        results = (
            search.filter_by_seizoen(Seizoen.WINTER)
            .filter_by_categorie(Categorie.VLEES)
            .results
        )

        ids = {r.id for r in results}
        # Bolognese (alle), erwtensoep (herfst/winter), stamppot (winter)
        assert ids == {"spaghetti-bolognese", "erwtensoep", "stamppot-boerenkool"}

    def test_filter_categorie_and_tags(self, search: RecipeSearch):
        """Combineer categorie en tags filter met fluent interface."""
        # Vegetarische recepten met budget tag
        results = (
            search.filter_by_categorie(Categorie.VEGETARISCH)
            .filter_by_tags(["budget"])
            .results
        )

        assert len(results) == 1
        assert results[0].id == "tomatensoep"

    def test_chain_multiple_filters(self, search: RecipeSearch):
        """Chain meerdere filters met fluent interface."""
        # Winter, budget recepten
        results = (
            search.filter_by_seizoen(Seizoen.WINTER).filter_by_tags(["budget"]).results
        )

        ids = {r.id for r in results}
        # Bolognese, erwtensoep, tomatensoep - allen met budget tag
        assert "spaghetti-bolognese" in ids
        assert "erwtensoep" in ids
        assert "tomatensoep" in ids


@pytest.fixture
def co2_kalender(tmp_path):
    """Minimale CO2-seizoenskalender voor RecipeSearch tests."""
    alle = [
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
    data = [
        {
            "nr": 1,
            "groente": "Tomaat",
            "lage_co2_maanden": ["jun", "jul", "aug", "sep", "okt"],
        },
        {"nr": 2, "groente": "Ui", "lage_co2_maanden": alle},
        {
            "nr": 3,
            "groente": "Boerenkool",
            "lage_co2_maanden": ["nov", "dec", "jan", "feb"],
        },
    ]
    path = tmp_path / "kalender.json"
    path.write_text(json.dumps(data))
    return SeizoenKalender(path)


class TestFilterByCo2Maand:
    """Tests voor filteren op CO2-seizoenskalender per maand."""

    def test_filter_februari(self, sample_recipes, co2_kalender):
        """Februari: boerenkool ✅, tomaat ❌, ui ✅."""
        search = RecipeSearch(sample_recipes)
        results = search.filter_by_co2_maand(co2_kalender, "feb").results
        ids = {r.id for r in results}

        # stamppot-boerenkool: boerenkool ✅ → 1/1 = 100% ✅
        assert "stamppot-boerenkool" in ids
        # tomatensoep: tomaat ❌ → 0/1 = 0% ❌
        assert "tomatensoep" not in ids
        # spaghetti-bolognese: geen herkenbare groenten → altijd geschikt ✅
        assert "spaghetti-bolognese" in ids
        # pasta-pesto: geen herkenbare groenten → altijd geschikt ✅
        assert "pasta-pesto" in ids

    def test_filter_juli(self, sample_recipes, co2_kalender):
        """Juli: tomaat ✅, boerenkool ❌, ui ✅."""
        search = RecipeSearch(sample_recipes)
        results = search.filter_by_co2_maand(co2_kalender, "jul").results
        ids = {r.id for r in results}

        # tomatensoep: tomaat ✅ → 1/1 = 100% ✅
        assert "tomatensoep" in ids
        # stamppot-boerenkool: boerenkool ❌ → 0/1 = 0% ❌
        assert "stamppot-boerenkool" not in ids

    def test_chaining_met_categorie(self, sample_recipes, co2_kalender):
        """CO2-filter chainbaar met andere filters."""
        search = RecipeSearch(sample_recipes)
        results = (
            search.filter_by_co2_maand(co2_kalender, "feb")
            .filter_by_categorie(Categorie.VLEES)
            .results
        )
        ids = {r.id for r in results}
        assert "stamppot-boerenkool" in ids
        assert "spaghetti-bolognese" in ids

    def test_lege_lijst(self, co2_kalender):
        """Lege receptenlijst retourneert lege lijst."""
        search = RecipeSearch([])
        results = search.filter_by_co2_maand(co2_kalender, "feb").results
        assert results == []


class TestEmptyRecipes:
    """Tests met lege receptenlijst."""

    def test_filter_empty_list(self):
        """Filters op lege lijst retourneren lege lijst."""
        search = RecipeSearch([])

        assert search.filter_by_seizoen(Seizoen.WINTER).results == []
        assert search.filter_by_categorie(Categorie.VLEES).results == []
        assert search.filter_by_tags(["italiaans"]).results == []
        assert search.search_by_naam("test").results == []
