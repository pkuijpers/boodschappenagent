"""Ingredient dataclass voor recepten."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Ingredient:
    """Een ingrediënt met naam, hoeveelheid, eenheid en optionele opmerking.

    Attributes:
        naam: De naam van het ingrediënt (bijv. "ui", "knoflook").
        hoeveelheid: De hoeveelheid van het ingrediënt (moet > 0 zijn).
        eenheid: De eenheid (bijv. "gram", "stuks", "eetlepel").
        opmerking: Optionele opmerking (bijv. "fijngesneden", "vers").
    """

    naam: str
    hoeveelheid: float
    eenheid: str
    opmerking: str | None = None

    def __post_init__(self) -> None:
        """Valideer de velden na initialisatie."""
        self._validate_naam()
        self._validate_hoeveelheid()

    def _validate_naam(self) -> None:
        """Valideer het naam veld."""
        if not self.naam or not self.naam.strip():
            msg = "naam mag niet leeg zijn"
            raise ValueError(msg)

    def _validate_hoeveelheid(self) -> None:
        """Valideer het hoeveelheid veld."""
        if self.hoeveelheid <= 0:
            msg = "hoeveelheid moet groter dan 0 zijn"
            raise ValueError(msg)

    def scale(self, factor: float) -> Ingredient:
        """Schaal de hoeveelheid met de gegeven factor.

        Args:
            factor: De schaalfactor (moet > 0 zijn).

        Returns:
            Een nieuw Ingredient object met de geschaalde hoeveelheid.

        Raises:
            ValueError: Als factor <= 0.
        """
        if factor <= 0:
            msg = "factor moet groter dan 0 zijn"
            raise ValueError(msg)

        return Ingredient(
            naam=self.naam,
            hoeveelheid=self.hoeveelheid * factor,
            eenheid=self.eenheid,
            opmerking=self.opmerking,
        )

    def to_dict(self) -> dict[str, Any]:
        """Converteer naar een dictionary voor JSON serialisatie.

        Returns:
            Dictionary representatie van het ingrediënt.
        """
        return {
            "naam": self.naam,
            "hoeveelheid": self.hoeveelheid,
            "eenheid": self.eenheid,
            "opmerking": self.opmerking,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Ingredient:
        """Maak een Ingredient van een dictionary.

        Args:
            data: Dictionary met ingrediënt data.

        Returns:
            Nieuw Ingredient object.
        """
        return cls(
            naam=data["naam"],
            hoeveelheid=data["hoeveelheid"],
            eenheid=data["eenheid"],
            opmerking=data.get("opmerking"),
        )
