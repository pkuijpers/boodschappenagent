"""Batch processor voor het verwerken van PDF batches met recepten."""

from __future__ import annotations

import json
import re
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from boodschappenagent.digitizer.pdf_processor import PDFProcessor
from boodschappenagent.digitizer.recipe_extractor import RecipeExtractor

# Type alias voor progress callback: (current, total, recipe_naam | None)
ProgressCallback = Callable[[int, int, str | None], None]


def _format_recipe_json(recipe_data: dict[str, Any]) -> str:
    """Format recept JSON met compacte arrays en ingrediënten.

    Ingrediënten worden op één regel gezet voor leesbaarheid.
    Simpele arrays (seizoenen, tags) worden ook compact gehouden.

    Args:
        recipe_data: De recept data.

    Returns:
        Geformatteerde JSON string.
    """
    # Start met standaard indent
    json_str = json.dumps(recipe_data, indent=2, ensure_ascii=False)

    # Compacteer ingredient objecten: {"naam": ..., "hoeveelheid": ...} op één regel
    ing_pattern = r'\{\s*\n\s*"naam":\s*"([^"]*)",\s*\n\s*"hoeveelheid":\s*(\d+(?:\.\d+)?),\s*\n\s*"eenheid":\s*"([^"]*)",\s*\n\s*"opmerking":\s*(null|"[^"]*")\s*\n\s*\}'

    def compact_ingredient(match: re.Match) -> str:
        naam = match.group(1)
        hoeveelheid = match.group(2)
        eenheid = match.group(3)
        opmerking = match.group(4)
        return f'{{"naam": "{naam}", "hoeveelheid": {hoeveelheid}, "eenheid": "{eenheid}", "opmerking": {opmerking}}}'

    json_str = re.sub(ing_pattern, compact_ingredient, json_str)

    # Compacteer simpele string arrays (seizoenen, tags) op één regel
    # Match: "key": [\n    "val1",\n    "val2"\n  ]
    def compact_string_array(match: re.Match) -> str:
        key = match.group(1)
        content = match.group(2)
        # Haal alle strings eruit en maak er een compacte array van
        strings = re.findall(r'"([^"]*)"', content)
        if strings:
            items = ", ".join(f'"{s}"' for s in strings)
            return f'"{key}": [{items}]'
        return f'"{key}": []'

    array_pattern = r'"(seizoenen|tags)":\s*\[\s*\n((?:\s*"[^"]*",?\s*\n?)+)\s*\]'
    json_str = re.sub(array_pattern, compact_string_array, json_str)

    return json_str


@dataclass
class BatchResult:
    """Resultaat van een batch verwerking.

    Attributes:
        batch_id: Unieke identifier voor de batch.
        pdf_path: Pad naar de verwerkte PDF.
        output_dir: Directory waar de output is opgeslagen.
        total_pages: Totaal aantal pagina's in de PDF.
        successful: Aantal succesvol geëxtraheerde recepten.
        failed: Aantal mislukte extracties.
        recipes: Lijst van succesvol geëxtraheerde recept dicts.
        errors: Lijst van fouten met pagina info.
    """

    batch_id: str
    pdf_path: Path
    output_dir: Path
    total_pages: int
    successful: int
    failed: int
    recipes: list[dict[str, Any]] = field(default_factory=list)
    errors: list[dict[str, Any]] = field(default_factory=list)


