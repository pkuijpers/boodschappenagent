"""Data models voor de menuplanner."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from boodschappenagent.models import Recipe


def _validate_dag_personen(dag: int, personen: int) -> None:
    """Valideer dag (0-6) en personen (>= 0) velden."""
    if not (0 <= dag <= 6):
        msg = "dag moet tussen 0 en 6 zijn"
        raise ValueError(msg)
    if personen < 0:
        msg = "personen moet >= 0 zijn"
        raise ValueError(msg)


@dataclass(frozen=True)
class DagInput:
    """Input voor een enkele dag.

    Attributes:
        dag: Weekdag (0=maandag, 6=zondag).
        personen: Aantal personen (0 = niet thuis).
    """

    dag: int
    personen: int

    def __post_init__(self) -> None:
        _validate_dag_personen(self.dag, self.personen)


@dataclass(frozen=True)
class DagPlanning:
    """Planning voor een enkele dag.

    Attributes:
        dag: Weekdag (0=maandag, 6=zondag).
        recept: Het geplande recept (None als niet thuis).
        personen: Aantal personen (0 = niet thuis).
    """

    dag: int
    recept: Recipe | None
    personen: int

    def __post_init__(self) -> None:
        _validate_dag_personen(self.dag, self.personen)
        if self.personen == 0 and self.recept is not None:
            msg = "recept moet None zijn als personen 0 is"
            raise ValueError(msg)
        if self.personen > 0 and self.recept is None:
            msg = "recept is verplicht als personen > 0 is"
            raise ValueError(msg)

    def to_dict(self) -> dict[str, Any]:
        """Converteer naar dictionary voor JSON serialisatie."""
        return {
            "dag": self.dag,
            "recept_id": self.recept.id if self.recept else None,
            "personen": self.personen,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any], recipes: dict[str, Recipe]) -> DagPlanning:
        """Maak DagPlanning van dictionary.

        Args:
            data: Dictionary met dag, recept_id, personen.
            recipes: Lookup dict van recept ID naar Recipe.

        Returns:
            DagPlanning instantie.

        Raises:
            ValueError: Als recept_id niet gevonden wordt.
        """
        recept_id = data["recept_id"]
        recept = None
        if recept_id is not None:
            if recept_id not in recipes:
                msg = f"recept niet gevonden: {recept_id}"
                raise ValueError(msg)
            recept = recipes[recept_id]
        return cls(dag=data["dag"], recept=recept, personen=data["personen"])


@dataclass(frozen=True)
class WeekMenu:
    """Een weekmenu met dagplanningen.

    Attributes:
        week_start: Maandag van de week (ISO date string YYYY-MM-DD).
        dagen: Lijst van DagPlanning objecten (maximaal 7).
    """

    week_start: str
    dagen: list[DagPlanning] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.week_start:
            msg = "week_start mag niet leeg zijn"
            raise ValueError(msg)
        if len(self.dagen) > 7:
            msg = "maximaal 7 dagen per week"
            raise ValueError(msg)
        dag_nummers = [d.dag for d in self.dagen]
        if len(dag_nummers) != len(set(dag_nummers)):
            msg = "dubbele dagen in weekmenu"
            raise ValueError(msg)

    @property
    def geplande_dagen(self) -> list[DagPlanning]:
        """Alleen dagen met een recept (niet-thuis-dagen uitgefilterd)."""
        return [d for d in self.dagen if d.recept is not None]

    def to_dict(self) -> dict[str, Any]:
        """Converteer naar dictionary voor JSON serialisatie."""
        return {
            "week_start": self.week_start,
            "dagen": [d.to_dict() for d in self.dagen],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any], recipes: dict[str, Recipe]) -> WeekMenu:
        """Maak WeekMenu van dictionary.

        Args:
            data: Dictionary met week_start en dagen.
            recipes: Lookup dict van recept ID naar Recipe.

        Returns:
            WeekMenu instantie.
        """
        dagen = [DagPlanning.from_dict(d, recipes) for d in data["dagen"]]
        return cls(week_start=data["week_start"], dagen=dagen)
