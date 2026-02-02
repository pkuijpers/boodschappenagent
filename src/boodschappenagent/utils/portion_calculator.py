"""Portieberekening met praktische afrondingslogica."""

from __future__ import annotations

import math
from decimal import ROUND_HALF_UP, Decimal

from boodschappenagent.models import Ingredient, Recipe


def _round_half_up(value: float, decimals: int = 0) -> float:
    """Rond af met 'half up' strategie (0.5 gaat naar boven).

    Python's ingebouwde round() gebruikt banker's rounding.
    Deze functie rondt 0.5 altijd naar boven af.
    """
    d = Decimal(str(value))
    if decimals == 0:
        rounded = d.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    else:
        quantize_str = "0." + "0" * decimals
        rounded = d.quantize(Decimal(quantize_str), rounding=ROUND_HALF_UP)
    return float(rounded)


class PortionCalculator:
    """Calculator voor het schalen van recepten met praktische afrondingen.

    Afrondingsregels per eenheid:
    - gram/ml: naar dichtstbijzijnde 5 (minimum 5)
    - stuks/teen: naar boven (hele getallen)
    - eetlepel/theelepel: naar dichtstbijzijnde 0.5
    - liter: naar dichtstbijzijnde 0.1
    - snuf/naar smaak: geen afronding
    """

    # Eenheden die naar boven worden afgerond (hele getallen)
    ROUND_UP_UNITS = frozenset({"stuks", "teen", "stuk"})

    # Eenheden die naar 5 worden afgerond
    ROUND_TO_5_UNITS = frozenset({"gram", "ml", "g"})

    # Eenheden die naar 0.5 worden afgerond
    ROUND_TO_HALF_UNITS = frozenset({"eetlepel", "theelepel", "el", "tl"})

    # Eenheden die naar 0.1 worden afgerond
    ROUND_TO_TENTH_UNITS = frozenset({"liter", "l"})

    # Eenheden die niet worden afgerond
    NO_ROUND_UNITS = frozenset({"snuf", "naar smaak", "mespunt"})

    def round_quantity(self, quantity: float, unit: str) -> float:
        """Rond een hoeveelheid af op basis van de eenheid.

        Args:
            quantity: De hoeveelheid om af te ronden.
            unit: De eenheid van de hoeveelheid.

        Returns:
            De afgeronde hoeveelheid.
        """
        unit_lower = unit.lower()

        if unit_lower in self.ROUND_UP_UNITS:
            return float(math.ceil(quantity))

        if unit_lower in self.ROUND_TO_5_UNITS:
            rounded = _round_half_up(quantity / 5) * 5
            return max(5.0, rounded)  # minimum 5

        if unit_lower in self.ROUND_TO_HALF_UNITS:
            return _round_half_up(quantity * 2) / 2

        if unit_lower in self.ROUND_TO_TENTH_UNITS:
            return _round_half_up(quantity, 1)

        if unit_lower in self.NO_ROUND_UNITS:
            return quantity

        # Onbekende eenheid: niet afronden
        return quantity

    def round_ingredient(self, ingredient: Ingredient) -> Ingredient:
        """Rond de hoeveelheid van een ingrediënt af.

        Args:
            ingredient: Het ingrediënt om af te ronden.

        Returns:
            Een nieuw Ingredient object met afgeronde hoeveelheid.
        """
        rounded_quantity = self.round_quantity(
            ingredient.hoeveelheid, ingredient.eenheid
        )
        return Ingredient(
            naam=ingredient.naam,
            hoeveelheid=rounded_quantity,
            eenheid=ingredient.eenheid,
            opmerking=ingredient.opmerking,
        )

    def scale_recipe(self, recipe: Recipe, porties: int) -> Recipe:
        """Schaal een recept naar het opgegeven aantal porties met afrondingen.

        Args:
            recipe: Het recept om te schalen.
            porties: Het gewenste aantal porties.

        Returns:
            Een nieuw Recipe object met geschaalde en afgeronde ingrediënten.

        Raises:
            ValueError: Als porties <= 0.
        """
        # Gebruik Recipe's scale methode voor de basis schaling
        scaled = recipe.scale_to_portions(porties)

        # Rond alle ingrediënten af
        rounded_ingredienten = [
            self.round_ingredient(ing) for ing in scaled.ingredienten
        ]

        return scaled.copy_with(ingredienten=rounded_ingredienten)
