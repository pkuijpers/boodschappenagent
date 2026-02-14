"""Tests voor de voorraad CLI."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from boodschappenagent.models import Basis, Categorie, Ingredient, Recipe, Seizoen
from boodschappenagent.voorraadbeheer.models import VoorraadItem, VoorraadType
from boodschappenagent.voorraadbeheer.presets import STANDAARD_HOUDBAAR, VERSE_BASICS
from boodschappenagent.voorraadbeheer.repository import VoorraadRepository


def _run_cli(args: list[str], voorraad_path: Path) -> int:
    """Run de voorraad CLI met gegeven argumenten."""
    from boodschappenagent.cli.voorraad import main

    full_args = ["--voorraad", str(voorraad_path)] + args
    with patch("sys.argv", ["voorraad"] + full_args):
        return main()


class TestCmdInit:
    def test_init_creates_voorraad_file(self, tmp_path: Path) -> None:
        voorraad_path = tmp_path / "voorraad.json"
        result = _run_cli(["init"], voorraad_path)
        assert result == 0
        assert voorraad_path.exists()

    def test_init_creates_all_presets(self, tmp_path: Path) -> None:
        voorraad_path = tmp_path / "voorraad.json"
        _run_cli(["init"], voorraad_path)

        repo = VoorraadRepository(voorraad_path)
        items = repo.load()
        namen = {i.naam for i in items}

        for naam in STANDAARD_HOUDBAAR:
            assert naam in namen, f"Houdbaar preset '{naam}' ontbreekt"
        for naam, _, _ in VERSE_BASICS:
            assert naam in namen, f"Verse basis preset '{naam}' ontbreekt"

    def test_init_sets_all_items_not_in_stock(self, tmp_path: Path) -> None:
        voorraad_path = tmp_path / "voorraad.json"
        _run_cli(["init"], voorraad_path)

        repo = VoorraadRepository(voorraad_path)
        items = repo.load()
        assert all(not i.op_voorraad for i in items)

    def test_init_assigns_correct_types(self, tmp_path: Path) -> None:
        voorraad_path = tmp_path / "voorraad.json"
        _run_cli(["init"], voorraad_path)

        repo = VoorraadRepository(voorraad_path)
        items = repo.load()
        items_by_naam = {i.naam: i for i in items}

        for naam in STANDAARD_HOUDBAAR:
            assert items_by_naam[naam].type is VoorraadType.HOUDBAAR
        for naam, _, _ in VERSE_BASICS:
            assert items_by_naam[naam].type is VoorraadType.VERS_BASIS


class TestCmdToon:
    def test_toon_empty_voorraad(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        voorraad_path = tmp_path / "voorraad.json"
        result = _run_cli(["toon"], voorraad_path)
        assert result == 0
        output = capsys.readouterr().out
        assert "leeg" in output.lower() or "geen" in output.lower()

    def test_toon_shows_items(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        voorraad_path = tmp_path / "voorraad.json"
        repo = VoorraadRepository(voorraad_path)
        repo.save(
            [
                VoorraadItem(
                    naam="pasta",
                    type=VoorraadType.HOUDBAAR,
                    op_voorraad=True,
                    laatst_gecheckt="2026-02-14",
                ),
                VoorraadItem(
                    naam="melk",
                    type=VoorraadType.VERS_BASIS,
                    op_voorraad=False,
                    laatst_gecheckt="2026-02-14",
                ),
            ]
        )

        result = _run_cli(["toon"], voorraad_path)
        assert result == 0
        output = capsys.readouterr().out
        assert "pasta" in output
        assert "melk" in output


class TestCmdSet:
    def test_set_item_op_voorraad(self, tmp_path: Path) -> None:
        voorraad_path = tmp_path / "voorraad.json"
        repo = VoorraadRepository(voorraad_path)
        repo.save(
            [
                VoorraadItem(
                    naam="pasta",
                    type=VoorraadType.HOUDBAAR,
                    op_voorraad=False,
                    laatst_gecheckt="2026-02-14",
                ),
            ]
        )

        result = _run_cli(["set", "pasta", "--op"], voorraad_path)
        assert result == 0

        items = repo.load()
        pasta = next(i for i in items if i.naam == "pasta")
        assert pasta.op_voorraad is True

    def test_set_item_leeg(self, tmp_path: Path) -> None:
        voorraad_path = tmp_path / "voorraad.json"
        repo = VoorraadRepository(voorraad_path)
        repo.save(
            [
                VoorraadItem(
                    naam="pasta",
                    type=VoorraadType.HOUDBAAR,
                    op_voorraad=True,
                    laatst_gecheckt="2026-02-14",
                ),
            ]
        )

        result = _run_cli(["set", "pasta", "--leeg"], voorraad_path)
        assert result == 0

        items = repo.load()
        pasta = next(i for i in items if i.naam == "pasta")
        assert pasta.op_voorraad is False

    def test_set_unknown_item_returns_error(self, tmp_path: Path) -> None:
        voorraad_path = tmp_path / "voorraad.json"
        result = _run_cli(["set", "onbekend", "--op"], voorraad_path)
        assert result == 1

    def test_set_updates_laatst_gecheckt(self, tmp_path: Path) -> None:
        voorraad_path = tmp_path / "voorraad.json"
        repo = VoorraadRepository(voorraad_path)
        repo.save(
            [
                VoorraadItem(
                    naam="pasta",
                    type=VoorraadType.HOUDBAAR,
                    op_voorraad=False,
                    laatst_gecheckt="2026-01-01",
                ),
            ]
        )

        _run_cli(["set", "pasta", "--op"], voorraad_path)

        items = repo.load()
        pasta = next(i for i in items if i.naam == "pasta")
        assert pasta.laatst_gecheckt != "2026-01-01"  # Updated to today


def _write_recipe(directory: Path, recipe: Recipe) -> None:
    """Write a recipe JSON file to a directory."""
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{recipe.id}.json"
    path.write_text(json.dumps(recipe.to_dict(), ensure_ascii=False), encoding="utf-8")


def _make_recipe(
    recipe_id: str,
    ingredienten: list[Ingredient],
) -> Recipe:
    return Recipe(
        id=recipe_id,
        naam=f"Recept {recipe_id}",
        categorie=Categorie.VEGETARISCH,
        basis=Basis.PASTA,
        seizoenen=[Seizoen.WINTER],
        basis_porties=2,
        ingredienten=ingredienten,
        bereidingstijd_min=20,
    )


def _run_sync_cli(args: list[str], voorraad_path: Path, recipes_dir: Path) -> int:
    """Run de voorraad CLI sync met gegeven argumenten."""
    from boodschappenagent.cli.voorraad import main

    full_args = [
        "--voorraad",
        str(voorraad_path),
        "--recipes-dir",
        str(recipes_dir),
    ] + args
    with patch("sys.argv", ["voorraad"] + full_args):
        return main()


def _setup_sync_recipes(tmp_path: Path) -> Path:
    """Maak test recipes aan voor sync tests. Retourneert recipes_dir."""
    recipes_dir = tmp_path / "recipes" / "cat"
    _write_recipe(
        recipes_dir,
        _make_recipe(
            "r1",
            [
                Ingredient(naam="selderij", hoeveelheid=2, eenheid="stengels"),
                Ingredient(naam="broccoli", hoeveelheid=200, eenheid="gram"),
            ],
        ),
    )
    _write_recipe(
        recipes_dir,
        _make_recipe(
            "r2",
            [
                Ingredient(naam="selderij", hoeveelheid=1, eenheid="stengels"),
                Ingredient(naam="broccoli", hoeveelheid=150, eenheid="gram"),
            ],
        ),
    )
    return tmp_path / "recipes"


class TestCmdSync:
    def test_sync_accepted_items_added(self, tmp_path: Path) -> None:
        recipes_dir = _setup_sync_recipes(tmp_path)
        voorraad_path = tmp_path / "voorraad.json"
        _run_cli(["init"], voorraad_path)

        with patch("builtins.input", side_effect=["j", "j"]):
            result = _run_sync_cli(["sync"], voorraad_path, recipes_dir)
        assert result == 0

        repo = VoorraadRepository(voorraad_path)
        namen = {i.naam for i in repo.load()}
        assert "broccoli" in namen
        assert "selderij" in namen

    def test_sync_rejected_items_not_added(self, tmp_path: Path) -> None:
        recipes_dir = _setup_sync_recipes(tmp_path)
        voorraad_path = tmp_path / "voorraad.json"
        _run_cli(["init"], voorraad_path)

        # broccoli=n, selderij=j (sorted by freq desc then name)
        with patch("builtins.input", side_effect=["n", "j"]):
            _run_sync_cli(["sync"], voorraad_path, recipes_dir)

        repo = VoorraadRepository(voorraad_path)
        namen = {i.naam for i in repo.load()}
        assert "broccoli" not in namen
        assert "selderij" in namen

    def test_sync_accepted_items_are_houdbaar(self, tmp_path: Path) -> None:
        recipes_dir = _setup_sync_recipes(tmp_path)
        voorraad_path = tmp_path / "voorraad.json"
        _run_cli(["init"], voorraad_path)

        with patch("builtins.input", side_effect=["j", "n"]):
            _run_sync_cli(["sync"], voorraad_path, recipes_dir)

        repo = VoorraadRepository(voorraad_path)
        items = repo.load()
        # broccoli accepted (first in alpha order at same freq)
        broccoli = next(i for i in items if i.naam == "broccoli")
        assert broccoli.type is VoorraadType.HOUDBAAR
        assert broccoli.op_voorraad is False

    def test_sync_does_not_duplicate_existing(self, tmp_path: Path) -> None:
        recipes_dir = tmp_path / "recipes" / "cat"
        _write_recipe(
            recipes_dir,
            _make_recipe(
                "r1",
                [Ingredient(naam="pasta", hoeveelheid=250, eenheid="gram")],
            ),
        )
        _write_recipe(
            recipes_dir,
            _make_recipe(
                "r2",
                [Ingredient(naam="pasta", hoeveelheid=300, eenheid="gram")],
            ),
        )

        voorraad_path = tmp_path / "voorraad.json"
        _run_cli(["init"], voorraad_path)
        # pasta already exists in init → no candidates → no input needed
        _run_sync_cli(["sync"], voorraad_path, tmp_path / "recipes")

        repo = VoorraadRepository(voorraad_path)
        items = repo.load()
        pasta_items = [i for i in items if i.naam == "pasta"]
        assert len(pasta_items) == 1

    def test_sync_respects_min_freq(self, tmp_path: Path) -> None:
        recipes_dir = _setup_sync_recipes(tmp_path)
        voorraad_path = tmp_path / "voorraad.json"
        _run_cli(["init"], voorraad_path)

        # min_freq=3 → no candidates (both at 2x) → no input needed
        _run_sync_cli(["sync", "--min-freq", "3"], voorraad_path, recipes_dir)

        repo = VoorraadRepository(voorraad_path)
        namen = {i.naam for i in repo.load()}
        assert "selderij" not in namen
        assert "broccoli" not in namen

    def test_sync_prints_summary(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        recipes_dir = _setup_sync_recipes(tmp_path)
        voorraad_path = tmp_path / "voorraad.json"
        _run_cli(["init"], voorraad_path)

        with patch("builtins.input", side_effect=["j", "n"]):
            _run_sync_cli(["sync"], voorraad_path, recipes_dir)

        output = capsys.readouterr().out
        assert "1" in output  # 1 item toegevoegd

    def test_sync_no_new_items(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        recipes_dir = tmp_path / "recipes" / "cat"
        _write_recipe(
            recipes_dir,
            _make_recipe(
                "r1",
                [Ingredient(naam="pasta", hoeveelheid=250, eenheid="gram")],
            ),
        )

        voorraad_path = tmp_path / "voorraad.json"
        _run_cli(["init"], voorraad_path)
        result = _run_sync_cli(["sync"], voorraad_path, tmp_path / "recipes")
        assert result == 0

        output = capsys.readouterr().out
        assert "geen" in output.lower() or "0" in output
