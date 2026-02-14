"""Tests voor VoorraadChecker suggestie-engine."""

from __future__ import annotations

from pathlib import Path

from boodschappenagent.models import Basis, Categorie, Ingredient, Recipe, Seizoen
from boodschappenagent.planner.history import MenuHistory
from boodschappenagent.planner.models import DagPlanning, WeekMenu
from boodschappenagent.voorraadbeheer.checker import VoorraadChecker
from boodschappenagent.voorraadbeheer.models import (
    SuggestiePrioriteit,
    VoorraadItem,
    VoorraadType,
)
from boodschappenagent.voorraadbeheer.repository import VoorraadRepository


def _make_recipe(
    recipe_id: str = "test-recept",
    naam: str = "Testrecept",
    ingredienten: list[Ingredient] | None = None,
) -> Recipe:
    return Recipe(
        id=recipe_id,
        naam=naam,
        categorie=Categorie.VEGETARISCH,
        basis=Basis.PASTA,
        seizoenen=[Seizoen.WINTER],
        basis_porties=2,
        ingredienten=ingredienten
        or [
            Ingredient(naam="pasta", hoeveelheid=250, eenheid="gram"),
            Ingredient(naam="olijfolie", hoeveelheid=2, eenheid="eetlepel"),
        ],
        bereidingstijd_min=20,
    )


def _make_week_menu(recipes: list[Recipe]) -> WeekMenu:
    dagen = [DagPlanning(dag=i, recept=r, personen=2) for i, r in enumerate(recipes)]
    return WeekMenu(week_start="2026-02-16", dagen=dagen)


def _make_item(
    naam: str,
    type: VoorraadType = VoorraadType.HOUDBAAR,
    op_voorraad: bool = True,
) -> VoorraadItem:
    return VoorraadItem(
        naam=naam, type=type, op_voorraad=op_voorraad, laatst_gecheckt="2026-02-14"
    )


class TestVoorraadCheckerVerseBasisSuggesties:
    def test_verse_basics_always_suggested(self, tmp_path: Path) -> None:
        repo = VoorraadRepository(tmp_path / "voorraad.json")
        repo.save(
            [
                _make_item("melk", VoorraadType.VERS_BASIS),
                _make_item("eieren", VoorraadType.VERS_BASIS),
            ]
        )
        history = MenuHistory(tmp_path / "history.json")
        checker = VoorraadChecker(repo)

        recipe = _make_recipe()
        menu = _make_week_menu([recipe])
        suggesties = checker.genereer_suggesties(menu, history, Seizoen.WINTER)

        vers_suggesties = [
            s for s in suggesties if s.prioriteit is SuggestiePrioriteit.HIGH
        ]
        namen = {s.naam for s in vers_suggesties}
        assert "melk" in namen
        assert "eieren" in namen

    def test_verse_basics_have_high_priority(self, tmp_path: Path) -> None:
        repo = VoorraadRepository(tmp_path / "voorraad.json")
        repo.save([_make_item("boter", VoorraadType.VERS_BASIS)])
        history = MenuHistory(tmp_path / "history.json")
        checker = VoorraadChecker(repo)

        menu = _make_week_menu([_make_recipe()])
        suggesties = checker.genereer_suggesties(menu, history, Seizoen.WINTER)

        boter = next(s for s in suggesties if s.naam == "boter")
        assert boter.prioriteit is SuggestiePrioriteit.HIGH


class TestVoorraadCheckerRecentGebruikSuggesties:
    def test_menu_ingredients_matching_houdbaar_items(self, tmp_path: Path) -> None:
        repo = VoorraadRepository(tmp_path / "voorraad.json")
        repo.save(
            [
                _make_item("pasta", VoorraadType.HOUDBAAR),
                _make_item("olijfolie", VoorraadType.HOUDBAAR),
            ]
        )
        history = MenuHistory(tmp_path / "history.json")
        checker = VoorraadChecker(repo)

        recipe = _make_recipe(
            ingredienten=[
                Ingredient(naam="pasta", hoeveelheid=250, eenheid="gram"),
                Ingredient(naam="olijfolie", hoeveelheid=2, eenheid="eetlepel"),
            ]
        )
        menu = _make_week_menu([recipe])
        suggesties = checker.genereer_suggesties(menu, history, Seizoen.WINTER)

        medium_suggesties = [
            s for s in suggesties if s.prioriteit is SuggestiePrioriteit.MEDIUM
        ]
        namen = {s.naam for s in medium_suggesties}
        assert "pasta" in namen
        assert "olijfolie" in namen

    def test_no_match_no_medium_suggesties(self, tmp_path: Path) -> None:
        repo = VoorraadRepository(tmp_path / "voorraad.json")
        repo.save([_make_item("rijst", VoorraadType.HOUDBAAR)])
        history = MenuHistory(tmp_path / "history.json")
        checker = VoorraadChecker(repo)

        recipe = _make_recipe(
            ingredienten=[
                Ingredient(naam="pasta", hoeveelheid=250, eenheid="gram"),
            ]
        )
        menu = _make_week_menu([recipe])
        suggesties = checker.genereer_suggesties(menu, history, Seizoen.WINTER)

        medium_suggesties = [
            s for s in suggesties if s.prioriteit is SuggestiePrioriteit.MEDIUM
        ]
        namen = {s.naam for s in medium_suggesties}
        assert "rijst" not in namen

    def test_medium_priority(self, tmp_path: Path) -> None:
        repo = VoorraadRepository(tmp_path / "voorraad.json")
        repo.save([_make_item("pasta", VoorraadType.HOUDBAAR)])
        history = MenuHistory(tmp_path / "history.json")
        checker = VoorraadChecker(repo)

        recipe = _make_recipe(
            ingredienten=[
                Ingredient(naam="pasta", hoeveelheid=250, eenheid="gram"),
            ]
        )
        menu = _make_week_menu([recipe])
        suggesties = checker.genereer_suggesties(menu, history, Seizoen.WINTER)

        pasta = next(s for s in suggesties if s.naam == "pasta")
        assert pasta.prioriteit is SuggestiePrioriteit.MEDIUM


