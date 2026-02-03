"""Recipe extractor: afbeeldingen naar recept data via Claude API."""

from __future__ import annotations

import base64
import json
import re

from anthropic import Anthropic


class RecipeExtractor:
    """Extraheert recept data uit afbeeldingen via Claude Vision API.

    Attributes:
        client: De Anthropic API client.
        model: Het te gebruiken Claude model.
    """

    # Claude Sonnet model - goede balans tussen kwaliteit en kosten
    DEFAULT_MODEL = "claude-sonnet-4-20250514"

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        """Initialiseer de RecipeExtractor.

        Args:
            api_key: Optionele API key. Als None, wordt ANTHROPIC_API_KEY gebruikt.
            model: Optioneel model om te gebruiken. Standaard claude-sonnet-4-20250514.
        """
        self.client = Anthropic(api_key=api_key)
        self.model = model or self.DEFAULT_MODEL

    def extract(self, image_bytes: bytes) -> dict:
        """Extraheer recept data uit een afbeelding.

        Args:
            image_bytes: De afbeelding als PNG bytes.

        Returns:
            Een dict met recept data (nog niet gevalideerd tegen Recipe model).

        Raises:
            ValueError: Als de API response geen geldige JSON bevat.
        """
        image_data = base64.standard_b64encode(image_bytes).decode("utf-8")

        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_data,
                            },
                        },
                        {
                            "type": "text",
                            "text": self._build_prompt(),
                        },
                    ],
                }
            ],
        )

        # Haal de tekst uit de response
        response_text = response.content[0].text

        return self._parse_response(response_text)

    def _build_prompt(self) -> str:
        """Bouw de extractie prompt met format instructies.

        Returns:
            De volledige prompt string.
        """
        return """Analyseer deze foto van een recept en extraheer de informatie.

Output: JSON formaat.

Gebruik exact dit formaat:
{
  "id": "recept-naam-als-slug",
  "naam": "Volledige Receptnaam",
  "categorie": "vlees|gevogelte|vis|vegetarisch|veganistisch",
  "basis": "pasta|rijst|aardappel|brood|geen",
  "seizoenen": ["lente", "zomer", "herfst", "winter", "alle"],
  "basis_porties": 2,
  "ingredienten": [
    {"naam": "ingredientnaam", "hoeveelheid": 100, "eenheid": "gram", "opmerking": null}
  ],
  "tags": ["tag1", "tag2"],
  "bereidingstijd_min": 30,
  "bereidingswijze": "Bereidingsinstructies...",
  "bron": null
}

Regels:
- id: lowercase, geen spaties, koppeltekens als scheidingsteken (slug format)
- seizoenen: kies uit lente, zomer, herfst, winter, of alle (als het jaarrond kan)
- categorie: kies op basis van hoofdeiwit:
  vlees (rund/varken/lam), gevogelte (kip/kalkoen),
  vis (zeevruchten), vegetarisch (eieren/kaas), veganistisch
- basis: ALTIJD invullen met de belangrijkste koolhydraatbron:
  pasta (ook noedels), rijst, aardappel, brood (ook tortillas, wraps, pitabrood), geen
- bereidingstijd_min: schat in minuten als niet aangegeven
- opmerking bij ingredient: alleen als er relevante info is (bijv. "fijngesneden")

Hoeveelheden:
- Reken ALTIJD om naar gram wanneer gewicht bekend is
- Voorbeelden:
  "1 stukje cheddar (60 g)" => hoeveelheid: 60, eenheid: "gram"
  "2 schalen kipreepjes (à 150 g)" => hoeveelheid: 300, eenheid: "gram"
  "1 blik tomaten (400 g)" => hoeveelheid: 400, eenheid: "gram"
- Toegestane eenheden: gram, ml, stuks, eetlepel, theelepel, teen, snuf, naar smaak
- Gebruik alleen stuks/eetlepel/etc. als er GEEN gewicht vermeld staat

Retourneer ALLEEN valide JSON, geen andere tekst of uitleg."""

    def _parse_response(self, response_text: str) -> dict:
        """Parse de API response naar een dict.

        Args:
            response_text: De ruwe tekst van de API response.

        Returns:
            De geparsde JSON als dict.

        Raises:
            ValueError: Als de response geen geldige JSON bevat.
        """
        # Probeer eerst directe JSON parsing
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass

        # Probeer JSON uit markdown code block te halen
        # Patronen: ```json ... ``` of ``` ... ```
        patterns = [
            r"```json\s*(.*?)\s*```",
            r"```\s*(.*?)\s*```",
        ]

        for pattern in patterns:
            match = re.search(pattern, response_text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    continue

        # Geen geldige JSON gevonden
        preview = response_text[:200]
        msg = f"Kon geen geldige JSON extraheren uit API response: {preview}"
        raise ValueError(msg)
