"""Enums voor recepten: Seizoen, Categorie en Basis."""

from enum import Enum


class Seizoen(Enum):
    """Seizoenen voor recepten."""

    LENTE = "lente"
    ZOMER = "zomer"
    HERFST = "herfst"
    WINTER = "winter"
    ALLE = "alle"


class Categorie(Enum):
    """Categorieën voor recepten op basis van proteïnebron."""

    VLEES = "vlees"  # rund, varken, lam
    GEVOGELTE = "gevogelte"  # kip, kalkoen, eend
    VIS = "vis"  # vis & zeevruchten
    VEGETARISCH = "vegetarisch"  # eieren, kaas, tofu
    VEGANISTISCH = "veganistisch"  # plantaardig


class Basis(Enum):
    """Koolhydraatbasis voor recepten."""

    PASTA = "pasta"  # spaghetti, penne, noedels
    RIJST = "rijst"  # basmati, risotto
    AARDAPPEL = "aardappel"  # gekookt, puree, friet
    BROOD = "brood"  # brood, deeg, wraps
    GEEN = "geen"  # salades, soepen zonder koolhydraat
