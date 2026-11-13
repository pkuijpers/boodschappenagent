"""Ingrediënt naam- en eenheidnormalisatie."""

from __future__ import annotations

# Synoniemen die ook een eenheid-wijziging impliceren
_NAAM_UNIT_OVERRIDES: dict[str, tuple[str, str]] = {
    "knoflookteen": ("knoflook", "teen"),
}

_NAAM_SYNONIEMEN: dict[str, str] = {
    "uien": "ui",
    "biologische ui": "ui",
    "biologische rode ui": "rode ui",
    "passata di pomodoro": "passata",
    "platte peterselie": "peterselie",
    "vers bladerdeeg": "bladerdeeg",
    "biologische tuinkers": "tuinkers",
    "sjalotten": "sjalot",
}

_EENHEID_SYNONIEMEN: dict[str, str] = {
    "snuf": "naar smaak",
    "el": "eetlepel",
    "tl": "theelepel",
    "g": "gram",
    "l": "liter",
    "kg": "kilogram",
}

# Eenheden die altijd naar een basiseenheid worden omgerekend: (basis, factor)
_BASISEENHEDEN: dict[str, tuple[str, float]] = {
    "liter": ("ml", 1000),
    "kilogram": ("gram", 1000),
}

_NIET_AGGREGEERBAAR: frozenset[str] = frozenset(
    {
        "naar smaak",
        "snuf",
        "mespunt",
    }
)


class IngredientNormalizer:
    """Normaliseert ingredientnamen en eenheden."""

    def __init__(self, extra_synoniemen: dict[str, str] | None = None) -> None:
        self._naam_synoniemen = dict(_NAAM_SYNONIEMEN)
        self._naam_unit_overrides = dict(_NAAM_UNIT_OVERRIDES)
        if extra_synoniemen:
            self._naam_synoniemen.update(extra_synoniemen)

    def normaliseer(self, naam: str, eenheid: str) -> tuple[str, str]:
        """Normaliseer naam en eenheid.

        Args:
            naam: Originele ingredientnaam.
            eenheid: Originele eenheid.

        Returns:
            Tuple van (genormaliseerde_naam, genormaliseerde_eenheid).
        """
        naam_lower = naam.lower()
        eenheid_lower = eenheid.lower()

        # Check naam+unit overrides eerst (bijv. knoflookteen → knoflook + teen)
        if naam_lower in self._naam_unit_overrides:
            naam_lower, eenheid_lower = self._naam_unit_overrides[naam_lower]
        elif naam_lower in self._naam_synoniemen:
            naam_lower = self._naam_synoniemen[naam_lower]

        # Eenheid normalisatie
        eenheid_lower = _EENHEID_SYNONIEMEN.get(eenheid_lower, eenheid_lower)

        return naam_lower, eenheid_lower

    def naar_basiseenheid(self, hoeveelheid: float, eenheid: str) -> tuple[float, str]:
        """Reken een (genormaliseerde) eenheid om naar zijn basiseenheid.

        Bijvoorbeeld 0.5 liter → 500 ml, 1 kilogram → 1000 gram.
        Eenheden zonder basiseenheid worden ongewijzigd teruggegeven.
        """
        if eenheid in _BASISEENHEDEN:
            basis, factor = _BASISEENHEDEN[eenheid]
            return hoeveelheid * factor, basis
        return hoeveelheid, eenheid

    def is_niet_aggregeerbaar(self, eenheid: str) -> bool:
        """Check of een eenheid niet-aggregeerbaar is."""
        return eenheid.lower() in _NIET_AGGREGEERBAAR
