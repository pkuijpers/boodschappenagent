"""Standaard voorraadartikelen en seizoensingrediënten.

Verse basics hebben standaard hoeveelheden (voor 2 personen, 1 week).
Houdbare voorraad is alleen op naam (binaire tracking).
"""

from __future__ import annotations

from collections import Counter

from boodschappenagent.boodschappenlijst.normalizer import IngredientNormalizer
from boodschappenagent.models import Recipe

# (naam, hoeveelheid, eenheid)
VERSE_BASICS: list[tuple[str, float, str]] = [
    ("melk", 1, "liter"),
    ("eieren", 6, "stuks"),
    ("boter", 250, "gram"),
    ("kaas", 500, "gram"),
    ("optimel", 1.5, "liter"),
    ("gelderse worst", 100, "gram"),
    ("rookvlees", 100, "gram"),
    ("kipfilet", 100, "gram"),
    ("yoghurt", 1, "liter"),
]

STANDAARD_HOUDBAAR: list[str] = [
    "arachideolie",
    "balsamicoazijn",
    "basmatirijst",
    "beschuit",
    "bier",
    "bier 0%",
    "bloem",
    "chips",
    "chocoladehagel",
    "cola",
    "gedroogde tijm",
    "gemalen komijn",
    "italiaanse kruiden",
    "jam",
    "keukenrol",
    "kippenbouillontablet",
    "knackebrod",
    "knoflook",
    "olijfolie",
    "ontbijtkoek",
    "papieren zakdoekjes",
    "passata",
    "pasta",
    "peper",
    "pijnboompitten",
    "pindakaas",
    "rode wijn",
    "sandwich spread",
    "snickers",
    "soep in zak",
    "sojasaus",
    "tissues",
    "twix",
    "vaatwasmiddel",
    "vruchtenhagel",
    "wasmiddel color",
    "wasmiddel wit",
    "wc-papier",
    "witte wijn",
    "zout",
]

SEIZOEN_INGREDIENTEN: dict[str, list[str]] = {
    "herfst": ["pompoen", "paddenstoelen", "kastanjechampignons"],
    "winter": ["rodekool", "spitskool", "kruimige aardappelen"],
    "lente": ["asperges", "doperwten"],
    "zomer": ["cherrytomaten", "trostomaten", "rucola"],
}


def extract_houdbaar_kandidaten(
    recipes: list[Recipe],
    normalizer: IngredientNormalizer,
    min_freq: int = 2,
    bestaande_namen: set[str] | None = None,
) -> list[tuple[str, int]]:
    """Extract houdbare kandidaten uit receptendatabase op basis van frequentie.

    Telt per recept (niet per ingrediëntregel) hoe vaak een genormaliseerde
    ingrediëntnaam voorkomt. Sluit "naar smaak" eenheden en bestaande namen uit.

    Args:
        recipes: Lijst recepten om te scannen.
        normalizer: Normalizer voor ingrediëntnamen.
        min_freq: Minimum aantal recepten waarin een ingrediënt moet voorkomen.
        bestaande_namen: Namen die al in de voorraad zitten (worden uitgesloten).

    Returns:
        Gesorteerde lijst van (naam, frequentie) tuples, hoog→laag.
    """
    if bestaande_namen is None:
        bestaande_namen = set()

    freq: Counter[str] = Counter()

    for recipe in recipes:
        gezien_in_recept: set[str] = set()
        for ing in recipe.ingredienten:
            naam, eenheid = normalizer.normaliseer(ing.naam, ing.eenheid)
            if normalizer.is_niet_aggregeerbaar(eenheid):
                continue
            if naam not in gezien_in_recept:
                freq[naam] += 1
                gezien_in_recept.add(naam)

    return sorted(
        [
            (naam, count)
            for naam, count in freq.items()
            if count >= min_freq and naam not in bestaande_namen
        ],
        key=lambda x: (-x[1], x[0]),
    )
