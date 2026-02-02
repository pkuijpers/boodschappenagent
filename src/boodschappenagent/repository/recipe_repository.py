"""Repository voor het laden en opslaan van recepten als JSON."""

from __future__ import annotations

import json
from pathlib import Path

from boodschappenagent.models import Recipe


class RecipeRepository:
    """Repository voor CRUD operaties op Recipe objecten in JSON formaat."""

    def load(self, path: Path) -> Recipe:
        """Laad een recept uit een JSON bestand.

        Args:
            path: Pad naar het JSON bestand.

        Returns:
            Het geladen Recipe object.

        Raises:
            FileNotFoundError: Als het bestand niet bestaat.
            ValueError: Als het JSON formaat ongeldig is.
        """
        if not path.exists():
            raise FileNotFoundError(f"Bestand niet gevonden: {path}")

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            msg = f"Ongeldig JSON formaat in {path}: {e}"
            raise ValueError(msg) from e

        return Recipe.from_dict(data)

    def load_all(self, directory: Path) -> list[Recipe]:
        """Laad alle recepten uit een directory (inclusief subdirectories).

        Args:
            directory: Pad naar de directory met JSON bestanden.

        Returns:
            Lijst van geladen Recipe objecten.
        """
        recipes = []
        for json_file in directory.rglob("*.json"):
            recipes.append(self.load(json_file))
        return recipes

    def save(self, recipe: Recipe, path: Path) -> None:
        """Sla een recept op als JSON bestand.

        Args:
            recipe: Het Recipe object om op te slaan.
            path: Pad waar het JSON bestand moet worden opgeslagen.
        """
        # Maak parent directories aan indien nodig
        path.parent.mkdir(parents=True, exist_ok=True)

        path.write_text(
            json.dumps(recipe.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def delete(self, path: Path) -> None:
        """Verwijder een recept bestand.

        Args:
            path: Pad naar het te verwijderen bestand.

        Raises:
            FileNotFoundError: Als het bestand niet bestaat.
        """
        if not path.exists():
            raise FileNotFoundError(f"Bestand niet gevonden: {path}")
        path.unlink()
