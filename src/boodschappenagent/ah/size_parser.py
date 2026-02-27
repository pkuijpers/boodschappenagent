"""Parser voor AH product size strings.

Converteert vrije-tekst verpakkingsgrootten zoals "1,5 l", "300 g",
"ca. 300 g" naar gestructureerde ParsedSize objecten.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Regex: optioneel prefix (ca.), getal (komma/punt),
# optioneel bereik, dan eenheid
_SIZE_PATTERN = re.compile(
    r"(?:ca\.?\s+)?"  # optioneel "ca." of "ca "
    r"(\d+[.,]?\d*)"  # getal (met optionele komma/punt decimaal)
    r"(?:-\d+[.,]?\d*)?"  # optioneel bereik (-3)
    r"\s+"  # spatie
    r"([a-zA-Z]+)",  # eenheid
)


@dataclass(frozen=True)
class ParsedSize:
    """Geparseerde verpakkingsgrootte.

    Attributes:
        hoeveelheid: Numerieke waarde (bijv. 1.5).
        eenheid: Eenheid als string (bijv. "l", "g", "stuks").
    """

    hoeveelheid: float
    eenheid: str


def parse_size(size: str) -> ParsedSize | None:
    """Parse een AH product size string naar een ParsedSize.

    Args:
        size: Vrije-tekst grootte, bijv. "1,5 l", "300 g", "ca. 300 g".

    Returns:
        ParsedSize als het parseerbaar is, anders None.
    """
    if not size or not size.strip():
        return None

    match = _SIZE_PATTERN.search(size.strip())
    if not match:
        return None

    getal_str = match.group(1).replace(",", ".")
    eenheid = match.group(2).lower()

    return ParsedSize(hoeveelheid=float(getal_str), eenheid=eenheid)
