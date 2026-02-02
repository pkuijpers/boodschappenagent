"""Enums voor recepten: Seizoen en Categorie."""

from enum import Enum


class Seizoen(Enum):
    """Seizoenen voor recepten."""

    LENTE = "lente"
    ZOMER = "zomer"
    HERFST = "herfst"
    WINTER = "winter"
    ALLE = "alle"


class Categorie(Enum):
    """Categorieën voor recepten."""

    PASTA = "pasta"
    OVENSCHOTEL = "ovenschotel"
    SOEP = "soep"
    STAMPPOT = "stamppot"
    ROERBAK = "roerbak"
    SALADE = "salade"
    OVERIG = "overig"
