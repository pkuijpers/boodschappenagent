"""CLI voor voorraadbeheer.

Usage:
    uv run python -m boodschappenagent.cli.voorraad init
    uv run python -m boodschappenagent.cli.voorraad toon
    uv run python -m boodschappenagent.cli.voorraad set pasta --op
    uv run python -m boodschappenagent.cli.voorraad set melk --leeg
    uv run python -m boodschappenagent.cli.voorraad check
    uv run python -m boodschappenagent.cli.voorraad sync
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from boodschappenagent.boodschappenlijst.normalizer import IngredientNormalizer
from boodschappenagent.models import Seizoen
from boodschappenagent.planner.history import MenuHistory
from boodschappenagent.planner.models import WeekMenu
from boodschappenagent.repository.recipe_repository import RecipeRepository
from boodschappenagent.voorraadbeheer.checker import VoorraadChecker
from boodschappenagent.voorraadbeheer.models import VoorraadItem, VoorraadType
from boodschappenagent.voorraadbeheer.presets import (
    STANDAARD_HOUDBAAR,
    VERSE_BASICS,
    extract_houdbaar_kandidaten,
)
from boodschappenagent.voorraadbeheer.repository import VoorraadRepository

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


def cmd_init(args: argparse.Namespace) -> int:
    """Initialiseer voorraad met standaard items uit presets."""
    repo = VoorraadRepository(Path(args.voorraad))
    vandaag = date.today().isoformat()

    items: list[VoorraadItem] = []
    for naam in STANDAARD_HOUDBAAR:
        items.append(
            VoorraadItem(
                naam=naam,
                type=VoorraadType.HOUDBAAR,
                op_voorraad=False,
                laatst_gecheckt=vandaag,
            )
        )
    for naam, _, _ in VERSE_BASICS:
        items.append(
            VoorraadItem(
                naam=naam,
                type=VoorraadType.VERS_BASIS,
                op_voorraad=False,
                laatst_gecheckt=vandaag,
            )
        )

    repo.save(items)
    print(f"Voorraad geïnitialiseerd: {len(items)} items ({args.voorraad})")
    print(f"  {len(STANDAARD_HOUDBAAR)} houdbaar, {len(VERSE_BASICS)} vers")
    return 0


def cmd_toon(args: argparse.Namespace) -> int:
    """Toon huidige voorraad status."""
    repo = VoorraadRepository(Path(args.voorraad))
    items = repo.load()

    if not items:
        print("Voorraad is leeg. Gebruik 'init' om standaard items toe te voegen.")
        return 0

    houdbaar = [i for i in items if i.type is VoorraadType.HOUDBAAR]
    vers = [i for i in items if i.type is VoorraadType.VERS_BASIS]

    for label, groep in [
        ("Houdbare voorraad", houdbaar),
        ("Verse basisproducten", vers),
    ]:
        if not groep:
            continue
        print(f"\n{label}")
        print(f"{'─' * 45}")
        for item in sorted(groep, key=lambda i: i.naam):
            status = "✓" if item.op_voorraad else "✗"
            print(f"  {status} {item.naam:<25} (gecheckt: {item.laatst_gecheckt})")

    op_voorraad = sum(1 for i in items if i.op_voorraad)
    print(f"\nTotaal: {op_voorraad}/{len(items)} op voorraad")
    return 0


def cmd_set(args: argparse.Namespace) -> int:
    """Markeer een item als op voorraad of leeg."""
    repo = VoorraadRepository(Path(args.voorraad))
    items = repo.load()

    naam_lower = args.naam.lower()
    bestaand = next((i for i in items if i.naam.lower() == naam_lower), None)

    if bestaand is None:
        print(f"Error: '{args.naam}' niet gevonden in voorraad.")
        return 1

    op_voorraad = args.op if args.op else not args.leeg
    updated = VoorraadItem(
        naam=bestaand.naam,
        type=bestaand.type,
        op_voorraad=op_voorraad,
        laatst_gecheckt=date.today().isoformat(),
    )
    repo.update_item(updated)

    status = "op voorraad" if op_voorraad else "leeg"
    print(f"{bestaand.naam}: {status}")
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    """Interactieve wekelijkse voorraadcheck."""
    repo = VoorraadRepository(Path(args.voorraad))
    items = repo.load()

    if not items:
        print("Voorraad is leeg. Gebruik 'init' om standaard items toe te voegen.")
        return 1

    menu_path = Path(args.menu)
    if not menu_path.exists():
        print(
            "Error: geen huidig menu gevonden. Gebruik 'menu plan' om er een te maken."
        )
        return 1

    # Laad menu
    recipes_dir = Path(args.recipes_dir)
    recipe_repo = RecipeRepository()
    recipes = []
    for subdir in sorted(recipes_dir.iterdir()):
        if subdir.is_dir() and subdir.name != "draft":
            recipes.extend(recipe_repo.load_all(subdir))
    recipes_by_id = {r.id: r for r in recipes}

    data = json.loads(menu_path.read_text(encoding="utf-8"))
    menu = WeekMenu.from_dict(data, recipes_by_id)

    history = MenuHistory(Path(args.history))
    seizoen = SEIZOEN_MAANDEN[date.today().month]

    checker = VoorraadChecker(repo)
    suggesties = checker.genereer_suggesties(menu, history, seizoen)

    if not suggesties:
        print("Geen items om te checken.")
        return 0

    print(f"\nVoorraadcheck ({len(suggesties)} items)")
    print(f"{'─' * 55}")

    gecheckt = 0
    op_voorraad = 0

    for i, suggestie in enumerate(suggesties, 1):
        print(f"\n  [{i}/{len(suggesties)}] {suggestie.naam}")
        print(f"    {suggestie.reden}")

        while True:
            antwoord = input("    Op voorraad? (j/n/skip): ").strip().lower()
            if antwoord in ("j", "ja", "y", "yes"):
                voorraad = True
                break
            if antwoord in ("n", "nee", "no"):
                voorraad = False
                break
            if antwoord in ("s", "skip", ""):
                voorraad = None
                break
            print("    Kies j(a), n(ee) of skip")

        if voorraad is not None:
            updated = VoorraadItem(
                naam=suggestie.naam,
                type=suggestie.type,
                op_voorraad=voorraad,
                laatst_gecheckt=date.today().isoformat(),
            )
            repo.update_item(updated)
            gecheckt += 1
            if voorraad:
                op_voorraad += 1

    print(f"\n{'─' * 55}")
    leeg = gecheckt - op_voorraad
    print(f"Klaar: {gecheckt} gecheckt, {op_voorraad} op voorraad, {leeg} leeg")
    return 0


def cmd_sync(args: argparse.Namespace) -> int:
    """Synchroniseer voorraad met receptendatabase."""
    repo = VoorraadRepository(Path(args.voorraad))
    recipes_dir = Path(args.recipes_dir)

    recipe_repo = RecipeRepository()
    recipes = []
    for subdir in sorted(recipes_dir.iterdir()):
        if subdir.is_dir() and subdir.name != "draft":
            recipes.extend(recipe_repo.load_all(subdir))

    bestaande_namen = {i.naam for i in repo.load()}
    normalizer = IngredientNormalizer()
    min_freq = args.min_freq

    kandidaten = extract_houdbaar_kandidaten(
        recipes, normalizer, min_freq=min_freq, bestaande_namen=bestaande_namen
    )

    print(f"Receptendatabase gescand: {len(recipes)} recepten")

    if not kandidaten:
        print(f"\nGeen nieuwe items gevonden (frequentie >= {min_freq}).")
        return 0

    print(f"\nKandidaten (frequentie >= {min_freq}):")
    print(f"{'─' * 45}")

    vandaag = date.today().isoformat()
    nieuwe_items = []
    for i, (naam, freq) in enumerate(kandidaten, 1):
        print(f"\n  [{i}/{len(kandidaten)}] {freq}x  {naam}")
        while True:
            antwoord = input("    Toevoegen? (j/n): ").strip().lower()
            if antwoord in ("j", "ja", "y", "yes"):
                nieuwe_items.append(
                    VoorraadItem(
                        naam=naam,
                        type=VoorraadType.HOUDBAAR,
                        op_voorraad=False,
                        laatst_gecheckt=vandaag,
                    )
                )
                break
            if antwoord in ("n", "nee", "no"):
                break
            print("    Kies j(a) of n(ee)")

    if nieuwe_items:
        items = repo.load()
        items.extend(nieuwe_items)
        repo.save(items)

    print(f"\n{'─' * 45}")
    print(f"{len(nieuwe_items)} items toegevoegd aan voorraad.")
    return 0


def main() -> int:
    """Main entry point voor de CLI."""
    parser = argparse.ArgumentParser(
        description="Voorraadbeheer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--voorraad",
        default="data/voorraad.json",
        help="Pad naar voorraad bestand (standaard: data/voorraad.json)",
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

    # init command
    subparsers.add_parser("init", help="Initialiseer voorraad met standaard items")

    # toon command
    subparsers.add_parser("toon", help="Toon huidige voorraad status")

    # set command
    set_parser = subparsers.add_parser(
        "set", help="Markeer een item als op voorraad of leeg"
    )
    set_parser.add_argument("naam", help="Naam van het item")
    set_group = set_parser.add_mutually_exclusive_group(required=True)
    set_group.add_argument("--op", action="store_true", help="Markeer als op voorraad")
    set_group.add_argument("--leeg", action="store_true", help="Markeer als leeg")

    # check command
    subparsers.add_parser("check", help="Interactieve wekelijkse voorraadcheck")

    # sync command
    sync_parser = subparsers.add_parser(
        "sync", help="Synchroniseer voorraad met receptendatabase"
    )
    sync_parser.add_argument(
        "--min-freq",
        type=int,
        default=2,
        help="Minimum frequentie in recepten (standaard: 2)",
    )

    args = parser.parse_args()

    commands = {
        "init": cmd_init,
        "toon": cmd_toon,
        "set": cmd_set,
        "check": cmd_check,
        "sync": cmd_sync,
    }

    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
