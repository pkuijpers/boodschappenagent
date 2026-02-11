"""Menu-geschiedenis persistentie in JSON formaat."""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from boodschappenagent.planner.models import WeekMenu


class MenuHistory:
    """Bijhouden en opslaan van menu-geschiedenis.

    Slaat op welke recepten wanneer gegeten zijn, zodat
    de planner herhalingen kan voorkomen.
    """

    def __init__(self, path: Path) -> None:
        self._path = path

    def load(self) -> list[dict[str, Any]]:
        """Laad geschiedenis entries uit JSON bestand.

        Returns:
            Lijst van entries. Lege lijst als bestand niet bestaat.

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

        return data

    def save(self, entries: list[dict[str, Any]]) -> None:
        """Sla geschiedenis entries op als JSON bestand.

        Args:
            entries: Lijst van geschiedenis entries.
        """
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(entries, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def add_week(self, week_menu: WeekMenu) -> None:
        """Voeg een weekmenu toe aan de geschiedenis.

        Laadt bestaande history, voegt nieuwe entries toe voor
        dagen met een recept (skipt niet-thuis), en schrijft terug.

        Args:
            week_menu: Het weekmenu om toe te voegen.
        """
        entries = self.load()
        week_start = date.fromisoformat(week_menu.week_start)

        for dag_planning in week_menu.geplande_dagen:
            datum = week_start + timedelta(days=dag_planning.dag)
            entries.append(
                {
                    "datum": datum.isoformat(),
                    "recept_id": dag_planning.recept.id,
                    "personen": dag_planning.personen,
                }
            )

        self.save(entries)

    def recent_recipe_ids(self, weken: int = 3) -> set[str]:
        """Geef recept-IDs die in de afgelopen X weken gegeten zijn.

        Args:
            weken: Aantal weken terug om te kijken (default 3).

        Returns:
            Set van recept IDs.
        """
        entries = self.load()
        cutoff = date.today() - timedelta(weeks=weken)

        return {
            entry["recept_id"]
            for entry in entries
            if date.fromisoformat(entry["datum"]) >= cutoff
        }
