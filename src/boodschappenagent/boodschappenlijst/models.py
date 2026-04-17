"""Data models voor de boodschappenlijst."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class BoodschappenRegel:
    """Een regel op de boodschappenlijst.

    Attributes:
        naam: Genormaliseerde ingredientnaam.
        hoeveelheid: Totale afgeronde hoeveelheid.
        eenheid: Eenheid.
        originele_namen: Alle originele namen (voor verificatie).
        opmerkingen: Unieke opmerkingen uit bronnen.
        recepten: Geordende tuple van recept-namen die aan deze regel
            bijdragen (eerste-gezien wint, zonder duplicaten).
    """

    naam: str
    hoeveelheid: float
    eenheid: str
    originele_namen: frozenset[str]
    opmerkingen: list[str] = field(default_factory=list)
    recepten: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.naam or not self.naam.strip():
            msg = "naam mag niet leeg zijn"
            raise ValueError(msg)
        if not self.eenheid or not self.eenheid.strip():
            msg = "eenheid mag niet leeg zijn"
            raise ValueError(msg)
        if not self.originele_namen:
            msg = "originele_namen mag niet leeg zijn"
            raise ValueError(msg)

    @property
    def display_naam(self) -> str:
        """Toon naam met aliassen als er meerdere originele namen zijn."""
        aliassen = sorted(self.originele_namen - {self.naam})
        if not aliassen:
            return self.naam
        return f"{self.naam} (ook: {', '.join(aliassen)})"

    def to_dict(self) -> dict[str, Any]:
        """Converteer naar dictionary voor JSON serialisatie."""
        return {
            "naam": self.naam,
            "hoeveelheid": self.hoeveelheid,
            "eenheid": self.eenheid,
            "originele_namen": sorted(self.originele_namen),
            "opmerkingen": list(self.opmerkingen),
            "recepten": list(self.recepten),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BoodschappenRegel:
        """Maak BoodschappenRegel van dictionary."""
        return cls(
            naam=data["naam"],
            hoeveelheid=data["hoeveelheid"],
            eenheid=data["eenheid"],
            originele_namen=frozenset(data["originele_namen"]),
            opmerkingen=data.get("opmerkingen", []),
            recepten=tuple(data.get("recepten", [])),
        )


@dataclass(frozen=True)
class Boodschappenlijst:
    """Een complete boodschappenlijst voor een week.

    Attributes:
        week_start: ISO date YYYY-MM-DD.
        regels: Alfabetisch gesorteerde boodschappenregels.
    """

    week_start: str
    regels: list[BoodschappenRegel] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.week_start or not self.week_start.strip():
            msg = "week_start mag niet leeg zijn"
            raise ValueError(msg)

    def to_dict(self) -> dict[str, Any]:
        """Converteer naar dictionary voor JSON serialisatie."""
        return {
            "week_start": self.week_start,
            "regels": [r.to_dict() for r in self.regels],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Boodschappenlijst:
        """Maak Boodschappenlijst van dictionary."""
        regels = [BoodschappenRegel.from_dict(r) for r in data.get("regels", [])]
        return cls(week_start=data["week_start"], regels=regels)
