"""Tests voor BatchProcessor."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from boodschappenagent.digitizer.batch_processor import BatchProcessor, BatchResult
from boodschappenagent.digitizer.pdf_processor import PDFProcessor
from boodschappenagent.digitizer.recipe_extractor import RecipeExtractor


class TestBatchResult:
    """Tests voor BatchResult dataclass."""

    def test_batch_result_creation(self, tmp_path: Path) -> None:
        """Test dat BatchResult correct wordt aangemaakt."""
        result = BatchResult(
            batch_id="test-batch",
            pdf_path=Path("test.pdf"),
            output_dir=tmp_path,
            total_pages=10,
            successful=8,
            failed=2,
            recipes=[{"id": "recept-1"}],
            errors=[{"page": 3, "error": "Parse error"}],
        )

        assert result.batch_id == "test-batch"
        assert result.total_pages == 10
        assert result.successful == 8
        assert result.failed == 2


class TestBatchProcessor:
    """Tests voor de BatchProcessor class."""

    @pytest.fixture
    def mock_pdf_processor(self) -> MagicMock:
        """Mock PDFProcessor."""
        processor = MagicMock(spec=PDFProcessor)
        processor.page_count.return_value = 2
        processor.extract_all_pages.return_value = iter(
            [
                (0, b"fake-png-1"),
                (1, b"fake-png-2"),
            ]
        )
        return processor

    @pytest.fixture
    def mock_recipe_extractor(self) -> MagicMock:
        """Mock RecipeExtractor."""
        extractor = MagicMock(spec=RecipeExtractor)
        extractor.extract.side_effect = [
            {
                "id": "recept-een",
                "naam": "Recept Een",
                "categorie": "vlees",
                "basis": "pasta",
                "seizoenen": ["alle"],
                "basis_porties": 2,
                "ingredienten": [],
                "tags": [],
                "bereidingstijd_min": 30,
                "bereidingswijze": None,
                "bron": None,
            },
            {
                "id": "recept-twee",
                "naam": "Recept Twee",
                "categorie": "vis",
                "basis": "rijst",
                "seizoenen": ["zomer"],
                "basis_porties": 4,
                "ingredienten": [],
                "tags": [],
                "bereidingstijd_min": 45,
                "bereidingswijze": None,
                "bron": None,
            },
        ]
        return extractor

    @pytest.fixture
    def processor(
        self,
        mock_pdf_processor: MagicMock,
        mock_recipe_extractor: MagicMock,
        tmp_path: Path,
    ) -> BatchProcessor:
        """Maak een BatchProcessor met mocks."""
        return BatchProcessor(
            pdf_processor=mock_pdf_processor,
            recipe_extractor=mock_recipe_extractor,
            output_base=tmp_path,
            rate_limit_delay=0,
        )

    def test_init(
        self,
        mock_pdf_processor: MagicMock,
        mock_recipe_extractor: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test BatchProcessor initialisatie."""
        processor = BatchProcessor(
            pdf_processor=mock_pdf_processor,
            recipe_extractor=mock_recipe_extractor,
            output_base=tmp_path,
        )

        assert processor.pdf_processor is mock_pdf_processor
        assert processor.recipe_extractor is mock_recipe_extractor
        assert processor.output_base == tmp_path

    def test_process_creates_batch_directory(
        self, processor: BatchProcessor, tmp_path: Path
    ) -> None:
        """Test dat process de batch directory aanmaakt."""
        result = processor.process(Path("test.pdf"), batch_id="my-batch")

        batch_dir = tmp_path / "my-batch"
        assert batch_dir.exists()
        assert result.output_dir == batch_dir

    def test_process_auto_generates_batch_id(self, processor: BatchProcessor) -> None:
        """Test dat een batch_id wordt gegenereerd als niet opgegeven."""
        result = processor.process(Path("test.pdf"))

        # Batch ID moet gebaseerd zijn op PDF naam
        assert "test" in result.batch_id

    def test_process_extracts_all_pages(
        self, processor: BatchProcessor, mock_pdf_processor: MagicMock
    ) -> None:
        """Test dat alle pagina's worden geëxtraheerd."""
        processor.process(Path("test.pdf"), batch_id="test")

        mock_pdf_processor.extract_all_pages.assert_called_once_with(Path("test.pdf"))

    def test_process_calls_extractor_for_each_page(
        self,
        processor: BatchProcessor,
        mock_recipe_extractor: MagicMock,
    ) -> None:
        """Test dat de extractor voor elke pagina wordt aangeroepen."""
        processor.process(Path("test.pdf"), batch_id="test")

        assert mock_recipe_extractor.extract.call_count == 2

    def test_process_saves_recipe_files(
        self, processor: BatchProcessor, tmp_path: Path
    ) -> None:
        """Test dat recept bestanden worden opgeslagen."""
        processor.process(Path("test.pdf"), batch_id="test")

        # Check dat JSON bestanden zijn aangemaakt
        batch_dir = tmp_path / "test"
        json_files = list(batch_dir.glob("*.json"))

        # 2 recepten + 1 manifest
        assert len(json_files) == 3

    def test_process_creates_manifest(
        self, processor: BatchProcessor, tmp_path: Path
    ) -> None:
        """Test dat een manifest bestand wordt aangemaakt."""
        processor.process(Path("test.pdf"), batch_id="test")

        manifest_path = tmp_path / "test" / "_manifest.json"
        assert manifest_path.exists()

        manifest = json.loads(manifest_path.read_text())
        assert manifest["batch_id"] == "test"
        assert manifest["total_pages"] == 2
        assert len(manifest["recipes"]) == 2

    def test_process_returns_batch_result(self, processor: BatchProcessor) -> None:
        """Test dat process een BatchResult retourneert."""
        result = processor.process(Path("test.pdf"), batch_id="test")

        assert isinstance(result, BatchResult)
        assert result.batch_id == "test"
        assert result.total_pages == 2
        assert result.successful == 2
        assert result.failed == 0
        assert len(result.recipes) == 2

    def test_process_handles_extraction_error(
        self,
        mock_pdf_processor: MagicMock,
        mock_recipe_extractor: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test dat extractie fouten correct worden afgehandeld."""
        # Eerste succesvol, tweede faalt
        mock_recipe_extractor.extract.side_effect = [
            {
                "id": "recept-een",
                "naam": "Recept Een",
                "categorie": "vlees",
                "basis": "pasta",
                "seizoenen": ["alle"],
                "basis_porties": 2,
                "ingredienten": [],
                "tags": [],
                "bereidingstijd_min": 30,
                "bereidingswijze": None,
                "bron": None,
            },
            ValueError("Kon geen JSON parsen"),
        ]

        processor = BatchProcessor(
            pdf_processor=mock_pdf_processor,
            recipe_extractor=mock_recipe_extractor,
            output_base=tmp_path,
            rate_limit_delay=0,
        )

        result = processor.process(Path("test.pdf"), batch_id="test")

        assert result.successful == 1
        assert result.failed == 1
        assert len(result.errors) == 1
        assert result.errors[0]["page"] == 1

    def test_process_with_rate_limit_delay(
        self,
        mock_pdf_processor: MagicMock,
        mock_recipe_extractor: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test dat rate limiting werkt."""
        mock_recipe_extractor.extract.side_effect = [
            {
                "id": "recept-een",
                "naam": "Recept Een",
                "categorie": "vlees",
                "basis": "pasta",
                "seizoenen": ["alle"],
                "basis_porties": 2,
                "ingredienten": [],
                "tags": [],
                "bereidingstijd_min": 30,
                "bereidingswijze": None,
                "bron": None,
            },
            {
                "id": "recept-twee",
                "naam": "Recept Twee",
                "categorie": "vis",
                "basis": "rijst",
                "seizoenen": ["zomer"],
                "basis_porties": 4,
                "ingredienten": [],
                "tags": [],
                "bereidingstijd_min": 45,
                "bereidingswijze": None,
                "bron": None,
            },
        ]

        processor = BatchProcessor(
            pdf_processor=mock_pdf_processor,
            recipe_extractor=mock_recipe_extractor,
            output_base=tmp_path,
            rate_limit_delay=0.1,  # Korte delay voor test
        )

        with patch("time.sleep") as mock_sleep:
            processor.process(Path("test.pdf"), batch_id="test")
            # Sleep wordt aangeroepen tussen pagina's (dus 1x voor 2 pagina's)
            assert mock_sleep.call_count == 1

    def test_manifest_contains_recipe_status(
        self, processor: BatchProcessor, tmp_path: Path
    ) -> None:
        """Test dat manifest status per recept bevat."""
        processor.process(Path("test.pdf"), batch_id="test")

        manifest_path = tmp_path / "test" / "_manifest.json"
        manifest = json.loads(manifest_path.read_text())

        for recipe in manifest["recipes"]:
            assert "status" in recipe
            assert recipe["status"] == "draft"
            assert "page" in recipe
            assert "file" in recipe
            assert "recipe_id" in recipe
            assert "recipe_naam" in recipe
