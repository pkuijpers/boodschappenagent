"""Recipe dataclass voor recepten."""

from __future__ import annotations

import re
from dataclasses import dataclass, field, replace
from typing import Any

from boodschappenagent.models.enums import Basis, Categorie, Seizoen
from boodschappenagent.models.ingredient import Ingredient

# Regex voor slug validatie: lowercase letters, cijfers en koppeltekens
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


@dataclass(frozen=True)
class Recipe:
    """Een recept met ingrediënten en metadata.

    Attributes:
        id: Unieke slug identifier (lowercase, geen spaties).
        naam: De naam van het recept (max 100 karakters).
        categorie: De categorie van het recept (proteïnebron).
        basis: De koolhydraatbasis van het recept.
        seizoenen: Deprecated — wordt genegeerd. Seizoensgeschiktheid wordt
            bepaald via de CO2-seizoenskalender. Behouden voor backward compat.
        basis_porties: Standaard aantal porties (>= 1).
        ingredienten: Lijst van ingrediënten.
        tags: Lijst van tags voor filtering.
        bereidingstijd_min: Bereidingstijd in minuten (> 0).
        bereidingswijze: Optionele bereidingsinstructies.
        bron: Optionele bron van het recept.
    """

    id: str
    naam: str
    categorie: Categorie
    basis: Basis
    basis_porties: int
    ingredienten: list[Ingredient]
    seizoenen: list[Seizoen] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    bereidingstijd_min: int = 30
    bereidingswijze: str | None = None
    bron: str | None = None

    def __post_init__(self) -> None:
        """Valideer de velden na initialisatie."""
        self._validate_id()
        self._validate_naam()
        self._validate_basis_porties()
        self._validate_bereidingstijd()

    def _validate_id(self) -> None:
        """Valideer het id veld (slug format)."""
        if not self.id:
            msg = "id mag niet leeg zijn"
            raise ValueError(msg)
        if not SLUG_PATTERN.match(self.id):
            msg = "id moet lowercase zijn zonder spaties (slug format: a-z, 0-9, -)"
            raise ValueError(msg)

    def _validate_naam(self) -> None:
        """Valideer het naam veld."""
        if not self.naam or not self.naam.strip():
            msg = "naam mag niet leeg zijn"
            raise ValueError(msg)
        if len(self.naam) > 100:
            msg = "naam mag niet langer dan 100 karakters zijn"
            raise ValueError(msg)

    def _validate_basis_porties(self) -> None:
        """Valideer basis_porties."""
        if self.basis_porties < 1:
            msg = "basis_porties moet minimaal 1 zijn"
            raise ValueError(msg)

    def _validate_bereidingstijd(self) -> None:
        """Valideer bereidingstijd_min."""
        if self.bereidingstijd_min <= 0:
            msg = "bereidingstijd_min moet groter dan 0 zijn"
            raise ValueError(msg)

    def scale_to_portions(self, porties: int) -> Recipe:
        """Schaal het recept naar het opgegeven aantal porties.

        Args:
            porties: Het gewenste aantal porties (moet > 0 zijn).

        Returns:
            Een nieuw Recipe object met geschaalde ingrediënten.

        Raises:
            ValueError: Als porties <= 0.
        """
        if porties <= 0:
            msg = "porties moet groter dan 0 zijn"
            raise ValueError(msg)

        factor = porties / self.basis_porties
        scaled_ingredienten = [ing.scale(factor) for ing in self.ingredienten]

        return self.copy_with(
            basis_porties=porties,
            ingredienten=scaled_ingredienten,
        )

    def copy_with(self, **changes: Any) -> Recipe:
        """Maak een kopie van dit recept met optioneel aangepaste velden.

        Args:
            **changes: Velden om te wijzigen in de kopie.

        Returns:
            Een nieuw Recipe object met de aangepaste velden.

        Example:
            >>> recipe.copy_with(basis_porties=4, tags=["nieuw"])
        """
        # Kopieer lijsten om mutatie van origineel te voorkomen
        if "seizoenen" not in changes:
            changes["seizoenen"] = list(self.seizoenen)
        if "ingredienten" not in changes:
            changes["ingredienten"] = list(self.ingredienten)
        if "tags" not in changes:
            changes["tags"] = list(self.tags)

        return replace(self, **changes)

    def to_dict(self) -> dict[str, Any]:
        """Converteer naar een dictionary voor JSON serialisatie.

        Returns:
            Dictionary representatie van het recept.
        """
        result = {
            "id": self.id,
            "naam": self.naam,
            "categorie": self.categorie.value,
            "basis": self.basis.value,
            "basis_porties": self.basis_porties,
            "ingredienten": [ing.to_dict() for ing in self.ingredienten],
            "tags": list(self.tags),
            "bereidingstijd_min": self.bereidingstijd_min,
            "bereidingswijze": self.bereidingswijze,
            "bron": self.bron,
        }
        if self.seizoenen:
            result["seizoenen"] = [s.value for s in self.seizoenen]
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Recipe:
        """Maak een Recipe van een dictionary.

        Args:
            data: Dictionary met recept data.

        Returns:
            Nieuw Recipe object.
        """
        ingredienten = [
            Ingredient.from_dict(ing) for ing in data.get("ingredienten", [])
        ]

        return cls(
            id=data["id"],
            naam=data["naam"],
            categorie=Categorie(data["categorie"]),
            basis=Basis(data["basis"]),
            seizoenen=[Seizoen(s) for s in data.get("seizoenen", [])],
            basis_porties=data["basis_porties"],
            ingredienten=ingredienten,
            tags=data.get("tags", []),
            bereidingstijd_min=data["bereidingstijd_min"],
            bereidingswijze=data.get("bereidingswijze"),
            bron=data.get("bron"),
        )
