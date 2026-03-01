"""Tests voor MenuPlanner: selectielogica voor weekmenu's."""

import json
from pathlib import Path

import pytest

from boodschappenagent.models import Basis, Categorie, Ingredient, Recipe
from boodschappenagent.planner.history import MenuHistory
from boodschappenagent.planner.menu_planner import MenuPlanner
from boodschappenagent.planner.models import DagInput, WeekMenu
from boodschappenagent.planner.seizoen_kalender import SeizoenKalender


def _make_recipe(
    recipe_id: str,
    categorie: Categorie = Categorie.VLEES,
    basis: Basis = Basis.PASTA,
    ingredienten: list[Ingredient] | None = None,
) -> Recipe:
    """Helper om snel een recept te maken voor tests."""
    return Recipe(
        id=recipe_id,
        naam=recipe_id.replace("-", " ").title(),
        categorie=categorie,
        basis=basis,
        basis_porties=4,
        ingredienten=ingredienten
        or [
            Ingredient(naam="iets", hoeveelheid=100, eenheid="gram"),
        ],
        bereidingstijd_min=30,
    )


@pytest.fixture
def kalender(tmp_path):
    """Minimale seizoenskalender voor planner tests."""
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
    zomer = ["jun", "jul", "aug", "sep", "okt"]
    data = [
        {"nr": 1, "groente": "Tomaat", "lage_co2_maanden": zomer},
        {"nr": 2, "groente": "Ui", "lage_co2_maanden": alle},
        {
            "nr": 3,
            "groente": "Boerenkool",
            "lage_co2_maanden": ["nov", "dec", "jan", "feb"],
        },
        {"nr": 4, "groente": "Paprika", "lage_co2_maanden": zomer},
        {"nr": 5, "groente": "Champignon", "lage_co2_maanden": alle},
    ]
    path = tmp_path / "kalender.json"
    path.write_text(json.dumps(data))
    return SeizoenKalender(path)


@pytest.fixture
def diverse_recipes() -> list[Recipe]:
    """10 recepten verspreid over categorieën en bases.

    Alle recepten hebben alleen 'iets' als ingrediënt (geen herkenbare
    groenten), dus ze passeren het CO2-filter altijd.
    """
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
def planner(
    diverse_recipes: list[Recipe],
    empty_history: MenuHistory,
    kalender: SeizoenKalender,
) -> MenuPlanner:
    """Deterministische planner met seed=42."""
    return MenuPlanner(diverse_recipes, empty_history, kalender, random_seed=42)


# Maand "feb" wordt als default gebruikt; alle test-recepten hebben geen
# herkenbare groenten en zijn dus altijd seizoensgeschikt.
_MAAND = "feb"


class TestPlanWeekBasic:
    """Basistests voor plan_week."""

    def test_retourneert_week_menu(self, planner: MenuPlanner) -> None:
        week_input = [DagInput(dag=i, personen=2) for i in range(7)]
        result = planner.plan_week(week_input, _MAAND, "2026-02-09")
        assert isinstance(result, WeekMenu)

    def test_alle_dagen_hebben_recept(self, planner: MenuPlanner) -> None:
        week_input = [DagInput(dag=i, personen=2) for i in range(7)]
        result = planner.plan_week(week_input, _MAAND, "2026-02-09")
        assert len(result.geplande_dagen) == 7
        for dag in result.dagen:
            assert dag.recept is not None

    def test_niet_thuis_krijgt_geen_recept(self, planner: MenuPlanner) -> None:
        week_input = [
            DagInput(dag=0, personen=2),
            DagInput(dag=1, personen=0),
            DagInput(dag=2, personen=2),
        ]
        result = planner.plan_week(week_input, _MAAND, "2026-02-09")
        assert len(result.dagen) == 3
        assert result.dagen[1].recept is None
        assert len(result.geplande_dagen) == 2

    def test_week_start_correct(self, planner: MenuPlanner) -> None:
        week_input = [DagInput(dag=0, personen=2)]
        result = planner.plan_week(week_input, _MAAND, "2026-02-09")
        assert result.week_start == "2026-02-09"


