"""Tests voor voorraadbeheer data models."""

from __future__ import annotations

import pytest

from boodschappenagent.voorraadbeheer.models import (
    CheckSuggestie,
    SuggestiePrioriteit,
    VoorraadItem,
    VoorraadType,
)


class TestVoorraadType:
    def test_houdbaar_value(self) -> None:
        assert VoorraadType.HOUDBAAR.value == "houdbaar"

    def test_vers_basis_value(self) -> None:
        assert VoorraadType.VERS_BASIS.value == "vers_basis"

    def test_from_string(self) -> None:
        assert VoorraadType("houdbaar") is VoorraadType.HOUDBAAR
        assert VoorraadType("vers_basis") is VoorraadType.VERS_BASIS


class TestSuggestiePrioriteit:
    def test_values(self) -> None:
        assert SuggestiePrioriteit.HIGH.value == "high"
        assert SuggestiePrioriteit.MEDIUM.value == "medium"
        assert SuggestiePrioriteit.LOW.value == "low"

    def test_ordering(self) -> None:
        prios = [
            SuggestiePrioriteit.LOW,
            SuggestiePrioriteit.HIGH,
            SuggestiePrioriteit.MEDIUM,
        ]
        gesorteerd = sorted(prios, key=lambda p: list(SuggestiePrioriteit).index(p))
        assert gesorteerd == [
            SuggestiePrioriteit.HIGH,
            SuggestiePrioriteit.MEDIUM,
            SuggestiePrioriteit.LOW,
        ]


class TestVoorraadItem:
    def test_create_valid(self) -> None:
        item = VoorraadItem(
            naam="pasta",
            type=VoorraadType.HOUDBAAR,
            op_voorraad=True,
            laatst_gecheckt="2026-02-14",
        )
        assert item.naam == "pasta"
        assert item.type is VoorraadType.HOUDBAAR
        assert item.op_voorraad is True
        assert item.laatst_gecheckt == "2026-02-14"

    def test_create_vers_basis(self) -> None:
        item = VoorraadItem(
            naam="melk",
            type=VoorraadType.VERS_BASIS,
            op_voorraad=False,
            laatst_gecheckt="2026-02-14",
        )
        assert item.type is VoorraadType.VERS_BASIS
        assert item.op_voorraad is False

    def test_frozen(self) -> None:
        item = VoorraadItem(
            naam="pasta",
            type=VoorraadType.HOUDBAAR,
            op_voorraad=True,
            laatst_gecheckt="2026-02-14",
        )
        with pytest.raises(AttributeError):
            item.op_voorraad = False  # type: ignore[misc]

    def test_naam_leeg_raises(self) -> None:
        with pytest.raises(ValueError, match="naam mag niet leeg zijn"):
            VoorraadItem(
                naam="",
                type=VoorraadType.HOUDBAAR,
                op_voorraad=True,
                laatst_gecheckt="2026-02-14",
            )

    def test_naam_whitespace_raises(self) -> None:
        with pytest.raises(ValueError, match="naam mag niet leeg zijn"):
            VoorraadItem(
                naam="  ",
                type=VoorraadType.HOUDBAAR,
                op_voorraad=True,
                laatst_gecheckt="2026-02-14",
            )

    def test_ongeldige_datum_raises(self) -> None:
        with pytest.raises(ValueError, match="Ongeldige datum"):
            VoorraadItem(
                naam="pasta",
                type=VoorraadType.HOUDBAAR,
                op_voorraad=True,
                laatst_gecheckt="not-a-date",
            )

    def test_lege_datum_raises(self) -> None:
        with pytest.raises(ValueError, match="laatst_gecheckt mag niet leeg zijn"):
            VoorraadItem(
                naam="pasta",
                type=VoorraadType.HOUDBAAR,
                op_voorraad=True,
                laatst_gecheckt="",
            )

    def test_to_dict(self) -> None:
        item = VoorraadItem(
            naam="pasta",
            type=VoorraadType.HOUDBAAR,
            op_voorraad=True,
            laatst_gecheckt="2026-02-14",
        )
        d = item.to_dict()
        assert d == {
            "naam": "pasta",
            "type": "houdbaar",
            "op_voorraad": True,
            "laatst_gecheckt": "2026-02-14",
        }

    def test_from_dict(self) -> None:
        data = {
            "naam": "melk",
            "type": "vers_basis",
            "op_voorraad": False,
            "laatst_gecheckt": "2026-02-14",
        }
        item = VoorraadItem.from_dict(data)
        assert item.naam == "melk"
        assert item.type is VoorraadType.VERS_BASIS
        assert item.op_voorraad is False

    def test_roundtrip_dict(self) -> None:
        item = VoorraadItem(
            naam="rijst",
            type=VoorraadType.HOUDBAAR,
            op_voorraad=False,
            laatst_gecheckt="2026-01-01",
        )
        assert VoorraadItem.from_dict(item.to_dict()) == item


class TestCheckSuggestie:
    def test_create_valid(self) -> None:
        s = CheckSuggestie(
            naam="melk",
            reden="Verse basis — standaard wekelijks",
            prioriteit=SuggestiePrioriteit.HIGH,
            type=VoorraadType.VERS_BASIS,
        )
        assert s.naam == "melk"
        assert s.reden == "Verse basis — standaard wekelijks"
        assert s.prioriteit is SuggestiePrioriteit.HIGH

    def test_naam_leeg_raises(self) -> None:
        with pytest.raises(ValueError, match="naam mag niet leeg zijn"):
            CheckSuggestie(
                naam="",
                reden="test",
                prioriteit=SuggestiePrioriteit.HIGH,
                type=VoorraadType.VERS_BASIS,
            )

    def test_reden_leeg_raises(self) -> None:
        with pytest.raises(ValueError, match="reden mag niet leeg zijn"):
            CheckSuggestie(
                naam="melk",
                reden="",
                prioriteit=SuggestiePrioriteit.HIGH,
                type=VoorraadType.VERS_BASIS,
            )

    def test_frozen(self) -> None:
        s = CheckSuggestie(
            naam="melk",
            reden="test",
            prioriteit=SuggestiePrioriteit.HIGH,
            type=VoorraadType.VERS_BASIS,
        )
        with pytest.raises(AttributeError):
            s.naam = "boter"  # type: ignore[misc]
