"""Tests voor MenuPlanner: selectielogica voor weekmenu's."""

from pathlib import Path

import pytest

from boodschappenagent.models import Basis, Categorie, Ingredient, Recipe, Seizoen
from boodschappenagent.planner.history import MenuHistory
from boodschappenagent.planner.menu_planner import MenuPlanner
from boodschappenagent.planner.models import DagInput, WeekMenu


def _make_recipe(
    recipe_id: str,
    categorie: Categorie = Categorie.VLEES,
    basis: Basis = Basis.PASTA,
    seizoenen: list[Seizoen] | None = None,
) -> Recipe:
    """Helper om snel een recept te maken voor tests."""
    return Recipe(
        id=recipe_id,
        naam=recipe_id.replace("-", " ").title(),
        categorie=categorie,
        basis=basis,
        seizoenen=seizoenen or [Seizoen.ALLE],
        basis_porties=4,
        ingredienten=[Ingredient(naam="iets", hoeveelheid=100, eenheid="gram")],
        bereidingstijd_min=30,
    )


@pytest.fixture
def diverse_recipes() -> list[Recipe]:
    """10 recepten verspreid over categorieën en bases."""
    return [
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


@pytest.fixture
def empty_history(tmp_path: Path) -> MenuHistory:
    """MenuHistory zonder geschiedenis."""
    return MenuHistory(tmp_path / "history.json")


@pytest.fixture
def planner(diverse_recipes: list[Recipe], empty_history: MenuHistory) -> MenuPlanner:
    """Deterministische planner met seed=42."""
    return MenuPlanner(diverse_recipes, empty_history, random_seed=42)


class TestPlanWeekBasic:
    """Basistests voor plan_week."""

    def test_retourneert_week_menu(self, planner: MenuPlanner) -> None:
        week_input = [DagInput(dag=i, personen=2) for i in range(7)]
        result = planner.plan_week(week_input, Seizoen.ALLE, "2026-02-09")
        assert isinstance(result, WeekMenu)

    def test_alle_dagen_hebben_recept(self, planner: MenuPlanner) -> None:
        week_input = [DagInput(dag=i, personen=2) for i in range(7)]
        result = planner.plan_week(week_input, Seizoen.ALLE, "2026-02-09")
        assert len(result.geplande_dagen) == 7
        for dag in result.dagen:
            assert dag.recept is not None

    def test_niet_thuis_krijgt_geen_recept(self, planner: MenuPlanner) -> None:
        week_input = [
            DagInput(dag=0, personen=2),
            DagInput(dag=1, personen=0),
            DagInput(dag=2, personen=2),
        ]
        result = planner.plan_week(week_input, Seizoen.ALLE, "2026-02-09")
        assert len(result.dagen) == 3
        assert result.dagen[1].recept is None
        assert len(result.geplande_dagen) == 2

    def test_week_start_correct(self, planner: MenuPlanner) -> None:
        week_input = [DagInput(dag=0, personen=2)]
        result = planner.plan_week(week_input, Seizoen.ALLE, "2026-02-09")
        assert result.week_start == "2026-02-09"


class TestPlanWeekSeizoen:
    """Tests voor seizoensfiltering."""

    def test_alleen_seizoensrecepten_geselecteerd(self, tmp_path: Path) -> None:
        recipes = [
            _make_recipe("winter-recept", seizoenen=[Seizoen.WINTER]),
            _make_recipe("zomer-recept", seizoenen=[Seizoen.ZOMER]),
            _make_recipe("alle-recept", seizoenen=[Seizoen.ALLE]),
        ]
        history = MenuHistory(tmp_path / "history.json")
        planner = MenuPlanner(recipes, history, random_seed=42)
        week_input = [DagInput(dag=0, personen=2)]
        result = planner.plan_week(week_input, Seizoen.WINTER, "2026-02-09")
        gekozen_id = result.dagen[0].recept.id
        assert gekozen_id in {"winter-recept", "alle-recept"}

    def test_alle_seizoen_altijd_mee(self, tmp_path: Path) -> None:
        recipes = [
            _make_recipe("alleen-alle", seizoenen=[Seizoen.ALLE]),
        ]
        history = MenuHistory(tmp_path / "history.json")
        planner = MenuPlanner(recipes, history, random_seed=42)
        week_input = [DagInput(dag=0, personen=2)]
        result = planner.plan_week(week_input, Seizoen.ZOMER, "2026-02-09")
        assert result.dagen[0].recept.id == "alleen-alle"

    def test_zomer_recept_nooit_in_winter(self, tmp_path: Path) -> None:
        """Met meerdere seeds: zomer-only recept mag nooit in winter gepland worden."""
        recipes = [
            _make_recipe("winter-recept", seizoenen=[Seizoen.WINTER]),
            _make_recipe("zomer-recept", seizoenen=[Seizoen.ZOMER]),
        ]
        history = MenuHistory(tmp_path / "history.json")
        week_input = [DagInput(dag=0, personen=2)]
        for seed in range(20):
            planner = MenuPlanner(recipes, history, random_seed=seed)
            result = planner.plan_week(week_input, Seizoen.WINTER, "2026-02-09")
            assert result.dagen[0].recept.id == "winter-recept"


class TestPlanWeekVariety:
    """Tests voor variatie-constraints."""

    def test_geen_opeenvolgende_zelfde_categorie(
        self, diverse_recipes: list[Recipe], empty_history: MenuHistory
    ) -> None:
        """Over meerdere seeds: nooit 2x dezelfde categorie achter elkaar."""
        week_input = [DagInput(dag=i, personen=2) for i in range(7)]
        for seed in range(20):
            planner = MenuPlanner(diverse_recipes, empty_history, random_seed=seed)
            result = planner.plan_week(week_input, Seizoen.ALLE, "2026-02-09")
            for i in range(len(result.dagen) - 1):
                cur = result.dagen[i].recept.categorie
                nxt = result.dagen[i + 1].recept.categorie
                assert cur != nxt, (
                    f"seed={seed}: dag {i} en {i + 1} "
                    f"hebben beide categorie {cur.value}"
                )

    def test_geen_opeenvolgende_zelfde_basis(
        self, diverse_recipes: list[Recipe], empty_history: MenuHistory
    ) -> None:
        """Over meerdere seeds: nooit 2x dezelfde basis achter elkaar."""
        week_input = [DagInput(dag=i, personen=2) for i in range(7)]
        for seed in range(20):
            planner = MenuPlanner(diverse_recipes, empty_history, random_seed=seed)
            result = planner.plan_week(week_input, Seizoen.ALLE, "2026-02-09")
            for i in range(len(result.dagen) - 1):
                cur = result.dagen[i].recept.basis
                nxt = result.dagen[i + 1].recept.basis
                assert cur != nxt, (
                    f"seed={seed}: dag {i} en {i + 1} hebben beide basis {cur.value}"
                )

    def test_geen_duplicaten_in_week(
        self, diverse_recipes: list[Recipe], empty_history: MenuHistory
    ) -> None:
        """Elk recept wordt maximaal 1x per week gebruikt."""
        week_input = [DagInput(dag=i, personen=2) for i in range(7)]
        for seed in range(20):
            planner = MenuPlanner(diverse_recipes, empty_history, random_seed=seed)
            result = planner.plan_week(week_input, Seizoen.ALLE, "2026-02-09")
            ids = [d.recept.id for d in result.dagen]
            assert len(ids) == len(set(ids)), f"seed={seed}: duplicaten gevonden"

    def test_recent_gegeten_niet_opnieuw(self, tmp_path: Path) -> None:
        """Recepten uit de geschiedenis worden niet opnieuw gekozen."""
        from datetime import date, timedelta

        recipes = [
            _make_recipe("recent-gegeten", Categorie.VLEES, Basis.PASTA),
            _make_recipe("niet-gegeten", Categorie.GEVOGELTE, Basis.RIJST),
        ]
        history = MenuHistory(tmp_path / "history.json")
        history.save(
            [
                {
                    "datum": (date.today() - timedelta(days=5)).isoformat(),
                    "recept_id": "recent-gegeten",
                    "personen": 2,
                }
            ]
        )
        week_input = [DagInput(dag=0, personen=2)]
        for seed in range(20):
            planner = MenuPlanner(recipes, history, random_seed=seed)
            result = planner.plan_week(week_input, Seizoen.ALLE, "2026-02-09")
            assert result.dagen[0].recept.id == "niet-gegeten"


class TestPlanWeekFallback:
    """Tests voor fallback wanneer strikte constraints niet voldaan kunnen worden."""

    def test_fallback_bij_beperkte_pool(self, tmp_path: Path) -> None:
        """Met slechts 3 recepten van dezelfde categorie, moet fallback relaxeren."""
        recipes = [
            _make_recipe("vlees-pasta", Categorie.VLEES, Basis.PASTA),
            _make_recipe("vlees-rijst", Categorie.VLEES, Basis.RIJST),
            _make_recipe("vlees-aardappel", Categorie.VLEES, Basis.AARDAPPEL),
        ]
        history = MenuHistory(tmp_path / "history.json")
        planner = MenuPlanner(recipes, history, random_seed=42)
        week_input = [DagInput(dag=i, personen=2) for i in range(3)]
        # Zonder fallback zou dit crashen na dag 1 (alles zelfde categorie)
        result = planner.plan_week(week_input, Seizoen.ALLE, "2026-02-09")
        assert len(result.geplande_dagen) == 3

    def test_raises_bij_nul_recepten(self, tmp_path: Path) -> None:
        """Zonder recepten moet er een fout komen."""
        history = MenuHistory(tmp_path / "history.json")
        planner = MenuPlanner([], history, random_seed=42)
        week_input = [DagInput(dag=0, personen=2)]
        with pytest.raises(ValueError, match="geen kandidaat-recepten"):
            planner.plan_week(week_input, Seizoen.ALLE, "2026-02-09")

    def test_fallback_bij_alle_recent_gegeten(self, tmp_path: Path) -> None:
        """Alle recepten recent gegeten: plan toch."""
        from datetime import date, timedelta

        recipes = [
            _make_recipe("recept-a", Categorie.VLEES, Basis.PASTA),
            _make_recipe("recept-b", Categorie.GEVOGELTE, Basis.RIJST),
        ]
        history = MenuHistory(tmp_path / "history.json")
        vandaag = date.today()
        d3 = (vandaag - timedelta(days=3)).isoformat()
        d5 = (vandaag - timedelta(days=5)).isoformat()
        history.save(
            [
                {"datum": d3, "recept_id": "recept-a", "personen": 2},
                {"datum": d5, "recept_id": "recept-b", "personen": 2},
            ]
        )
        planner = MenuPlanner(recipes, history, random_seed=42)
        week_input = [DagInput(dag=0, personen=2)]
        result = planner.plan_week(week_input, Seizoen.ALLE, "2026-02-09")
        assert result.dagen[0].recept is not None


class TestVervangRecept:
    """Tests voor het vervangen van een enkel recept in een weekmenu."""

    def test_andere_dagen_ongewijzigd(self, planner: MenuPlanner) -> None:
        week_input = [DagInput(dag=i, personen=2) for i in range(5)]
        menu = planner.plan_week(week_input, Seizoen.ALLE, "2026-02-09")
        originele_ids = {d.dag: d.recept.id for d in menu.dagen}

        nieuw_menu = planner.vervang_recept(menu, 2, Seizoen.ALLE)

        for dag in nieuw_menu.dagen:
            if dag.dag != 2:
                assert dag.recept.id == originele_ids[dag.dag]

    def test_vervangen_dag_heeft_ander_recept(self, planner: MenuPlanner) -> None:
        week_input = [DagInput(dag=i, personen=2) for i in range(5)]
        menu = planner.plan_week(week_input, Seizoen.ALLE, "2026-02-09")
        oud_recept_id = menu.dagen[2].recept.id

        nieuw_menu = planner.vervang_recept(menu, 2, Seizoen.ALLE)
        assert nieuw_menu.dagen[2].recept.id != oud_recept_id

    def test_retourneert_nieuw_weekmenu(self, planner: MenuPlanner) -> None:
        week_input = [DagInput(dag=i, personen=2) for i in range(3)]
        menu = planner.plan_week(week_input, Seizoen.ALLE, "2026-02-09")
        nieuw_menu = planner.vervang_recept(menu, 1, Seizoen.ALLE)
        assert nieuw_menu is not menu


class TestPlanWeekDeterministic:
    """Tests voor determinisme via random_seed."""

    def test_zelfde_seed_zelfde_resultaat(
        self, diverse_recipes: list[Recipe], empty_history: MenuHistory
    ) -> None:
        """Twee planners met dezelfde seed produceren identiek menu."""
        week_input = [DagInput(dag=i, personen=2) for i in range(7)]
        planner_a = MenuPlanner(diverse_recipes, empty_history, random_seed=99)
        planner_b = MenuPlanner(diverse_recipes, empty_history, random_seed=99)

        result_a = planner_a.plan_week(week_input, Seizoen.ALLE, "2026-02-09")
        result_b = planner_b.plan_week(week_input, Seizoen.ALLE, "2026-02-09")

        ids_a = [d.recept.id for d in result_a.dagen]
        ids_b = [d.recept.id for d in result_b.dagen]
        assert ids_a == ids_b

    def test_andere_seed_ander_resultaat(
        self, diverse_recipes: list[Recipe], empty_history: MenuHistory
    ) -> None:
        """Twee planners met verschillende seeds produceren meestal ander menu."""
        week_input = [DagInput(dag=i, personen=2) for i in range(7)]
        planner_a = MenuPlanner(diverse_recipes, empty_history, random_seed=1)
        planner_b = MenuPlanner(diverse_recipes, empty_history, random_seed=2)

        result_a = planner_a.plan_week(week_input, Seizoen.ALLE, "2026-02-09")
        result_b = planner_b.plan_week(week_input, Seizoen.ALLE, "2026-02-09")

        ids_a = [d.recept.id for d in result_a.dagen]
        ids_b = [d.recept.id for d in result_b.dagen]
        assert ids_a != ids_b
