"""Voorraad check suggestie-engine."""

from __future__ import annotations

from boodschappenagent.boodschappenlijst.normalizer import IngredientNormalizer
from boodschappenagent.models import Seizoen
from boodschappenagent.planner.models import WeekMenu
from boodschappenagent.voorraadbeheer.models import (
    CheckSuggestie,
    SuggestiePrioriteit,
    VoorraadType,
)
from boodschappenagent.voorraadbeheer.presets import SEIZOEN_INGREDIENTEN
from boodschappenagent.voorraadbeheer.repository import VoorraadRepository


class VoorraadChecker:
    """Genereert suggesties voor de wekelijkse voorraadcheck.

    Prioriteiten:
        HIGH: verse basisproducten (altijd checken)
        MEDIUM: houdbare items die in het weekmenu voorkomen
        LOW: seizoensgebonden items
    """

    def __init__(
        self,
        repository: VoorraadRepository,
        normalizer: IngredientNormalizer | None = None,
    ) -> None:
        self._repository = repository
        self._normalizer = normalizer or IngredientNormalizer()

    def genereer_suggesties(
        self,
        week_menu: WeekMenu,
        seizoen: Seizoen,
    ) -> list[CheckSuggestie]:
        """Genereer check suggesties voor de weekplanning.

        Args:
            week_menu: Het geplande weekmenu.
            seizoen: Huidig seizoen.

        Returns:
            Gesorteerde lijst suggesties (HIGH → MEDIUM → LOW, dan alfabetisch).
        """
        items = self._repository.load()
        if not items:
            return []

        gezien: set[str] = set()
        suggesties: list[CheckSuggestie] = []

        # HIGH: verse basics
        for item in items:
            if item.type is VoorraadType.VERS_BASIS:
                suggesties.append(
                    CheckSuggestie(
                        naam=item.naam,
                        reden="Verse basis — standaard wekelijks",
                        prioriteit=SuggestiePrioriteit.HIGH,
                        type=item.type,
                    )
                )
                gezien.add(item.naam)

        # MEDIUM: houdbare items die in het weekmenu voorkomen
        menu_ingredienten = self._ingredienten_uit_menu(week_menu)
        houdbaar_namen = {i.naam for i in items if i.type is VoorraadType.HOUDBAAR}
        matching = houdbaar_namen & menu_ingredienten
        for naam in matching:
            if naam not in gezien:
                item = next(i for i in items if i.naam == naam)
                suggesties.append(
                    CheckSuggestie(
                        naam=naam,
                        reden="Gebruikt in het weekmenu",
                        prioriteit=SuggestiePrioriteit.MEDIUM,
                        type=item.type,
                    )
                )
                gezien.add(naam)

        # LOW: seizoensgebonden items
        seizoen_namen = set(SEIZOEN_INGREDIENTEN.get(seizoen.value, []))
        seizoen_match = houdbaar_namen & seizoen_namen
        for naam in seizoen_match:
            if naam not in gezien:
                item = next(i for i in items if i.naam == naam)
                suggesties.append(
                    CheckSuggestie(
                        naam=naam,
                        reden=f"Seizoen ({seizoen.value}) — check voorraad",
                        prioriteit=SuggestiePrioriteit.LOW,
                        type=item.type,
                    )
                )
                gezien.add(naam)

        # Sorteer: prioriteit (HIGH < MEDIUM < LOW), dan alfabetisch
        prio_order = list(SuggestiePrioriteit)
        suggesties.sort(key=lambda s: (prio_order.index(s.prioriteit), s.naam))

        return suggesties

    def _ingredienten_uit_menu(self, week_menu: WeekMenu) -> set[str]:
        """Haal unieke, genormaliseerde ingredientnamen uit het weekmenu."""
        namen: set[str] = set()
        for dag in week_menu.geplande_dagen:
            assert dag.recept is not None
            for ing in dag.recept.ingredienten:
                naam, _ = self._normalizer.normaliseer(ing.naam, ing.eenheid)
                namen.add(naam)
        return namen
