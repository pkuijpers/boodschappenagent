"""
Unit tests for ProductScorer.

Run with: uv run pytest tests/test_product_scorer.py -v
"""

import pytest

from boodschappenagent.ah.models import Product
from boodschappenagent.ah.product_scorer import ProductScorer

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def scorer():
    """ProductScorer instance."""
    return ProductScorer()


def _product(
    title: str,
    brand: str = "AH",
    is_orderable: bool = True,
    **kwargs,
) -> Product:
    """Helper to create Product instances for testing."""
    defaults = {
        "id": hash(title) % 100000,
        "size": "1 stuk",
        "price": 1.99,
        "category": "Test",
    }
    defaults.update(kwargs)
    return Product(
        title=title,
        brand=brand,
        is_orderable=is_orderable,
        **defaults,
    )


# =============================================================================
# Title Similarity Tests
# =============================================================================


class TestTitleSimilarity:
    """Tests for title similarity scoring."""

    def test_exact_single_word_short_title_scores_higher(self, scorer):
        """Short title with search term scores higher than long title."""
        short = _product("AH Broccoli")
        long = _product("Honig Mix aardappel, broccoli & rundervink", brand="Honig")

        score_short = scorer.score_product("broccoli", short)
        score_long = scorer.score_product("broccoli", long)

        assert score_short.title_score > score_long.title_score

    def test_all_words_match_scores_higher(self, scorer):
        """Title where all search words match scores higher."""
        good = _product("AH Yoghurt Griekse stijl")
        bad = _product("Campina High protein yoghurt", brand="Campina")

        score_good = scorer.score_product("griekse yoghurt", good)
        score_bad = scorer.score_product("griekse yoghurt", bad)

        assert score_good.title_score > score_bad.title_score

    def test_no_words_match(self, scorer):
        """Title with no matching words scores zero."""
        product = _product("AH Sinaasappelsap")
        score = scorer.score_product("broccoli", product)

        assert score.title_score == 0.0

    def test_coverage_penalizes_long_titles(self, scorer):
        """Longer titles with same match have lower coverage."""
        short = _product("AH Tomaten")
        long = _product("Looye Honingtomaten cherry extra lekker", brand="Looye")

        score_short = scorer.score_product("tomaten", short)
        score_long = scorer.score_product("tomaten", long)

        # Both match "tomaten" but short title has better coverage
        assert score_short.title_score > score_long.title_score


# =============================================================================
# Brand Preference Tests
# =============================================================================


class TestBrandPreference:
    """Tests for brand preference scoring."""

    def test_ah_brand_gets_bonus(self, scorer):
        """AH brand products get a bonus."""
        product = _product("AH Broccoli", brand="AH")
        score = scorer.score_product("broccoli", product)

        assert score.brand_score > 0

    def test_ah_biologisch_gets_bonus(self, scorer):
        """AH Biologisch products get a bonus."""
        product = _product("AH Biologisch Rode kool", brand="AH Biologisch")
        score = scorer.score_product("rode kool", product)

        assert score.brand_score > 0

    def test_other_brand_no_bonus(self, scorer):
        """Non-AH brand products get no bonus."""
        product = _product("Honig Mix broccoli", brand="Honig")
        score = scorer.score_product("broccoli", product)

        assert score.brand_score == 0.0


# =============================================================================
# Processed Penalty Tests
# =============================================================================


class TestProcessedPenalty:
    """Tests for processed food penalty."""

    def test_mix_in_title_penalized(self, scorer):
        """Products with 'mix' in title get penalized."""
        product = _product("Honig Mix aardappel, broccoli & rundervink", brand="Honig")
        score = scorer.score_product("broccoli", product)

        assert score.penalty_processed < 0

    def test_no_penalty_for_fresh(self, scorer):
        """Fresh products get no penalty."""
        product = _product("AH Broccoli")
        score = scorer.score_product("broccoli", product)

        assert score.penalty_processed == 0.0

    def test_no_penalty_when_search_is_processed(self, scorer):
        """No penalty when search term itself contains processed indicator."""
        product = _product("AH Kruidenmix Italiaans")
        score = scorer.score_product("kruidenmix", product)

        assert score.penalty_processed == 0.0


# =============================================================================
# Orderable Tests
# =============================================================================


