"""CO2-gebaseerde groente-seizoenskalender voor receptfiltering."""

from __future__ import annotations

import json
import re
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

# Korte groente-namen (≤3 tekens) vereisen een woordgrens aan het begin
# om false positives te voorkomen (bijv. "ui" in "kruimige").
_KORTE_NAAM_DREMPEL = 3


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

        # Jaar-rond groenten (alle 12 maanden beschikbaar)
        self._jaar_rond: set[str] = {
            naam for naam, maanden in self._groenten.items() if len(maanden) == 12
        }

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

    def _bevat_groente(self, zoekterm: str, ingredientnaam: str) -> bool:
        """Controleer of een zoekterm voorkomt in de ingrediëntnaam.

        Voor korte zoektermen (≤3 tekens) wordt een woordgrens vereist aan
        het begin om false positives te voorkomen (bijv. "ui" in "kruimige").
        """
        if len(zoekterm) <= _KORTE_NAAM_DREMPEL:
            return bool(re.search(rf"\b{re.escape(zoekterm)}", ingredientnaam))
        return zoekterm in ingredientnaam

    def match_ingredient(self, ingredientnaam: str) -> str | None:
        """Match een ingrediëntnaam tegen de seizoenskalender.

        Retourneert de eerste (langste) match. Zie ``match_alle_groenten``
        voor het vinden van alle groenten in een samengesteld ingrediënt.

        Args:
            ingredientnaam: Naam van het ingrediënt uit een recept.

        Returns:
            De kalender-groente (lowercase) of None als geen match.
        """
        matches = self.match_alle_groenten(ingredientnaam)
        return matches[0] if matches else None

    def match_alle_groenten(self, ingredientnaam: str) -> list[str]:
        """Vind alle kalender-groenten in een ingrediëntnaam.

        Gebruikt substring matching met langste-match-eerst strategie.
        Stamming is bidirectioneel:
        - Kalender→ingrediënt: "tomaat" → "toma" matcht op "cherrytomaten"
        - Ingrediënt→kalender: "peulen" → "peul" matcht op "peultjes"

        Voor korte groente-namen (≤3 tekens) wordt een woordgrens vereist
        om false positives te voorkomen (bijv. "ui" in "kruimige").

        Args:
            ingredientnaam: Naam van het ingrediënt uit een recept.

        Returns:
            Lijst van gematchte kalender-groenten (lowercase), kan leeg zijn.
        """
        naam_lower = ingredientnaam.lower()
        gevonden: list[str] = []

        for groente in self._groenten_namen_sorted:
            if groente in gevonden:
                continue
            if self._bevat_groente(groente, naam_lower):
                gevonden.append(groente)
                continue
            # Stam-matching kalender→ingrediënt:
            # "tomaat" → "toma" matcht op "cherrytomaten"
            for trim in (1, 2):
                stam = groente[:-trim]
                if len(stam) >= 4 and stam in naam_lower:
                    gevonden.append(groente)
                    break

        # Bidirectionele stam-matching ingrediënt→kalender:
        # "peulen" → stam "peul" matcht op "peultjes"
        # Alleen voor enkelvoudige kalendergroenten om false positives
        # met bijvoeglijke naamwoorden te voorkomen
        for woord in naam_lower.split():
            for groente in self._groenten_namen_sorted:
                if groente in gevonden or " " in groente:
                    continue
                for trim in (1, 2):
                    stam = woord[:-trim] if len(woord) > trim else ""
                    if len(stam) >= 4 and stam in groente:
                        gevonden.append(groente)
                        break

        return gevonden

    def recept_is_seizoensgeschikt(self, recipe: Recipe, maand: str) -> bool:
        """Bepaal of een recept seizoensgeschikt is voor de gegeven maand.

        Een recept is geschikt als de meerderheid (>50%) van de herkenbare
        seizoensgroenten lage CO2 heeft voor de maand. Jaar-rond groenten
        (alle 12 maanden beschikbaar) worden uitgesloten van de telling.
        Recepten zonder herkenbare seizoensgroenten zijn altijd geschikt.

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
            for groente in self.match_alle_groenten(ingredient.naam):
                if groente not in self._jaar_rond:
                    herkend += 1
                    if groente in seizoens_groenten:
                        in_seizoen += 1

        # Geen herkenbare seizoensgroenten → altijd geschikt
        if herkend == 0:
            return True

        # Strikte meerderheid: >50%, niet >=50%
        return in_seizoen / herkend > 0.5
