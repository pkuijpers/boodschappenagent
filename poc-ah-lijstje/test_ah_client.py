"""
Unit tests for AH Client.

Run with: uv run pytest poc-ah-lijstje/test_ah_client.py -v
"""

import pytest
from unittest.mock import Mock, patch

from ah_client import AHClient, Product, FavoriteList


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_product_data():
    """Sample product data as returned by AH API."""
    return {
        "id": 33693,
        "title": "AH Halfvolle melk",
        "brand": "AH",
        "salesUnitSize": "1,5 l",
        "category": "Zuivel, eieren/Halfvolle melk",
        "priceV2": {"now": {"amount": 1.79}},
        "availability": {"isOrderable": True},
    }


@pytest.fixture
def sample_product(sample_product_data):
    """Sample Product instance."""
    return Product.from_api(sample_product_data)


@pytest.fixture
def sample_products():
    """List of sample products for testing matching."""
    return [
        Product(
            id=1,
            title="AH Halfvolle melk",
            brand="AH",
            size="1 l",
            price=1.29,
            category="Zuivel",
            is_orderable=True,
        ),
        Product(
            id=2,
            title="AH Vrije uitloop eieren M",
            brand="AH",
            size="10 stuks",
            price=4.19,
            category="Eieren",
            is_orderable=True,
        ),
        Product(
            id=3,
            title="AH Knoflook",
            brand="AH",
            size="2 stuks",
            price=1.39,
            category="Groenten",
            is_orderable=True,
        ),
        Product(
            id=4,
            title="Mutti Passata gezeefde tomaten",
            brand="Mutti",
            size="720 ml",
            price=3.09,
            category="Conserven",
            is_orderable=True,
        ),
        Product(
            id=5,
            title="AH Scharrel kipfilet",
            brand="AH",
            size="300 g",
            price=4.99,
            category="Vlees",
            is_orderable=True,
        ),
        Product(
            id=6,
            title="Arla Biologisch halfvolle melk",
            brand="Arla",
            size="1 l",
            price=1.79,
            category="Zuivel",
            is_orderable=True,
        ),
    ]


@pytest.fixture
def mock_client():
    """Create a mock AH client without actual HTTP session."""
    with patch.object(AHClient, "__init__", lambda self, cookies: None):
        client = AHClient.__new__(AHClient)
        client.session = Mock()
        return client


# =============================================================================
# Product Tests
# =============================================================================


class TestProduct:
    """Tests for Product dataclass."""

    def test_from_api_complete_data(self, sample_product_data):
        """Test Product.from_api with complete data."""
        product = Product.from_api(sample_product_data)

        assert product.id == 33693
        assert product.title == "AH Halfvolle melk"
        assert product.brand == "AH"
        assert product.size == "1,5 l"
        assert product.price == 1.79
        assert product.category == "Zuivel, eieren/Halfvolle melk"
        assert product.is_orderable is True

    def test_from_api_missing_optional_fields(self):
        """Test Product.from_api with missing optional fields."""
        data = {
            "id": 123,
            "title": "Test Product",
        }
        product = Product.from_api(data)

        assert product.id == 123
        assert product.title == "Test Product"
        assert product.brand == ""
        assert product.size == ""
        assert product.price == 0
        assert product.category == ""
        assert product.is_orderable is False

    def test_from_api_nested_price(self):
        """Test price extraction from nested structure."""
        data = {
            "id": 1,
            "title": "Test",
            "priceV2": {"now": {"amount": 2.99}},
        }
        product = Product.from_api(data)
        assert product.price == 2.99

    def test_from_api_missing_price(self):
        """Test handling of missing price data."""
        data = {"id": 1, "title": "Test", "priceV2": {}}
        product = Product.from_api(data)
        assert product.price == 0


# =============================================================================
# FavoriteList Tests
# =============================================================================


class TestFavoriteList:
    """Tests for FavoriteList dataclass."""

    def test_from_api_basic(self):
        """Test FavoriteList.from_api with basic data."""
        data = {
            "id": "abc-123",
            "description": "Mijn Lijst",
            "totalSize": 5,
            "items": [{"id": "item1", "productId": 100, "quantity": 2}],
        }
        lst = FavoriteList.from_api(data)

        assert lst.id == "abc-123"
        assert lst.name == "Mijn Lijst"
        assert lst.total_items == 5
        assert len(lst.items) == 1
        assert lst.products is None

    def test_from_api_with_products(self, sample_product_data):
        """Test FavoriteList.from_api with products included."""
        data = {
            "id": "abc-123",
            "description": "Met Producten",
            "totalSize": 1,
            "items": [],
            "products": [sample_product_data],
        }
        lst = FavoriteList.from_api(data)

        assert lst.products is not None
        assert len(lst.products) == 1
        assert lst.products[0].title == "AH Halfvolle melk"

    def test_from_api_empty_products(self):
        """Test FavoriteList.from_api with empty products list."""
        data = {
            "id": "abc-123",
            "description": "Leeg",
            "totalSize": 0,
            "items": [],
            "products": [],
        }
        lst = FavoriteList.from_api(data)
        assert lst.products is None  # Empty list becomes None