class TestVoorraadCheckerSeizoenSuggesties:
    def test_seizoen_items_suggested(self, tmp_path: Path) -> None:
        repo = VoorraadRepository(tmp_path / "voorraad.json")
        repo.save([_make_item("pompoen", VoorraadType.HOUDBAAR)])
        history = MenuHistory(tmp_path / "history.json")
        checker = VoorraadChecker(repo)

        menu = _make_week_menu([_make_recipe()])
        suggesties = checker.genereer_suggesties(menu, history, Seizoen.HERFST)

        low_suggesties = [
            s for s in suggesties if s.prioriteit is SuggestiePrioriteit.LOW
        ]
        namen = {s.naam for s in low_suggesties}
        assert "pompoen" in namen

    def test_no_seizoen_match_no_low(self, tmp_path: Path) -> None:
        repo = VoorraadRepository(tmp_path / "voorraad.json")
        repo.save([_make_item("pompoen", VoorraadType.HOUDBAAR)])
        history = MenuHistory(tmp_path / "history.json")
        checker = VoorraadChecker(repo)

        menu = _make_week_menu([_make_recipe()])
        suggesties = checker.genereer_suggesties(menu, history, Seizoen.ZOMER)

        low_suggesties = [
            s for s in suggesties if s.prioriteit is SuggestiePrioriteit.LOW
        ]
        namen = {s.naam for s in low_suggesties}
        assert "pompoen" not in namen


class TestVoorraadCheckerSortering:
    def test_sorted_by_priority_then_name(self, tmp_path: Path) -> None:
        repo = VoorraadRepository(tmp_path / "voorraad.json")
        repo.save(
            [
                _make_item("melk", VoorraadType.VERS_BASIS),
                _make_item("boter", VoorraadType.VERS_BASIS),
                _make_item("pasta", VoorraadType.HOUDBAAR),
                _make_item("pompoen", VoorraadType.HOUDBAAR),
            ]
        )
        history = MenuHistory(tmp_path / "history.json")
        checker = VoorraadChecker(repo)

        recipe = _make_recipe(
            ingredienten=[
                Ingredient(naam="pasta", hoeveelheid=250, eenheid="gram"),
            ]
        )
        menu = _make_week_menu([recipe])
        suggesties = checker.genereer_suggesties(menu, history, Seizoen.HERFST)

        # HIGH comes first, then MEDIUM, then LOW
        prioriteiten = [s.prioriteit for s in suggesties]
        high_idx = [
            i for i, p in enumerate(prioriteiten) if p is SuggestiePrioriteit.HIGH
        ]
        medium_idx = [
            i for i, p in enumerate(prioriteiten) if p is SuggestiePrioriteit.MEDIUM
        ]
        low_idx = [
            i for i, p in enumerate(prioriteiten) if p is SuggestiePrioriteit.LOW
        ]

        if high_idx and medium_idx:
            assert max(high_idx) < min(medium_idx)
        if medium_idx and low_idx:
            assert max(medium_idx) < min(low_idx)

    def test_alphabetical_within_priority(self, tmp_path: Path) -> None:
        repo = VoorraadRepository(tmp_path / "voorraad.json")
        repo.save(
            [
                _make_item("melk", VoorraadType.VERS_BASIS),
                _make_item("boter", VoorraadType.VERS_BASIS),
                _make_item("eieren", VoorraadType.VERS_BASIS),
            ]
        )
        history = MenuHistory(tmp_path / "history.json")
        checker = VoorraadChecker(repo)

        menu = _make_week_menu([_make_recipe()])
        suggesties = checker.genereer_suggesties(menu, history, Seizoen.WINTER)

        high = [s for s in suggesties if s.prioriteit is SuggestiePrioriteit.HIGH]
        namen = [s.naam for s in high]
        assert namen == sorted(namen)


class TestVoorraadCheckerNoDuplicates:
    def test_item_not_duplicated_across_priorities(self, tmp_path: Path) -> None:
        """Item matching MEDIUM+LOW appears once (highest prio)."""
        repo = VoorraadRepository(tmp_path / "voorraad.json")
        repo.save([_make_item("pompoen", VoorraadType.HOUDBAAR)])
        history = MenuHistory(tmp_path / "history.json")
        checker = VoorraadChecker(repo)

        recipe = _make_recipe(
            ingredienten=[
                Ingredient(naam="pompoen", hoeveelheid=500, eenheid="gram"),
            ]
        )
        menu = _make_week_menu([recipe])
        suggesties = checker.genereer_suggesties(menu, history, Seizoen.HERFST)

        pompoen_suggesties = [s for s in suggesties if s.naam == "pompoen"]
        assert len(pompoen_suggesties) == 1
        # Should be MEDIUM (higher than LOW)
        assert pompoen_suggesties[0].prioriteit is SuggestiePrioriteit.MEDIUM


class TestVoorraadCheckerEmptyVoorraad:
    def test_empty_voorraad_no_suggesties(self, tmp_path: Path) -> None:
        repo = VoorraadRepository(tmp_path / "voorraad.json")
        history = MenuHistory(tmp_path / "history.json")
        checker = VoorraadChecker(repo)

        menu = _make_week_menu([_make_recipe()])
        suggesties = checker.genereer_suggesties(menu, history, Seizoen.WINTER)

        assert suggesties == []
