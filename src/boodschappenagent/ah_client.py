"""
Albert Heijn "Mijn Lijstjes" API Client

POC implementatie voor het automatisch toevoegen van producten aan een AH lijstje.
"""

import json
from dataclasses import dataclass

import requests


@dataclass
class Product:
    """AH Product data."""

    id: int
    title: str
    brand: str
    size: str
    price: float
    category: str
    is_orderable: bool

    @classmethod
    def from_api(cls, data: dict) -> Product:
        return cls(
            id=data["id"],
            title=data["title"],
            brand=data.get("brand", ""),
            size=data.get("salesUnitSize", ""),
            price=data.get("priceV2", {}).get("now", {}).get("amount", 0),
            category=data.get("category", ""),
            is_orderable=data.get("availability", {}).get("isOrderable", False),
        )


@dataclass
class FavoriteList:
    """AH Favorite List data."""

    id: str
    name: str
    total_items: int
    items: list[dict]
    products: list[Product] | None = None  # Optional: full product details

    @classmethod
    def from_api(cls, data: dict) -> FavoriteList:
        products = None
        if "products" in data and data["products"]:
            products = [Product.from_api(p) for p in data["products"]]

        return cls(
            id=data["id"],
            name=data["description"],
            total_items=data.get("totalSize", 0),
            items=data.get("items", []),
            products=products,
        )