# =============================================================================
# find_product_in_list Tests
# =============================================================================


class TestFindProductInList:
    """Tests for AHClient.find_product_in_list method."""

    def test_exact_match(self, mock_client, sample_products):
        """Test exact title match (case-insensitive)."""
        result = mock_client.find_product_in_list("ah halfvolle melk", sample_products)
        assert result is not None
        assert result.id == 1

    def test_exact_match_case_insensitive(self, mock_client, sample_products):
        """Test that matching is case-insensitive."""
        result = mock_client.find_product_in_list("AH HALFVOLLE MELK", sample_products)
        assert result is not None
        assert result.id == 1

    def test_all_words_match(self, mock_client, sample_products):
        """Test matching when all search words appear in title."""
        result = mock_client.find_product_in_list(
            "vrije uitloop eieren", sample_products
        )
        assert result is not None
        assert result.id == 2

    def test_main_keyword_match(self, mock_client, sample_products):
        """Test matching on main keyword (longest word)."""
        result = mock_client.find_product_in_list("knoflook", sample_products)
        assert result is not None
        assert result.id == 3

    def test_base_ingredient_extraction_eieren(self, mock_client, sample_products):
        """Test base ingredient extraction: scharreleieren -> eieren."""
        result = mock_client.find_product_in_list("scharreleieren", sample_products)
        assert result is not None
        assert result.id == 2  # Should match "AH Vrije uitloop eieren M"

    def test_base_ingredient_extraction_melk(self, mock_client, sample_products):
        """Test base ingredient extraction: halfvolle melk -> melk."""
        # First product with "melk" in title should match
        result = mock_client.find_product_in_list("magere melk", sample_products)
        assert result is not None
        assert "melk" in result.title.lower()

    def test_no_match_returns_none(self, mock_client, sample_products):
        """Test that no match returns None."""
        result = mock_client.find_product_in_list("biefstuk", sample_products)
        assert result is None

    def test_empty_products_list(self, mock_client):
        """Test with empty products list."""
        result = mock_client.find_product_in_list("melk", [])
        assert result is None

    def test_passata_match(self, mock_client, sample_products):
        """Test matching passata."""
        result = mock_client.find_product_in_list("passata", sample_products)
        assert result is not None
        assert result.id == 4

    def test_compound_search_term(self, mock_client, sample_products):
        """Test search with multiple words."""
        result = mock_client.find_product_in_list("scharrel kipfilet", sample_products)
        assert result is not None
        assert result.id == 5


# =============================================================================
# smart_search Tests
# =============================================================================


class TestSmartSearch:
    """Tests for AHClient.smart_search method."""

    def test_finds_in_reference_list(self, mock_client, sample_products):
        """Test that product is found in reference list first."""
        mock_client.search_products = Mock(return_value=[])

        product, source = mock_client.smart_search(
            "knoflook", reference_products=sample_products
        )

        assert product is not None
        assert product.id == 3
        assert source == "reference"
        mock_client.search_products.assert_not_called()

    def test_falls_back_to_search(self, mock_client, sample_products):
        """Test fallback to API search when not in reference list."""
        api_product = Product(
            id=999,
            title="AH Pancetta",
            brand="AH",
            size="100 g",
            price=2.49,
            category="Vlees",
            is_orderable=True,
        )
        mock_client.search_products = Mock(return_value=[api_product])

        product, source = mock_client.smart_search(
            "pancetta", reference_products=sample_products
        )

        assert product is not None
        assert product.id == 999
        assert source == "search"
        mock_client.search_products.assert_called_once_with("pancetta", limit=10)

    def test_not_found_anywhere(self, mock_client, sample_products):
        """Test when product is not found anywhere."""
        mock_client.search_products = Mock(return_value=[])

        product, source = mock_client.smart_search(
            "iets_dat_niet_bestaat", reference_products=sample_products
        )

        assert product is None
        assert source == "not_found"

    def test_fetches_reference_list_by_id(self, mock_client, sample_products):
        """Test that reference list is fetched by ID if not provided."""
        mock_list = FavoriteList(
            id="test-id", name="Test", total_items=1, items=[], products=sample_products
        )
        mock_client.get_list_with_products = Mock(return_value=mock_list)
        mock_client.search_products = Mock(return_value=[])

        product, source = mock_client.smart_search(
            "knoflook", reference_list_id="test-id"
        )

        assert product is not None
        assert source == "reference"
        mock_client.get_list_with_products.assert_called_once_with("test-id")

    def test_preloaded_products_preferred(self, mock_client, sample_products):
        """Test that preloaded products are used over fetching by ID."""
        mock_client.get_list_with_products = Mock()

        product, source = mock_client.smart_search(
            "knoflook",
            reference_list_id="ignored-id",
            reference_products=sample_products,
        )

        assert product is not None
        mock_client.get_list_with_products.assert_not_called()


# =============================================================================
# API Method Tests (with mocking)
# =============================================================================


