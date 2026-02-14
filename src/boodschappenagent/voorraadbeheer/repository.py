"""Voorraad persistentie in JSON formaat."""

from __future__ import annotations

import json
from pathlib import Path

from boodschappenagent.voorraadbeheer.models import VoorraadItem


class VoorraadRepository:
    """Laad en bewaar voorraad items als JSON.

    Volgt hetzelfde patroon als MenuHistory voor JSON persistentie.
    """

    def __init__(self, path: Path) -> None:
        self._path = path

    def load(self) -> list[VoorraadItem]:
        """Laad alle voorraad items.

        Returns:
            Lijst van VoorraadItem. Lege lijst als bestand niet bestaat.

        Raises:
            ValueError: Als het JSON formaat ongeldig is.
        """
        if not self._path.exists():
            return []

        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            msg = f"Ongeldig JSON formaat in {self._path}: {e}"
            raise ValueError(msg) from e

        return [VoorraadItem.from_dict(d) for d in data]

    def save(self, items: list[VoorraadItem]) -> None:
        """Sla voorraad items op als JSON.

        Args:
            items: Lijst van VoorraadItem.
        """
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps([i.to_dict() for i in items], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def update_item(self, item: VoorraadItem) -> None:
        """Update of voeg een item toe (match op naam, case-insensitive).

        Args:
            item: Het item om te updaten of toe te voegen.
        """
        items = self.load()
        naam_lower = item.naam.lower()
        nieuwe_items = [i for i in items if i.naam.lower() != naam_lower]
        nieuwe_items.append(item)
        self.save(nieuwe_items)

    def op_voorraad_namen(self) -> set[str]:
        """Geef namen van alle items die op voorraad zijn.

        Returns:
            Set van itemnamen.
        """
        return {i.naam for i in self.load() if i.op_voorraad}
