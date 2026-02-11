"""Tests voor MenuHistory: JSON persistentie van menu-geschiedenis."""

from datetime import date, timedelta
from pathlib import Path

import pytest

from boodschappenagent.models import Basis, Categorie, Ingredient, Recipe, Seizoen
from boodschappenagent.planner.history import MenuHistory
from boodschappenagent.planner.models import DagPlanning, WeekMenu


def _make_recipe(recipe_id: str = "test-recept") -> Recipe:
    """Helper om snel een recept te maken voor tests."""
    return Recipe(
        id=recipe_id,
        naam=recipe_id.replace("-", " ").title(),
        categorie=Categorie.VLEES,
        basis=Basis.PASTA,
        seizoenen=[Seizoen.ALLE],
        basis_porties=4,
        ingredienten=[Ingredient(naam="iets", hoeveelheid=100, eenheid="gram")],
        bereidingstijd_min=30,
    )


class TestMenuHistoryLoad:
    """Tests voor het laden van geschiedenis."""

    def test_load_bestaand_bestand(self, tmp_path: Path) -> None:
        path = tmp_path / "history.json"
        path.write_text(
            '[{"datum": "2026-02-10", "recept_id": "pasta-bolognese", "personen": 4}]'
        )
        history = MenuHistory(path)
        entries = history.load()
        assert len(entries) == 1
        assert entries[0]["recept_id"] == "pasta-bolognese"

    def test_load_niet_bestaand_retourneert_leeg(self, tmp_path: Path) -> None:
        path = tmp_path / "niet-bestaand.json"
        history = MenuHistory(path)
        entries = history.load()
        assert entries == []

    def test_load_ongeldig_json_raises(self, tmp_path: Path) -> None:
        path = tmp_path / "corrupt.json"
        path.write_text("dit is geen json")
        history = MenuHistory(path)
        with pytest.raises(ValueError, match="Ongeldig JSON"):
            history.load()


class TestMenuHistorySave:
    """Tests voor het opslaan van geschiedenis."""

    def test_save_maakt_bestand(self, tmp_path: Path) -> None:
        path = tmp_path / "history.json"
        history = MenuHistory(path)
        entries = [{"datum": "2026-02-10", "recept_id": "kip-teriyaki", "personen": 2}]
        history.save(entries)
        assert path.exists()

    def test_roundtrip_save_load(self, tmp_path: Path) -> None:
        path = tmp_path / "history.json"
        history = MenuHistory(path)
        entries = [
            {"datum": "2026-02-10", "recept_id": "pasta-bolognese", "personen": 4},
            {"datum": "2026-02-11", "recept_id": "kip-teriyaki", "personen": 2},
        ]
        history.save(entries)
        loaded = history.load()
        assert loaded == entries

    def test_save_overschrijft_bestaand(self, tmp_path: Path) -> None:
        path = tmp_path / "history.json"
        history = MenuHistory(path)
        history.save([{"datum": "2026-02-10", "recept_id": "oud", "personen": 2}])
        history.save([{"datum": "2026-02-11", "recept_id": "nieuw", "personen": 3}])
        loaded = history.load()
        assert len(loaded) == 1
        assert loaded[0]["recept_id"] == "nieuw"


class TestMenuHistoryAddWeek:
    """Tests voor het toevoegen van een weekmenu aan de geschiedenis."""

    def test_add_week_voegt_entries_toe(self, tmp_path: Path) -> None:
        path = tmp_path / "history.json"
        history = MenuHistory(path)
        week = WeekMenu(
            week_start="2026-02-09",
            dagen=[
                DagPlanning(dag=0, recept=_make_recipe("pasta-bolognese"), personen=4),
                DagPlanning(dag=1, recept=_make_recipe("kip-teriyaki"), personen=2),
            ],
        )
        history.add_week(week)
        entries = history.load()
        assert len(entries) == 2
        assert entries[0]["recept_id"] == "pasta-bolognese"
        assert entries[0]["datum"] == "2026-02-09"
        assert entries[1]["recept_id"] == "kip-teriyaki"
        assert entries[1]["datum"] == "2026-02-10"

    def test_add_week_skipt_niet_thuis(self, tmp_path: Path) -> None:
        path = tmp_path / "history.json"
        history = MenuHistory(path)
        week = WeekMenu(
            week_start="2026-02-09",
            dagen=[
                DagPlanning(dag=0, recept=_make_recipe("pasta-bolognese"), personen=4),
                DagPlanning(dag=1, recept=None, personen=0),
                DagPlanning(dag=2, recept=_make_recipe("kip-teriyaki"), personen=2),
            ],
        )
        history.add_week(week)
        entries = history.load()
        assert len(entries) == 2
        ids = {e["recept_id"] for e in entries}
        assert ids == {"pasta-bolognese", "kip-teriyaki"}

    def test_add_week_append_aan_bestaande_history(self, tmp_path: Path) -> None:
        path = tmp_path / "history.json"
        history = MenuHistory(path)
        history.save(
            [{"datum": "2026-02-02", "recept_id": "oud-recept", "personen": 2}]
        )
        week = WeekMenu(
            week_start="2026-02-09",
            dagen=[
                DagPlanning(dag=0, recept=_make_recipe("nieuw-recept"), personen=3),
            ],
        )
        history.add_week(week)
        entries = history.load()
        assert len(entries) == 2
        assert entries[0]["recept_id"] == "oud-recept"
        assert entries[1]["recept_id"] == "nieuw-recept"

    def test_add_week_lege_history(self, tmp_path: Path) -> None:
        path = tmp_path / "history.json"
        history = MenuHistory(path)
        week = WeekMenu(
            week_start="2026-02-09",
            dagen=[
                DagPlanning(dag=0, recept=_make_recipe(), personen=2),
            ],
        )
        history.add_week(week)
        entries = history.load()
        assert len(entries) == 1


class TestMenuHistoryRecentIds:
    """Tests voor recent_recipe_ids."""

    def _entry(self, days_ago: int, recept_id: str, personen: int = 2) -> dict:
        datum = (date.today() - timedelta(days=days_ago)).isoformat()
        return {"datum": datum, "recept_id": recept_id, "personen": personen}

    def test_default_3_weken(self, tmp_path: Path) -> None:
        path = tmp_path / "history.json"
        history = MenuHistory(path)
        history.save(
            [
                self._entry(7, "recent-1"),
                self._entry(14, "recent-2", personen=4),
            ]
        )
        ids = history.recent_recipe_ids()
        assert ids == {"recent-1", "recent-2"}

    def test_custom_weken(self, tmp_path: Path) -> None:
        path = tmp_path / "history.json"
        history = MenuHistory(path)
        history.save(
            [
                self._entry(3, "recent"),
                self._entry(10, "oud"),
            ]
        )
        ids = history.recent_recipe_ids(weken=1)
        assert ids == {"recent"}

    def test_lege_history(self, tmp_path: Path) -> None:
        path = tmp_path / "history.json"
        history = MenuHistory(path)
        ids = history.recent_recipe_ids()
        assert ids == set()

    def test_oude_entries_uitgesloten(self, tmp_path: Path) -> None:
        path = tmp_path / "history.json"
        history = MenuHistory(path)
        history.save([self._entry(30, "oud")])
        ids = history.recent_recipe_ids()
        assert ids == set()