class TestAPIMethodsWithMocking:
    """Tests for API methods using mocked responses."""

    def test_get_lists(self, mock_client):
        """Test get_lists method."""
        mock_response = {
            "favoriteListV2": [
                {"id": "list-1", "description": "Lijst 1", "totalSize": 5, "items": []},
                {
                    "id": "list-2",
                    "description": "Lijst 2",
                    "totalSize": 10,
                    "items": [],
                },
            ]
        }
        mock_client._execute = Mock(return_value=mock_response)

        lists = mock_client.get_lists()

        assert len(lists) == 2
        assert lists[0].name == "Lijst 1"
        assert lists[1].total_items == 10

    def test_get_list_with_products(self, mock_client, sample_product_data):
        """Test get_list_with_products method."""
        mock_response = {
            "favoriteListV2": [
                {
                    "id": "list-1",
                    "description": "Met Producten",
                    "totalSize": 1,
                    "items": [],
                    "products": [sample_product_data],
                }
            ]
        }
        mock_client._execute = Mock(return_value=mock_response)

        lst = mock_client.get_list_with_products("list-1")

        assert lst.name == "Met Producten"
        assert lst.products is not None
        assert len(lst.products) == 1

    def test_get_list_with_products_not_found(self, mock_client):
        """Test get_list_with_products when list not found."""
        mock_client._execute = Mock(return_value={"favoriteListV2": []})

        with pytest.raises(Exception, match="List not found"):
            mock_client.get_list_with_products("nonexistent")

    def test_create_list_success(self, mock_client):
        """Test create_list method."""
        mock_response = {
            "favoriteListAddV2": {
                "status": "SUCCESS",
                "errorMessage": None,
                "result": {"id": "new-list-id"},
            }
        }
        mock_client._execute = Mock(return_value=mock_response)

        list_id = mock_client.create_list("Nieuwe Lijst")

        assert list_id == "new-list-id"

    def test_create_list_failure(self, mock_client):
        """Test create_list when API returns error."""
        mock_response = {
            "favoriteListAddV2": {
                "status": "ERROR",
                "errorMessage": "Lijst bestaat al",
                "result": None,
            }
        }
        mock_client._execute = Mock(return_value=mock_response)

        with pytest.raises(Exception, match="Failed to create list"):
            mock_client.create_list("Bestaande Lijst")

    def test_search_products(self, mock_client, sample_product_data):
        """Test search_products method."""
        mock_response = {"searchProducts": {"products": [sample_product_data]}}
        mock_client._execute = Mock(return_value=mock_response)

        products = mock_client.search_products("melk", limit=5)

        assert len(products) == 1
        assert products[0].title == "AH Halfvolle melk"

    def test_add_products_to_list_success(self, mock_client):
        """Test add_products_to_list method."""
        mock_response = {
            "favoriteListProductsAddV2": {
                "status": "SUCCESS",
                "errorMessage": None,
                "result": {
                    "id": "list-1",
                    "description": "Test",
                    "totalSize": 3,
                    "items": [],
                },
            }
        }
        mock_client._execute = Mock(return_value=mock_response)

        result = mock_client.add_products_to_list("list-1", [(123, 1), (456, 2)])

        assert result["totalSize"] == 3

    def test_add_products_to_list_failure(self, mock_client):
        """Test add_products_to_list when API returns error."""
        mock_response = {
            "favoriteListProductsAddV2": {
                "status": "ERROR",
                "errorMessage": "Product niet gevonden",
                "result": None,
            }
        }
        mock_client._execute = Mock(return_value=mock_response)

        with pytest.raises(Exception, match="Failed to add products"):
            mock_client.add_products_to_list("list-1", [(999, 1)])


# =============================================================================
# Integration-style Tests
# =============================================================================


class TestBaseIngredients:
    """Tests specifically for BASE_INGREDIENTS matching."""

    def test_all_base_ingredients_defined(self, mock_client):
        """Verify BASE_INGREDIENTS list is properly defined."""
        assert hasattr(mock_client, "BASE_INGREDIENTS")
        assert "eieren" in mock_client.BASE_INGREDIENTS
        assert "melk" in mock_client.BASE_INGREDIENTS
        assert "kaas" in mock_client.BASE_INGREDIENTS

    @pytest.mark.parametrize(
        "search_term,expected_base",
        [
            ("scharreleieren", "eieren"),
            ("halfvolle melk", "melk"),
            ("oude kaas", "kaas"),
            ("volkoren brood", "brood"),
            ("roomboter", "boter"),
            ("griekse yoghurt", "yoghurt"),
            ("kipfilet", "kip"),
        ],
    )
    def test_base_ingredient_matching(self, mock_client, search_term, expected_base):
        """Test that various compound words match their base ingredients."""
        # Create a product with just the base ingredient
        products = [
            Product(
                id=1,
                title=f"AH {expected_base.title()}",
                brand="AH",
                size="1 stuk",
                price=1.00,
                category="Test",
                is_orderable=True,
            )
        ]

        result = mock_client.find_product_in_list(search_term, products)

        assert (
            result is not None
        ), f"'{search_term}' should match product with '{expected_base}'"
