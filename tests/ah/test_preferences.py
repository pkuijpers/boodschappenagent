"""Tests voor MatchVoorkeur, MatchReviewItem en MatchVoorkeurenRepository."""

import json

import pytest

from boodschappenagent.ah.preferences import (
    MatchReviewItem,
    MatchVoorkeur,
    MatchVoorkeurenRepository,
)

# ── MatchVoorkeur ──────────────────────────────────────────────────────────────


class TestMatchVoorkeur:
    """T002: MatchVoorkeur frozen dataclass validatie en serialisatie."""

    def test_aanmaken_geldige_voorkeur(self):
        """MatchVoorkeur aanmaken met geldige velden."""
        v = MatchVoorkeur(
            ingredient_naam="melk",
            article_id=123456,
            product_naam="AH Volle melk 1L",
            updated_at="2026-05-14T10:00:00",
        )
        assert v.ingredient_naam == "melk"
        assert v.article_id == 123456
        assert v.product_naam == "AH Volle melk 1L"
        assert v.updated_at == "2026-05-14T10:00:00"

    def test_to_dict_retourneert_alle_velden(self):
        """to_dict() bevat alle vier velden."""
        v = MatchVoorkeur(
            ingredient_naam="oregano",
            article_id=789012,
            product_naam="AH Oregano gedroogd 15g",
            updated_at="2026-05-14T10:01:00",
        )
        d = v.to_dict()
        assert d == {
            "ingredient_naam": "oregano",
            "article_id": 789012,
            "product_naam": "AH Oregano gedroogd 15g",
            "updated_at": "2026-05-14T10:01:00",
        }

    def test_from_dict_reconstrueert_object(self):
        """from_dict() reconstrueert identiek object."""
        data = {
            "ingredient_naam": "melk",
            "article_id": 123456,
            "product_naam": "AH Volle melk 1L",
            "updated_at": "2026-05-14T10:00:00",
        }
        v = MatchVoorkeur.from_dict(data)
        assert v.ingredient_naam == "melk"
        assert v.article_id == 123456

    def test_roundtrip_to_dict_from_dict(self):
        """to_dict() gevolgd door from_dict() geeft gelijk object."""
        v = MatchVoorkeur(
            ingredient_naam="pasta",
            article_id=111,
            product_naam="AH Penne 500g",
            updated_at="2026-01-01T00:00:00",
        )
        assert MatchVoorkeur.from_dict(v.to_dict()) == v

    def test_frozen_dataclass_is_immutable(self):
        """MatchVoorkeur is frozen — attributen zijn niet wijzigbaar."""
        v = MatchVoorkeur(
            ingredient_naam="melk",
            article_id=123456,
            product_naam="AH Volle melk 1L",
            updated_at="2026-05-14T10:00:00",
        )
        with pytest.raises((AttributeError, TypeError)):
            v.article_id = 999  # type: ignore[misc]

    def test_validatie_lege_ingredient_naam(self):
        """Lege ingredient_naam gooit ValueError."""
        with pytest.raises(ValueError, match="ingredient_naam"):
            MatchVoorkeur(
                ingredient_naam="",
                article_id=123,
                product_naam="Test",
                updated_at="2026-01-01T00:00:00",
            )

    def test_validatie_whitespace_ingredient_naam(self):
        """Ingredient_naam met alleen whitespace gooit ValueError."""
        with pytest.raises(ValueError, match="ingredient_naam"):
            MatchVoorkeur(
                ingredient_naam="   ",
                article_id=123,
                product_naam="Test",
                updated_at="2026-01-01T00:00:00",
            )

    def test_validatie_negatief_article_id(self):
        """Negatief article_id gooit ValueError."""
        with pytest.raises(ValueError, match="article_id"):
            MatchVoorkeur(
                ingredient_naam="melk",
                article_id=-1,
                product_naam="Test",
                updated_at="2026-01-01T00:00:00",
            )

    def test_validatie_nul_article_id(self):
        """article_id=0 gooit ValueError (moet positief zijn)."""
        with pytest.raises(ValueError, match="article_id"):
            MatchVoorkeur(
                ingredient_naam="melk",
                article_id=0,
                product_naam="Test",
                updated_at="2026-01-01T00:00:00",
            )


# ── MatchReviewItem ────────────────────────────────────────────────────────────


