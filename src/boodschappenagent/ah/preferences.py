"""Match-voorkeur opslag: bewaar en haal op welke AH-producten per ingredient."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MatchVoorkeur:
    """Een opgeslagen product-voorkeur per ingredientnaam.

    Attributes:
        ingredient_naam: Genormaliseerde (lowercase) ingredientnaam.
        article_id: AH product article ID.
        product_naam: Productnaam voor weergave (zonder extra lookup).
        updated_at: Tijdstip van opslaan als ISO 8601 string.
    """

    ingredient_naam: str
    article_id: int
    product_naam: str
    updated_at: str

    def __post_init__(self) -> None:
        if not self.ingredient_naam or not self.ingredient_naam.strip():
            raise ValueError("ingredient_naam mag niet leeg zijn")
        if self.article_id <= 0:
            raise ValueError("article_id moet een positief getal zijn")

    def to_dict(self) -> dict:
        return {
            "ingredient_naam": self.ingredient_naam,
            "article_id": self.article_id,
            "product_naam": self.product_naam,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> MatchVoorkeur:
        return cls(
            ingredient_naam=data["ingredient_naam"],
            article_id=data["article_id"],
            product_naam=data["product_naam"],
            updated_at=data["updated_at"],
        )


@dataclass
class MatchReviewItem:
    """Een enkel item in de match-review UI.

    Attributes:
        id: UUID-string — stabiele identifier voor HTMX targeting.
        naam: Weergavenaam van het ingredient.
        hoeveelheid: Gevraagde hoeveelheid (kan None zijn voor handmatige items).
        eenheid: Eenheid (gram, liter, stuks, …).
        product: Gematcht AH product; None = geen match.
        bron: Herkomst van de match:
            "voorkeur" | "voorkeur_niet_beschikbaar" | "referentie" |
            "zoekopdracht" | "niet_gevonden".
        gecorrigeerd: True als de gebruiker de match handmatig heeft gewijzigd.
        aantal: Berekend aantal voor AH-lijst (via bereken_aantal).
    """

    id: str
    naam: str
    hoeveelheid: float | None
    eenheid: str
    product: object | None  # Product (Any om circulaire import te vermijden)
    bron: str
    gecorrigeerd: bool
    aantal: int


class MatchVoorkeurenRepository:
    """Bewaar en haal MatchVoorkeur objecten op uit data/match_preferences.json."""

    def __init__(self, path: Path) -> None:
        self._path = path

    def get(self, ingredient_naam: str) -> MatchVoorkeur | None:
        """Haal voorkeur op voor genormaliseerde ingredientnaam.

        Geeft None terug als de naam niet gevonden is.
        """
        data = self._load()
        key = ingredient_naam.lower().strip()
        if key not in data:
            return None
        return MatchVoorkeur.from_dict(data[key])

    def save(self, voorkeur: MatchVoorkeur) -> None:
        """Sla voorkeur op (upsert op ingredient_naam)."""
        data = self._load()
        data[voorkeur.ingredient_naam] = voorkeur.to_dict()
        self._write(data)

    def delete(self, ingredient_naam: str) -> None:
        """Verwijder voorkeur; no-op als naam niet bestaat."""
        data = self._load()
        key = ingredient_naam.lower().strip()
        if key in data:
            data.pop(key)
            self._write(data)

    def _load(self) -> dict:
        if not self._path.exists():
            return {}
        return json.loads(self._path.read_text(encoding="utf-8"))

    def _write(self, data: dict) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