class AHClient:
    """Client voor de Albert Heijn GraphQL API."""

    ENDPOINT = "https://www.ah.nl/gql"

    DEFAULT_HEADERS = {
        "Content-Type": "application/json",
        "x-client-platform-type": "Web",
        "x-client-name": "ah-favorites",
        "x-client-version": "1.5.75",
        "Origin": "https://www.ah.nl",
        "Referer": "https://www.ah.nl/favorieten",
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64; rv:147.0) Gecko/20100101 Firefox/147.0"
        ),
    }

    def __init__(self, cookies: dict):
        """
        Initialize client with session cookies.

        Args:
            cookies: Dict met cookies (minimaal SSID nodig)
        """
        self.session = requests.Session()
        self.session.headers.update(self.DEFAULT_HEADERS)
        self.session.cookies.update(cookies)

    @classmethod
    def from_cookie_file(cls, path: str) -> AHClient:
        """Load client from exported cookies JSON file."""
        with open(path) as f:
            cookies = json.load(f)
        return cls(cookies)

    @classmethod
    def from_har_file(cls, path: str) -> AHClient:
        """Extract cookies from HAR file and create client."""
        with open(path) as f:
            har = json.load(f)

        cookies = {}
        for entry in har["log"]["entries"]:
            for cookie in entry["request"].get("cookies", []):
                cookies[cookie["name"]] = cookie["value"]

        return cls(cookies)

    def _execute(self, query: str, variables: dict, operation_name: str) -> dict:
        """Execute GraphQL query/mutation."""
        payload = {
            "operationName": operation_name,
            "variables": variables,
            "query": query,
        }

        response = self.session.post(self.ENDPOINT, json=payload)
        response.raise_for_status()

        result = response.json()
        if "errors" in result:
            raise Exception(f"GraphQL errors: {result['errors']}")

        return result["data"]

    # =========================================================================
    # Lists
    # =========================================================================

    def get_lists(self) -> list[FavoriteList]:
        """Get all favorite lists (without product details)."""
        query = """
        query favoriteList($ids: [String!]!) {
          favoriteListV2(ids: $ids) {
            id
            description
            totalSize
            items {
              id
              productId
              quantity
            }
          }
        }
        """
        data = self._execute(query, {"ids": []}, "favoriteList")
        return [FavoriteList.from_api(lst) for lst in data["favoriteListV2"]]

    def get_list_with_products(self, list_id: str) -> FavoriteList:
        """
        Get a specific list with full product details.

        Args:
            list_id: UUID of the list

        Returns:
            FavoriteList with products populated
        """
        query = """
        query favoriteListWithProducts($ids: [String!]!) {
          favoriteListV2(ids: $ids) {
            id
            description
            totalSize
            items {
              id
              productId
              quantity
            }
            products {
              id
              title
              brand
              salesUnitSize
              category
              priceV2 {
                now { amount }
              }
              availability {
                isOrderable
              }
            }
          }
        }
        """
        data = self._execute(query, {"ids": [list_id]}, "favoriteListWithProducts")
        if not data["favoriteListV2"]:
            raise Exception(f"List not found: {list_id}")
        return FavoriteList.from_api(data["favoriteListV2"][0])

    # Base ingredients to extract from compound words
    # e.g., "scharreleieren" -> "eieren"
    BASE_INGREDIENTS = [
        "eieren",
        "melk",
        "kaas",
        "brood",
        "boter",
        "yoghurt",
        "vlees",
        "kip",
        "vis",
        "groente",
        "fruit",
        "pasta",
        "rijst",
        "aardappel",
    ]

    def find_product_in_list(
        self, search_term: str, products: list[Product]
    ) -> Product | None:
        """
        Find a matching product in a list of products.

        Matching strategy:
        1. Exact title match (case-insensitive)
        2. All search words appear in title
        3. Main keyword appears in title
        4. Base ingredient from compound word (e.g., "scharreleieren" -> "eieren")
        5. Category match (e.g., both are in "Zuivel, eieren")

        Args:
            search_term: Search term to match
            products: List of products to search in

        Returns:
            Best matching product or None
        """
        if not products:
            return None

        search_lower = search_term.lower()
        search_words = search_lower.split()

        # 1. Exact match
        for p in products:
            if search_lower == p.title.lower():
                return p

        # 2. All words match
        for p in products:
            title_lower = p.title.lower()
            if all(word in title_lower for word in search_words):
                return p

        # 3. Main keyword (first word or longest word) matches
        main_word = max(search_words, key=len) if search_words else search_lower
        for p in products:
            if main_word in p.title.lower():
                return p

        # 4. Extract base ingredient from compound words
        # e.g., "scharreleieren" contains "eieren", "halfvolle melk" contains "melk"
        for base in self.BASE_INGREDIENTS:
            # Check if base ingredient is in the search term
            if base in search_lower or any(base in word for word in search_words):
                # Find products that contain this base ingredient
                for p in products:
                    title_lower = p.title.lower()
                    if base in title_lower:
                        return p

        return None

    def smart_search(
        self,
        search_term: str,
        reference_list_id: str | None = None,
        reference_products: list[Product] | None = None,
        limit: int = 10,
    ) -> tuple[Product | None, str]:
        """
        Smart search: first check reference list, then fall back to API search.

        Args:
            search_term: Search term
            reference_list_id: Optional list ID to check first (will fetch products)
            reference_products: Optional pre-loaded products to check first
            limit: Max results for API search fallback

        Returns:
            Tuple of (Product, source) where source is "reference" or "search"
        """
        # Get reference products if list_id provided
        if reference_list_id and not reference_products:
            ref_list = self.get_list_with_products(reference_list_id)
            reference_products = ref_list.products

        # Check reference list first
        if reference_products:
            match = self.find_product_in_list(search_term, reference_products)
            if match:
                return (match, "reference")

        # Fall back to API search
        results = self.search_products(search_term, limit=limit)
        if results:
            return (results[0], "search")

        return (None, "not_found")

    def create_list(self, name: str) -> str:
        """
        Create a new favorite list.

        Returns:
            ID of the created list
        """
        query = """
        mutation addFavoriteList($description: String!) {
          favoriteListAddV2(description: $description) {
            status
            errorMessage
            result {
              id
            }
          }
        }
        """
        data = self._execute(query, {"description": name}, "addFavoriteList")
        result = data["favoriteListAddV2"]

        if result["status"] != "SUCCESS":
            raise Exception(f"Failed to create list: {result['errorMessage']}")

        return result["result"]["id"]

    # =========================================================================
    # Products
    # =========================================================================

    def search_products(self, query: str, limit: int = 10) -> list[Product]:
        """
        Search for products.

        Args:
            query: Search term
            limit: Max number of results (default 10)

        Returns:
            List of matching products
        """
        gql_query = """
        query productSearch($input: SearchProductsInput!) {
          searchProducts(input: $input) {
            products {
              id
              title
              brand
              salesUnitSize
              category
              priceV2 {
                now { amount }
              }
              availability {
                isOrderable
              }
            }
          }
        }
        """

        variables = {
            "input": {
                "query": query,
                "extraConsents": None,
                "searchInput": {
                    "page": {
                        "size": limit,
                        "number": 0,
                        "merged": False,
                    },
                    "intent": {
                        "orderId": None,
                        "intent": "ONLINE",
                        "storeId": None,
                    },
                },
                "sortType": "RELEVANCE",
            }
        }

        data = self._execute(gql_query, variables, "productSearch")
        return [Product.from_api(p) for p in data["searchProducts"]["products"]]

    def add_products_to_list(
        self, list_id: str, products: list[tuple[int, int]]
    ) -> dict:
        """
        Add products to a favorite list.

        Args:
            list_id: UUID of the list
            products: List of (product_id, quantity) tuples

        Returns:
            Updated list data
        """
        query = """
        mutation addProducts($id: String!, $products: [FavoriteListProductMutation!]!) {
          favoriteListProductsAddV2(id: $id, products: $products) {
            status
            errorMessage
            result {
              id
              description
              totalSize
              items {
                id
                productId
                quantity
              }
            }
          }
        }
        """

        variables = {
            "id": list_id,
            "products": [{"productId": pid, "quantity": qty} for pid, qty in products],
        }

        data = self._execute(query, variables, "addProducts")
        result = data["favoriteListProductsAddV2"]

        if result["status"] != "SUCCESS":
            raise Exception(f"Failed to add products: {result['errorMessage']}")

        return result["result"]