class TestPlanWeekCo2Filtering:
    """Tests voor CO2-seizoensfiltering in de planner."""

    def test_alleen_seizoensgeschikte_recepten(self, tmp_path, kalender):
        """Recept met niet-seizoensgroenten wordt niet gekozen."""
        winter_recept = _make_recipe(
            "stampot",
            Categorie.VLEES,
            Basis.AARDAPPEL,
            ingredienten=[
                Ingredient(naam="boerenkool", hoeveelheid=500, eenheid="gram"),
                Ingredient(naam="ui", hoeveelheid=1, eenheid="stuks"),
            ],
        )
        zomer_recept = _make_recipe(
            "salade",
            Categorie.VEGETARISCH,
            Basis.GEEN,
            ingredienten=[
                Ingredient(naam="tomaat", hoeveelheid=3, eenheid="stuks"),
                Ingredient(naam="paprika", hoeveelheid=1, eenheid="stuks"),
            ],
        )
        recipes = [winter_recept, zomer_recept]
        history = MenuHistory(tmp_path / "history.json")
        week_input = [DagInput(dag=0, personen=2)]

        # In februari: boerenkool ✅, ui ✅, tomaat ❌, paprika ❌
        for seed in range(20):
            planner = MenuPlanner(recipes, history, kalender, random_seed=seed)
            result = planner.plan_week(week_input, "feb", "2026-02-09")
            assert result.dagen[0].recept.id == "stampot"

    def test_zomer_recept_wel_in_juli(self, tmp_path, kalender):
        """In juli zijn zomergroenten wel geschikt."""
        zomer_recept = _make_recipe(
            "salade",
            Categorie.VEGETARISCH,
            Basis.GEEN,
            ingredienten=[
                Ingredient(naam="tomaat", hoeveelheid=3, eenheid="stuks"),
                Ingredient(naam="paprika", hoeveelheid=1, eenheid="stuks"),
            ],
        )
        recipes = [zomer_recept]
        history = MenuHistory(tmp_path / "history.json")
        planner = MenuPlanner(recipes, history, kalender, random_seed=42)
        week_input = [DagInput(dag=0, personen=2)]
        result = planner.plan_week(week_input, "jul", "2026-07-06")
        assert result.dagen[0].recept.id == "salade"

    def test_recept_zonder_groenten_altijd_geschikt(self, tmp_path, kalender):
        """Recept zonder herkenbare groenten passeert altijd het CO2-filter."""
        recept = _make_recipe("pasta-carbonara")
        recipes = [recept]
        history = MenuHistory(tmp_path / "history.json")
        planner = MenuPlanner(recipes, history, kalender, random_seed=42)
        week_input = [DagInput(dag=0, personen=2)]
        result = planner.plan_week(week_input, "feb", "2026-02-09")
        assert result.dagen[0].recept.id == "pasta-carbonara"


class TestPlanWeekVariety:
    """Tests voor variatie-constraints."""

    def test_geen_opeenvolgende_zelfde_categorie(
        self,
        diverse_recipes: list[Recipe],
        empty_history: MenuHistory,
        kalender,
    ) -> None:
        """Over meerdere seeds: nooit 2x dezelfde categorie achter elkaar."""
        week_input = [DagInput(dag=i, personen=2) for i in range(7)]
        for seed in range(20):
            planner = MenuPlanner(
                diverse_recipes, empty_history, kalender, random_seed=seed
            )
            result = planner.plan_week(week_input, _MAAND, "2026-02-09")
            for i in range(len(result.dagen) - 1):
                cur = result.dagen[i].recept.categorie
                nxt = result.dagen[i + 1].recept.categorie
                assert cur != nxt, (
                    f"seed={seed}: dag {i} en {i + 1} "
                    f"hebben beide categorie {cur.value}"
                )

    def test_geen_opeenvolgende_zelfde_basis(
        self,
        diverse_recipes: list[Recipe],
        empty_history: MenuHistory,
        kalender,
    ) -> None:
        """Over meerdere seeds: nooit 2x dezelfde basis achter elkaar."""
        week_input = [DagInput(dag=i, personen=2) for i in range(7)]
        for seed in range(20):
            planner = MenuPlanner(
                diverse_recipes, empty_history, kalender, random_seed=seed
            )
            result = planner.plan_week(week_input, _MAAND, "2026-02-09")
            for i in range(len(result.dagen) - 1):
                cur = result.dagen[i].recept.basis
                nxt = result.dagen[i + 1].recept.basis
                assert cur != nxt, (
                    f"seed={seed}: dag {i} en {i + 1} hebben beide basis {cur.value}"
                )

    def test_geen_duplicaten_in_week(
        self,
        diverse_recipes: list[Recipe],
        empty_history: MenuHistory,
        kalender,
    ) -> None:
        """Elk recept wordt maximaal 1x per week gebruikt."""
        week_input = [DagInput(dag=i, personen=2) for i in range(7)]
        for seed in range(20):
            planner = MenuPlanner(
                diverse_recipes, empty_history, kalender, random_seed=seed
            )
            result = planner.plan_week(week_input, _MAAND, "2026-02-09")
            ids = [d.recept.id for d in result.dagen]
            assert len(ids) == len(set(ids)), f"seed={seed}: duplicaten gevonden"

    def test_recent_gegeten_niet_opnieuw(self, tmp_path: Path, kalender) -> None:
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
            planner = MenuPlanner(recipes, history, kalender, random_seed=seed)
            result = planner.plan_week(week_input, _MAAND, "2026-02-09")
            assert result.dagen[0].recept.id == "niet-gegeten"