class TestOrderable:
    """Tests for orderability scoring."""

    def test_not_orderable_gets_massive_penalty(self, scorer):
        """Non-orderable products get a massive penalty."""
        product = _product("AH Broccoli", is_orderable=False)
        score = scorer.score_product("broccoli", product)

        assert score.orderable_score < -100

    def test_orderable_no_penalty(self, scorer):
        """Orderable products get no penalty."""
        product = _product("AH Broccoli", is_orderable=True)
        score = scorer.score_product("broccoli", product)

        assert score.orderable_score == 0.0


# =============================================================================
# Rank Products Tests
# =============================================================================


class TestRankProducts:
    """Tests for ranking multiple products."""

    def test_broccoli_ranks_fresh_over_mix(self, scorer):
        """Fresh broccoli should rank above Honig Mix."""
        fresh = _product("AH Broccoli")
        mix = _product("Honig Mix aardappel, broccoli & rundervink", brand="Honig")

        ranked = scorer.rank_products("broccoli", [mix, fresh])

        assert ranked[0].product is fresh

    def test_tomaten_ranks_ah_over_premium(self, scorer):
        """AH Tomaten should rank above Looye Honingtomaten."""
        ah = _product("AH Tomaten")
        premium = _product("Looye Honingtomaten", brand="Looye")

        ranked = scorer.rank_products("tomaten", [premium, ah])

        assert ranked[0].product is ah

    def test_griekse_yoghurt_ranks_correctly(self, scorer):
        """AH Yoghurt Griekse stijl should rank above Campina High protein."""
        ah = _product("AH Yoghurt Griekse stijl")
        campina = _product(
            "Campina High protein Greek yoghurt 1,5% fat", brand="Campina"
        )

        ranked = scorer.rank_products("griekse yoghurt", [campina, ah])

        assert ranked[0].product is ah

    def test_empty_list_returns_empty(self, scorer):
        """Empty product list returns empty ranking."""
        ranked = scorer.rank_products("broccoli", [])

        assert ranked == []

    def test_best_match_returns_top_product(self, scorer):
        """best_match returns the highest-scoring product."""
        fresh = _product("AH Broccoli")
        mix = _product("Honig Mix aardappel, broccoli & rundervink", brand="Honig")

        best = scorer.best_match("broccoli", [mix, fresh])

        assert best is fresh

    def test_best_match_returns_none_for_empty(self, scorer):
        """best_match returns None for empty list."""
        best = scorer.best_match("broccoli", [])

        assert best is None


# =============================================================================
# Real-World Scenario Tests
# =============================================================================


class TestRealWorldScenarios:
    """Parametrized tests based on actual ordering failures."""

    @pytest.mark.parametrize(
        "search_term,correct,wrong",
        [
            (
                "broccoli",
                _product("AH Broccoli"),
                _product("Honig Mix aardappel, broccoli & rundervink", brand="Honig"),
            ),
            (
                "courgettes",
                _product("AH Courgette"),
                _product("Honig Mix aardappel, courgette & kip", brand="Honig"),
            ),
            (
                "tomaten",
                _product("AH Tomaten"),
                _product("Looye Honingtomaten", brand="Looye"),
            ),
            (
                "griekse yoghurt",
                _product("AH Yoghurt Griekse stijl"),
                _product(
                    "Campina High protein Greek yoghurt 1,5% fat",
                    brand="Campina",
                ),
            ),
        ],
    )
    def test_correct_product_ranks_higher(self, scorer, search_term, correct, wrong):
        """Verify the correct product scores higher than the known wrong match."""
        score_correct = scorer.score_product(search_term, correct)
        score_wrong = scorer.score_product(search_term, wrong)

        assert score_correct.total > score_wrong.total, (
            f"For '{search_term}': "
            f"'{correct.title}' ({score_correct.total:.1f}) should score higher than "
            f"'{wrong.title}' ({score_wrong.total:.1f})"
        )


# =============================================================================
# ProductScore Tests
# =============================================================================


class TestProductScore:
    """Tests for ProductScore dataclass."""

    def test_is_frozen(self, scorer):
        """ProductScore should be immutable."""
        product = _product("AH Broccoli")
        score = scorer.score_product("broccoli", product)

        with pytest.raises(AttributeError):
            score.total = 999.0

    def test_has_category_penalty_field(self, scorer):
        """ProductScore should have a penalty_category field."""
        product = _product("AH Broccoli")
        score = scorer.score_product("broccoli", product)

        assert hasattr(score, "penalty_category")
        assert score.penalty_category == 0.0


# =============================================================================
# Word Match Tests
# =============================================================================


