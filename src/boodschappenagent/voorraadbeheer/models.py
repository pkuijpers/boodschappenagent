"""Data models voor voorraadbeheer."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Any


class VoorraadType(str, Enum):
    """Type voorraaditem."""

    HOUDBAAR = "houdbaar"
    VERS_BASIS = "vers_basis"


class SuggestiePrioriteit(str, Enum):
    """Prioriteit van een check suggestie."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass(frozen=True)
class VoorraadItem:
    """Een item in de voorraad.

    Attributes:
        naam: Genormaliseerde ingredientnaam.
        type: HOUDBAAR of VERS_BASIS.
        op_voorraad: True als het item aanwezig is.
        laatst_gecheckt: ISO date YYYY-MM-DD van laatste check.
    """

    naam: str
    type: VoorraadType
    op_voorraad: bool
    laatst_gecheckt: str

    def __post_init__(self) -> None:
        if not self.naam or not self.naam.strip():
            msg = "naam mag niet leeg zijn"
            raise ValueError(msg)
        if not self.laatst_gecheckt:
            msg = "laatst_gecheckt mag niet leeg zijn"
            raise ValueError(msg)
        try:
            date.fromisoformat(self.laatst_gecheckt)
        except ValueError as e:
            msg = f"Ongeldige datum: {e}"
            raise ValueError(msg) from e

    def to_dict(self) -> dict[str, Any]:
        """Converteer naar dictionary voor JSON serialisatie."""
        return {
            "naam": self.naam,
            "type": self.type.value,
            "op_voorraad": self.op_voorraad,
            "laatst_gecheckt": self.laatst_gecheckt,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> VoorraadItem:
        """Maak VoorraadItem van dictionary."""
        return cls(
            naam=data["naam"],
            type=VoorraadType(data["type"]),
            op_voorraad=data["op_voorraad"],
            laatst_gecheckt=data["laatst_gecheckt"],
        )


@dataclass(frozen=True)
class CheckSuggestie:
    """Een suggestie om een voorraaditem te checken.

    Attributes:
        naam: Ingredientnaam.
        reden: Waarom deze suggestie (voor display).
        prioriteit: HIGH, MEDIUM, LOW.
        type: VoorraadType van het item.
    """

    naam: str
    reden: str
    prioriteit: SuggestiePrioriteit
    type: VoorraadType

    def __post_init__(self) -> None:
        if not self.naam or not self.naam.strip():
            msg = "naam mag niet leeg zijn"
            raise ValueError(msg)
        if not self.reden or not self.reden.strip():
            msg = "reden mag niet leeg zijn"
            raise ValueError(msg)
