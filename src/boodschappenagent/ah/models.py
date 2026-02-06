"""AH data models."""

from dataclasses import dataclass


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