class TestWordMatch:
    """Tests for _word_match helper (word-level matching)."""

    def test_exact_match(self, scorer):
        assert scorer._word_match("melk", "melk") is True

    def test_exact_match_different_words(self, scorer):
        assert scorer._word_match("melk", "kaas") is False

    def test_plural_prefix_ui_uien(self, scorer):
        """ui -> uien (Dutch plural, 2 extra chars)."""
        assert scorer._word_match("ui", "uien") is True

    def test_plural_prefix_broccoli_broccolini(self, scorer):
        """broccoli -> broccolini (2 extra chars)."""
        assert scorer._word_match("broccoli", "broccolini") is True

    def test_no_long_prefix_melk_melkchocolade(self, scorer):
        """melk should NOT match melkchocolade (9 extra chars)."""
        assert scorer._word_match("melk", "melkchocolade") is False

    def test_no_long_prefix_ui_uitloop(self, scorer):
        """ui should NOT match uitloop."""
        assert scorer._word_match("ui", "uitloop") is False

    def test_reverse_plural_courgettes_courgette(self, scorer):
        """courgettes -> courgette (reverse plural)."""
        assert scorer._word_match("courgettes", "courgette") is True

    def test_compound_suffix_bloem_tarwebloem(self, scorer):
        """bloem matches tarwebloem (Dutch compound, suffix >= 4 chars)."""
        assert scorer._word_match("bloem", "tarwebloem") is True

    def test_compound_suffix_eieren_scharreleieren(self, scorer):
        """eieren matches scharreleieren."""
        assert scorer._word_match("eieren", "scharreleieren") is True

    def test_compound_suffix_boter_roomboter(self, scorer):
        """boter matches roomboter."""
        assert scorer._word_match("boter", "roomboter") is True

    def test_no_short_suffix_ui_bosui(self, scorer):
        """ui (2 chars) should NOT match bosui via suffix (min 4 chars)."""
        assert scorer._word_match("ui", "bosui") is False

    def test_reverse_suffix_scharreleieren_eieren(self, scorer):
        """scharreleieren should match title word eieren (reverse suffix)."""
        assert scorer._word_match("scharreleieren", "eieren") is True

    def test_no_reverse_suffix_short_word(self, scorer):
        """Short title words (< 4 chars) should not match via reverse suffix."""
        assert scorer._word_match("kipfilet", "kip") is False

    def test_no_substring_ui_vuilniszakken(self, scorer):
        """ui should NOT match vuilniszakken."""
        assert scorer._word_match("ui", "vuilniszakken") is False

    def test_no_substring_zout_ongezouten(self, scorer):
        """zout should NOT match ongezouten."""
        assert scorer._word_match("zout", "ongezouten") is False

    def test_kaas_matches_pindakaas_suffix(self, scorer):
        """kaas matches pindakaas (suffix, 4 chars)."""
        assert scorer._word_match("kaas", "pindakaas") is True


# =============================================================================
# Word-Level Title Similarity Tests
# =============================================================================


class TestTitleSimilarityWordLevel:
    """Tests for word-level title matching (prevents substring false positives)."""

    def test_ui_does_not_match_vuilniszakken(self, scorer):
        score = scorer._title_similarity(
            "ui", "Swirl Vuilniszakken met fixeerband 30 liter"
        )
        assert score == 0.0

    def test_ui_matches_ah_uien(self, scorer):
        score = scorer._title_similarity("ui", "AH Gele uien")
        assert score > 0.0

    def test_melk_does_not_match_melkchocolade(self, scorer):
        score = scorer._title_similarity("melk", "Kitkat Mini melkchocolade uitdeelzak")
        assert score == 0.0

    def test_zout_does_not_match_ongezouten(self, scorer):
        score = scorer._title_similarity("zout", "AH Roomboter ongezouten")
        assert score == 0.0

    def test_tomaten_matches_honingtomaten_via_suffix(self, scorer):
        """tomaten should still match Honingtomaten via compound suffix."""
        score = scorer._title_similarity("tomaten", "Looye Honingtomaten")
        assert score > 0.0

    def test_coverage_capped_at_one(self, scorer):
        """Coverage should not exceed 1.0."""
        # 4 search words, 1 title word: coverage = min(4/1, 1) = 1.0
        score = scorer._title_similarity("geraspte kaas voor ovengratin", "Pindakaas")
        # "kaas" matches "pindakaas" (suffix), so 1/4 words match
        # score = 0.25*60 + 1.0*40 = 55, NOT 0.25*60 + 4.0*40 = 175
        assert score <= 60.0

    def test_scharreleieren_matches_eieren_in_title(self, scorer):
        """scharreleieren should match via suffix on title word 'eieren'."""
        score = scorer._title_similarity("scharreleieren", "AH Vrije uitloop eieren M")
        assert score > 0.0