class BatchProcessor:
    """Verwerkt PDF batches met recepten.

    Orchestreert de PDF extractie, Claude API calls, en opslag van drafts.

    Attributes:
        pdf_processor: De PDF processor voor pagina extractie.
        recipe_extractor: De recipe extractor voor AI extractie.
        output_base: Basis directory voor output (standaard data/recipes/draft).
        rate_limit_delay: Delay in seconden tussen API calls.
    """

    def __init__(
        self,
        pdf_processor: PDFProcessor,
        recipe_extractor: RecipeExtractor,
        output_base: Path | None = None,
        rate_limit_delay: float = 1.0,
    ) -> None:
        """Initialiseer de BatchProcessor.

        Args:
            pdf_processor: De PDF processor voor pagina extractie.
            recipe_extractor: De recipe extractor voor AI extractie.
            output_base: Basis directory voor output. Standaard data/recipes/draft.
            rate_limit_delay: Delay in seconden tussen API calls. Standaard 1.0.
        """
        self.pdf_processor = pdf_processor
        self.recipe_extractor = recipe_extractor
        self.output_base = output_base or Path("data/recipes/draft")
        self.rate_limit_delay = rate_limit_delay

    def process(
        self,
        pdf_path: Path,
        batch_id: str | None = None,
        on_progress: ProgressCallback | None = None,
    ) -> BatchResult:
        """Verwerk een PDF batch.

        Args:
            pdf_path: Pad naar de PDF met recepten.
            batch_id: Optionele batch identifier. Als None, wordt afgeleid van PDF naam.
            on_progress: Optionele callback voor voortgang (current, total, recipe_naam).

        Returns:
            BatchResult met verwerking statistieken en geëxtraheerde recepten.
        """
        # Genereer batch_id als niet opgegeven
        if batch_id is None:
            batch_id = self._generate_batch_id(pdf_path)

        # Maak output directory
        output_dir = self.output_base / batch_id
        output_dir.mkdir(parents=True, exist_ok=True)

        # Haal aantal pagina's op
        total_pages = self.pdf_processor.page_count(pdf_path)

        # Initialiseer resultaat tracking
        recipes: list[dict[str, Any]] = []
        errors: list[dict[str, Any]] = []
        manifest_recipes: list[dict[str, Any]] = []

        # Verwerk elke pagina
        first_page = True
        for page_num, image_bytes in self.pdf_processor.extract_all_pages(pdf_path):
            # Rate limiting (niet voor eerste pagina)
            if not first_page:
                time.sleep(self.rate_limit_delay)
            first_page = False

            try:
                # Extraheer recept via Claude API
                recipe_data = self.recipe_extractor.extract(image_bytes)
                recipes.append(recipe_data)

                # Sla recept op als JSON
                recipe_file = self._save_recipe(output_dir, page_num, recipe_data)

                # Progress callback
                recipe_naam = recipe_data.get("naam", "Onbekend")
                if on_progress:
                    on_progress(page_num + 1, total_pages, recipe_naam)

                # Voeg toe aan manifest
                manifest_recipes.append(
                    {
                        "page": page_num,
                        "file": recipe_file.name,
                        "status": "draft",
                        "recipe_id": recipe_data.get("id", "unknown"),
                        "recipe_naam": recipe_naam,
                        "validation_errors": [],
                    }
                )

            except (ValueError, KeyError) as e:
                # Log de fout
                error_info = {
                    "page": page_num,
                    "error": str(e),
                    "error_type": type(e).__name__,
                }
                errors.append(error_info)

                # Progress callback (met None voor mislukte extractie)
                if on_progress:
                    on_progress(page_num + 1, total_pages, None)

                # Voeg mislukte pagina toe aan manifest
                manifest_recipes.append(
                    {
                        "page": page_num,
                        "file": None,
                        "status": "failed",
                        "recipe_id": None,
                        "recipe_naam": None,
                        "validation_errors": [str(e)],
                    }
                )

        # Genereer en sla manifest op
        self._save_manifest(
            output_dir=output_dir,
            batch_id=batch_id,
            pdf_path=pdf_path,
            total_pages=total_pages,
            recipes=manifest_recipes,
        )

        return BatchResult(
            batch_id=batch_id,
            pdf_path=pdf_path,
            output_dir=output_dir,
            total_pages=total_pages,
            successful=len(recipes),
            failed=len(errors),
            recipes=recipes,
            errors=errors,
        )

    def _generate_batch_id(self, pdf_path: Path) -> str:
        """Genereer een batch_id op basis van de PDF naam en timestamp.

        Args:
            pdf_path: Pad naar de PDF.

        Returns:
            Een unieke batch identifier.
        """
        stem = pdf_path.stem.lower().replace(" ", "-")
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        return f"{stem}-{timestamp}"

    def _save_recipe(
        self, output_dir: Path, page_num: int, recipe_data: dict[str, Any]
    ) -> Path:
        """Sla een recept op als JSON bestand.

        Args:
            output_dir: Directory voor opslag.
            page_num: Paginanummer (voor bestandsnaam prefix).
            recipe_data: De recept data.

        Returns:
            Pad naar het opgeslagen bestand.
        """
        recipe_id = recipe_data.get("id", f"recept-pagina-{page_num}")
        filename = f"{page_num + 1:02d}-{recipe_id}.json"
        file_path = output_dir / filename

        file_path.write_text(
            _format_recipe_json(recipe_data),
            encoding="utf-8",
        )

        return file_path

    def _save_manifest(
        self,
        output_dir: Path,
        batch_id: str,
        pdf_path: Path,
        total_pages: int,
        recipes: list[dict[str, Any]],
    ) -> Path:
        """Sla het batch manifest op.

        Args:
            output_dir: Directory voor opslag.
            batch_id: De batch identifier.
            pdf_path: Pad naar de bron PDF.
            total_pages: Totaal aantal pagina's.
            recipes: Lijst van recept info voor manifest.

        Returns:
            Pad naar het manifest bestand.
        """
        manifest = {
            "batch_id": batch_id,
            "pdf_source": str(pdf_path),
            "processed_at": datetime.now().isoformat(),
            "total_pages": total_pages,
            "recipes": recipes,
        }

        manifest_path = output_dir / "_manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        return manifest_path
