"""PDF processor voor het extraheren van pagina's als afbeeldingen."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import fitz  # PyMuPDF


class PDFProcessor:
    """Verwerkt PDF bestanden en extraheert pagina's als PNG afbeeldingen.

    Attributes:
        dpi: De resolutie voor image extractie (standaard 300).
    """

    def __init__(self, dpi: int = 300) -> None:
        """Initialiseer de PDFProcessor.

        Args:
            dpi: De resolutie voor image extractie (standaard 300).
        """
        self.dpi = dpi

    def page_count(self, pdf_path: Path) -> int:
        """Retourneer het aantal pagina's in de PDF.

        Args:
            pdf_path: Pad naar het PDF bestand.

        Returns:
            Het aantal pagina's in de PDF.

        Raises:
            FileNotFoundError: Als het bestand niet bestaat.
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF bestand niet gevonden: {pdf_path}")

        with fitz.open(pdf_path) as doc:
            return len(doc)

    def extract_page(self, pdf_path: Path, page_num: int) -> bytes:
        """Extraheer een pagina als PNG afbeelding.

        Args:
            pdf_path: Pad naar het PDF bestand.
            page_num: Het paginanummer (0-indexed).

        Returns:
            De pagina als PNG bytes.

        Raises:
            FileNotFoundError: Als het bestand niet bestaat.
            IndexError: Als het paginanummer ongeldig is.
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF bestand niet gevonden: {pdf_path}")

        if page_num < 0:
            raise IndexError(f"Paginanummer moet >= 0 zijn, kreeg: {page_num}")

        with fitz.open(pdf_path) as doc:
            if page_num >= len(doc):
                raise IndexError(
                    f"Paginanummer {page_num} is ongeldig, "
                    f"PDF heeft {len(doc)} pagina's"
                )

            page = doc[page_num]
            # Bereken zoom factor voor gewenste DPI (72 is standaard PDF DPI)
            zoom = self.dpi / 72
            matrix = fitz.Matrix(zoom, zoom)
            pixmap = page.get_pixmap(matrix=matrix)

            return pixmap.tobytes("png")

    def extract_all_pages(self, pdf_path: Path) -> Iterator[tuple[int, bytes]]:
        """Extraheer alle pagina's als PNG afbeeldingen.

        Args:
            pdf_path: Pad naar het PDF bestand.

        Yields:
            Tuples van (paginanummer, PNG bytes) voor elke pagina.

        Raises:
            FileNotFoundError: Als het bestand niet bestaat.
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF bestand niet gevonden: {pdf_path}")

        with fitz.open(pdf_path) as doc:
            zoom = self.dpi / 72
            matrix = fitz.Matrix(zoom, zoom)

            for page_num in range(len(doc)):
                page = doc[page_num]
                pixmap = page.get_pixmap(matrix=matrix)
                yield page_num, pixmap.tobytes("png")
