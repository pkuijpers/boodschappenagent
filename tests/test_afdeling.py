"""Unit tests voor ah/afdeling.py — Afdeling enum en categorie_naar_afdeling()."""

import pytest

from boodschappenagent.ah.afdeling import Afdeling, categorie_naar_afdeling


@pytest.mark.parametrize(
    "category, verwacht",
    [
        # Koelkast
        ("Zuivel, eieren", Afdeling.KOELKAST),
        ("Vlees", Afdeling.KOELKAST),
        ("Vleeswaren", Afdeling.KOELKAST),
        ("Vis", Afdeling.KOELKAST),
        ("Kaas", Afdeling.KOELKAST),
        ("Maaltijden, salades", Afdeling.KOELKAST),
        ("Vegetarisch, vegan en plantaardig", Afdeling.KOELKAST),
        # Diepvries
        ("Diepvries", Afdeling.DIEPVRIES),
        # Voorraadkast
        ("Groente, aardappelen", Afdeling.VOORRAADKAST),
        ("Pasta, rijst, wereldkeuken", Afdeling.VOORRAADKAST),
        ("Soepen, sauzen, kruiden, olie", Afdeling.VOORRAADKAST),
        ("Borrel, chips, snacks", Afdeling.VOORRAADKAST),
        # Overig / fallback
        ("", Afdeling.OVERIG),
        ("Onbekende categorie XYZ", Afdeling.OVERIG),
        # Hiërarchisch formaat — hoofd wordt geëxtraheerd vóór de slash
        ("Zuivel, eieren/Halfvolle melk", Afdeling.KOELKAST),
        ("Diepvries/Sperziebonen (diepvries)", Afdeling.DIEPVRIES),
    ],
)
def test_categorie_naar_afdeling(category: str, verwacht: Afdeling) -> None:
    """categorie_naar_afdeling() mapt elke AH-hoofdcategorie naar de juiste afdeling."""
    assert categorie_naar_afdeling(category) == verwacht
