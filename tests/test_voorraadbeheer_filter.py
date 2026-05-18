"""Tests voor BoodschappenlijstFilter."""

from __future__ import annotations

from pathlib import Path

from boodschappenagent.boodschappenlijst.models import (
    Boodschappenlijst,
    BoodschappenRegel,
)
from boodschappenagent.boodschappenlijst.filter import BoodschappenlijstFilter
from boodschappenagent.voorraadbeheer.models import VoorraadItem, VoorraadType
from boodschappenagent.voorraadbeheer.repository import VoorraadRepository


def _make_regel(
    naam: str, hoeveelheid: float = 1.0, eenheid: str = "stuks"
) -> BoodschappenRegel:
    return BoodschappenRegel(
        naam=naam,
        hoeveelheid=hoeveelheid,
        eenheid=eenheid,
        originele_namen=frozenset({naam}),
    )


def _make_item(
    naam: str,
    type: VoorraadType = VoorraadType.HOUDBAAR,
    op_voorraad: bool = True,
) -> VoorraadItem:
    return VoorraadItem(
        naam=naam, type=type, op_voorraad=op_voorraad, laatst_gecheckt="2026-02-14"
    )


class TestFilterOpVoorraad:
    def test_removes_items_in_stock(self, tmp_path: Path) -> None:
        repo = VoorraadRepository(tmp_path / "voorraad.json")
        repo.save([_make_item("pasta", op_voorraad=True)])

        lijst = Boodschappenlijst(
            week_start="2026-02-16",
            regels=[
                _make_regel("pasta", 250, "gram"),
                _make_regel("tomaat", 3, "stuks"),
            ],
        )

        filt = BoodschappenlijstFilter(repo)
        result = filt.filter_op_voorraad(lijst)

        namen = {r.naam for r in result.regels}
        assert "pasta" not in namen
        assert "tomaat" in namen

    def test_keeps_items_not_in_stock(self, tmp_path: Path) -> None:
        repo = VoorraadRepository(tmp_path / "voorraad.json")
        repo.save([_make_item("pasta", op_voorraad=False)])

        lijst = Boodschappenlijst(
            week_start="2026-02-16",
            regels=[_make_regel("pasta", 250, "gram")],
        )

        filt = BoodschappenlijstFilter(repo)
        result = filt.filter_op_voorraad(lijst)

        namen = {r.naam for r in result.regels}
        assert "pasta" in namen

    def test_preserves_week_start(self, tmp_path: Path) -> None:
        repo = VoorraadRepository(tmp_path / "voorraad.json")
        lijst = Boodschappenlijst(week_start="2026-02-16", regels=[])

        filt = BoodschappenlijstFilter(repo)
        result = filt.filter_op_voorraad(lijst)
        assert result.week_start == "2026-02-16"


class TestVerseBasicsToevoegen:
    def test_adds_verse_basics_not_in_stock(self, tmp_path: Path) -> None:
        repo = VoorraadRepository(tmp_path / "voorraad.json")
        repo.save(
            [
                _make_item("melk", VoorraadType.VERS_BASIS, op_voorraad=False),
                _make_item("eieren", VoorraadType.VERS_BASIS, op_voorraad=True),
            ]
        )

        lijst = Boodschappenlijst(week_start="2026-02-16", regels=[])

        filt = BoodschappenlijstFilter(repo)
        result = filt.filter_op_voorraad(lijst)

        namen = {r.naam for r in result.regels}
        assert "melk" in namen
        assert "eieren" not in namen

    def test_verse_basics_have_correct_details(self, tmp_path: Path) -> None:
        repo = VoorraadRepository(tmp_path / "voorraad.json")
        repo.save([_make_item("melk", VoorraadType.VERS_BASIS, op_voorraad=False)])

        lijst = Boodschappenlijst(week_start="2026-02-16", regels=[])

        filt = BoodschappenlijstFilter(repo)
        result = filt.filter_op_voorraad(lijst)

        melk = next(r for r in result.regels if r.naam == "melk")
        assert melk.hoeveelheid > 0
        assert melk.eenheid != ""