# =============================================================================
# NON_FOOD / Extended Processed Penalty Tests
# =============================================================================


class TestExtendedPenalties:
    """Tests for expanded penalty indicators."""

    def test_soep_in_title_penalized(self, scorer):
        product = _product("AH Biologisch Courgettesoep")
        score = scorer.score_product("courgettes", product)
        assert score.penalty_processed < 0

    def test_chocolade_in_title_penalized(self, scorer):
        product = _product("Kitkat Mini melkchocolade uitdeelzak", brand="Kitkat")
        score = scorer.score_product("melk", product)
        assert score.penalty_processed < 0

    def test_reiniger_in_title_penalized(self, scorer):
        product = _product("AH Allesreiniger bloemen & fruit")
        score = scorer.score_product("bloem", product)
        assert score.penalty_processed < 0

    def test_vuilniszakken_penalized(self, scorer):
        product = _product("Swirl Vuilniszakken met fixeerband", brand="Swirl")
        score = scorer.score_product("ui", product)
        assert score.penalty_processed < 0

    def test_koek_in_title_penalized(self, scorer):
        product = _product("Bolletje Ontbijtkoek naturel gesneden", brand="Bolletje")
        score = scorer.score_product("gesneden rodekool", product)
        assert score.penalty_processed < 0


# =============================================================================
# Category Penalty Tests
# =============================================================================


class TestCategoryPenalty:
    """Tests for category-based penalty."""

    def test_huishouden_category_penalized(self, scorer):
        product = _product(
            "AH Allesreiniger",
            category="Huishouden/Schoonmaakmiddelen",
        )
        score = scorer.score_product("bloem", product)
        assert score.penalty_category <= -50.0

    def test_food_category_no_penalty(self, scorer):
        product = _product("AH Tarwebloem", category="Meel, suiker/Bakmeel")
        score = scorer.score_product("bloem", product)
        assert score.penalty_category == 0.0

    def test_empty_category_no_penalty(self, scorer):
        product = _product("AH Tarwebloem", category="")
        score = scorer.score_product("bloem", product)
        assert score.penalty_category == 0.0

    def test_persoonlijke_verzorging_penalized(self, scorer):
        product = _product(
            "AH Shampoo",
            category="Persoonlijke verzorging/Haarverzorging",
        )
        score = scorer.score_product("shampoo", product)
        assert score.penalty_category <= -50.0


# =============================================================================
# Real-World Reference List False Positive Tests
# =============================================================================


class TestReferenceListFalsePositives:
    """Tests based on actual bestelling-2.md failures.

    These products should score VERY LOW (negative or near-zero) to prevent
    them from being selected in reference list matching.
    """

    @pytest.mark.parametrize(
        "search_term,wrong_title,wrong_brand,wrong_category",
        [
            (
                "ui",
                "Swirl Vuilniszakken met fixeerband 30 liter",
                "Swirl",
                "Huishouden",
            ),
            (
                "bloem",
                "AH Allesreiniger bloemen & fruit",
                "AH",
                "Huishouden/Schoonmaakmiddelen",
            ),
            (
                "melk",
                "Kitkat Mini melkchocolade uitdeelzak",
                "Kitkat",
                "Snoep",
            ),
            (
                "zout",
                "AH Biologisch Roomboter ongezouten",
                "AH",
                "Zuivel",
            ),
            (
                "gesneden rodekool",
                "Bolletje Ontbijtkoek naturel gesneden",
                "Bolletje",
                "Brood, koek",
            ),
            (
                "vegetarische kipstuckjes",
                "AH Scharrel kipfilet 2 stuks",
                "AH",
                "Vlees",
            ),
        ],
    )
    def test_wrong_product_scores_below_threshold(
        self, scorer, search_term, wrong_title, wrong_brand, wrong_category
    ):
        """Wrong products from reference list should score below reference threshold."""
        product = _product(wrong_title, brand=wrong_brand, category=wrong_category)
        score = scorer.score_product(search_term, product)

        # Reference match threshold is 40.0 - these should be below it
        assert score.total < 40.0, (
            f"For '{search_term}': '{wrong_title}' scored {score.total:.1f} "
            f"(title={score.title_score:.1f}, brand={score.brand_score:.1f}, "
            f"processed={score.penalty_processed:.1f}, "
            f"category={score.penalty_category:.1f})"
        )
