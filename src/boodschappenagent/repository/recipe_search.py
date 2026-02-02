"""Zoek- en filterfunctionaliteit voor recepten."""

from __future__ import annotations

from difflib import SequenceMatcher

from boodschappenagent.models import Categorie, Recipe, Seizoen


class RecipeSearch:
    """Zoek- en filterfunctionaliteit voor recepten.

    Ondersteunt fluent interface voor het chainen van filters:
        search.filter_by_seizoen(Seizoen.WINTER).filter_by_categorie(Categorie.SOEP).results

    Ondersteunt:
    - Filteren op seizoen (inclusief "alle")
    - Filteren op categorie
    - Filteren op tags (AND/OR)
    - Zoeken op naam (met fuzzy matching)
    """

    # Minimum similarity score voor fuzzy matching (0.0 - 1.0)
    FUZZY_THRESHOLD = 0.6

    def __init__(self, recipes: list[Recipe]) -> None:
        """Initialiseer met een lijst recepten.

        Args:
            recipes: De recepten om in te zoeken.
        """
        self._recipes = recipes

    @property
    def results(self) -> list[Recipe]:
        """Retourneer de huidige gefilterde recepten.

        Returns:
            Lijst van recepten na alle toegepaste filters.
        """
        return list(self._recipes)

    def filter_by_seizoen(self, seizoen: Seizoen) -> RecipeSearch:
        """Filter recepten die passen bij het opgegeven seizoen.

        Recepten met Seizoen.ALLE worden altijd meegenomen.

        Args:
            seizoen: Het seizoen om op te filteren.

        Returns:
            Nieuwe RecipeSearch met gefilterde recepten.
        """
        filtered = [
            r
            for r in self._recipes
            if seizoen in r.seizoenen or Seizoen.ALLE in r.seizoenen
        ]
        return RecipeSearch(filtered)

    def filter_by_categorie(self, categorie: Categorie) -> RecipeSearch:
        """Filter recepten op categorie.

        Args:
            categorie: De categorie om op te filteren.

        Returns:
            Nieuwe RecipeSearch met gefilterde recepten.
        """
        filtered = [r for r in self._recipes if r.categorie == categorie]
        return RecipeSearch(filtered)

    def filter_by_tags(
        self, tags: list[str], *, match_all: bool = True
    ) -> RecipeSearch:
        """Filter recepten op tags.

        Args:
            tags: De tags om op te filteren.
            match_all: Als True, moet recept ALLE tags hebben (AND).
                      Als False, moet recept MINSTENS ÉÉN tag hebben (OR).

        Returns:
            Nieuwe RecipeSearch met gefilterde recepten.
        """
        if not tags:
            return RecipeSearch(list(self._recipes))

        tags_set = set(tags)

        if match_all:
            # AND: recept moet alle tags hebben
            filtered = [r for r in self._recipes if tags_set.issubset(set(r.tags))]
        else:
            # OR: recept moet minstens één tag hebben
            filtered = [r for r in self._recipes if tags_set.intersection(set(r.tags))]

        return RecipeSearch(filtered)

    def search_by_naam(self, query: str) -> RecipeSearch:
        """Zoek recepten op naam (met fuzzy matching).

        Zoekt eerst op exacte substring match (case-insensitive),
        daarna op fuzzy matching voor kleine typfouten.

        Args:
            query: De zoekterm.

        Returns:
            Nieuwe RecipeSearch met gematchte recepten.
        """
        if not query:
            return RecipeSearch(list(self._recipes))

        query_lower = query.lower()
        results = []

        for recipe in self._recipes:
            naam_lower = recipe.naam.lower()

            # Exacte substring match
            if query_lower in naam_lower:
                results.append(recipe)
                continue

            # Fuzzy matching op hele naam
            if self._fuzzy_match(query_lower, naam_lower):
                results.append(recipe)
                continue

            # Fuzzy matching op individuele woorden
            naam_words = naam_lower.split()
            for word in naam_words:
                if self._fuzzy_match(query_lower, word):
                    results.append(recipe)
                    break

        return RecipeSearch(results)

    def _fuzzy_match(self, query: str, target: str) -> bool:
        """Check of query fuzzy matcht met target.

        Args:
            query: De zoekterm.
            target: De tekst om mee te matchen.

        Returns:
            True als de similarity score boven de threshold is.
        """
        ratio = SequenceMatcher(None, query, target).ratio()
        return ratio >= self.FUZZY_THRESHOLD
