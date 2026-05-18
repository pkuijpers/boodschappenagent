"""AH integratie: koppelt boodschappenlijst aan Albert Heijn API."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from boodschappenagent.ah.client import AHClient
from boodschappenagent.ah.models import Product
from boodschappenagent.ah.quantity_calculator import bereken_aantal
from boodschappenagent.boodschappenlijst.models import (
    Boodschappenlijst,
    BoodschappenRegel,
)

if TYPE_CHECKING:
    from boodschappenagent.ah.preferences import MatchVoorkeurenRepository

# Vertaling van AHClient smart_search bronnen naar Nederlandse termen
_BRON_VERTALING = {
    "reference": "referentie",
    "search": "zoekopdracht",
    "not_found": "niet_gevonden",
}

DEFAULT_REFERENTIE_LIJST_NAAM = "boodschappen"
VOORRAAD_LIJST_NAAM = "Voorraad"


@dataclass(frozen=True)
class ProductMatch:
    """Resultaat van het matchen van een boodschappenregel aan een AH product.

    Attributes:
        regel: De originele boodschappenregel.
        product: Het gematchte AH product, of None.
        bron: Waar het product gevonden is: "referentie", "zoekopdracht",
              of "niet_gevonden".
    """

    regel: Any  # BoodschappenRegel (Any om circulaire import te vermijden)
    product: Product | None
    bron: str
    aantal: int = 1

    @property
    def gevonden(self) -> bool:
        """Of er een product gevonden is."""
        return self.product is not None


@dataclass(frozen=True)
class SyncResultaat:
    """Resultaat van het synchroniseren van een boodschappenlijst naar AH.

    Attributes:
        lijst_id: ID van de aangemaakte AH lijst.
        lijst_naam: Naam van de AH lijst.
        matches: Alle match-resultaten.
    """

    lijst_id: str
    lijst_naam: str
    matches: list[ProductMatch] = field(default_factory=list)

    @property
    def gevonden(self) -> list[ProductMatch]:
        """Alle matches waar een product gevonden is."""
        return [m for m in self.matches if m.gevonden]

    @property
    def niet_gevonden(self) -> list[ProductMatch]:
        """Alle matches waar geen product gevonden is."""
        return [m for m in self.matches if not m.gevonden]

    @property
    def samenvatting(self) -> dict[str, int]:
        """Samenvatting met aantallen."""
        return {
            "totaal": len(self.matches),
            "gevonden": len(self.gevonden),
            "niet_gevonden": len(self.niet_gevonden),
        }


class AHIntegratie:
    """Koppelt een boodschappenlijst aan de Albert Heijn API.

    Zoekt producten, maakt een AH favorieten-lijst aan,
    en voegt gevonden producten toe.
    """

    VOORRAAD_LIJST_NAAM = VOORRAAD_LIJST_NAAM

    def __init__(self, client: AHClient) -> None:
        self._client = client

    def zoek_producten(
        self,
        lijst: Boodschappenlijst,
        referentie_lijst_id: str | None = None,
        voorkeuren_repo: MatchVoorkeurenRepository | None = None,
    ) -> list[ProductMatch]:
        """Zoek AH producten voor alle regels op de boodschappenlijst.

        Past opgeslagen product-voorkeuren toe vóór smart_search.

        Args:
            lijst: De boodschappenlijst om te matchen.
            referentie_lijst_id: Optioneel ID van een bestaande AH lijst
                om als referentie te gebruiken (snellere matching).
            voorkeuren_repo: Optionele repository met opgeslagen product-
                voorkeuren per ingredientnaam.

        Returns:
            Lijst van ProductMatch resultaten, een per boodschappenregel.
        """
        # Laad referentie-producten eenmalig
        reference_products = None
        if referentie_lijst_id:
            ref_list = self._client.get_list_with_products(referentie_lijst_id)
            reference_products = ref_list.products
        else:
            # Auto-detect "boodschappen" lijst
            found = self._client.find_list_by_name(DEFAULT_REFERENTIE_LIJST_NAAM)
            if found:
                ref_list = self._client.get_list_with_products(found.id)
                reference_products = ref_list.products

        matches = []
        for regel in lijst.regels:
            product, bron = self._zoek_met_voorkeur(
                regel, reference_products, voorkeuren_repo
            )
            aantal = bereken_aantal(regel, product) if product else 1
            matches.append(
                ProductMatch(
                    regel=regel,
                    product=product,
                    bron=bron,
                    aantal=aantal,
                )
            )

        return matches

    def _zoek_met_voorkeur(
        self,
        regel: Any,
        reference_products: list[Product] | None,
        voorkeuren_repo: MatchVoorkeurenRepository | None,
    ) -> tuple[Product | None, str]:
        """Zoek product voor één regel, met voorkeur-lookup als eerste stap."""
        if voorkeuren_repo is not None:
            voorkeur = voorkeuren_repo.get(regel.naam)
            if voorkeur is not None:
                # Controleer of het voorkeurs-product nog besteld kan worden
                zoekresultaten = self._client.search_products(regel.naam)
                voorkeur_product = next(
                    (p for p in zoekresultaten if p.id == voorkeur.article_id),
                    None,
                )
                if voorkeur_product is not None and voorkeur_product.is_orderable:
                    return voorkeur_product, "voorkeur"
                # Voorkeur niet (meer) beschikbaar — gebruik smart_search als fallback
                product, bron_raw = self._client.smart_search(
                    regel.naam,
                    reference_products=reference_products,
                )
                return product, "voorkeur_niet_beschikbaar"

        # Geen voorkeur of geen repo — standaard smart_search
        product, bron_raw = self._client.smart_search(
            regel.naam,
            reference_products=reference_products,
        )
        return product, _BRON_VERTALING.get(bron_raw, bron_raw)

    def create_list(self, naam: str) -> str:
        """Maak een nieuwe AH favorieten-lijst aan en geef het ID terug."""
        return self._client.create_list(naam)

    def add_products_to_list(
        self,
        lijst_id: str,
        producten: list[tuple[int, int]],
    ) -> None:
        """Voeg producten toe aan een AH favorieten-lijst."""
        self._client.add_products_to_list(lijst_id, producten)

    def zoek_producten_voor_correctie(
        self, query: str, limit: int = 10
    ) -> list[Product]:
        """Zoek producten voor de correctie-flow (productmatch review)."""
        return self._client.search_products(query)[:limit]

    def kies_product_voor_regel(
        self, regel: BoodschappenRegel, product: Product
    ) -> ProductMatch:
        """Bereken ProductMatch voor een handmatig gekozen product."""
        aantal = bereken_aantal(regel, product)
        return ProductMatch(
            regel=regel, product=product, bron="zoekopdracht", aantal=aantal
        )

    def haal_voorraad_producten(self) -> list[Product]:
        """Haal producten op uit de AH 'Voorraad' favorietenlijst."""
        lijst = self._client.find_list_by_name(self.VOORRAAD_LIJST_NAAM)
        if lijst is None:
            return []
        met_producten = self._client.get_list_with_products(lijst.id)
        return met_producten.products or []

    def sync_naar_lijst(
        self,
        lijst: Boodschappenlijst,
        lijst_naam: str | None = None,
        referentie_lijst_id: str | None = None,
    ) -> SyncResultaat:
        """Synchroniseer een boodschappenlijst naar een AH favorieten-lijst.

        Maakt een nieuwe AH lijst aan, zoekt producten, en voegt
        gevonden producten toe.

        Args:
            lijst: De boodschappenlijst om te synchroniseren.
            lijst_naam: Naam voor de AH lijst. Default: "Boodschappen {week_start}".
            referentie_lijst_id: Optioneel ID van een referentielijst.

        Returns:
            SyncResultaat met alle match-resultaten en lijst-info.
        """
        naam = lijst_naam or f"Boodschappen {lijst.week_start}"
        lijst_id = self._client.create_list(naam)

        matches = self.zoek_producten(lijst, referentie_lijst_id=referentie_lijst_id)

        # Voeg alleen gevonden producten toe, dedupliceer op product ID
        product_quantities: dict[int, int] = {}
        for m in matches:
            if m.gevonden:
                product_quantities[m.product.id] = (
                    product_quantities.get(m.product.id, 0) + m.aantal
                )
        gevonden = list(product_quantities.items())
        if gevonden:
            self._client.add_products_to_list(lijst_id, gevonden)

        return SyncResultaat(
            lijst_id=lijst_id,
            lijst_naam=naam,
            matches=matches,
        )
