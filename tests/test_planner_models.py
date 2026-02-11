"""Tests voor planner data models: DagInput, DagPlanning, WeekMenu."""

import pytest

from boodschappenagent.models import Basis, Categorie, Ingredient, Recipe, Seizoen
from boodschappenagent.planner.models import DagInput, DagPlanning, WeekMenu


def _make_recipe(
    recipe_id: str = "test-recept",
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


class TestDagInput:
    """Tests voor DagInput dataclass."""

    def test_create_valid(self) -> None:
        dag_input = DagInput(dag=0, personen=2)
        assert dag_input.dag == 0
        assert dag_input.personen == 2

    def test_create_niet_thuis(self) -> None:
        dag_input = DagInput(dag=3, personen=0)
        assert dag_input.personen == 0

    def test_alle_weekdagen_geldig(self) -> None:
        for dag in range(7):
            dag_input = DagInput(dag=dag, personen=2)
            assert dag_input.dag == dag

    def test_dag_te_laag_raises(self) -> None:
        with pytest.raises(ValueError, match="dag moet tussen 0 en 6 zijn"):
            DagInput(dag=-1, personen=2)

    def test_dag_te_hoog_raises(self) -> None:
        with pytest.raises(ValueError, match="dag moet tussen 0 en 6 zijn"):
            DagInput(dag=7, personen=2)

    def test_personen_negatief_raises(self) -> None:
        with pytest.raises(ValueError, match="personen moet >= 0 zijn"):
            DagInput(dag=0, personen=-1)

    def test_frozen(self) -> None:
        dag_input = DagInput(dag=0, personen=2)
        with pytest.raises(AttributeError):
            dag_input.dag = 1  # type: ignore[misc]


class TestDagPlanning:
    """Tests voor DagPlanning dataclass."""

    def test_create_valid(self) -> None:
        recept = _make_recipe()
        dag = DagPlanning(dag=0, recept=recept, personen=2)
        assert dag.dag == 0
        assert dag.recept == recept
        assert dag.personen == 2

    def test_create_niet_thuis(self) -> None:
        dag = DagPlanning(dag=3, recept=None, personen=0)
        assert dag.recept is None
        assert dag.personen == 0

    def test_personen_nul_met_recept_raises(self) -> None:
        with pytest.raises(ValueError, match="recept moet None zijn als personen 0"):
            DagPlanning(dag=0, recept=_make_recipe(), personen=0)

    def test_personen_zonder_recept_raises(self) -> None:
        with pytest.raises(ValueError, match="recept is verplicht als personen > 0"):
            DagPlanning(dag=0, recept=None, personen=2)

    def test_dag_out_of_range_raises(self) -> None:
        with pytest.raises(ValueError, match="dag moet tussen 0 en 6 zijn"):
            DagPlanning(dag=7, recept=_make_recipe(), personen=2)

    def test_personen_negatief_raises(self) -> None:
        with pytest.raises(ValueError, match="personen moet >= 0 zijn"):
            DagPlanning(dag=0, recept=None, personen=-1)

    def test_to_dict(self) -> None:
        dag = DagPlanning(dag=1, recept=_make_recipe(), personen=3)
        result = dag.to_dict()
        assert result == {
            "dag": 1,
            "recept_id": "test-recept",
            "personen": 3,
        }

    def test_to_dict_niet_thuis(self) -> None:
        dag = DagPlanning(dag=5, recept=None, personen=0)
        result = dag.to_dict()
        assert result == {
            "dag": 5,
            "recept_id": None,
            "personen": 0,
        }

    def test_frozen(self) -> None:
        dag = DagPlanning(dag=0, recept=_make_recipe(), personen=2)
        with pytest.raises(AttributeError):
            dag.recept = None  # type: ignore[misc]


class TestWeekMenu:
    """Tests voor WeekMenu dataclass."""

    def test_create_valid(self) -> None:
        dagen = [DagPlanning(dag=0, recept=_make_recipe(), personen=2)]
        menu = WeekMenu(week_start="2026-02-09", dagen=dagen)
        assert menu.week_start == "2026-02-09"
        assert len(menu.dagen) == 1

    def test_lege_week(self) -> None:
        menu = WeekMenu(week_start="2026-02-09", dagen=[])
        assert len(menu.dagen) == 0

    def test_volledige_week(self) -> None:
        dagen = []
        for dag_nr in range(7):
            recept = _make_recipe(f"recept-{dag_nr}")
            dagen.append(DagPlanning(dag=dag_nr, recept=recept, personen=2))
        menu = WeekMenu(week_start="2026-02-09", dagen=dagen)
        assert len(menu.dagen) == 7

    def test_meer_dan_7_dagen_raises(self) -> None:
        recept = _make_recipe()
        dagen = [
            DagPlanning(dag=i % 7, recept=recept, personen=2) for i in range(8)
        ]
        with pytest.raises(ValueError, match="maximaal 7 dagen per week"):
            WeekMenu(week_start="2026-02-09", dagen=dagen)

    def test_dubbele_dagen_raises(self) -> None:
        recept = _make_recipe()
        dagen = [
            DagPlanning(dag=0, recept=recept, personen=2),
            DagPlanning(dag=0, recept=recept, personen=3),
        ]
        with pytest.raises(ValueError, match="dubbele dagen in weekmenu"):
            WeekMenu(week_start="2026-02-09", dagen=dagen)

    def test_week_start_leeg_raises(self) -> None:
        dagen = [DagPlanning(dag=0, recept=_make_recipe(), personen=2)]
        with pytest.raises(ValueError, match="week_start mag niet leeg zijn"):
            WeekMenu(week_start="", dagen=dagen)

    def test_geplande_dagen_filtert_niet_thuis(self) -> None:
        recept = _make_recipe()
        dagen = [
            DagPlanning(dag=0, recept=recept, personen=2),
            DagPlanning(dag=1, recept=None, personen=0),
            DagPlanning(dag=2, recept=recept, personen=4),
        ]
        menu = WeekMenu(week_start="2026-02-09", dagen=dagen)
        geplande = menu.geplande_dagen
        assert len(geplande) == 2
        assert all(d.recept is not None for d in geplande)

    def test_to_dict(self) -> None:
        recept = _make_recipe()
        dagen = [
            DagPlanning(dag=0, recept=recept, personen=2),
            DagPlanning(dag=1, recept=None, personen=0),
        ]
        menu = WeekMenu(week_start="2026-02-09", dagen=dagen)
        result = menu.to_dict()
        assert result == {
            "week_start": "2026-02-09",
            "dagen": [
                {"dag": 0, "recept_id": "test-recept", "personen": 2},
                {"dag": 1, "recept_id": None, "personen": 0},
            ],
        }

    def test_frozen(self) -> None:
        dagen = [DagPlanning(dag=0, recept=_make_recipe(), personen=2)]
        menu = WeekMenu(week_start="2026-02-09", dagen=dagen)
        with pytest.raises(AttributeError):
            menu.week_start = "2026-02-16"  # type: ignore[misc]
