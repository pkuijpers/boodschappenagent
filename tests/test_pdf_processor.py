"""Tests voor PDFProcessor."""

from pathlib import Path

import fitz
import pytest

from boodschappenagent.digitizer import PDFProcessor


@pytest.fixture(scope="module")
def tiny_test_pdf(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Maak een minimale test PDF (2 pagina's) voor snelle tests."""
    path = tmp_path_factory.mktemp("data") / "test.pdf"
    doc = fitz.open()
    # Pagina 1
    page1 = doc.new_page(width=100, height=100)
    page1.insert_text((10, 50), "Test pagina 1")
    # Pagina 2
    page2 = doc.new_page(width=100, height=100)
    page2.insert_text((10, 50), "Test pagina 2")
    doc.save(path)
    doc.close()
    return path


class TestPDFProcessor:
    """Tests voor de PDFProcessor class."""

    @pytest.fixture
    def processor(self) -> PDFProcessor:
        """Maak een PDFProcessor instance."""
        return PDFProcessor(dpi=72)  # Lage DPI voor snelle tests

    @pytest.fixture
    def sample_pdf(self, tiny_test_pdf: Path) -> Path:
        """Gebruik de kleine test PDF."""
        return tiny_test_pdf

    def test_init_default_dpi(self) -> None:
        """Test dat default DPI 300 is."""
        processor = PDFProcessor()
        assert processor.dpi == 300

    def test_init_custom_dpi(self) -> None:
        """Test dat custom DPI wordt ingesteld."""
        processor = PDFProcessor(dpi=150)
        assert processor.dpi == 150

    def test_page_count(self, processor: PDFProcessor, sample_pdf: Path) -> None:
        """Test dat page_count het juiste aantal pagina's retourneert."""
        count = processor.page_count(sample_pdf)
        assert count == 2  # De test PDF heeft 2 pagina's

    def test_page_count_file_not_found(self, processor: PDFProcessor) -> None:
        """Test dat FileNotFoundError wordt geworpen voor niet-bestaande PDF."""
        with pytest.raises(FileNotFoundError):
            processor.page_count(Path("niet-bestaand.pdf"))

    def test_extract_page_returns_bytes(
        self, processor: PDFProcessor, sample_pdf: Path
    ) -> None:
        """Test dat extract_page PNG bytes retourneert."""
        image_bytes = processor.extract_page(sample_pdf, page_num=0)
        assert isinstance(image_bytes, bytes)
        assert len(image_bytes) > 0
        # PNG magic bytes
        assert image_bytes[:8] == b"\x89PNG\r\n\x1a\n"

    def test_extract_page_invalid_page_number(
        self, processor: PDFProcessor, sample_pdf: Path
    ) -> None:
        """Test dat IndexError wordt geworpen voor ongeldige pagina."""
        with pytest.raises(IndexError):
            processor.extract_page(sample_pdf, page_num=100)

    def test_extract_page_negative_page_number(
        self, processor: PDFProcessor, sample_pdf: Path
    ) -> None:
        """Test dat IndexError wordt geworpen voor negatieve pagina."""
        with pytest.raises(IndexError):
            processor.extract_page(sample_pdf, page_num=-1)

    def test_extract_all_pages_yields_tuples(
        self, processor: PDFProcessor, sample_pdf: Path
    ) -> None:
        """Test dat extract_all_pages tuples yield met (page_num, bytes)."""
        pages = list(processor.extract_all_pages(sample_pdf))
        assert len(pages) == 2

        for page_num, image_bytes in pages:
            assert isinstance(page_num, int)
            assert isinstance(image_bytes, bytes)
            # PNG magic bytes
            assert image_bytes[:8] == b"\x89PNG\r\n\x1a\n"

    def test_extract_all_pages_sequential_numbers(
        self, processor: PDFProcessor, sample_pdf: Path
    ) -> None:
        """Test dat page numbers sequentieel zijn (0-indexed)."""
        pages = list(processor.extract_all_pages(sample_pdf))
        page_nums = [num for num, _ in pages]
        assert page_nums == list(range(2))
