"""
Test script: Voeg 10 testproducten toe aan TestAI lijstje.

Gebruikt smart search: eerst checken of product in 'boodschappen' lijst staat,
anders vallen we terug op API search.
"""

from boodschappenagent import AHClient, Product

# TestAI lijst ID (doel)
TEST_LIST_ID = "65eedcca-01e6-4bce-800f-1ec811970cc1"

# Boodschappen lijst ID (referentie voor bestaande producten)
BOODSCHAPPEN_LIST_ID = "bcfcc918-7e08-4cc1-be9e-e89aa3840f6a"

# Testset producten met zoektermen
# NOTE: Zoektermen zijn geoptimaliseerd na eerste test
TEST_PRODUCTS = [
    {
        "ingredient": "Halfvolle melk 1L",
        "search": "halfvolle melk",
        "target_size": "1 l",
    },
    {
        "ingredient": "Scharrelei 10 stuks",
        "search": "scharreleieren 10",
        "target_size": "10",
    },
    {"ingredient": "Rundergehakt 500g", "search": "rundergehakt", "target_size": "500"},
    {
        "ingredient": "Verse spinazie 250g",
        "search": "verse spinazie",
        "target_size": "250",
    },
    {
        "ingredient": "Knoflook",
        "search": "knoflook",
        "target_size": None,
    },  # "knoflook vers" gaf olijven
    {
        "ingredient": "Parmezaanse kaas",
        "search": "parmigiano reggiano",
        "target_size": None,
    },
    {"ingredient": "Spaghetti 500g", "search": "spaghetti", "target_size": "500"},
    {"ingredient": "Passata 700ml", "search": "passata", "target_size": "700"},
    {"ingredient": "Verse basilicum", "search": "verse basilicum", "target_size": None},
    {"ingredient": "Pancetta 100g", "search": "pancetta", "target_size": "100"},
]


def select_best_product(
    products: list[Product], target_size: str | None
) -> Product | None:
    """
    Selecteer het beste product uit de zoekresultaten.

    Strategie:
    1. Filter op bestelbaar
    2. Prefereer AH huismerk (goedkoper)
    3. Match op grootte indien opgegeven
    4. Neem eerste resultaat als fallback
    """
    if not products:
        return None

    # Filter alleen bestelbare producten
    orderable = [p for p in products if p.is_orderable]
    if not orderable:
        orderable = products  # Fallback naar alle producten

    # Als target_size opgegeven, probeer te matchen
    if target_size:
        size_matches = [p for p in orderable if target_size.lower() in p.size.lower()]
        if size_matches:
            orderable = size_matches

    # Prefereer AH huismerk
    ah_products = [p for p in orderable if p.brand.upper() == "AH"]
    if ah_products:
        return ah_products[0]

    # Anders eerste resultaat
    return orderable[0]


def main():
    print("=" * 60)
    print("TEST: 10 producten toevoegen aan TestAI lijstje")
    print("(met smart search: eerst boodschappen lijst checken)")
    print("=" * 60)
    print()

    # Load client
    client = AHClient.from_har_file("testPOC.har")

    # Load boodschappen products once (for efficiency)
    print("Loading boodschappen lijst als referentie...")
    boodschappen = client.get_list_with_products(BOODSCHAPPEN_LIST_ID)
    print(f"  {len(boodschappen.products)} producten geladen")

    results = []
    products_to_add = []
    from_reference = 0
    from_search = 0

    # Zoek elk product
    for i, test in enumerate(TEST_PRODUCTS, 1):
        ingredient = test["ingredient"]
        search_term = test["search"]
        target_size = test["target_size"]

        print(f"\n[{i}/10] Zoeken: '{ingredient}'")
        print(f"        Zoekterm: '{search_term}'")

        try:
            # Smart search: eerst boodschappen, dan API
            product, source = client.smart_search(
                search_term, reference_products=boodschappen.products, limit=10
            )

            if not product:
                print("        ❌ Geen resultaten gevonden")
                results.append(
                    {
                        "ingredient": ingredient,
                        "status": "NOT_FOUND",
                        "product": None,
                        "source": "not_found",
                    }
                )
                continue

            # If from search, apply size filter
            if source == "search" and target_size:
                search_results = client.search_products(search_term, limit=10)
                best = select_best_product(search_results, target_size)
                if best:
                    product = best

            source_icon = "📋" if source == "reference" else "🔍"
            print(f"        ✅ {source_icon} [{source}] {product.title}")
            print(
                f"           Merk: {product.brand}, Grootte: {product.size}, "
                f"Prijs: €{product.price:.2f}"
            )

            if source == "reference":
                from_reference += 1
            else:
                from_search += 1

            products_to_add.append((product.id, 1))
            results.append(
                {
                    "ingredient": ingredient,
                    "status": "FOUND",
                    "product": product,
                    "source": source,
                }
            )

        except Exception as e:
            print(f"        ❌ Error: {e}")
            results.append(
                {
                    "ingredient": ingredient,
                    "status": "ERROR",
                    "product": None,
                    "source": "error",
                    "error": str(e),
                }
            )

    # Voeg alle gevonden producten toe aan de lijst
    print("\n" + "=" * 60)
    print("TOEVOEGEN AAN LIJST")
    print("=" * 60)

    if products_to_add:
        print(f"\n{len(products_to_add)} producten toevoegen aan TestAI...")

        try:
            result = client.add_products_to_list(TEST_LIST_ID, products_to_add)
            print(f"✅ Succesvol! Lijst heeft nu {result['totalSize']} items.")
        except Exception as e:
            print(f"❌ Fout bij toevoegen: {e}")

    # Samenvatting
    print("\n" + "=" * 60)
    print("SAMENVATTING")
    print("=" * 60)

    found = sum(1 for r in results if r["status"] == "FOUND")
    not_found = sum(1 for r in results if r["status"] in ["NOT_FOUND", "NO_MATCH"])
    errors = sum(1 for r in results if r["status"] == "ERROR")

    print(f"\n✅ Gevonden en toegevoegd: {found}/10")
    print(f"   📋 Uit boodschappen lijst: {from_reference}")
    print(f"   🔍 Via API search: {from_search}")
    print(f"❌ Niet gevonden: {not_found}/10")
    print(f"⚠️  Errors: {errors}/10")

    print("\n--- Details ---")
    total_price = 0
    for r in results:
        status_icon = "✅" if r["status"] == "FOUND" else "❌"
        if r["product"]:
            p = r["product"]
            source = r.get("source", "?")
            source_icon = "📋" if source == "reference" else "🔍"
            total_price += p.price
            title = p.title[:32]
            print(
                f"{status_icon} {source_icon} {r['ingredient']:22} → "
                f"{title:32} €{p.price:.2f}"
            )
        else:
            print(f"{status_icon}    {r['ingredient']:22} → NIET GEVONDEN")

    print(f"\n💰 Totale prijs: €{total_price:.2f}")


if __name__ == "__main__":
    main()
