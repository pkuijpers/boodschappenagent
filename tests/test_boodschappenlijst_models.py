"""Tests voor boodschappenlijst data models: BoodschappenRegel, Boodschappenlijst."""

import pytest

from boodschappenagent.boodschappenlijst.models import (
    Boodschappenlijst,
    BoodschappenRegel,
)


class TestBoodschappenRegel:
    """Tests voor BoodschappenRegel dataclass."""

    def test_create_valid(self) -> None:
        regel = BoodschappenRegel(
            naam="ui",
            hoeveelheid=2.0,
            eenheid="stuks",
            originele_namen=frozenset({"ui"}),
        )
        assert regel.naam == "ui"
        assert regel.hoeveelheid == 2.0
        assert regel.eenheid == "stuks"
        assert regel.originele_namen == frozenset({"ui"})
        assert regel.opmerkingen == []

    def test_create_met_opmerkingen(self) -> None:
        regel = BoodschappenRegel(
            naam="ui",
            hoeveelheid=2.0,
            eenheid="stuks",
            originele_namen=frozenset({"ui", "uien"}),
            opmerkingen=["fijngesneden", "geel"],
        )
        assert regel.opmerkingen == ["fijngesneden", "geel"]

    def test_frozen(self) -> None:
        regel = BoodschappenRegel(
            naam="ui",
            hoeveelheid=2.0,
            eenheid="stuks",
            originele_namen=frozenset({"ui"}),
        )
        with pytest.raises(AttributeError):
            regel.naam = "peper"  # type: ignore[misc]

    def test_naam_leeg_raises(self) -> None:
        with pytest.raises(ValueError, match="naam mag niet leeg zijn"):
            BoodschappenRegel(
                naam="",
                hoeveelheid=1.0,
                eenheid="stuks",
                originele_namen=frozenset({"ui"}),
            )

    def test_naam_whitespace_raises(self) -> None:
        with pytest.raises(ValueError, match="naam mag niet leeg zijn"):
            BoodschappenRegel(
                naam="  ",
                hoeveelheid=1.0,
                eenheid="stuks",
                originele_namen=frozenset({"ui"}),
            )

    def test_eenheid_leeg_raises(self) -> None:
        with pytest.raises(ValueError, match="eenheid mag niet leeg zijn"):
            BoodschappenRegel(
                naam="ui",
                hoeveelheid=1.0,
                eenheid="",
                originele_namen=frozenset({"ui"}),
            )

    def test_originele_namen_leeg_raises(self) -> None:
        with pytest.raises(ValueError, match="originele_namen mag niet leeg zijn"):
            BoodschappenRegel(
                naam="ui",
                hoeveelheid=1.0,
                eenheid="stuks",
                originele_namen=frozenset(),
            )

    def test_display_naam_zonder_aliassen(self) -> None:
        regel = BoodschappenRegel(
            naam="ui",
            hoeveelheid=2.0,
            eenheid="stuks",
            originele_namen=frozenset({"ui"}),
        )
        assert regel.display_naam == "ui"

    def test_display_naam_met_aliassen(self) -> None:
        regel = BoodschappenRegel(
            naam="ui",
            hoeveelheid=2.0,
            eenheid="stuks",
            originele_namen=frozenset({"ui", "uien"}),
        )
        assert regel.display_naam == "ui (ook: uien)"

    def test_display_naam_met_meerdere_aliassen(self) -> None:
        regel = BoodschappenRegel(
            naam="ui",
            hoeveelheid=2.0,
            eenheid="stuks",
            originele_namen=frozenset({"ui", "uien", "biologische ui"}),
        )
        display = regel.display_naam
        assert display.startswith("ui (ook: ")
        assert "uien" in display
        assert "biologische ui" in display

    def test_to_dict(self) -> None:
        regel = BoodschappenRegel(
            naam="ui",
            hoeveelheid=2.0,
            eenheid="stuks",
            originele_namen=frozenset({"ui", "uien"}),
            opmerkingen=["fijngesneden"],
        )
        result = regel.to_dict()
        assert result == {
            "naam": "ui",
            "hoeveelheid": 2.0,
            "eenheid": "stuks",
            "originele_namen": ["ui", "uien"],  # gesorteerd
            "opmerkingen": ["fijngesneden"],
            "recepten": [],
        }

    def test_from_dict(self) -> None:
        data = {
            "naam": "ui",
            "hoeveelheid": 2.0,
            "eenheid": "stuks",
            "originele_namen": ["ui", "uien"],
            "opmerkingen": ["fijngesneden"],
        }
        regel = BoodschappenRegel.from_dict(data)
        assert regel.naam == "ui"
        assert regel.hoeveelheid == 2.0
        assert regel.eenheid == "stuks"
        assert regel.originele_namen == frozenset({"ui", "uien"})
        assert regel.opmerkingen == ["fijngesneden"]

    def test_to_dict_from_dict_roundtrip(self) -> None:
        regel = BoodschappenRegel(
            naam="peterselie",
            hoeveelheid=1.0,
            eenheid="eetlepel",
            originele_namen=frozenset({"peterselie", "platte peterselie"}),
            opmerkingen=["fijngehakt"],
        )
        restored = BoodschappenRegel.from_dict(regel.to_dict())
        assert restored.naam == regel.naam
        assert restored.hoeveelheid == regel.hoeveelheid
        assert restored.eenheid == regel.eenheid
        assert restored.originele_namen == regel.originele_namen
        assert restored.opmerkingen == regel.opmerkingen

    def test_recepten_default_is_lege_tuple(self) -> None:
        regel = BoodschappenRegel(
            naam="ui",
            hoeveelheid=2.0,
            eenheid="stuks",
            originele_namen=frozenset({"ui"}),
        )
        assert regel.recepten == ()

    def test_recepten_geordende_tuple(self) -> None:
        regel = BoodschappenRegel(
            naam="ui",
            hoeveelheid=2.0,
            eenheid="stuks",
            originele_namen=frozenset({"ui"}),
            recepten=("pasta bolognese", "groentesoep", "quiche"),
        )
        assert regel.recepten == ("pasta bolognese", "groentesoep", "quiche")

    def test_to_dict_bevat_recepten(self) -> None:
        regel = BoodschappenRegel(
            naam="ui",
            hoeveelheid=2.0,
            eenheid="stuks",
            originele_namen=frozenset({"ui"}),
            recepten=("pasta bolognese", "groentesoep"),
        )
        result = regel.to_dict()
        assert result["recepten"] == ["pasta bolognese", "groentesoep"]

    def test_from_dict_leest_recepten(self) -> None:
        data = {
            "naam": "ui",
            "hoeveelheid": 2.0,
            "eenheid": "stuks",
            "originele_namen": ["ui"],
            "opmerkingen": [],
            "recepten": ["pasta bolognese", "groentesoep"],
        }
        regel = BoodschappenRegel.from_dict(data)
        assert regel.recepten == ("pasta bolognese", "groentesoep")

    def test_from_dict_zonder_recepten_lege_tuple(self) -> None:
        """Backwards-compat: oude JSON zonder 'recepten' sleutel werkt."""
        data = {
            "naam": "ui",
            "hoeveelheid": 2.0,
            "eenheid": "stuks",
            "originele_namen": ["ui"],
            "opmerkingen": [],
        }
        regel = BoodschappenRegel.from_dict(data)
        assert regel.recepten == ()

    def test_to_dict_from_dict_roundtrip_met_recepten(self) -> None:
        regel = BoodschappenRegel(
            naam="ui",
            hoeveelheid=2.0,
            eenheid="stuks",
            originele_namen=frozenset({"ui"}),
            recepten=("pasta bolognese", "soep"),
        )
        restored = BoodschappenRegel.from_dict(regel.to_dict())
        assert restored.recepten == regel.recepten


