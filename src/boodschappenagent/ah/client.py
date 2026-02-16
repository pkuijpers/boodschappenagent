"""Albert Heijn GraphQL API Client met OAuth2 token authenticatie."""

import requests

from boodschappenagent.ah.auth import AHTokenManager
from boodschappenagent.ah.models import FavoriteList, Product
from boodschappenagent.ah.product_scorer import ProductScorer


class AHClient:
    """Client voor de Albert Heijn GraphQL API (Mobile API)."""

    ENDPOINT = "https://api.ah.nl/graphql"

    DEFAULT_HEADERS = {
        "Content-Type": "application/json",
        "User-Agent": "Appie/8.22.3",
        "X-Application": "AHWEBSHOP",
    }

    def __init__(self, token_manager: AHTokenManager):
        """Initialize client with token manager for authentication."""
        self.token_manager = token_manager
        self.session = requests.Session()
        self.session.headers.update(self.DEFAULT_HEADERS)

    @classmethod
    def from_token_file(cls, path: str | None = None) -> AHClient:
        """Create client using stored tokens."""
        from pathlib import Path

        token_path = Path(path) if path else None
        return cls(AHTokenManager(token_path=token_path))

    def _execute(self, query: str, variables: dict, operation_name: str) -> dict:
        """Execute GraphQL query/mutation."""
        # Ensure valid token before each request
        token = self.token_manager.get_access_token()
        self.session.headers["Authorization"] = f"Bearer {token}"

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
        """Get a specific list with full product details."""
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

    def find_list_by_name(self, name: str) -> FavoriteList | None:
        """Find a favorite list by name (case-insensitive).

        Args:
            name: The list name to search for.

        Returns:
            FavoriteList if found, None otherwise.
        """
        lists = self.get_lists()
        name_lower = name.lower()
        for lst in lists:
            if lst.name.lower() == name_lower:
                return lst
        return None

    REFERENCE_MATCH_THRESHOLD = 40.0

    def find_product_in_list(
        self, search_term: str, products: list[Product]
    ) -> Product | None:
        """Find a matching product in a list using scored matching.

        Uses ProductScorer to evaluate all products and returns the best
        match only if it exceeds a minimum quality threshold.
        """
        if not products:
            return None

        scorer = ProductScorer()
        ranked = scorer.rank_products(search_term, products)

        if ranked and ranked[0].total >= self.REFERENCE_MATCH_THRESHOLD:
            return ranked[0].product

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

        Returns:
            Tuple of (Product, source) where source is "reference" or "search"
        """
        if reference_list_id and not reference_products:
            ref_list = self.get_list_with_products(reference_list_id)
            reference_products = ref_list.products

        if reference_products:
            match = self.find_product_in_list(search_term, reference_products)
            if match:
                return (match, "reference")

        results = self.search_products(search_term, limit=limit)
        if results:
            scorer = ProductScorer()
            best = scorer.best_match(search_term, results)
            if best:
                return (best, "search")

        return (None, "not_found")

    def create_list(self, name: str) -> str:
        """Create a new favorite list. Returns the list ID."""
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
        """Search for products."""
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
        self, list_id: str, products: list[tuple[int, int]], batch_size: int = 15
    ) -> dict:
        """Add products to a favorite list (in batches to avoid API limits)."""
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

        result = None
        for i in range(0, len(products), batch_size):
            batch = products[i : i + batch_size]
            variables = {
                "id": list_id,
                "products": [{"productId": pid, "quantity": qty} for pid, qty in batch],
            }

            data = self._execute(query, variables, "addProducts")
            result = data["favoriteListProductsAddV2"]

            if result["status"] != "SUCCESS":
                raise Exception(f"Failed to add products: {result['errorMessage']}")

        return result["result"]


# =============================================================================
# CLI voor quick testing
# =============================================================================

LOGIN_URL = (
    "https://login.ah.nl/secure/oauth/authorize"
    "?client_id=appie"
    "&redirect_uri=appie://login-exit"
    "&response_type=code"
)

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m boodschappenagent.ah.client <command> [args...]")
        print()
        print("Commands:")
        print("  login <code>             - Login with authorization code")
        print("  lists                    - Show all lists")
        print("  products <list_id>       - Show products in a list")
        print("  search <query>           - Search products")
        print("  smart <query> <ref_list> - Smart search (check ref list first)")
        print("  create <name>            - Create new list")
        print("  add <list_id> <product_id> [qty]  - Add product to list")
        print()
        print("First-time setup:")
        print(f"  1. Open: {LOGIN_URL}")
        print("  2. Log in with your AH account")
        print("  3. Copy the code from the redirect URL")
        print("  4. Run: python -m boodschappenagent.ah.client login <code>")
        sys.exit(1)

    command = sys.argv[1]

    if command == "login":
        if len(sys.argv) < 3:
            print(f"Open this URL and log in:\n  {LOGIN_URL}")
            print("\nThen run:")
            print("  python -m boodschappenagent.ah.client login <code>")
            sys.exit(1)
        auth_code = sys.argv[2]
        token_manager = AHTokenManager()
        token_manager.login(auth_code)
        print("Login successful! Tokens saved.")
        sys.exit(0)

    # All other commands need authentication
    token_manager = AHTokenManager()
    if not token_manager.is_authenticated():
        print("Not authenticated. Run 'login' first.")
        print(f"  Open: {LOGIN_URL}")
        sys.exit(1)

    client = AHClient(token_manager)

    if command == "lists":
        lists = client.get_lists()
        print(f"\nFound {len(lists)} lists:")
        for lst in lists:
            print(f"  - {lst.name} ({lst.total_items} items) [{lst.id}]")

    elif command == "products":
        list_id = sys.argv[2] if len(sys.argv) > 2 else None
        if not list_id:
            print("Usage: products <list_id>")
            sys.exit(1)
        lst = client.get_list_with_products(list_id)
        print(f"\nProducts in '{lst.name}' ({lst.total_items} items):")
        if lst.products:
            for p in lst.products[:20]:
                print(f"  [{p.id}] {p.title} - {p.size} - \u20ac{p.price:.2f}")
            if len(lst.products) > 20:
                print(f"  ... and {len(lst.products) - 20} more")

    elif command == "search":
        query = sys.argv[2] if len(sys.argv) > 2 else "melk"
        products = client.search_products(query, limit=5)
        print(f"\nSearch results for '{query}':")
        for p in products:
            print(f"  [{p.id}] {p.title} - {p.size} - \u20ac{p.price:.2f}")

    elif command == "smart":
        query = sys.argv[2] if len(sys.argv) > 2 else "melk"
        ref_list = sys.argv[3] if len(sys.argv) > 3 else None
        product, source = client.smart_search(query, reference_list_id=ref_list)
        if product:
            print(f"\nSmart search for '{query}':")
            print(f"  Source: {source}")
            print(
                f"  [{product.id}] {product.title} - {product.size} - "
                f"\u20ac{product.price:.2f}"
            )
        else:
            print(f"\nNo results for '{query}'")

    elif command == "create":
        name = sys.argv[2] if len(sys.argv) > 2 else "TestAPI"
        list_id = client.create_list(name)
        print(f"\nCreated list '{name}' with ID: {list_id}")

    elif command == "add":
        list_id = sys.argv[2]
        product_id = int(sys.argv[3])
        qty = int(sys.argv[4]) if len(sys.argv) > 4 else 1
        result = client.add_products_to_list(list_id, [(product_id, qty)])
        print(
            f"\nAdded product {product_id} to list. Total items: {result['totalSize']}"
        )

    else:
        print(f"Unknown command: {command}")
