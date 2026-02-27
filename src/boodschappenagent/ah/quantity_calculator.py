"""Bereken het benodigde aantal producten op basis van boodschappenregel en AH product.

Vergelijkt de gewenste hoeveelheid (bijv. 2 liter melk) met de
verpakkingsgrootte van het AH product (bijv. 1 l) en berekent hoeveel
eenheden besteld moeten worden. Rondt altijd naar boven af — er wordt
nooit minder besteld dan nodig.
"""

from __future__ import annotations

import math

from boodschappenagent.ah.models import Product
from boodschappenagent.ah.size_parser import parse_size
from boodschappenagent.boodschappenlijst.models import BoodschappenRegel

# Mapping van eenheid naar (basiseenheid, factor).
# Eenheden met dezelfde basiseenheid zijn onderling vergelijkbaar.
_EENHEID_NAAR_BASIS: dict[str, tuple[str, float]] = {
    # volume
    "liter": ("ml", 1000.0),
    "l": ("ml", 1000.0),
    "ml": ("ml", 1.0),
    "dl": ("ml", 100.0),
    # gewicht
    "kilogram": ("g", 1000.0),
    "kg": ("g", 1000.0),
    "gram": ("g", 1.0),
    "g": ("g", 1.0),
    # stuks
    "stuks": ("stuks", 1.0),
    "stuk": ("stuks", 1.0),
    "st": ("stuks", 1.0),
}

# Eenheden waarvoor geen berekening mogelijk is (altijd quantity=1).
_NIET_BEREKENBAAR: frozenset[str] = frozenset(
    {
        "naar smaak",
        "snuf",
        "mespunt",
        "eetlepel",
        "theelepel",
        "el",
        "tl",
        "teen",
    }
)


def bereken_aantal(regel: BoodschappenRegel, product: Product) -> int:
    """Bereken hoeveel eenheden van een product besteld moeten worden.

    Args:
        regel: De boodschappenregel met gewenste hoeveelheid en eenheid.
        product: Het gematchte AH product met verpakkingsgrootte.

    Returns:
        Aantal te bestellen eenheden (minimaal 1, altijd naar boven afgerond).
    """
    if regel.eenheid in _NIET_BEREKENBAAR:
        return 1

    parsed = parse_size(product.size)
    if parsed is None:
        return 1

    regel_basis = _EENHEID_NAAR_BASIS.get(regel.eenheid)
    product_basis = _EENHEID_NAAR_BASIS.get(parsed.eenheid)

    if regel_basis is None or product_basis is None:
        return 1

    # Eenheden moeten compatibel zijn (zelfde basiseenheid)
    if regel_basis[0] != product_basis[0]:
        return 1

    nodig = regel.hoeveelheid * regel_basis[1]
    per_verpakking = parsed.hoeveelheid * product_basis[1]

    if per_verpakking <= 0:
        return 1

    return max(1, math.ceil(nodig / per_verpakking))
