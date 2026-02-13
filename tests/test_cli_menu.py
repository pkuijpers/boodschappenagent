"""Tests voor de menu CLI tool."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

from boodschappenagent.models import Basis, Categorie, Ingredient, Recipe, Seizoen


def _make_recipe(
    recipe_id: str,
    categorie: Categorie = Categorie.VLEES,
    basis: Basis = Basis.PASTA,
) -> Recipe:
    """Helper om snel een recept te maken voor tests."""
    return Recipe(
        id=recipe_id,
        naam=recipe_id.replace("-", " ").title(),
        categorie=categorie,
        basis=basis,
        seizoenen=[Seizoen.ALLE],
        basis_porties=4,
        ingredienten=[Ingredient(naam="iets", hoeveelheid=100, eenheid="gram")],
        bereidingstijd_min=30,
    )


def _setup_recipes_dir(base: Path) -> Path:
    """Maak een recipes dir met diverse recepten."""
    recipes_dir = base / "recipes"
    recipes_dir.mkdir()
    recipes = [
        _make_recipe("vlees-pasta", Categorie.VLEES, Basis.PASTA),
        _make_recipe("vlees-rijst", Categorie.VLEES, Basis.RIJST),
        _make_recipe("gevogelte-brood", Categorie.GEVOGELTE, Basis.BROOD),
        _make_recipe("gevogelte-aardappel", Categorie.GEVOGELTE, Basis.AARDAPPEL),
        _make_recipe("vis-pasta", Categorie.VIS, Basis.PASTA),
        _make_recipe("vis-rijst", Categorie.VIS, Basis.RIJST),
        _make_recipe("veg-aardappel", Categorie.VEGETARISCH, Basis.AARDAPPEL),
        _make_recipe("veg-geen", Categorie.VEGETARISCH, Basis.GEEN),
        _make_recipe("vegan-rijst", Categorie.VEGANISTISCH, Basis.RIJST),
        _make_recipe("vegan-brood", Categorie.VEGANISTISCH, Basis.BROOD),
    ]
    for r in recipes:
        cat_dir = recipes_dir / r.categorie.value
        cat_dir.mkdir(exist_ok=True)
        path = cat_dir / f"{r.id}.json"
        path.write_text(json.dumps(r.to_dict(), ensure_ascii=False), encoding="utf-8")
    return recipes_dir


class TestDetectSeizoen:
    """Tests voor seizoen auto-detectie."""

    def test_winter_januari(self) -> None:
        from boodschappenagent.cli.menu import _detect_seizoen

        assert _detect_seizoen(date(2026, 1, 15)) == Seizoen.WINTER

    def test_winter_februari(self) -> None:
        from boodschappenagent.cli.menu import _detect_seizoen

        assert _detect_seizoen(date(2026, 2, 13)) == Seizoen.WINTER

    def test_winter_december(self) -> None:
        from boodschappenagent.cli.menu import _detect_seizoen

        assert _detect_seizoen(date(2026, 12, 1)) == Seizoen.WINTER

    def test_lente(self) -> None:
        from boodschappenagent.cli.menu import _detect_seizoen

        assert _detect_seizoen(date(2026, 4, 15)) == Seizoen.LENTE

    def test_zomer(self) -> None:
        from boodschappenagent.cli.menu import _detect_seizoen

        assert _detect_seizoen(date(2026, 7, 1)) == Seizoen.ZOMER

    def test_herfst(self) -> None:
        from boodschappenagent.cli.menu import _detect_seizoen

        assert _detect_seizoen(date(2026, 10, 20)) == Seizoen.HERFST


class TestDagNamen:
    """Tests voor dag naam conversie."""

    def test_naam_naar_nummer(self) -> None:
        from boodschappenagent.cli.menu import _parse_dag

        assert _parse_dag("ma") == 0
        assert _parse_dag("di") == 1
        assert _parse_dag("wo") == 2
        assert _parse_dag("do") == 3
        assert _parse_dag("vr") == 4
        assert _parse_dag("za") == 5
        assert _parse_dag("zo") == 6

    def test_nummer_als_string(self) -> None:
        from boodschappenagent.cli.menu import _parse_dag

        assert _parse_dag("0") == 0
        assert _parse_dag("6") == 6

    def test_onbekend_raises(self) -> None:
        from boodschappenagent.cli.menu import _parse_dag

        with pytest.raises(ValueError, match="onbekende dag"):
            _parse_dag("xx")

    def test_nummer_naar_naam(self) -> None:
        from boodschappenagent.cli.menu import DAG_NAMEN_LANG

        assert DAG_NAMEN_LANG[0] == "maandag"
        assert DAG_NAMEN_LANG[6] == "zondag"


class TestComputeWeekStart:
    """Tests voor week start berekening."""

    def test_maandag_geeft_zichzelf(self) -> None:
        from boodschappenagent.cli.menu import _compute_week_start

        # 2026-02-09 is maandag
        assert _compute_week_start(date(2026, 2, 9)) == "2026-02-09"

    def test_woensdag_geeft_volgende_maandag(self) -> None:
        from boodschappenagent.cli.menu import _compute_week_start

        # 2026-02-11 is woensdag → volgende maandag = 2026-02-16
        assert _compute_week_start(date(2026, 2, 11)) == "2026-02-16"

    def test_zondag_geeft_volgende_maandag(self) -> None:
        from boodschappenagent.cli.menu import _compute_week_start

        # 2026-02-15 is zondag → volgende maandag = 2026-02-16
        assert _compute_week_start(date(2026, 2, 15)) == "2026-02-16"


class TestCmdPlan:
    """Tests voor het plan command."""

    def test_plan_maakt_menu_bestand(self, tmp_path: Path) -> None:
        from boodschappenagent.cli.menu import cmd_plan

        recipes_dir = _setup_recipes_dir(tmp_path)
        history_path = tmp_path / "history.json"
        menu_path = tmp_path / "current_menu.json"

        args = _make_plan_args(
            recipes_dir=str(recipes_dir),
            history=str(history_path),
            menu=str(menu_path),
            personen=2,
            vrij=None,
            seizoen=None,
            week=None,
            dagen=None,
        )

        with patch("boodschappenagent.cli.menu.date") as mock_date:
            mock_date.today.return_value = date(2026, 2, 9)  # maandag
            mock_date.fromisoformat = date.fromisoformat
            result = cmd_plan(args)

        assert result == 0
        assert menu_path.exists()
        data = json.loads(menu_path.read_text())
        assert data["week_start"] == "2026-02-09"
        assert len(data["dagen"]) == 7

    def test_plan_met_vrije_dagen(self, tmp_path: Path) -> None:
        from boodschappenagent.cli.menu import cmd_plan

        recipes_dir = _setup_recipes_dir(tmp_path)
        history_path = tmp_path / "history.json"
        menu_path = tmp_path / "current_menu.json"

        args = _make_plan_args(
            recipes_dir=str(recipes_dir),
            history=str(history_path),
            menu=str(menu_path),
            personen=2,
            vrij="za,zo",
            seizoen=None,
            week="2026-02-09",
            dagen=None,
        )

        result = cmd_plan(args)

        assert result == 0
        data = json.loads(menu_path.read_text())
        # za=5, zo=6 moeten personen=0 hebben
        dagen_by_dag = {d["dag"]: d for d in data["dagen"]}
        assert dagen_by_dag[5]["personen"] == 0
        assert dagen_by_dag[5]["recept_id"] is None
        assert dagen_by_dag[6]["personen"] == 0
        assert dagen_by_dag[6]["recept_id"] is None

    def test_plan_met_seizoen_override(self, tmp_path: Path) -> None:
        from boodschappenagent.cli.menu import cmd_plan

        recipes_dir = _setup_recipes_dir(tmp_path)
        history_path = tmp_path / "history.json"
        menu_path = tmp_path / "current_menu.json"

        args = _make_plan_args(
            recipes_dir=str(recipes_dir),
            history=str(history_path),
            menu=str(menu_path),
            personen=2,
            vrij=None,
            seizoen="zomer",
            week="2026-02-09",
            dagen=None,
        )

        result = cmd_plan(args)
        assert result == 0

    def test_plan_met_dagen_override(self, tmp_path: Path) -> None:
        from boodschappenagent.cli.menu import cmd_plan

        recipes_dir = _setup_recipes_dir(tmp_path)
        history_path = tmp_path / "history.json"
        menu_path = tmp_path / "current_menu.json"

        args = _make_plan_args(
            recipes_dir=str(recipes_dir),
            history=str(history_path),
            menu=str(menu_path),
            personen=2,
            vrij=None,
            seizoen=None,
            week="2026-02-09",
            dagen="ma:4,vr:3",
        )

        result = cmd_plan(args)

        assert result == 0
        data = json.loads(menu_path.read_text())
        dagen_by_dag = {d["dag"]: d for d in data["dagen"]}
        assert dagen_by_dag[0]["personen"] == 4  # ma
        assert dagen_by_dag[4]["personen"] == 3  # vr
        assert dagen_by_dag[1]["personen"] == 2  # di = default


class TestCmdToon:
    """Tests voor het toon command."""

    def test_toon_bestaand_menu(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        from boodschappenagent.cli.menu import cmd_toon

        recipes_dir = _setup_recipes_dir(tmp_path)
        menu_path = tmp_path / "current_menu.json"
        menu_data = {
            "week_start": "2026-02-09",
            "dagen": [
                {"dag": 0, "recept_id": "vlees-pasta", "personen": 2},
                {"dag": 1, "recept_id": None, "personen": 0},
            ],
        }
        menu_path.write_text(json.dumps(menu_data), encoding="utf-8")

        args = _make_base_args(
            recipes_dir=str(recipes_dir),
            menu=str(menu_path),
        )

        result = cmd_toon(args)

        assert result == 0
        output = capsys.readouterr().out
        assert "Vlees Pasta" in output
        assert "Maandag" in output

    def test_toon_geen_menu(self, tmp_path: Path) -> None:
        from boodschappenagent.cli.menu import cmd_toon

        menu_path = tmp_path / "current_menu.json"
        args = _make_base_args(
            recipes_dir=str(tmp_path / "recipes"),
            menu=str(menu_path),
        )

        result = cmd_toon(args)
        assert result == 1


class TestCmdVervang:
    """Tests voor het vervang command."""

    def test_vervang_recept(self, tmp_path: Path) -> None:
        from boodschappenagent.cli.menu import cmd_vervang

        recipes_dir = _setup_recipes_dir(tmp_path)
        history_path = tmp_path / "history.json"
        menu_path = tmp_path / "current_menu.json"

        menu_data = {
            "week_start": "2026-02-09",
            "dagen": [
                {"dag": 0, "recept_id": "vlees-pasta", "personen": 2},
                {"dag": 1, "recept_id": "vis-rijst", "personen": 2},
                {"dag": 2, "recept_id": "gevogelte-brood", "personen": 2},
            ],
        }
        menu_path.write_text(json.dumps(menu_data), encoding="utf-8")

        args = _make_vervang_args(
            recipes_dir=str(recipes_dir),
            history=str(history_path),
            menu=str(menu_path),
            dag="ma",
            seizoen=None,
            personen=None,
            vrij=False,
        )

        result = cmd_vervang(args)

        assert result == 0
        new_data = json.loads(menu_path.read_text())
        dag0 = next(d for d in new_data["dagen"] if d["dag"] == 0)
        # Recept moet veranderd zijn (ander recept dan vlees-pasta)
        assert dag0["recept_id"] != "vlees-pasta"

    def test_vervang_personen(self, tmp_path: Path) -> None:
        from boodschappenagent.cli.menu import cmd_vervang

        recipes_dir = _setup_recipes_dir(tmp_path)
        menu_path = tmp_path / "current_menu.json"

        menu_data = {
            "week_start": "2026-02-09",
            "dagen": [
                {"dag": 0, "recept_id": "vlees-pasta", "personen": 2},
                {"dag": 1, "recept_id": "vis-rijst", "personen": 2},
            ],
        }
        menu_path.write_text(json.dumps(menu_data), encoding="utf-8")

        args = _make_vervang_args(
            recipes_dir=str(recipes_dir),
            history=str(tmp_path / "history.json"),
            menu=str(menu_path),
            dag="ma",
            seizoen=None,
            personen=4,
            vrij=False,
        )

        result = cmd_vervang(args)

        assert result == 0
        new_data = json.loads(menu_path.read_text())
        dag0 = next(d for d in new_data["dagen"] if d["dag"] == 0)
        assert dag0["personen"] == 4
        # Recept blijft hetzelfde
        assert dag0["recept_id"] == "vlees-pasta"

    def test_vervang_vrij(self, tmp_path: Path) -> None:
        from boodschappenagent.cli.menu import cmd_vervang

        recipes_dir = _setup_recipes_dir(tmp_path)
        menu_path = tmp_path / "current_menu.json"

        menu_data = {
            "week_start": "2026-02-09",
            "dagen": [
                {"dag": 0, "recept_id": "vlees-pasta", "personen": 2},
                {"dag": 1, "recept_id": "vis-rijst", "personen": 2},
            ],
        }
        menu_path.write_text(json.dumps(menu_data), encoding="utf-8")

        args = _make_vervang_args(
            recipes_dir=str(recipes_dir),
            history=str(tmp_path / "history.json"),
            menu=str(menu_path),
            dag="ma",
            seizoen=None,
            personen=None,
            vrij=True,
        )

        result = cmd_vervang(args)

        assert result == 0
        new_data = json.loads(menu_path.read_text())
        dag0 = next(d for d in new_data["dagen"] if d["dag"] == 0)
        assert dag0["personen"] == 0
        assert dag0["recept_id"] is None

    def test_vervang_vrij_naar_koken(self, tmp_path: Path) -> None:
        """Vrije dag weer activeren met --personen."""
        from boodschappenagent.cli.menu import cmd_vervang

        recipes_dir = _setup_recipes_dir(tmp_path)
        menu_path = tmp_path / "current_menu.json"

        menu_data = {
            "week_start": "2026-02-09",
            "dagen": [
                {"dag": 0, "recept_id": None, "personen": 0},
                {"dag": 1, "recept_id": "vis-rijst", "personen": 2},
            ],
        }
        menu_path.write_text(json.dumps(menu_data), encoding="utf-8")

        args = _make_vervang_args(
            recipes_dir=str(recipes_dir),
            history=str(tmp_path / "history.json"),
            menu=str(menu_path),
            dag="ma",
            seizoen=None,
            personen=2,
            vrij=False,
        )

        result = cmd_vervang(args)

        assert result == 0
        new_data = json.loads(menu_path.read_text())
        dag0 = next(d for d in new_data["dagen"] if d["dag"] == 0)
        assert dag0["personen"] == 2
        assert dag0["recept_id"] is not None

    def test_vervang_meerdere_dagen_vrij(self, tmp_path: Path) -> None:
        from boodschappenagent.cli.menu import cmd_vervang

        recipes_dir = _setup_recipes_dir(tmp_path)
        menu_path = tmp_path / "current_menu.json"

        menu_data = {
            "week_start": "2026-02-09",
            "dagen": [
                {"dag": 0, "recept_id": "vlees-pasta", "personen": 2},
                {"dag": 1, "recept_id": "vis-rijst", "personen": 2},
                {"dag": 5, "recept_id": "gevogelte-brood", "personen": 2},
                {"dag": 6, "recept_id": "veg-aardappel", "personen": 2},
            ],
        }
        menu_path.write_text(json.dumps(menu_data), encoding="utf-8")

        args = _make_vervang_args(
            recipes_dir=str(recipes_dir),
            history=str(tmp_path / "history.json"),
            menu=str(menu_path),
            dag="za,zo",
            seizoen=None,
            personen=None,
            vrij=True,
        )

        result = cmd_vervang(args)

        assert result == 0
        new_data = json.loads(menu_path.read_text())
        dag5 = next(d for d in new_data["dagen"] if d["dag"] == 5)
        dag6 = next(d for d in new_data["dagen"] if d["dag"] == 6)
        assert dag5["personen"] == 0
        assert dag5["recept_id"] is None
        assert dag6["personen"] == 0
        assert dag6["recept_id"] is None

    def test_vervang_meerdere_dagen_personen(self, tmp_path: Path) -> None:
        from boodschappenagent.cli.menu import cmd_vervang

        recipes_dir = _setup_recipes_dir(tmp_path)
        menu_path = tmp_path / "current_menu.json"

        menu_data = {
            "week_start": "2026-02-09",
            "dagen": [
                {"dag": 0, "recept_id": "vlees-pasta", "personen": 2},
                {"dag": 4, "recept_id": "vis-rijst", "personen": 2},
            ],
        }
        menu_path.write_text(json.dumps(menu_data), encoding="utf-8")

        args = _make_vervang_args(
            recipes_dir=str(recipes_dir),
            history=str(tmp_path / "history.json"),
            menu=str(menu_path),
            dag="ma,vr",
            seizoen=None,
            personen=4,
            vrij=False,
        )

        result = cmd_vervang(args)

        assert result == 0
        new_data = json.loads(menu_path.read_text())
        dag0 = next(d for d in new_data["dagen"] if d["dag"] == 0)
        dag4 = next(d for d in new_data["dagen"] if d["dag"] == 4)
        assert dag0["personen"] == 4
        assert dag0["recept_id"] == "vlees-pasta"
        assert dag4["personen"] == 4
        assert dag4["recept_id"] == "vis-rijst"

    def test_vervang_meerdere_dagen_recept(self, tmp_path: Path) -> None:
        from boodschappenagent.cli.menu import cmd_vervang

        recipes_dir = _setup_recipes_dir(tmp_path)
        menu_path = tmp_path / "current_menu.json"

        menu_data = {
            "week_start": "2026-02-09",
            "dagen": [
                {"dag": 0, "recept_id": "vlees-pasta", "personen": 2},
                {"dag": 1, "recept_id": "vis-rijst", "personen": 2},
                {"dag": 2, "recept_id": "gevogelte-brood", "personen": 2},
            ],
        }
        menu_path.write_text(json.dumps(menu_data), encoding="utf-8")

        args = _make_vervang_args(
            recipes_dir=str(recipes_dir),
            history=str(tmp_path / "history.json"),
            menu=str(menu_path),
            dag="ma,di",
            seizoen=None,
            personen=None,
            vrij=False,
        )

        result = cmd_vervang(args)

        assert result == 0
        new_data = json.loads(menu_path.read_text())
        dag0 = next(d for d in new_data["dagen"] if d["dag"] == 0)
        dag1 = next(d for d in new_data["dagen"] if d["dag"] == 1)
        assert dag0["recept_id"] != "vlees-pasta"
        assert dag1["recept_id"] != "vis-rijst"

    def test_vervang_recept_op_vrije_dag(self, tmp_path: Path) -> None:
        """Vervang zonder --personen op een vrije dag activeert met default personen."""
        from boodschappenagent.cli.menu import cmd_vervang

        recipes_dir = _setup_recipes_dir(tmp_path)
        menu_path = tmp_path / "current_menu.json"

        menu_data = {
            "week_start": "2026-02-09",
            "dagen": [
                {"dag": 0, "recept_id": "vlees-pasta", "personen": 2},
                {"dag": 1, "recept_id": None, "personen": 0},
                {"dag": 4, "recept_id": "vis-rijst", "personen": 4},
            ],
        }
        menu_path.write_text(json.dumps(menu_data), encoding="utf-8")

        args = _make_vervang_args(
            recipes_dir=str(recipes_dir),
            history=str(tmp_path / "history.json"),
            menu=str(menu_path),
            dag="di",
            seizoen=None,
            personen=None,
            vrij=False,
        )

        result = cmd_vervang(args)

        assert result == 0
        new_data = json.loads(menu_path.read_text())
        dag1 = next(d for d in new_data["dagen"] if d["dag"] == 1)
        # Moet een recept hebben gekregen
        assert dag1["recept_id"] is not None
        # Personen afgeleid van andere dagen (mediaan/meest voorkomend)
        assert dag1["personen"] > 0

    def test_vervang_geen_menu(self, tmp_path: Path) -> None:
        from boodschappenagent.cli.menu import cmd_vervang

        menu_path = tmp_path / "current_menu.json"
        args = _make_vervang_args(
            recipes_dir=str(tmp_path / "recipes"),
            history=str(tmp_path / "history.json"),
            menu=str(menu_path),
            dag="ma",
            seizoen=None,
            personen=None,
            vrij=False,
        )

        result = cmd_vervang(args)
        assert result == 1


class TestCmdAccepteer:
    """Tests voor het accepteer command."""

    def test_accepteer_slaat_op_in_history(self, tmp_path: Path) -> None:
        from boodschappenagent.cli.menu import cmd_accepteer

        recipes_dir = _setup_recipes_dir(tmp_path)
        history_path = tmp_path / "history.json"
        menu_path = tmp_path / "current_menu.json"

        menu_data = {
            "week_start": "2026-02-09",
            "dagen": [
                {"dag": 0, "recept_id": "vlees-pasta", "personen": 2},
                {"dag": 1, "recept_id": None, "personen": 0},
                {"dag": 2, "recept_id": "vis-rijst", "personen": 3},
            ],
        }
        menu_path.write_text(json.dumps(menu_data), encoding="utf-8")

        args = _make_accepteer_args(
            recipes_dir=str(recipes_dir),
            history=str(history_path),
            menu=str(menu_path),
        )

        result = cmd_accepteer(args)

        assert result == 0
        assert not menu_path.exists()
        history = json.loads(history_path.read_text())
        assert len(history) == 2  # dag 0 en dag 2 (dag 1 is niet thuis)
        assert history[0]["recept_id"] == "vlees-pasta"
        assert history[1]["recept_id"] == "vis-rijst"

    def test_accepteer_geen_menu(self, tmp_path: Path) -> None:
        from boodschappenagent.cli.menu import cmd_accepteer

        menu_path = tmp_path / "current_menu.json"
        args = _make_accepteer_args(
            recipes_dir=str(tmp_path / "recipes"),
            history=str(tmp_path / "history.json"),
            menu=str(menu_path),
        )

        result = cmd_accepteer(args)
        assert result == 1


# --- Helpers voor argparse.Namespace mock ---


def _make_base_args(**kwargs: str) -> type:
    """Maak een simpel args object."""
    import argparse

    return argparse.Namespace(**kwargs)


def _make_plan_args(**kwargs: str | int | None) -> type:
    """Maak args voor plan command."""
    import argparse

    return argparse.Namespace(command="plan", **kwargs)


def _make_vervang_args(**kwargs: str | None) -> type:
    """Maak args voor vervang command."""
    import argparse

    return argparse.Namespace(command="vervang", **kwargs)


def _make_accepteer_args(**kwargs: str) -> type:
    """Maak args voor accepteer command."""
    import argparse

    return argparse.Namespace(command="accepteer", **kwargs)
