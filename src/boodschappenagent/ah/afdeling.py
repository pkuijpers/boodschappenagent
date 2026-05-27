"""AH-afdeling mapping — domeinmodule voor winkellocatie-indeling."""

from enum import Enum


class Afdeling(str, Enum):
    """Winkellocatie van een AH-product."""

    KOELKAST = "Koelkast"
    VOORRAADKAST = "Voorraadkast"
    DIEPVRIES = "Diepvries"
    OVERIG = "Overig"


AFDELING_VOLGORDE: dict[Afdeling, int] = {
    Afdeling.KOELKAST: 1,
    Afdeling.VOORRAADKAST: 2,
    Afdeling.DIEPVRIES: 3,
    Afdeling.OVERIG: 4,
}

_HOOFD_CATEGORIE_NAAR_AFDELING: dict[str, Afdeling] = {
    # Koelkast
    "Zuivel, eieren": Afdeling.KOELKAST,
    "Vlees": Afdeling.KOELKAST,
    "Vleeswaren": Afdeling.KOELKAST,
    "Vis": Afdeling.KOELKAST,
    "Kaas": Afdeling.KOELKAST,
    "Maaltijden, salades": Afdeling.KOELKAST,
    "Vegetarisch, vegan en plantaardig": Afdeling.KOELKAST,
    # Diepvries
    "Diepvries": Afdeling.DIEPVRIES,
    # Voorraadkast
    "Groente, aardappelen": Afdeling.VOORRAADKAST,
    "Fruit, verse sappen": Afdeling.VOORRAADKAST,
    "Pasta, rijst, wereldkeuken": Afdeling.VOORRAADKAST,
    "Soepen, sauzen, kruiden, olie": Afdeling.VOORRAADKAST,
    "Borrel, chips, snacks": Afdeling.VOORRAADKAST,
    "Ontbijtgranen, beleg": Afdeling.VOORRAADKAST,
    "Bakkerij": Afdeling.VOORRAADKAST,
    "Dranken": Afdeling.VOORRAADKAST,
    "Wijn, bier en gedestilleerd": Afdeling.VOORRAADKAST,
    "Thee, koffie en cacao": Afdeling.VOORRAADKAST,
    "Snoep en koek": Afdeling.VOORRAADKAST,
    "Baby en kind": Afdeling.VOORRAADKAST,
    # Overig (non-food)
    "Drogisterij en gezondheid": Afdeling.OVERIG,
    "Huishouden": Afdeling.OVERIG,
    "Bloemen en planten": Afdeling.OVERIG,
}


def categorie_naar_afdeling(category: str) -> Afdeling:
    """Geef de winkellocatie (Afdeling) voor een AH-productcategorie.

    Accepteert zowel 'HoofdCategorie' als 'HoofdCategorie/SubCategorie' formaat.
    Lege of onbekende categorieën mappen naar Afdeling.OVERIG.
    """
    if not category or not category.strip():
        return Afdeling.OVERIG
    hoofd = category.split("/")[0].strip()
    return _HOOFD_CATEGORIE_NAAR_AFDELING.get(hoofd, Afdeling.OVERIG)
