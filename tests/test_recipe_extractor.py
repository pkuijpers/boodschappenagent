"""Tests voor RecipeExtractor."""

import base64
import json
from unittest.mock import MagicMock, patch

import pytest

from boodschappenagent.digitizer.recipe_extractor import RecipeExtractor


class TestRecipeExtractor:
    """Tests voor de RecipeExtractor class."""

    @pytest.fixture
    def extractor(self) -> RecipeExtractor:
        """Maak een RecipeExtractor instance met mock API key."""
        return RecipeExtractor(api_key="test-api-key")

    @pytest.fixture
    def sample_image_bytes(self) -> bytes:
        """Minimale PNG bytes voor testing."""
        # 1x1 pixel transparante PNG
        return base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4"
            "nGNgYGBgAAAABQABpfZFQAAAAABJRU5ErkJggg=="
        )

    @pytest.fixture
    def sample_recipe_response(self) -> dict:
        """Voorbeeld recept response van Claude API."""
        return {
            "id": "spaghetti-bolognese",
            "naam": "Spaghetti Bolognese",
            "categorie": "vlees",
            "basis": "pasta",
            "seizoenen": ["alle"],
            "basis_porties": 2,
            "ingredienten": [
                {
                    "naam": "spaghetti",
                    "hoeveelheid": 200,
                    "eenheid": "gram",
                    "opmerking": None,
                },
                {
                    "naam": "rundergehakt",
                    "hoeveelheid": 250,
                    "eenheid": "gram",
                    "opmerking": None,
                },
            ],
            "tags": ["italiaans", "budget"],
            "bereidingstijd_min": 35,
            "bereidingswijze": "1. Kook de spaghetti...",
            "bron": None,
        }

    def test_init_with_api_key(self) -> None:
        """Test dat API key wordt doorgegeven aan client."""
        with patch("boodschappenagent.digitizer.recipe_extractor.Anthropic") as mock:
            RecipeExtractor(api_key="test-key")
            mock.assert_called_once_with(api_key="test-key")

    def test_init_without_api_key_uses_env(self) -> None:
        """Test dat zonder API key de environment variable wordt gebruikt."""
        with patch("boodschappenagent.digitizer.recipe_extractor.Anthropic") as mock:
            RecipeExtractor()
            mock.assert_called_once_with(api_key=None)

    def test_build_prompt_contains_format_instructions(
        self, extractor: RecipeExtractor
    ) -> None:
        """Test dat de prompt format instructies bevat."""
        prompt = extractor._build_prompt()

        # Check voor belangrijke instructies
        assert "JSON" in prompt
        assert "categorie" in prompt
        assert "vlees" in prompt
        assert "gevogelte" in prompt
        assert "vis" in prompt
        assert "vegetarisch" in prompt
        assert "veganistisch" in prompt
        assert "basis" in prompt
        assert "pasta" in prompt
        assert "seizoenen" in prompt
        assert "slug" in prompt.lower() or "lowercase" in prompt.lower()

    def test_extract_returns_dict(
        self,
        extractor: RecipeExtractor,
        sample_image_bytes: bytes,
        sample_recipe_response: dict,
    ) -> None:
        """Test dat extract een dict retourneert."""
        # Mock de API response
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps(sample_recipe_response))]
        extractor.client.messages.create = MagicMock(return_value=mock_response)

        result = extractor.extract(sample_image_bytes)

        assert isinstance(result, dict)
        assert result["id"] == "spaghetti-bolognese"
        assert result["naam"] == "Spaghetti Bolognese"

    def test_extract_sends_image_to_api(
        self,
        extractor: RecipeExtractor,
        sample_image_bytes: bytes,
        sample_recipe_response: dict,
    ) -> None:
        """Test dat de image correct naar de API wordt gestuurd."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps(sample_recipe_response))]
        extractor.client.messages.create = MagicMock(return_value=mock_response)

        extractor.extract(sample_image_bytes)

        # Controleer dat create werd aangeroepen met image data
        call_args = extractor.client.messages.create.call_args
        messages = call_args.kwargs["messages"]
        assert len(messages) == 1
        assert messages[0]["role"] == "user"

        # Check image content
        content = messages[0]["content"]
        image_block = next((c for c in content if c.get("type") == "image"), None)
        assert image_block is not None
        assert image_block["source"]["type"] == "base64"
        assert image_block["source"]["media_type"] == "image/png"

    def test_extract_handles_json_in_markdown_block(
        self,
        extractor: RecipeExtractor,
        sample_image_bytes: bytes,
        sample_recipe_response: dict,
    ) -> None:
        """Test dat JSON in markdown code block correct wordt geparsed."""
        # Claude kan JSON in markdown block retourneren
        json_in_markdown = f"```json\n{json.dumps(sample_recipe_response)}\n```"

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json_in_markdown)]
        extractor.client.messages.create = MagicMock(return_value=mock_response)

        result = extractor.extract(sample_image_bytes)

        assert result["id"] == "spaghetti-bolognese"

    def test_extract_raises_on_invalid_json(
        self, extractor: RecipeExtractor, sample_image_bytes: bytes
    ) -> None:
        """Test dat ValueError wordt geworpen bij ongeldige JSON."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Dit is geen JSON")]
        extractor.client.messages.create = MagicMock(return_value=mock_response)

        with pytest.raises(ValueError, match="JSON"):
            extractor.extract(sample_image_bytes)

    def test_extract_uses_correct_model(
        self,
        extractor: RecipeExtractor,
        sample_image_bytes: bytes,
        sample_recipe_response: dict,
    ) -> None:
        """Test dat het juiste Claude model wordt gebruikt."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps(sample_recipe_response))]
        extractor.client.messages.create = MagicMock(return_value=mock_response)

        extractor.extract(sample_image_bytes)

        call_args = extractor.client.messages.create.call_args
        # Controleer dat een Sonnet model wordt gebruikt (goede balans prijs/kwaliteit)
        assert "claude" in call_args.kwargs["model"]