class TestBoodschappenlijst:
    """Tests voor Boodschappenlijst dataclass."""

    def test_create_valid(self) -> None:
        regel = BoodschappenRegel(
            naam="ui",
            hoeveelheid=2.0,
            eenheid="stuks",
            originele_namen=frozenset({"ui"}),
        )
        lijst = Boodschappenlijst(week_start="2026-02-09", regels=[regel])
        assert lijst.week_start == "2026-02-09"
        assert len(lijst.regels) == 1

    def test_lege_lijst(self) -> None:
        lijst = Boodschappenlijst(week_start="2026-02-09", regels=[])
        assert lijst.regels == []

    def test_frozen(self) -> None:
        lijst = Boodschappenlijst(week_start="2026-02-09", regels=[])
        with pytest.raises(AttributeError):
            lijst.week_start = "2026-02-16"  # type: ignore[misc]

    def test_week_start_leeg_raises(self) -> None:
        with pytest.raises(ValueError, match="week_start mag niet leeg zijn"):
            Boodschappenlijst(week_start="", regels=[])

    def test_to_dict(self) -> None:
        regel = BoodschappenRegel(
            naam="ui",
            hoeveelheid=2.0,
            eenheid="stuks",
            originele_namen=frozenset({"ui"}),
        )
        lijst = Boodschappenlijst(week_start="2026-02-09", regels=[regel])
        result = lijst.to_dict()
        assert result == {
            "week_start": "2026-02-09",
            "regels": [
                {
                    "naam": "ui",
                    "hoeveelheid": 2.0,
                    "eenheid": "stuks",
                    "originele_namen": ["ui"],
                    "opmerkingen": [],
                    "recepten": [],
                }
            ],
        }

    def test_from_dict(self) -> None:
        data = {
            "week_start": "2026-02-09",
            "regels": [
                {
                    "naam": "ui",
                    "hoeveelheid": 2.0,
                    "eenheid": "stuks",
                    "originele_namen": ["ui"],
                    "opmerkingen": [],
                }
            ],
        }
        lijst = Boodschappenlijst.from_dict(data)
        assert lijst.week_start == "2026-02-09"
        assert len(lijst.regels) == 1
        assert lijst.regels[0].naam == "ui"

    def test_to_dict_from_dict_roundtrip(self) -> None:
        regels = [
            BoodschappenRegel(
                naam="knoflook",
                hoeveelheid=3.0,
                eenheid="teen",
                originele_namen=frozenset({"knoflook", "knoflookteen"}),
                opmerkingen=["geperst"],
            ),
            BoodschappenRegel(
                naam="ui",
                hoeveelheid=2.0,
                eenheid="stuks",
                originele_namen=frozenset({"ui"}),
            ),
        ]
        lijst = Boodschappenlijst(week_start="2026-02-09", regels=regels)
        restored = Boodschappenlijst.from_dict(lijst.to_dict())
        assert restored.week_start == lijst.week_start
        assert len(restored.regels) == len(lijst.regels)
        for orig, rest in zip(lijst.regels, restored.regels, strict=True):
            assert rest.naam == orig.naam
            assert rest.hoeveelheid == orig.hoeveelheid
            assert rest.originele_namen == orig.originele_namen