class TestMatchReviewItem:
    """T003: MatchReviewItem mutable dataclass velden en defaults."""

    def test_aanmaken_met_product(self):
        """MatchReviewItem aanmaken met een product (gevonden match)."""
        item = MatchReviewItem(
            id="uuid-1",
            naam="melk",
            hoeveelheid=1.0,
            eenheid="liter",
            product=object(),
            bron="zoekopdracht",
            gecorrigeerd=False,
            aantal=1,
        )
        assert item.id == "uuid-1"
        assert item.naam == "melk"
        assert item.hoeveelheid == 1.0
        assert item.eenheid == "liter"
        assert item.bron == "zoekopdracht"
        assert item.gecorrigeerd is False
        assert item.aantal == 1

    def test_aanmaken_zonder_product(self):
        """MatchReviewItem met product=None (geen match)."""
        item = MatchReviewItem(
            id="uuid-2",
            naam="quinoa",
            hoeveelheid=200.0,
            eenheid="gram",
            product=None,
            bron="niet_gevonden",
            gecorrigeerd=False,
            aantal=1,
        )
        assert item.product is None
        assert item.bron == "niet_gevonden"

    def test_gecorrigeerd_default_false(self):
        """gecorrigeerd is False tenzij expliciet anders gezet."""
        item = MatchReviewItem(
            id="uuid-3",
            naam="pasta",
            hoeveelheid=500.0,
            eenheid="gram",
            product=None,
            bron="niet_gevonden",
            gecorrigeerd=False,
            aantal=1,
        )
        assert item.gecorrigeerd is False

    def test_gecorrigeerd_kan_worden_bijgewerkt(self):
        """MatchReviewItem is mutable — gecorrigeerd kan op True worden gezet."""
        item = MatchReviewItem(
            id="uuid-4",
            naam="melk",
            hoeveelheid=1.0,
            eenheid="liter",
            product=None,
            bron="zoekopdracht",
            gecorrigeerd=False,
            aantal=1,
        )
        item.gecorrigeerd = True
        assert item.gecorrigeerd is True

    def test_hoeveelheid_kan_none_zijn(self):
        """hoeveelheid mag None zijn (handmatig artikel zonder hoeveelheid)."""
        item = MatchReviewItem(
            id="uuid-5",
            naam="zeep",
            hoeveelheid=None,
            eenheid="stuks",
            product=None,
            bron="niet_gevonden",
            gecorrigeerd=False,
            aantal=1,
        )
        assert item.hoeveelheid is None

    @pytest.mark.parametrize(
        "bron",
        [
            "voorkeur",
            "voorkeur_niet_beschikbaar",
            "referentie",
            "zoekopdracht",
            "niet_gevonden",
        ],
    )
    def test_bron_accepteert_alle_geldige_waarden(self, bron):
        """bron accepteert de vijf gedefinieerde waarden per data-model.md."""
        item = MatchReviewItem(
            id="uuid-6",
            naam="test",
            hoeveelheid=1.0,
            eenheid="stuks",
            product=None,
            bron=bron,
            gecorrigeerd=False,
            aantal=1,
        )
        assert item.bron == bron


# ── MatchVoorkeurenRepository ──────────────────────────────────────────────────


class TestMatchVoorkeurenRepository:
    """T021: MatchVoorkeurenRepository get/save/delete gedrag."""

    @pytest.fixture
    def repo(self, tmp_path) -> MatchVoorkeurenRepository:
        """Repository met tijdelijk pad (geen echte data/match_preferences.json)."""
        return MatchVoorkeurenRepository(tmp_path / "match_preferences.json")

    @pytest.fixture
    def repo_met_melk(self, repo) -> MatchVoorkeurenRepository:
        """Repository met één opgeslagen voorkeur voor 'melk'."""
        repo.save(
            MatchVoorkeur(
                ingredient_naam="melk",
                article_id=123456,
                product_naam="AH Volle melk 1L",
                updated_at="2026-05-14T10:00:00",
            )
        )
        return repo

    def test_get_onbekende_naam_retourneert_none(self, repo):
        """get() retourneert None voor een onbekende ingredientnaam."""
        assert repo.get("quinoa") is None

    def test_get_bekende_naam_retourneert_voorkeur(self, repo_met_melk):
        """get() retourneert MatchVoorkeur voor een bekende naam."""
        v = repo_met_melk.get("melk")
        assert v is not None
        assert v.article_id == 123456
        assert v.product_naam == "AH Volle melk 1L"

    def test_save_upsert_overschrijft_bestaande_voorkeur(self, repo_met_melk):
        """save() overschrijft bestaande voorkeur voor dezelfde naam (upsert)."""
        nieuwe_voorkeur = MatchVoorkeur(
            ingredient_naam="melk",
            article_id=999999,
            product_naam="Campina Melk 1L",
            updated_at="2026-05-15T09:00:00",
        )
        repo_met_melk.save(nieuwe_voorkeur)
        v = repo_met_melk.get("melk")
        assert v is not None
        assert v.article_id == 999999

    def test_delete_verwijdert_voorkeur(self, repo_met_melk):
        """delete() verwijdert een bestaande voorkeur."""
        repo_met_melk.delete("melk")
        assert repo_met_melk.get("melk") is None

    def test_delete_noop_voor_onbekende_naam(self, repo):
        """delete() is een no-op als de naam niet bestaat (geen fout)."""
        repo.delete("niet_bestaand_ingredient")  # Mag geen exception gooien

    def test_save_maakt_bestand_aan_bij_eerste_opslag(self, tmp_path):
        """save() maakt data/match_preferences.json aan bij eerste opslag."""
        pad = tmp_path / "subdir" / "match_preferences.json"
        repo = MatchVoorkeurenRepository(pad)
        assert not pad.exists()
        repo.save(
            MatchVoorkeur(
                ingredient_naam="oregano",
                article_id=789012,
                product_naam="AH Oregano gedroogd 15g",
                updated_at="2026-05-14T10:01:00",
            )
        )
        assert pad.exists()

    def test_persistentie_tussen_instanties(self, tmp_path):
        """Data van één instantie is leesbaar door een nieuwe instantie."""
        pad = tmp_path / "match_preferences.json"
        repo1 = MatchVoorkeurenRepository(pad)
        repo1.save(
            MatchVoorkeur(
                ingredient_naam="pasta",
                article_id=111,
                product_naam="AH Penne 500g",
                updated_at="2026-01-01T00:00:00",
            )
        )

        repo2 = MatchVoorkeurenRepository(pad)
        v = repo2.get("pasta")
        assert v is not None
        assert v.article_id == 111

    def test_json_bestandsformaat(self, tmp_path):
        """Opgeslagen bestand heeft verwacht JSON formaat (genest dict op naam)."""
        pad = tmp_path / "match_preferences.json"
        repo = MatchVoorkeurenRepository(pad)
        repo.save(
            MatchVoorkeur(
                ingredient_naam="melk",
                article_id=123456,
                product_naam="AH Volle melk 1L",
                updated_at="2026-05-14T10:00:00",
            )
        )

        raw = json.loads(pad.read_text(encoding="utf-8"))
        assert "melk" in raw
        assert raw["melk"]["article_id"] == 123456
