"""Boodschappenlijst generator: WeekMenu → Boodschappenlijst."""

from __future__ import annotations

from boodschappenagent.boodschappenlijst.models import (
    Boodschappenlijst,
    BoodschappenRegel,
)
from boodschappenagent.boodschappenlijst.normalizer import IngredientNormalizer
from boodschappenagent.planner.models import WeekMenu
from boodschappenagent.utils import PortionCalculator


class BoodschappenlijstGenerator:
    """Genereert een boodschappenlijst uit een WeekMenu."""

    def __init__(
        self,
        normalizer: IngredientNormalizer,
        portion_calculator: PortionCalculator,
    ) -> None:
        self._normalizer = normalizer
        self._calculator = portion_calculator

    def genereer(self, week_menu: WeekMenu) -> Boodschappenlijst:
        """Genereer een boodschappenlijst uit een weekmenu.

        Args:
            week_menu: Het weekmenu om te verwerken.

        Returns:
            Een Boodschappenlijst met geaggregeerde ingrediënten.
        """
        # Accumulators per (norm_naam, norm_eenheid)
        hoeveelheden: dict[tuple[str, str], float] = {}
        originele_namen: dict[tuple[str, str], set[str]] = {}
        opmerkingen: dict[tuple[str, str], list[str]] = {}
        recepten_per_key: dict[tuple[str, str], list[str]] = {}

        for dag in week_menu.geplande_dagen:
            assert dag.recept is not None  # geplande_dagen filtert None
            scaled = dag.recept.scale_to_portions(dag.personen)
            recept_naam = dag.recept.naam

            for ing in scaled.ingredienten:
                norm_naam, norm_eenheid = self._normalizer.normaliseer(
                    ing.naam, ing.eenheid
                )
                key = (norm_naam, norm_eenheid)

                # Hoeveelheid accumuleren
                if self._normalizer.is_niet_aggregeerbaar(norm_eenheid):
                    hoeveelheden[key] = 1.0
                else:
                    hoeveelheden[key] = hoeveelheden.get(key, 0.0) + ing.hoeveelheid

                # Originele namen bijhouden
                if key not in originele_namen:
                    originele_namen[key] = set()
                originele_namen[key].add(ing.naam)

                # Opmerkingen bijhouden (None filteren, dedupliceren)
                if key not in opmerkingen:
                    opmerkingen[key] = []
                if ing.opmerking and ing.opmerking not in opmerkingen[key]:
                    opmerkingen[key].append(ing.opmerking)

                # Recepten bijhouden (week-volgorde, dedupliceren)
                if key not in recepten_per_key:
                    recepten_per_key[key] = []
                if recept_naam not in recepten_per_key[key]:
                    recepten_per_key[key].append(recept_naam)

        # Regels aanmaken met afronding NA aggregatie
        regels = []
        for key, totaal in hoeveelheden.items():
            norm_naam, norm_eenheid = key
            afgerond = self._calculator.round_quantity(totaal, norm_eenheid)
            regels.append(
                BoodschappenRegel(
                    naam=norm_naam,
                    hoeveelheid=afgerond,
                    eenheid=norm_eenheid,
                    originele_namen=frozenset(originele_namen[key]),
                    opmerkingen=opmerkingen[key],
                    recepten=tuple(recepten_per_key[key]),
                )
            )

        # Sorteer alfabetisch op naam
        regels.sort(key=lambda r: r.naam)

        return Boodschappenlijst(week_start=week_menu.week_start, regels=regels)
