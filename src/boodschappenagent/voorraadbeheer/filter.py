"""Boodschappenlijst filtering op basis van voorraad."""

from __future__ import annotations

from boodschappenagent.boodschappenlijst.models import (
    Boodschappenlijst,
    BoodschappenRegel,
)
from boodschappenagent.voorraadbeheer.models import VoorraadType
from boodschappenagent.voorraadbeheer.presets import VERSE_BASICS
from boodschappenagent.voorraadbeheer.repository import VoorraadRepository


class BoodschappenlijstFilter:
    """Filtert een boodschappenlijst op basis van voorraad.

    - Verwijdert items die op voorraad zijn
    - Voegt verse basisproducten toe die niet op voorraad zijn
    - Voegt houdbare producten toe die niet op voorraad zijn
    """

    def __init__(self, repository: VoorraadRepository) -> None:
        self._repository = repository

    def filter_op_voorraad(self, lijst: Boodschappenlijst) -> Boodschappenlijst:
        """Filter de boodschappenlijst op voorraad.

        1. Verwijder regels waarvan de naam op voorraad is.
        2. Voeg verse basics toe die niet op voorraad zijn
           en nog niet in de lijst staan.
        3. Voeg houdbare producten toe die niet op voorraad zijn
           en nog niet in de lijst staan.
        4. Sorteer alfabetisch.

        Args:
            lijst: De originele boodschappenlijst.

        Returns:
            Nieuwe gefilterde Boodschappenlijst.
        """
        op_voorraad = self._repository.op_voorraad_namen()

        # Stap 1: filter items die op voorraad zijn
        regels = [r for r in lijst.regels if r.naam not in op_voorraad]

        # Stap 2: voeg verse basics toe die niet op voorraad zijn
        bestaande_namen = {r.naam for r in regels}
        items = self._repository.load()
        verse_basis_niet_op_voorraad = {
            i.naam
            for i in items
            if i.type is VoorraadType.VERS_BASIS and not i.op_voorraad
        }

        for naam, hoeveelheid, eenheid in VERSE_BASICS:
            if naam in verse_basis_niet_op_voorraad and naam not in bestaande_namen:
                regels.append(
                    BoodschappenRegel(
                        naam=naam,
                        hoeveelheid=hoeveelheid,
                        eenheid=eenheid,
                        originele_namen=frozenset({naam}),
                    )
                )
                bestaande_namen.add(naam)

        # Stap 3: voeg houdbare producten toe die niet op voorraad zijn
        houdbaar_niet_op_voorraad = [
            i
            for i in items
            if i.type is VoorraadType.HOUDBAAR
            and not i.op_voorraad
            and i.naam not in bestaande_namen
        ]
        for item in houdbaar_niet_op_voorraad:
            regels.append(
                BoodschappenRegel(
                    naam=item.naam,
                    hoeveelheid=1,
                    eenheid="stuks",
                    originele_namen=frozenset({item.naam}),
                )
            )
            bestaande_namen.add(item.naam)

        # Stap 4: sorteer alfabetisch
        regels.sort(key=lambda r: r.naam)

        return Boodschappenlijst(week_start=lijst.week_start, regels=regels)
