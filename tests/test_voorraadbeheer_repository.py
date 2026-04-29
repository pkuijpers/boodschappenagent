"""Tests voor VoorraadRepository."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from boodschappenagent.voorraadbeheer.models import VoorraadItem, VoorraadType
from boodschappenagent.voorraadbeheer.repository import VoorraadRepository


def _make_item(
    naam: str = "pasta",
    type: VoorraadType = VoorraadType.HOUDBAAR,
    op_voorraad: bool = True,
    laatst_gecheckt: str = "2026-02-14",
) -> VoorraadItem:
    return VoorraadItem(
        naam=naam,
        type=type,
        op_voorraad=op_voorraad,
        laatst_gecheckt=laatst_gecheckt,
    )


class TestVoorraadRepositoryLoad:
    def test_load_nonexistent_returns_empty(self, tmp_path: Path) -> None:
        repo = VoorraadRepository(tmp_path / "voorraad.json")
        assert repo.load() == []

    def test_load_existing_file(self, tmp_path: Path) -> None:
        path = tmp_path / "voorraad.json"
        data = [
            {
                "naam": "pasta",
                "type": "houdbaar",
                "op_voorraad": True,
                "laatst_gecheckt": "2026-02-14",
            }
        ]
        path.write_text(json.dumps(data), encoding="utf-8")

        repo = VoorraadRepository(path)
        items = repo.load()
        assert len(items) == 1
        assert items[0].naam == "pasta"
        assert items[0].type is VoorraadType.HOUDBAAR

    def test_load_invalid_json_raises(self, tmp_path: Path) -> None:
        path = tmp_path / "voorraad.json"
        path.write_text("not json!", encoding="utf-8")

        repo = VoorraadRepository(path)
        with pytest.raises(ValueError, match="Ongeldig JSON formaat"):
            repo.load()


class TestVoorraadRepositorySave:
    def test_save_creates_file(self, tmp_path: Path) -> None:
        path = tmp_path / "voorraad.json"
        repo = VoorraadRepository(path)
        repo.save([_make_item()])
        assert path.exists()

    def test_save_creates_parent_dirs(self, tmp_path: Path) -> None:
        path = tmp_path / "sub" / "dir" / "voorraad.json"
        repo = VoorraadRepository(path)
        repo.save([_make_item()])
        assert path.exists()

    def test_roundtrip_save_load(self, tmp_path: Path) -> None:
        path = tmp_path / "voorraad.json"
        repo = VoorraadRepository(path)
        items = [
            _make_item("pasta", VoorraadType.HOUDBAAR, True),
            _make_item("melk", VoorraadType.VERS_BASIS, False),
        ]
        repo.save(items)
        loaded = repo.load()
        assert loaded == items

    def test_save_pretty_prints_json(self, tmp_path: Path) -> None:
        path = tmp_path / "voorraad.json"
        repo = VoorraadRepository(path)
        repo.save([_make_item()])
        content = path.read_text(encoding="utf-8")
        assert "\n" in content  # Pretty-printed, not compact


class TestVoorraadRepositoryUpdateItem:
    def test_update_existing_item(self, tmp_path: Path) -> None:
        path = tmp_path / "voorraad.json"
        repo = VoorraadRepository(path)
        repo.save([_make_item("pasta", op_voorraad=True)])

        updated = _make_item("pasta", op_voorraad=False)
        repo.update_item(updated)

        items = repo.load()
        assert len(items) == 1
        assert items[0].op_voorraad is False

    def test_update_adds_new_item(self, tmp_path: Path) -> None:
        path = tmp_path / "voorraad.json"
        repo = VoorraadRepository(path)
        repo.save([_make_item("pasta")])

        repo.update_item(_make_item("rijst"))

        items = repo.load()
        assert len(items) == 2
        namen = {i.naam for i in items}
        assert namen == {"pasta", "rijst"}

    def test_update_case_insensitive_match(self, tmp_path: Path) -> None:
        path = tmp_path / "voorraad.json"
        repo = VoorraadRepository(path)
        repo.save([_make_item("Pasta")])

        updated = _make_item("pasta", op_voorraad=False)
        repo.update_item(updated)

        items = repo.load()
        assert len(items) == 1
        assert items[0].naam == "pasta"
        assert items[0].op_voorraad is False


class TestVoorraadRepositorySyncMetAHNamen:
    def test_nieuw_ah_item_wordt_toegevoegd(self, tmp_path: Path) -> None:
        repo = VoorraadRepository(tmp_path / "voorraad.json")
        repo.sync_met_ah_namen({"Melk", "Eieren"})
        namen = {i.naam for i in repo.load()}
        assert namen == {"melk", "eieren"}

    def test_nieuw_item_standaard_niet_op_voorraad(self, tmp_path: Path) -> None:
        repo = VoorraadRepository(tmp_path / "voorraad.json")
        repo.sync_met_ah_namen({"Melk"})
        assert repo.load()[0].op_voorraad is False

    def test_bestaand_item_behoudt_op_voorraad_status(self, tmp_path: Path) -> None:
        path = tmp_path / "voorraad.json"
        repo = VoorraadRepository(path)
        repo.save([_make_item("melk", op_voorraad=False)])
        repo.sync_met_ah_namen({"Melk"})
        items = repo.load()
        assert len(items) == 1
        assert items[0].naam == "melk"
        assert items[0].op_voorraad is False

    def test_item_niet_op_ah_lijst_wordt_verwijderd(self, tmp_path: Path) -> None:
        path = tmp_path / "voorraad.json"
        repo = VoorraadRepository(path)
        repo.save([_make_item("pasta"), _make_item("rijst")])
        repo.sync_met_ah_namen({"pasta"})
        namen = {i.naam for i in repo.load()}
        assert namen == {"pasta"}

    def test_lege_ah_lijst_verwijdert_alle_items(self, tmp_path: Path) -> None:
        path = tmp_path / "voorraad.json"
        repo = VoorraadRepository(path)
        repo.save([_make_item("pasta")])
        repo.sync_met_ah_namen(set())
        assert repo.load() == []


class TestVoorraadRepositoryOpVoorraadNamen:
    def test_returns_names_in_stock(self, tmp_path: Path) -> None:
        path = tmp_path / "voorraad.json"
        repo = VoorraadRepository(path)
        repo.save(
            [
                _make_item("pasta", op_voorraad=True),
                _make_item("rijst", op_voorraad=False),
                _make_item("melk", VoorraadType.VERS_BASIS, op_voorraad=True),
            ]
        )

        namen = repo.op_voorraad_namen()
        assert namen == {"pasta", "melk"}

    def test_empty_returns_empty_set(self, tmp_path: Path) -> None:
        repo = VoorraadRepository(tmp_path / "voorraad.json")
        assert repo.op_voorraad_namen() == set()
