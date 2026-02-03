"""CLI voor bulk recepten digitalisatie.

Usage:
    uv run python -m boodschappenagent.cli.digitize process scans/batch.pdf
    uv run python -m boodschappenagent.cli.digitize status batch-001
    uv run python -m boodschappenagent.cli.digitize review batch-001 --recipe 01
    uv run python -m boodschappenagent.cli.digitize accept batch-001 --recipe 01
    uv run python -m boodschappenagent.cli.digitize accept batch-001 --all
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from boodschappenagent.digitizer import BatchProcessor, PDFProcessor, RecipeExtractor
from boodschappenagent.models import Recipe


def _print_progress(current: int, total: int, recipe_naam: str | None) -> None:
    """Print een progress bar naar stdout."""
    bar_width = 30
    progress = current / total
    filled = int(bar_width * progress)
    bar = "█" * filled + "░" * (bar_width - filled)

    # Truncate recipe naam voor display
    if recipe_naam:
        display_name = recipe_naam[:35] + "..." if len(recipe_naam) > 38 else recipe_naam
    else:
        display_name = "(mislukt)"

    # \r om naar begin van regel te gaan, overwrite vorige output
    sys.stdout.write(f"\r  [{bar}] {current}/{total} - {display_name:<40}")
    sys.stdout.flush()

    # Newline na laatste item
    if current == total:
        print()


def cmd_process(args: argparse.Namespace) -> int:
    """Verwerk een PDF batch."""
    pdf_path = Path(args.pdf)

    if not pdf_path.exists():
        print(f"Error: PDF bestand niet gevonden: {pdf_path}")
        return 1

    print(f"Verwerken van: {pdf_path}")

    # Initialiseer componenten
    pdf_processor = PDFProcessor(dpi=args.dpi)
    recipe_extractor = RecipeExtractor()
    batch_processor = BatchProcessor(
        pdf_processor=pdf_processor,
        recipe_extractor=recipe_extractor,
        output_base=Path(args.output),
        rate_limit_delay=args.delay,
    )

    # Verwerk de batch
    total_pages = pdf_processor.page_count(pdf_path)
    print(f"Aantal pagina's: {total_pages}")
    print("Extractie gestart...")

    result = batch_processor.process(
        pdf_path, batch_id=args.batch_id, on_progress=_print_progress
    )

    # Print resultaat
    print()
    print(f"Batch ID: {result.batch_id}")
    print(f"Output: {result.output_dir}")
    print(f"Totaal: {result.total_pages} pagina's")
    print(f"Succesvol: {result.successful}")
    print(f"Mislukt: {result.failed}")

    if result.errors:
        print()
        print("Fouten:")
        for error in result.errors:
            print(f"  Pagina {error['page']}: {error['error']}")

    print()
    print("Review de recepten met:")
    print(f"  uv run python -m boodschappenagent.cli.digitize status {result.batch_id}")

    return 0


def cmd_status(args: argparse.Namespace) -> int:
    """Toon status van een batch."""
    batch_dir = Path(args.output) / args.batch_id
    manifest_path = batch_dir / "_manifest.json"

    if not manifest_path.exists():
        print(f"Error: Batch niet gevonden: {args.batch_id}")
        return 1

    manifest = json.loads(manifest_path.read_text())

    print(f"Batch: {manifest['batch_id']}")
    print(f"Bron: {manifest['pdf_source']}")
    print(f"Verwerkt: {manifest['processed_at']}")
    print(f"Totaal: {manifest['total_pages']} recepten")
    print()

    # Tel statussen
    status_counts = {"draft": 0, "accepted": 0, "rejected": 0, "failed": 0}
    for recipe in manifest["recipes"]:
        status = recipe.get("status", "draft")
        status_counts[status] = status_counts.get(status, 0) + 1

    print("Status:")
    for status, count in status_counts.items():
        if count > 0:
            print(f"  {status}: {count}")

    print()
    print("Recepten:")
    for recipe in manifest["recipes"]:
        status_icon = {
            "draft": "⏳",
            "accepted": "✅",
            "rejected": "❌",
            "failed": "💥",
        }.get(recipe["status"], "?")

        if recipe["file"]:
            page = recipe["page"]
            naam = recipe["recipe_naam"]
            print(f"  {status_icon} [{page:02d}] {naam} ({recipe['file']})")
        else:
            page = recipe["page"]
            errors = recipe.get("validation_errors", ["Onbekende fout"])
            print(f"  {status_icon} [{page:02d}] MISLUKT - {errors[0]}")

    return 0


def cmd_review(args: argparse.Namespace) -> int:
    """Review een specifiek recept."""
    batch_dir = Path(args.output) / args.batch_id
    manifest_path = batch_dir / "_manifest.json"

    if not manifest_path.exists():
        print(f"Error: Batch niet gevonden: {args.batch_id}")
        return 1

    manifest = json.loads(manifest_path.read_text())

    # Zoek recept op basis van pagina of bestandsnaam
    recipe_ref = args.recipe
    recipe_info = None

    for r in manifest["recipes"]:
        # Match op pagina nummer of bestandsnaam prefix
        if str(r["page"]).zfill(2) == recipe_ref.zfill(2):
            recipe_info = r
            break
        if r["file"] and r["file"].startswith(recipe_ref):
            recipe_info = r
            break

    if recipe_info is None:
        print(f"Error: Recept niet gevonden: {recipe_ref}")
        return 1

    if recipe_info["file"] is None:
        print(f"Error: Recept extractie is mislukt voor pagina {recipe_info['page']}")
        return 1

    # Laad en toon recept
    recipe_path = batch_dir / recipe_info["file"]
    recipe_data = json.loads(recipe_path.read_text())

    print(f"Recept: {recipe_data['naam']}")
    print(f"ID: {recipe_data['id']}")
    print(f"Status: {recipe_info['status']}")
    print(f"Bestand: {recipe_info['file']}")
    print()
    print(f"Categorie: {recipe_data['categorie']}")
    print(f"Basis: {recipe_data['basis']}")
    print(f"Seizoenen: {', '.join(recipe_data['seizoenen'])}")
    print(f"Porties: {recipe_data['basis_porties']}")
    print(f"Bereidingstijd: {recipe_data['bereidingstijd_min']} min")
    print()
    print("Ingrediënten:")
    for ing in recipe_data["ingredienten"]:
        opmerking = f" ({ing['opmerking']})" if ing.get("opmerking") else ""
        print(f"  - {ing['hoeveelheid']} {ing['eenheid']} {ing['naam']}{opmerking}")

    if recipe_data.get("bereidingswijze"):
        print()
        print("Bereidingswijze:")
        print(recipe_data["bereidingswijze"])

    print()
    print("Acties:")
    cmd = f"uv run python -m boodschappenagent.cli.digitize accept {args.batch_id}"
    print(f"  Accept: {cmd} --recipe {recipe_ref}")
    print(f"  Edit:   {recipe_path}")

    return 0


def cmd_accept(args: argparse.Namespace) -> int:
    """Accepteer een of alle recepten en verplaats naar definitieve locatie."""
    batch_dir = Path(args.output) / args.batch_id
    manifest_path = batch_dir / "_manifest.json"
    recipes_base = Path("data/recipes")

    if not manifest_path.exists():
        print(f"Error: Batch niet gevonden: {args.batch_id}")
        return 1

    manifest = json.loads(manifest_path.read_text())

    # Bepaal welke recepten te accepteren
    recipes_to_accept = []

    if args.all:
        recipes_to_accept = [
            r for r in manifest["recipes"] if r["status"] == "draft" and r["file"]
        ]
    elif args.recipe:
        recipe_ref = args.recipe
        for r in manifest["recipes"]:
            if str(r["page"]).zfill(2) == recipe_ref.zfill(2):
                recipes_to_accept = [r]
                break
            if r["file"] and r["file"].startswith(recipe_ref):
                recipes_to_accept = [r]
                break

    if not recipes_to_accept:
        print("Geen recepten om te accepteren.")
        return 0

    accepted_count = 0
    for recipe_info in recipes_to_accept:
        recipe_path = batch_dir / recipe_info["file"]
        recipe_data = json.loads(recipe_path.read_text())

        # Valideer tegen Recipe model
        try:
            Recipe.from_dict(recipe_data)
        except (ValueError, KeyError) as e:
            print(f"Validatie fout voor {recipe_info['recipe_naam']}: {e}")
            continue

        # Bepaal doellocatie op basis van categorie
        target_dir = recipes_base / recipe_data["categorie"]
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / f"{recipe_data['id']}.json"

        # Kopieer naar definitieve locatie
        shutil.copy2(recipe_path, target_path)

        # Update manifest status
        recipe_info["status"] = "accepted"

        print(f"✅ {recipe_data['naam']} -> {target_path}")
        accepted_count += 1

    # Sla bijgewerkte manifest op
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print()
    print(f"Geaccepteerd: {accepted_count} recepten")

    return 0


def main() -> int:
    """Main entry point voor de CLI."""
    parser = argparse.ArgumentParser(
        description="Bulk recepten digitalisatie tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--output",
        "-o",
        default="data/recipes/draft",
        help="Basis output directory (standaard: data/recipes/draft)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # process command
    process_parser = subparsers.add_parser(
        "process",
        help="Verwerk een PDF batch met recepten",
    )
    process_parser.add_argument(
        "pdf",
        help="Pad naar de PDF met recepten",
    )
    process_parser.add_argument(
        "--batch-id",
        "-b",
        help="Batch identifier (standaard: afgeleid van PDF naam)",
    )
    process_parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="DPI voor image extractie (standaard: 300)",
    )
    process_parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Delay tussen API calls in seconden (standaard: 1.0)",
    )

    # status command
    status_parser = subparsers.add_parser(
        "status",
        help="Toon status van een batch",
    )
    status_parser.add_argument(
        "batch_id",
        help="Batch identifier",
    )

    # review command
    review_parser = subparsers.add_parser(
        "review",
        help="Review een specifiek recept",
    )
    review_parser.add_argument(
        "batch_id",
        help="Batch identifier",
    )
    review_parser.add_argument(
        "--recipe",
        "-r",
        required=True,
        help="Recept pagina nummer (bijv. 01) of bestandsnaam prefix",
    )

    # accept command
    accept_parser = subparsers.add_parser(
        "accept",
        help="Accepteer een of alle recepten",
    )
    accept_parser.add_argument(
        "batch_id",
        help="Batch identifier",
    )
    accept_group = accept_parser.add_mutually_exclusive_group(required=True)
    accept_group.add_argument(
        "--recipe",
        "-r",
        help="Recept pagina nummer (bijv. 01) of bestandsnaam prefix",
    )
    accept_group.add_argument(
        "--all",
        "-a",
        action="store_true",
        help="Accepteer alle draft recepten",
    )

    args = parser.parse_args()

    # Voer het juiste command uit
    commands = {
        "process": cmd_process,
        "status": cmd_status,
        "review": cmd_review,
        "accept": cmd_accept,
    }

    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