class TestGecombineerdFilterEnToevoegen:
    def test_filter_and_add_in_one_flow(self, tmp_path: Path) -> None:
        repo = VoorraadRepository(tmp_path / "voorraad.json")
        repo.save(
            [
                _make_item("pasta", VoorraadType.HOUDBAAR, op_voorraad=True),
                _make_item("rijst", VoorraadType.HOUDBAAR, op_voorraad=False),
                _make_item("melk", VoorraadType.VERS_BASIS, op_voorraad=False),
                _make_item("eieren", VoorraadType.VERS_BASIS, op_voorraad=True),
            ]
        )

        lijst = Boodschappenlijst(
            week_start="2026-02-16",
            regels=[
                _make_regel("pasta", 250, "gram"),
                _make_regel("rijst", 300, "gram"),
                _make_regel("tomaat", 3, "stuks"),
            ],
        )

        filt = BoodschappenlijstFilter(repo)
        result = filt.filter_op_voorraad(lijst)

        namen = {r.naam for r in result.regels}
        # pasta is op voorraad → verwijderd
        assert "pasta" not in namen
        # rijst is niet op voorraad → behouden
        assert "rijst" in namen
        # tomaat is niet in voorraad → behouden
        assert "tomaat" in namen
        # melk is vers_basis + niet op voorraad → toegevoegd
        assert "melk" in namen
        # eieren is vers_basis + op voorraad → niet toegevoegd
        assert "eieren" not in namen

    def test_no_duplicate_when_verse_basic_already_in_list(
        self, tmp_path: Path
    ) -> None:
        repo = VoorraadRepository(tmp_path / "voorraad.json")
        repo.save([_make_item("melk", VoorraadType.VERS_BASIS, op_voorraad=False)])

        lijst = Boodschappenlijst(
            week_start="2026-02-16",
            regels=[_make_regel("melk", 0.5, "liter")],
        )

        filt = BoodschappenlijstFilter(repo)
        result = filt.filter_op_voorraad(lijst)

        melk_regels = [r for r in result.regels if r.naam == "melk"]
        # melk stond al in de lijst en is niet op voorraad → behouden (niet dubbel)
        assert len(melk_regels) == 1

    def test_result_sorted_alphabetically(self, tmp_path: Path) -> None:
        repo = VoorraadRepository(tmp_path / "voorraad.json")
        repo.save([_make_item("melk", VoorraadType.VERS_BASIS, op_voorraad=False)])

        lijst = Boodschappenlijst(
            week_start="2026-02-16",
            regels=[_make_regel("tomaat"), _make_regel("aardappel")],
        )

        filt = BoodschappenlijstFilter(repo)
        result = filt.filter_op_voorraad(lijst)

        namen = [r.naam for r in result.regels]
        assert namen == sorted(namen)


class TestVoegPantryToe:
    """T016: voeg_pantry_toe() voegt pantry-items toe zonder stap-1 filter."""

    def test_voeg_verse_basis_toe_die_niet_op_voorraad_is(self, tmp_path: Path) -> None:
        """VERS_BASIS item niet op voorraad → toegevoegd aan lijst."""
        repo = VoorraadRepository(tmp_path / "voorraad.json")
        repo.save([_make_item("melk", VoorraadType.VERS_BASIS, op_voorraad=False)])

        lijst = Boodschappenlijst(week_start="2026-02-16", regels=[])
        filt = BoodschappenlijstFilter(repo)
        result = filt.voeg_pantry_toe(lijst)

        namen = {r.naam for r in result.regels}
        assert "melk" in namen

    def test_voeg_houdbaar_toe_dat_niet_op_voorraad_is(self, tmp_path: Path) -> None:
        """HOUDBAAR item niet op voorraad → toegevoegd aan lijst."""
        repo = VoorraadRepository(tmp_path / "voorraad.json")
        repo.save([_make_item("pasta", VoorraadType.HOUDBAAR, op_voorraad=False)])

        lijst = Boodschappenlijst(week_start="2026-02-16", regels=[])
        filt = BoodschappenlijstFilter(repo)
        result = filt.voeg_pantry_toe(lijst)

        namen = {r.naam for r in result.regels}
        assert "pasta" in namen

    def test_voegt_geen_item_op_voorraad_toe(self, tmp_path: Path) -> None:
        """Item dat op voorraad is wordt NIET toegevoegd."""
        repo = VoorraadRepository(tmp_path / "voorraad.json")
        repo.save([_make_item("pasta", VoorraadType.HOUDBAAR, op_voorraad=True)])

        lijst = Boodschappenlijst(week_start="2026-02-16", regels=[])
        filt = BoodschappenlijstFilter(repo)
        result = filt.voeg_pantry_toe(lijst)

        namen = {r.naam for r in result.regels}
        assert "pasta" not in namen

    def test_filtert_niet_op_voorraad(self, tmp_path: Path) -> None:
        """Items op voorraad worden NIET gefilterd — stap 1 overgeslagen."""
        repo = VoorraadRepository(tmp_path / "voorraad.json")
        repo.save([_make_item("pasta", VoorraadType.HOUDBAAR, op_voorraad=True)])

        lijst = Boodschappenlijst(
            week_start="2026-02-16",
            regels=[_make_regel("pasta", 500, "g")],
        )
        filt = BoodschappenlijstFilter(repo)
        result = filt.voeg_pantry_toe(lijst)

        namen = {r.naam for r in result.regels}
        assert "pasta" in namen

    def test_geen_duplicaten(self, tmp_path: Path) -> None:
        """Item al in lijst → niet nogmaals toegevoegd door pantry."""
        repo = VoorraadRepository(tmp_path / "voorraad.json")
        repo.save([_make_item("pasta", VoorraadType.HOUDBAAR, op_voorraad=False)])

        lijst = Boodschappenlijst(
            week_start="2026-02-16",
            regels=[_make_regel("pasta", 500, "g")],
        )
        filt = BoodschappenlijstFilter(repo)
        result = filt.voeg_pantry_toe(lijst)

        pasta_regels = [r for r in result.regels if r.naam == "pasta"]
        assert len(pasta_regels) == 1