# =============================================================================
# CLI voor quick testing
# =============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python ah_client.py <har_file> [command] [args...]")
        print()
        print("Commands:")
        print("  lists                    - Show all lists")
        print("  products <list_id>       - Show products in a list")
        print("  search <query>           - Search products")
        print("  smart <query> <ref_list> - Smart search (check ref list first)")
        print("  create <name>            - Create new list")
        print("  add <list_id> <product_id> [qty]  - Add product to list")
        sys.exit(1)

    har_file = sys.argv[1]
    command = sys.argv[2] if len(sys.argv) > 2 else "lists"

    print(f"Loading cookies from {har_file}...")
    client = AHClient.from_har_file(har_file)

    if command == "lists":
        lists = client.get_lists()
        print(f"\nFound {len(lists)} lists:")
        for lst in lists:
            print(f"  - {lst.name} ({lst.total_items} items) [{lst.id}]")

    elif command == "products":
        list_id = sys.argv[3] if len(sys.argv) > 3 else None
        if not list_id:
            print("Usage: products <list_id>")
            sys.exit(1)
        lst = client.get_list_with_products(list_id)
        print(f"\nProducts in '{lst.name}' ({lst.total_items} items):")
        if lst.products:
            for p in lst.products[:20]:  # Show first 20
                print(f"  [{p.id}] {p.title} - {p.size} - €{p.price:.2f}")
            if len(lst.products) > 20:
                print(f"  ... and {len(lst.products) - 20} more")

    elif command == "search":
        query = sys.argv[3] if len(sys.argv) > 3 else "melk"
        products = client.search_products(query, limit=5)
        print(f"\nSearch results for '{query}':")
        for p in products:
            print(f"  [{p.id}] {p.title} - {p.size} - €{p.price:.2f}")

    elif command == "smart":
        query = sys.argv[3] if len(sys.argv) > 3 else "melk"
        ref_list = sys.argv[4] if len(sys.argv) > 4 else None
        product, source = client.smart_search(query, reference_list_id=ref_list)
        if product:
            print(f"\nSmart search for '{query}':")
            print(f"  Source: {source}")
            print(
                f"  [{product.id}] {product.title} - {product.size} - "
                f"€{product.price:.2f}"
            )
        else:
            print(f"\nNo results for '{query}'")

    elif command == "create":
        name = sys.argv[3] if len(sys.argv) > 3 else "TestAPI"
        list_id = client.create_list(name)
        print(f"\nCreated list '{name}' with ID: {list_id}")

    elif command == "add":
        list_id = sys.argv[3]
        product_id = int(sys.argv[4])
        qty = int(sys.argv[5]) if len(sys.argv) > 5 else 1
        result = client.add_products_to_list(list_id, [(product_id, qty)])
        print(
            f"\nAdded product {product_id} to list. Total items: {result['totalSize']}"
        )

    else:
        print(f"Unknown command: {command}")
