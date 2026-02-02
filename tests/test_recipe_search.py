"""Tests voor RecipeSearch zoek- en filterfunctionaliteit."""

import pytest

from boodschappenagent.models import Categorie, Ingredient, Recipe, Seizoen
from boodschappenagent.repository.recipe_search import RecipeSearch


@pytest.fixture
def sample_recipes() -> list[Recipe]:
    """Verzameling recepten voor tests."""
    return [
        Recipe(
            id="spaghetti-bolognese",
            naam="Spaghetti Bolognese",
            categorie=Categorie.PASTA,
            seizoenen=[Seizoen.ALLE],
            basis_porties=2,
            ingredienten=[
                Ingredient(naam="spaghetti", hoeveelheid=200, eenheid="gram"),
                Ingredient(naam="gehakt", hoeveelheid=250, eenheid="gram"),
            ],
            tags=["vlees", "italiaans", "budget"],
            bereidingstijd_min=35,
        ),
        Recipe(
            id="pasta-pesto",
            naam="Pasta met Pesto",
            categorie=Categorie.PASTA,
            seizoenen=[Seizoen.LENTE, Seizoen.ZOMER],
            basis_porties=2,
            ingredienten=[
                Ingredient(naam="pasta", hoeveelheid=200, eenheid="gram"),
            ],
            tags=["vegetarisch", "italiaans", "snel"],
            bereidingstijd_min=15,
        ),
        Recipe(
            id="erwtensoep",
            naam="Erwtensoep",
            categorie=Categorie.SOEP,
            seizoenen=[Seizoen.HERFST, Seizoen.WINTER],
            basis_porties=4,
            ingredienten=[
                Ingredient(naam="erwten", hoeveelheid=500, eenheid="gram"),
            ],
            tags=["vlees", "hollands", "budget"],
            bereidingstijd_min=120,
        ),
        Recipe(
            id="tomatensoep",
            naam="Tomatensoep",
            categorie=Categorie.SOEP,
            seizoenen=[Seizoen.ALLE],
            basis_porties=4,
            ingredienten=[
                Ingredient(naam="tomaten", hoeveelheid=500, eenheid="gram"),
            ],
            tags=["vegetarisch", "budget"],
            bereidingstijd_min=45,
        ),
        Recipe(
            id="stamppot-boerenkool",
            naam="Stamppot Boerenkool",
            categorie=Categorie.STAMPPOT,
            seizoenen=[Seizoen.WINTER],
            basis_porties=4,
            ingredienten=[
                Ingredient(naam="boerenkool", hoeveelheid=500, eenheid="gram"),
            ],
            tags=["vlees", "hollands"],
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
    """Tests voor filteren op categorie."""

    def test_filter_by_single_categorie(self, search: RecipeSearch):
        """Filter recepten voor één categorie."""
        pasta_recipes = search.filter_by_categorie(Categorie.PASTA).results

        assert len(pasta_recipes) == 2
        ids = {r.id for r in pasta_recipes}
        assert ids == {"spaghetti-bolognese", "pasta-pesto"}

    def test_filter_by_categorie_soep(self, search: RecipeSearch):
        """Filter recepten voor soep categorie."""
        soep_recipes = search.filter_by_categorie(Categorie.SOEP).results

        assert len(soep_recipes) == 2
        ids = {r.id for r in soep_recipes}
        assert ids == {"erwtensoep", "tomatensoep"}

    def test_filter_by_categorie_returns_empty_for_no_matches(
        self, search: RecipeSearch
    ):
        """Leeg resultaat als geen recepten matchen."""
        salade_recipes = search.filter_by_categorie(Categorie.SALADE).results
        assert salade_recipes == []


class TestFilterByTags:
    """Tests voor filteren op tags."""

    def test_filter_by_single_tag(self, search: RecipeSearch):
        """Filter recepten met één tag."""
        vegetarisch = search.filter_by_tags(["vegetarisch"]).results

        ids = {r.id for r in vegetarisch}
        assert ids == {"pasta-pesto", "tomatensoep"}

    def test_filter_by_multiple_tags_and(self, search: RecipeSearch):
        """Filter recepten die ALLE opgegeven tags hebben (AND)."""
        # Recepten met zowel "vlees" als "budget"
        results = search.filter_by_tags(["vlees", "budget"], match_all=True).results

        ids = {r.id for r in results}
        assert ids == {"spaghetti-bolognese", "erwtensoep"}

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
        # Winter soepen - nu met fluent chaining
        results = (
            search.filter_by_seizoen(Seizoen.WINTER)
            .filter_by_categorie(Categorie.SOEP)
            .results
        )

        ids = {r.id for r in results}
        # Erwtensoep (herfst/winter, soep) en tomatensoep (alle, soep)
        assert ids == {"erwtensoep", "tomatensoep"}

    def test_filter_categorie_and_tags(self, search: RecipeSearch):
        """Combineer categorie en tags filter met fluent interface."""
        # Vegetarische soepen
        results = (
            search.filter_by_categorie(Categorie.SOEP)
            .filter_by_tags(["vegetarisch"])
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


class TestEmptyRecipes:
    """Tests met lege receptenlijst."""

    def test_filter_empty_list(self):
        """Filters op lege lijst retourneren lege lijst."""
        search = RecipeSearch([])

        assert search.filter_by_seizoen(Seizoen.WINTER).results == []
        assert search.filter_by_categorie(Categorie.PASTA).results == []
        assert search.filter_by_tags(["vlees"]).results == []
        assert search.search_by_naam("test").results == []
