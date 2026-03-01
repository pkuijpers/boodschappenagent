"""CO2-gebaseerde groente-seizoenskalender voor receptfiltering."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from boodschappenagent.models import Recipe

# Default pad naar de seizoenskalender
_DEFAULT_PATH = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "reference"
    / "groenten_seizoenskalender.json"
)

GELDIGE_MAANDEN = {
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
}


class SeizoenKalender:
    """CO2-gebaseerde groente-seizoensfiltering.

    Laadt een groenten-seizoenskalender uit JSON en biedt:
    - Opvragen welke groenten lage CO2 hebben per maand
    - Fuzzy/substring matching van ingrediëntnamen tegen kalender-groenten
    - Beoordeling of een recept seizoensgeschikt is (meerderheidsregel)
    """

    def __init__(self, kalender_path: Path | None = None) -> None:
        """Laad de groenten-seizoenskalender uit JSON.

        Args:
            kalender_path: Pad naar het JSON-bestand. Gebruikt default als None.

        Raises:
            FileNotFoundError: Als het bestand niet bestaat.
        """
        path = kalender_path or _DEFAULT_PATH
        if not path.exists():
            msg = f"seizoenskalender niet gevonden: {path}"
            raise FileNotFoundError(msg)

        with open(path) as f:
            raw = json.load(f)

        # Sla groenten op als lowercase naam → set van lage CO2 maanden
        self._groenten: dict[str, set[str]] = {}
        for entry in raw:
            naam = entry["groente"].lower()
            maanden = set(entry["lage_co2_maanden"])
            self._groenten[naam] = maanden

        # Sorteer op lengte (langste eerst) voor greedy matching
        self._groenten_namen_sorted = sorted(
            self._groenten.keys(),
            key=len,
            reverse=True,
        )

    def groenten_in_seizoen(self, maand: str) -> set[str]:
        """Retourneer set van groenten met lage CO2 voor de gegeven maand.

        Args:
            maand: Maandafkorting (jan, feb, mrt, ..., dec).

        Returns:
            Set van groente-namen (lowercase) met lage CO2.

        Raises:
            ValueError: Bij ongeldige maandafkorting.
        """
        if maand not in GELDIGE_MAANDEN:
            verwacht = ", ".join(sorted(GELDIGE_MAANDEN))
            msg = f"ongeldige maand: '{maand}' (verwacht: {verwacht})"
            raise ValueError(msg)

        return {naam for naam, maanden in self._groenten.items() if maand in maanden}

    def match_ingredient(self, ingredientnaam: str) -> str | None:
        """Match een ingrediëntnaam tegen de seizoenskalender.

        Gebruikt substring matching: de kalender-groente (of stam) moet een
        substring zijn van de ingrediëntnaam. Langste match wint om te
        voorkomen dat bijv. "ui" matcht op "aubergine".

        Stamming: voor groenten langer dan 3 tekens wordt ook de stam
        geprobeerd (laatste teken verwijderd), zodat bijv. "tomaat" →
        "tomat" matcht op "cherrytomaten".

        Args:
            ingredientnaam: Naam van het ingrediënt uit een recept.

        Returns:
            De kalender-groente (lowercase) of None als geen match.
        """
        naam_lower = ingredientnaam.lower()

        for groente in self._groenten_namen_sorted:
            if groente in naam_lower:
                return groente
            # Stam-matching voor Nederlandse meervoudsvormen:
            # "tomaat" → "toma" matcht op "cherrytomaten"
            # Probeer 1 en 2 tekens verwijderen, stam moet ≥4 tekens zijn
            for trim in (1, 2):
                stam = groente[:-trim]
                if len(stam) >= 4 and stam in naam_lower:
                    return groente

        return None

    def recept_is_seizoensgeschikt(self, recipe: Recipe, maand: str) -> bool:
        """Bepaal of een recept seizoensgeschikt is voor de gegeven maand.

        Een recept is geschikt als de meerderheid (>50%) van de herkenbare
        groenten lage CO2 heeft voor de maand. Ingrediënten die niet in de
        kalender voorkomen worden genegeerd. Recepten zonder herkenbare
        groenten zijn altijd geschikt.

        Args:
            recipe: Het recept om te beoordelen.
            maand: Maandafkorting (jan, feb, ..., dec).

        Returns:
            True als het recept seizoensgeschikt is.
        """
        seizoens_groenten = self.groenten_in_seizoen(maand)

        herkend = 0
        in_seizoen = 0

        for ingredient in recipe.ingredienten:
            groente = self.match_ingredient(ingredient.naam)
            if groente is not None:
                herkend += 1
                if groente in seizoens_groenten:
                    in_seizoen += 1

        # Geen herkenbare groenten → altijd geschikt
        if herkend == 0:
            return True

        # Strikte meerderheid: >50%, niet >=50%
        return in_seizoen / herkend > 0.5