class TestPlanWeekFallback:
    """Tests voor fallback wanneer strikte constraints niet voldaan kunnen worden."""

    def test_fallback_bij_beperkte_pool(self, tmp_path: Path, kalender) -> None:
        """Met slechts 3 recepten van dezelfde categorie, moet fallback relaxeren."""
        recipes = [
            _make_recipe("vlees-pasta", Categorie.VLEES, Basis.PASTA),
            _make_recipe("vlees-rijst", Categorie.VLEES, Basis.RIJST),
            _make_recipe("vlees-aardappel", Categorie.VLEES, Basis.AARDAPPEL),
        ]
        history = MenuHistory(tmp_path / "history.json")
        planner = MenuPlanner(recipes, history, kalender, random_seed=42)
        week_input = [DagInput(dag=i, personen=2) for i in range(3)]
        result = planner.plan_week(week_input, _MAAND, "2026-02-09")
        assert len(result.geplande_dagen) == 3

    def test_raises_bij_nul_recepten(self, tmp_path: Path, kalender) -> None:
        """Zonder recepten moet er een fout komen."""
        history = MenuHistory(tmp_path / "history.json")
        planner = MenuPlanner([], history, kalender, random_seed=42)
        week_input = [DagInput(dag=0, personen=2)]
        with pytest.raises(ValueError, match="geen kandidaat-recepten"):
            planner.plan_week(week_input, _MAAND, "2026-02-09")

    def test_fallback_bij_alle_recent_gegeten(self, tmp_path: Path, kalender) -> None:
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
        planner = MenuPlanner(recipes, history, kalender, random_seed=42)
        week_input = [DagInput(dag=0, personen=2)]
        result = planner.plan_week(week_input, _MAAND, "2026-02-09")
        assert result.dagen[0].recept is not None


class TestVervangRecept:
    """Tests voor het vervangen van een enkel recept in een weekmenu."""

    def test_andere_dagen_ongewijzigd(self, planner: MenuPlanner) -> None:
        week_input = [DagInput(dag=i, personen=2) for i in range(5)]
        menu = planner.plan_week(week_input, _MAAND, "2026-02-09")
        originele_ids = {d.dag: d.recept.id for d in menu.dagen}

        nieuw_menu = planner.vervang_recept(menu, 2, _MAAND)

        for dag in nieuw_menu.dagen:
            if dag.dag != 2:
                assert dag.recept.id == originele_ids[dag.dag]

    def test_vervangen_dag_heeft_ander_recept(self, planner: MenuPlanner) -> None:
        week_input = [DagInput(dag=i, personen=2) for i in range(5)]
        menu = planner.plan_week(week_input, _MAAND, "2026-02-09")
        oud_recept_id = menu.dagen[2].recept.id

        nieuw_menu = planner.vervang_recept(menu, 2, _MAAND)
        assert nieuw_menu.dagen[2].recept.id != oud_recept_id

    def test_retourneert_nieuw_weekmenu(self, planner: MenuPlanner) -> None:
        week_input = [DagInput(dag=i, personen=2) for i in range(3)]
        menu = planner.plan_week(week_input, _MAAND, "2026-02-09")
        nieuw_menu = planner.vervang_recept(menu, 1, _MAAND)
        assert nieuw_menu is not menu


class TestPlanWeekDeterministic:
    """Tests voor determinisme via random_seed."""

    def test_zelfde_seed_zelfde_resultaat(
        self,
        diverse_recipes: list[Recipe],
        empty_history: MenuHistory,
        kalender,
    ) -> None:
        """Twee planners met dezelfde seed produceren identiek menu."""
        week_input = [DagInput(dag=i, personen=2) for i in range(7)]
        planner_a = MenuPlanner(
            diverse_recipes, empty_history, kalender, random_seed=99
        )
        planner_b = MenuPlanner(
            diverse_recipes, empty_history, kalender, random_seed=99
        )

        result_a = planner_a.plan_week(week_input, _MAAND, "2026-02-09")
        result_b = planner_b.plan_week(week_input, _MAAND, "2026-02-09")

        ids_a = [d.recept.id for d in result_a.dagen]
        ids_b = [d.recept.id for d in result_b.dagen]
        assert ids_a == ids_b

    def test_andere_seed_ander_resultaat(
        self,
        diverse_recipes: list[Recipe],
        empty_history: MenuHistory,
        kalender,
    ) -> None:
        """Twee planners met verschillende seeds produceren meestal ander menu."""
        week_input = [DagInput(dag=i, personen=2) for i in range(7)]
        planner_a = MenuPlanner(diverse_recipes, empty_history, kalender, random_seed=1)
        planner_b = MenuPlanner(diverse_recipes, empty_history, kalender, random_seed=2)

        result_a = planner_a.plan_week(week_input, _MAAND, "2026-02-09")
        result_b = planner_b.plan_week(week_input, _MAAND, "2026-02-09")

        ids_a = [d.recept.id for d in result_a.dagen]
        ids_b = [d.recept.id for d in result_b.dagen]
        assert ids_a != ids_b
