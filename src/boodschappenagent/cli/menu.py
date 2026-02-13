"""CLI voor weekmenu planning.

Usage:
    uv run python -m boodschappenagent.cli.menu plan
    uv run python -m boodschappenagent.cli.menu plan -p 2 --vrij za,zo
    uv run python -m boodschappenagent.cli.menu plan --dagen ma:4,vr:3 --vrij zo
    uv run python -m boodschappenagent.cli.menu toon
    uv run python -m boodschappenagent.cli.menu vervang di
    uv run python -m boodschappenagent.cli.menu boodschappen
    uv run python -m boodschappenagent.cli.menu accepteer
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path

from boodschappenagent.boodschappenlijst import (
    BoodschappenlijstGenerator,
    IngredientNormalizer,
)
from boodschappenagent.models import Seizoen
from boodschappenagent.planner.history import MenuHistory
from boodschappenagent.planner.menu_planner import MenuPlanner
from boodschappenagent.planner.models import DagInput, DagPlanning, WeekMenu
from boodschappenagent.repository.recipe_repository import RecipeRepository
from boodschappenagent.utils import PortionCalculator

DAG_NAMEN = {"ma": 0, "di": 1, "wo": 2, "do": 3, "vr": 4, "za": 5, "zo": 6}
DAG_NAMEN_LANG = {
    0: "maandag",
    1: "dinsdag",
    2: "woensdag",
    3: "donderdag",
    4: "vrijdag",
    5: "zaterdag",
    6: "zondag",
}

SEIZOEN_MAANDEN = {
    12: Seizoen.WINTER,
    1: Seizoen.WINTER,
    2: Seizoen.WINTER,
    3: Seizoen.LENTE,
    4: Seizoen.LENTE,
    5: Seizoen.LENTE,
    6: Seizoen.ZOMER,
    7: Seizoen.ZOMER,
    8: Seizoen.ZOMER,
    9: Seizoen.HERFST,
    10: Seizoen.HERFST,
    11: Seizoen.HERFST,
}


def _detect_seizoen(d: date) -> Seizoen:
    """Detecteer seizoen op basis van datum."""
    return SEIZOEN_MAANDEN[d.month]


def _parse_dag(dag_str: str) -> int:
    """Parse een dag string naar nummer (0-6).

    Accepteert: ma/di/wo/do/vr/za/zo of 0-6.

    Raises:
        ValueError: Als de dag niet herkend wordt.
    """
    lower = dag_str.lower().strip()
    if lower in DAG_NAMEN:
        return DAG_NAMEN[lower]
    if lower.isdigit() and 0 <= int(lower) <= 6:
        return int(lower)
    msg = f"onbekende dag: {dag_str}"
    raise ValueError(msg)


def _compute_week_start(d: date) -> str:
    """Bereken de eerstvolgende maandag (inclusief vandaag als het maandag is)."""
    weekday = d.weekday()  # 0=maandag
    if weekday == 0:
        return d.isoformat()
    days_until_monday = 7 - weekday
    return (d + timedelta(days=days_until_monday)).isoformat()


def _load_recipes(recipes_dir: str) -> list:
    """Laad alle recepten uit de recipes directory (excl. draft/)."""
    repo = RecipeRepository()
    base = Path(recipes_dir)
    recipes = []
    for subdir in sorted(base.iterdir()):
        if subdir.is_dir() and subdir.name != "draft":
            recipes.extend(repo.load_all(subdir))
    return recipes


def _print_menu(menu: WeekMenu) -> None:
    """Print een weekmenu als tabel."""
    print(f"\nWeekmenu (week van {menu.week_start})")
    print(f"{'─' * 65}")
    print(f"  {'Dag':<12} {'Recept':<30} {'Cat.':<12} {'Pers.':>5}")
    print(f"{'─' * 65}")

    for dag in sorted(menu.dagen, key=lambda d: d.dag):
        dag_naam = DAG_NAMEN_LANG[dag.dag].capitalize()
        if dag.recept is None:
            print(f"  {dag_naam:<12} {'— vrij —':<30} {'':12} {'':>5}")
        else:
            naam = dag.recept.naam
            if len(naam) > 28:
                naam = naam[:25] + "..."
            cat = dag.recept.categorie.value
            print(f"  {dag_naam:<12} {naam:<30} {cat:<12} {dag.personen:>5}")

    print(f"{'─' * 65}")


def cmd_plan(args: argparse.Namespace) -> int:
    """Genereer een weekmenu."""
    recipes = _load_recipes(args.recipes_dir)
    if not recipes:
        print("Error: geen recepten gevonden")
        return 1

    history = MenuHistory(Path(args.history))

    seizoen = Seizoen(args.seizoen) if args.seizoen else _detect_seizoen(date.today())
    week_start = args.week or _compute_week_start(date.today())

    # Personen per dag opbouwen
    personen_per_dag = dict.fromkeys(range(7), args.personen)

    # Vrije dagen verwerken
    if args.vrij:
        for dag_str in args.vrij.split(","):
            dag_nr = _parse_dag(dag_str.strip())
            personen_per_dag[dag_nr] = 0

    # Per-dag overrides verwerken
    if args.dagen:
        for entry in args.dagen.split(","):
            dag_str, pers_str = entry.strip().split(":")
            dag_nr = _parse_dag(dag_str)
            personen_per_dag[dag_nr] = int(pers_str)

    # Week input maken
    week_input = [DagInput(dag=i, personen=p) for i, p in personen_per_dag.items()]

    # Plannen
    planner = MenuPlanner(recipes, history)
    menu = planner.plan_week(week_input, seizoen, week_start)

    # Opslaan
    menu_path = Path(args.menu)
    menu_path.parent.mkdir(parents=True, exist_ok=True)
    menu_path.write_text(
        json.dumps(menu.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    _print_menu(menu)
    print(f"\nMenu opgeslagen: {menu_path}")
    print(f"Seizoen: {seizoen.value}")
    return 0


def cmd_toon(args: argparse.Namespace) -> int:
    """Toon het huidige weekmenu."""
    menu_path = Path(args.menu)
    if not menu_path.exists():
        print("Error: geen huidig menu gevonden. Gebruik 'plan' om er een te maken.")
        return 1

    recipes = _load_recipes(args.recipes_dir)
    recipes_by_id = {r.id: r for r in recipes}

    data = json.loads(menu_path.read_text(encoding="utf-8"))
    menu = WeekMenu.from_dict(data, recipes_by_id)

    _print_menu(menu)
    return 0


def cmd_vervang(args: argparse.Namespace) -> int:
    """Vervang het recept, personen, of vrije dag voor een specifieke dag."""
    menu_path = Path(args.menu)
    if not menu_path.exists():
        print("Error: geen huidig menu gevonden. Gebruik 'plan' om er een te maken.")
        return 1

    recipes = _load_recipes(args.recipes_dir)
    recipes_by_id = {r.id: r for r in recipes}
    history = MenuHistory(Path(args.history))

    data = json.loads(menu_path.read_text(encoding="utf-8"))
    menu = WeekMenu.from_dict(data, recipes_by_id)

    dag_nrs = [_parse_dag(d.strip()) for d in args.dag.split(",")]
    seizoen = Seizoen(args.seizoen) if args.seizoen else _detect_seizoen(date.today())
    planner = MenuPlanner(recipes, history)

    for dag_nr in dag_nrs:
        dag_naam = DAG_NAMEN_LANG[dag_nr].capitalize()

        if args.vrij:
            menu = _update_dag(menu, dag_nr, recept=None, personen=0)
            print(f"{dag_naam}: vrij gezet")
        elif args.personen is not None:
            target = _find_dag(menu, dag_nr)
            if target and target.recept is None:
                menu = _activate_dag(menu, dag_nr, args.personen, planner, seizoen)
                nieuw = _find_dag(menu, dag_nr)
                print(f"{dag_naam}: {nieuw.recept.naam} ({args.personen} pers.)")
            else:
                menu = _update_dag(
                    menu, dag_nr, recept=target.recept, personen=args.personen
                )
                print(f"{dag_naam}: {args.personen} personen")
        else:
            oud = _find_dag(menu, dag_nr)
            if oud and oud.recept is None:
                # Vrije dag activeren met standaard personen
                default_pers = _default_personen(menu)
                menu = _activate_dag(menu, dag_nr, default_pers, planner, seizoen)
                nieuw = _find_dag(menu, dag_nr)
                print(f"{dag_naam}: vrij -> {nieuw.recept.naam} ({default_pers} pers.)")
            else:
                oud_naam = oud.recept.naam if oud and oud.recept else None
                menu = planner.vervang_recept(menu, dag_nr, seizoen)
                nieuw = _find_dag(menu, dag_nr)
                nieuw_naam = nieuw.recept.naam if nieuw and nieuw.recept else None
                print(f"{dag_naam}: {oud_naam} -> {nieuw_naam}")

    # Opslaan
    menu_path.write_text(
        json.dumps(menu.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print()
    _print_menu(menu)
    return 0


def _default_personen(menu: WeekMenu) -> int:
    """Bepaal standaard personen op basis van geplande dagen."""
    geplande = menu.geplande_dagen
    if not geplande:
        return 2
    counts = {d.personen for d in geplande}
    return max(counts, key=lambda p: sum(1 for d in geplande if d.personen == p))


def _find_dag(menu: WeekMenu, dag_nr: int) -> DagPlanning | None:
    """Vind de DagPlanning voor een specifiek dagnummer."""
    for d in menu.dagen:
        if d.dag == dag_nr:
            return d
    return None


def _update_dag(
    menu: WeekMenu,
    dag_nr: int,
    *,
    recept: object | None,
    personen: int,
) -> WeekMenu:
    """Maak een nieuw WeekMenu met aangepaste dag."""
    nieuwe_dagen = [
        DagPlanning(dag=d.dag, recept=recept, personen=personen)
        if d.dag == dag_nr
        else d
        for d in menu.dagen
    ]
    return WeekMenu(week_start=menu.week_start, dagen=nieuwe_dagen)


def _activate_dag(
    menu: WeekMenu,
    dag_nr: int,
    personen: int,
    planner: MenuPlanner,
    seizoen: Seizoen,
) -> WeekMenu:
    """Activeer een vrije dag: plan een recept en zet personen."""
    # Eerst een tijdelijk recept zetten zodat vervang_recept werkt
    # We gebruiken plan_week logica niet direct, maar vervang_recept
    # verwacht een dag met recept. We zetten eerst een placeholder.
    from boodschappenagent.repository.recipe_search import RecipeSearch

    seasonal = RecipeSearch(planner._recipes).filter_by_seizoen(seizoen).results
    used_ids = {d.recept.id for d in menu.geplande_dagen if d.dag != dag_nr}
    candidates = [r for r in seasonal if r.id not in used_ids]
    if not candidates:
        candidates = seasonal
    recept = planner._rng.choice(candidates)

    nieuwe_dagen = [
        DagPlanning(dag=d.dag, recept=recept, personen=personen)
        if d.dag == dag_nr
        else d
        for d in menu.dagen
    ]
    return WeekMenu(week_start=menu.week_start, dagen=nieuwe_dagen)


def _print_boodschappenlijst(lijst: object) -> None:
    """Print een boodschappenlijst als tabel."""
    if not lijst.regels:
        print("\nGeen ingrediënten nodig (alleen vrije dagen).")
        return

    print(f"\nBoodschappenlijst (week van {lijst.week_start})")
    print(f"{'─' * 55}")
    print(f"  {'Ingrediënt':<25} {'Hoeveelheid':>12} {'Eenheid':<15}")
    print(f"{'─' * 55}")

    for regel in lijst.regels:
        naam = regel.display_naam
        if len(naam) > 23:
            naam = naam[:20] + "..."
        hoeveelheid = (
            str(int(regel.hoeveelheid))
            if regel.hoeveelheid == int(regel.hoeveelheid)
            else f"{regel.hoeveelheid:.1f}"
        )
        print(f"  {naam:<25} {hoeveelheid:>12} {regel.eenheid:<15}")

    print(f"{'─' * 55}")
    print(f"  Totaal: {len(lijst.regels)} ingrediënten")


def cmd_boodschappen(args: argparse.Namespace) -> int:
    """Genereer een boodschappenlijst voor het huidige weekmenu."""
    menu_path = Path(args.menu)
    if not menu_path.exists():
        print("Error: geen huidig menu gevonden. Gebruik 'plan' om er een te maken.")
        return 1

    recipes = _load_recipes(args.recipes_dir)
    recipes_by_id = {r.id: r for r in recipes}

    data = json.loads(menu_path.read_text(encoding="utf-8"))
    menu = WeekMenu.from_dict(data, recipes_by_id)

    generator = BoodschappenlijstGenerator(
        normalizer=IngredientNormalizer(),
        portion_calculator=PortionCalculator(),
    )
    lijst = generator.genereer(menu)

    _print_boodschappenlijst(lijst)
    return 0


def cmd_accepteer(args: argparse.Namespace) -> int:
    """Accepteer het huidige menu en sla op in geschiedenis."""
    menu_path = Path(args.menu)
    if not menu_path.exists():
        print("Error: geen huidig menu gevonden. Gebruik 'plan' om er een te maken.")
        return 1

    recipes = _load_recipes(args.recipes_dir)
    recipes_by_id = {r.id: r for r in recipes}

    data = json.loads(menu_path.read_text(encoding="utf-8"))
    menu = WeekMenu.from_dict(data, recipes_by_id)

    history = MenuHistory(Path(args.history))
    history.add_week(menu)

    menu_path.unlink()

    geplande = len(menu.geplande_dagen)
    print(f"Menu geaccepteerd: {geplande} recepten opgeslagen in geschiedenis.")
    return 0


def main() -> int:
    """Main entry point voor de CLI."""
    parser = argparse.ArgumentParser(
        description="Weekmenu planner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--recipes-dir",
        default="data/recipes",
        help="Directory met recepten (standaard: data/recipes)",
    )
    parser.add_argument(
        "--history",
        default="data/history.json",
        help="Pad naar history bestand (standaard: data/history.json)",
    )
    parser.add_argument(
        "--menu",
        default="data/current_menu.json",
        help="Pad naar huidig menu bestand (standaard: data/current_menu.json)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # plan command
    plan_parser = subparsers.add_parser(
        "plan",
        help="Genereer een weekmenu",
    )
    plan_parser.add_argument(
        "--personen",
        "-p",
        type=int,
        default=2,
        help="Standaard aantal personen per dag (standaard: 2)",
    )
    plan_parser.add_argument(
        "--vrij",
        "-v",
        help="Vrije dagen, komma-gescheiden (bijv. za,zo of 5,6)",
    )
    plan_parser.add_argument(
        "--seizoen",
        "-s",
        choices=["lente", "zomer", "herfst", "winter", "alle"],
        help="Seizoen override (standaard: auto-detect)",
    )
    plan_parser.add_argument(
        "--week",
        "-w",
        help="Week start datum YYYY-MM-DD (standaard: aankomende maandag)",
    )
    plan_parser.add_argument(
        "--dagen",
        "-d",
        help="Per-dag personen, formaat dag:pers (bijv. ma:4,vr:3)",
    )

    # toon command
    subparsers.add_parser(
        "toon",
        help="Toon het huidige weekmenu",
    )

    # vervang command
    vervang_parser = subparsers.add_parser(
        "vervang",
        help="Vervang het recept voor een dag",
    )
    vervang_parser.add_argument(
        "dag",
        help="Weekdag (ma/di/wo/do/vr/za/zo of 0-6)",
    )
    vervang_parser.add_argument(
        "--seizoen",
        "-s",
        choices=["lente", "zomer", "herfst", "winter", "alle"],
        help="Seizoen override (standaard: auto-detect)",
    )
    vervang_parser.add_argument(
        "--personen",
        "-p",
        type=int,
        help="Wijzig aantal personen voor deze dag",
    )
    vervang_parser.add_argument(
        "--vrij",
        "-v",
        action="store_true",
        help="Markeer dag als vrij (niet koken)",
    )

    # boodschappen command
    subparsers.add_parser(
        "boodschappen",
        help="Genereer een boodschappenlijst voor het huidige menu",
    )

    # accepteer command
    subparsers.add_parser(
        "accepteer",
        help="Accepteer het menu en sla op in geschiedenis",
    )

    args = parser.parse_args()

    commands = {
        "plan": cmd_plan,
        "toon": cmd_toon,
        "vervang": cmd_vervang,
        "boodschappen": cmd_boodschappen,
        "accepteer": cmd_accepteer,
    }

    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
