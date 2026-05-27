"""
Experiment: steekproef van AH productcategorieën

Zoekt 100 ingrediënten uit de receptendatabase op via de AH API en toont
alle unieke `category`-waarden die terugkomen — inclusief de ruwe hierachie
(bijv. "Zuivel, eieren/Halfvolle melk") — zodat we de Afdeling-mapping kunnen
valideren en verbeteren.

Gebruik:
    uv run python experiments/sample_ah_categories.py
"""

import json
import random
import sys
import time
from collections import Counter
from pathlib import Path

# Voeg src toe aan path (zodat we boodschappenagent kunnen importeren)
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from boodschappenagent.ah.auth import AHTokenManager
from boodschappenagent.ah.client import AHClient

# ---------------------------------------------------------------------------
# Stap 1: Laad alle ingrediënten uit de receptendatabase
# ---------------------------------------------------------------------------

DATA_DIR = Path(__file__).parent.parent / "data" / "recipes"


def laad_ingredienten() -> list[str]:
    ingredienten: set[str] = set()
    for json_file in DATA_DIR.rglob("*.json"):
        try:
            with open(json_file) as f:
                recept = json.load(f)
            for ing in recept.get("ingredienten", []):
                naam = ing.get("naam", "").strip()
                if naam:
                    ingredienten.add(naam)
        except Exception as e:
            print(f"  [WARN] Kon {json_file.name} niet lezen: {e}", file=sys.stderr)
    return sorted(ingredienten)


# ---------------------------------------------------------------------------
# Stap 2: Steekproef van 100 ingrediënten (reproduceerbaar)
# ---------------------------------------------------------------------------

SAMPLE_SIZE = 100
RANDOM_SEED = 42


def kies_steekproef(ingredienten: list[str], n: int = SAMPLE_SIZE) -> list[str]:
    rng = random.Random(RANDOM_SEED)
    return rng.sample(ingredienten, min(n, len(ingredienten)))


# ---------------------------------------------------------------------------
# Stap 3: Zoek elk ingredient op via de AH API (top-1 resultaat)
# ---------------------------------------------------------------------------

RATE_LIMIT_DELAY = 0.3  # seconden tussen requests


def haal_categorie(client: AHClient, zoekterm: str) -> str | None:
    """Zoek product en geef de category van het eerste resultaat."""
    try:
        resultaten = client.search_products(zoekterm, limit=1)
        if resultaten:
            return resultaten[0].category or "(leeg)"
        return "(geen resultaat)"
    except Exception as e:
        return f"(fout: {e})"


# ---------------------------------------------------------------------------
# Stap 4: Analyseer en rapporteer
# ---------------------------------------------------------------------------


def analyseer(resultaten: list[dict]) -> None:
    # Alle unieke categorieën (volledig pad)
    alle_cats = [r["category"] for r in resultaten if r["category"]]

    # Hoofd-afdelingen (eerste segment vóór de /)
    def hoofd(cat: str) -> str:
        return cat.split("/")[0].strip() if cat else "(leeg)"

    hoofd_teller: Counter = Counter(hoofd(c) for c in alle_cats)

    print("\n" + "=" * 70)
    print("HOOFD-AFDELINGEN (gesorteerd op frequentie)")
    print("=" * 70)
    for afd, n in hoofd_teller.most_common():
        bar = "█" * n
        print(f"  {n:3d}  {afd:<40s}  {bar}")

    print("\n" + "=" * 70)
    print("ALLE UNIEKE CATEGORIEËN (volledig pad)")
    print("=" * 70)
    unieke_cats = sorted(set(alle_cats))
    for cat in unieke_cats:
        print(f"  {cat}")

    print("\n" + "=" * 70)
    print("DETAIL: ingredient → category")
    print("=" * 70)
    for r in sorted(resultaten, key=lambda x: (hoofd(x["category"]), x["category"])):
        print(f"  {r['ingredient']:<45s}  →  {r['category']}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    # Auth check
    token_manager = AHTokenManager()
    if not token_manager.is_authenticated():
        print("Niet ingelogd. Voer eerst `uv run python -m boodschappenagent.ah.client login <code>` uit.")
        sys.exit(1)

    client = AHClient(token_manager)

    # Laad ingrediënten en kies steekproef
    print("Ingrediënten laden uit receptendatabase…")
    ingredienten = laad_ingredienten()
    print(f"  {len(ingredienten)} unieke ingrediënten gevonden")

    steekproef = kies_steekproef(ingredienten)
    print(f"  Steekproef van {len(steekproef)} ingrediënten (seed={RANDOM_SEED})\n")

    # Zoek via API
    print(f"AH API doorzoeken ({RATE_LIMIT_DELAY}s tussen requests)…")
    resultaten: list[dict] = []

    for i, ingredient in enumerate(steekproef, 1):
        cat = haal_categorie(client, ingredient)
        resultaten.append({"ingredient": ingredient, "category": cat or ""})

        status = f"[{i:3d}/{len(steekproef)}] {ingredient:<40s} → {cat}"
        print(f"  {status}")

        if i < len(steekproef):
            time.sleep(RATE_LIMIT_DELAY)

    # Sla ruwe resultaten op voor later
    output_path = Path(__file__).parent / "sample_ah_categories_results.json"
    with open(output_path, "w") as f:
        json.dump(resultaten, f, ensure_ascii=False, indent=2)
    print(f"\nResultaten opgeslagen in {output_path.name}")

    # Analyseer
    analyseer(resultaten)


if __name__ == "__main__":
    main()
