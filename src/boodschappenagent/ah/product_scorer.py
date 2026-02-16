"""Product scoring for smarter search result ranking."""

from __future__ import annotations

from dataclasses import dataclass

from boodschappenagent.ah.models import Product


@dataclass(frozen=True)
class ProductScore:
    """Score breakdown for a product match.

    Attributes:
        product: The scored product.
        total: The total computed score (higher is better).
        title_score: How well the title matches the search term.
        brand_score: Brand preference bonus.
        orderable_score: Penalty if not orderable.
        penalty_processed: Penalty for processed food indicators.
        penalty_category: Penalty for non-food product categories.
    """

    product: Product
    total: float
    title_score: float
    brand_score: float
    orderable_score: float
    penalty_processed: float
    penalty_category: float = 0.0


class ProductScorer:
    """Score and rank AH search results for a given search term."""

    PROCESSED_INDICATORS = frozenset(
        {
            "mix",
            "saus",
            "kit",
            "maaltijd",
            "pakket",
            "bereiding",
            "kruidenmix",
            "roerbak",
            "soep",
            "chocolade",
            "koek",
            "chips",
            "sap",
        }
    )

    NON_FOOD_INDICATORS = frozenset(
        {
            "reiniger",
            "allesreiniger",
            "schoonmaak",
            "vuilniszakken",
            "wasmiddel",
            "zeep",
            "shampoo",
            "tandpasta",
        }
    )

    NON_FOOD_CATEGORIES = frozenset(
        {
            "huishouden",
            "schoonmaakmiddelen",
            "wasmiddelen",
            "persoonlijke verzorging",
            "diervoeding",
        }
    )

    AH_BRANDS = frozenset({"AH", "AH Biologisch"})

    def score_product(self, search_term: str, product: Product) -> ProductScore:
        """Score a single product against a search term."""
        title_score = self._title_similarity(search_term, product.title)
        brand_score = self._brand_preference(product.brand)
        orderable_score = 0.0 if product.is_orderable else -1000.0
        penalty_processed = self._processed_penalty(search_term, product.title)
        penalty_category = self._category_penalty(product)

        total = (
            title_score
            + brand_score
            + orderable_score
            + penalty_processed
            + penalty_category
        )

        return ProductScore(
            product=product,
            total=total,
            title_score=title_score,
            brand_score=brand_score,
            orderable_score=orderable_score,
            penalty_processed=penalty_processed,
            penalty_category=penalty_category,
        )

    def rank_products(
        self, search_term: str, products: list[Product]
    ) -> list[ProductScore]:
        """Score and rank all products, best first."""
        scored = [self.score_product(search_term, p) for p in products]
        return sorted(scored, key=lambda s: s.total, reverse=True)

    def best_match(self, search_term: str, products: list[Product]) -> Product | None:
        """Return the highest-scoring product, or None if list is empty."""
        if not products:
            return None
        ranked = self.rank_products(search_term, products)
        return ranked[0].product

    def _word_match(self, search_word: str, title_word: str) -> bool:
        """Check if a search word matches a title word.

        Rules:
        1. Exact match: "melk" == "melk"
        2. Prefix with max 3 extra chars (plurals): "ui" -> "uien"
           but NOT "melk" -> "melkchocolade"
        3. Reverse prefix with max 3 extra chars: "courgettes" -> "courgette"
        4. Suffix with min 4 chars (Dutch compounds): "bloem" in "tarwebloem"
        """
        if search_word == title_word:
            return True

        # Prefix: title_word is search_word + small suffix (plurals)
        if title_word.startswith(search_word):
            extra = len(title_word) - len(search_word)
            if extra <= 3:
                return True

        # Reverse prefix: search_word is title_word + small suffix
        if search_word.startswith(title_word):
            extra = len(search_word) - len(title_word)
            if extra <= 3:
                return True

        # Suffix: Dutch compound words (tarwebloem -> bloem)
        if len(search_word) >= 4 and title_word.endswith(search_word):
            return True

        # Reverse suffix: search is compound, title has base
        # (scharreleieren -> eieren, roomboter -> boter)
        return len(title_word) >= 4 and search_word.endswith(title_word)

    def _title_similarity(self, search_term: str, title: str) -> float:
        """Score title match based on word-level matching and coverage.

        Uses _word_match for word-level comparison instead of substring
        matching, preventing false positives like "ui" in "vuilniszakken".
        """
        search_words = search_term.lower().split()
        if not search_words:
            return 0.0

        title_words = title.lower().split()
        if not title_words:
            return 0.0

        words_matched = sum(
            1
            for sw in search_words
            if any(self._word_match(sw, tw) for tw in title_words)
        )
        match_ratio = words_matched / len(search_words)

        if match_ratio == 0.0:
            return 0.0

        coverage = min(len(search_words) / len(title_words), 1.0)

        return (match_ratio * 60.0) + (coverage * 40.0)

    def _brand_preference(self, brand: str) -> float:
        """Prefer AH own-brand for basic groceries."""
        if brand in self.AH_BRANDS:
            return 10.0
        return 0.0

    def _processed_penalty(self, search_term: str, title: str) -> float:
        """Penalize processed food and non-food products."""
        search_lower = search_term.lower()
        title_lower = title.lower()

        search_words = set(search_lower.split())

        # No penalty if search itself contains indicator
        if search_words & self.PROCESSED_INDICATORS:
            return 0.0
        if search_words & self.NON_FOOD_INDICATORS:
            return 0.0

        # Non-food gets heavier penalty (use substring for compound words)
        if any(ind in title_lower for ind in self.NON_FOOD_INDICATORS):
            return -50.0

        # Processed food penalty (use substring for compound words like "courgettesoep")
        if any(ind in title_lower for ind in self.PROCESSED_INDICATORS):
            return -30.0

        return 0.0

    def _category_penalty(self, product: Product) -> float:
        """Penalize non-food products based on category."""
        category_lower = product.category.lower()
        if not category_lower:
            return 0.0

        for non_food in self.NON_FOOD_CATEGORIES:
            if non_food in category_lower:
                return -100.0

        return 0.0
