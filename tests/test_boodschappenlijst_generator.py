"""Tests voor BoodschappenlijstGenerator."""

from boodschappenagent.boodschappenlijst.generator import BoodschappenlijstGenerator
from boodschappenagent.boodschappenlijst.normalizer import IngredientNormalizer
from boodschappenagent.models import Basis, Categorie, Ingredient, Recipe
from boodschappenagent.planner.models import DagPlanning, WeekMenu
from boodschappenagent.utils import PortionCalculator


def _make_recipe(
    recipe_id: str = "test-recept",
    ingredienten: list[Ingredient] | None = None,
    basis_porties: int = 4,
) -> Recipe:
    """Helper om snel een recept te maken voor tests."""
    if ingredienten is None:
        ingredienten = [Ingredient(naam="ui", hoeveelheid=2, eenheid="stuks")]
    return Recipe(
        id=recipe_id,
        naam=recipe_id.replace("-", " ").title(),
        categorie=Categorie.VLEES,
        basis=Basis.PASTA,
        basis_porties=basis_porties,
        ingredienten=ingredienten,
        bereidingstijd_min=30,
    )


def _make_generator() -> BoodschappenlijstGenerator:
    return BoodschappenlijstGenerator(
        normalizer=IngredientNormalizer(),
        portion_calculator=PortionCalculator(),
    )


class TestGenereerLeegMenu:
    """Tests voor lege en niet-thuis menu's."""

    def test_leeg_weekmenu(self) -> None:
        gen = _make_generator()
        menu = WeekMenu(week_start="2026-02-09", dagen=[])
        result = gen.genereer(menu)
        assert result.week_start == "2026-02-09"
        assert result.regels == []

    def test_alleen_niet_thuis_dagen(self) -> None:
        gen = _make_generator()
        menu = WeekMenu(
            week_start="2026-02-09",
            dagen=[
                DagPlanning(dag=0, recept=None, personen=0),
                DagPlanning(dag=1, recept=None, personen=0),
            ],
        )
        result = gen.genereer(menu)
        assert result.regels == []


class TestGenereerEnkelRecept:
    """Tests voor een enkel recept."""

    def test_ongeschaald(self) -> None:
        """Recept voor 4 personen, 4 personen gevraagd → geen schaling."""
        gen = _make_generator()
        recept = _make_recipe(
            ingredienten=[
                Ingredient(naam="ui", hoeveelheid=2, eenheid="stuks"),
                Ingredient(naam="knoflook", hoeveelheid=3, eenheid="teen"),
            ],
            basis_porties=4,
        )
        menu = WeekMenu(
            week_start="2026-02-09",
            dagen=[DagPlanning(dag=0, recept=recept, personen=4)],
        )
        result = gen.genereer(menu)
        assert len(result.regels) == 2
        namen = {r.naam for r in result.regels}
        assert namen == {"knoflook", "ui"}

        ui_regel = next(r for r in result.regels if r.naam == "ui")
        assert ui_regel.hoeveelheid == 2.0
        assert ui_regel.eenheid == "stuks"

    def test_geschaald(self) -> None:
        """Recept voor 4, gevraagd voor 2 → halve hoeveelheden."""
        gen = _make_generator()
        recept = _make_recipe(
            ingredienten=[
                Ingredient(naam="pasta", hoeveelheid=400, eenheid="gram"),
            ],
            basis_porties=4,
        )
        menu = WeekMenu(
            week_start="2026-02-09",
            dagen=[DagPlanning(dag=0, recept=recept, personen=2)],
        )
        result = gen.genereer(menu)
        pasta = result.regels[0]
        assert pasta.naam == "pasta"
        assert pasta.hoeveelheid == 200.0  # 400/2 = 200, afgerond naar 5 = 200

    def test_naar_smaak_items(self) -> None:
        """Naar smaak items krijgen hoeveelheid 1."""
        gen = _make_generator()
        recept = _make_recipe(
            ingredienten=[
                Ingredient(naam="peper", hoeveelheid=1, eenheid="naar smaak"),
            ],
        )
        menu = WeekMenu(
            week_start="2026-02-09",
            dagen=[DagPlanning(dag=0, recept=recept, personen=4)],
        )
        result = gen.genereer(menu)
        peper = result.regels[0]
        assert peper.hoeveelheid == 1.0
        assert peper.eenheid == "naar smaak"


class TestGenereerMeerdereRecepten:
    """Tests voor meerdere recepten."""

    def test_geen_overlap(self) -> None:
        """Twee recepten zonder gedeelde ingrediënten."""
        gen = _make_generator()
        r1 = _make_recipe(
            recipe_id="recept-a",
            ingredienten=[Ingredient(naam="ui", hoeveelheid=2, eenheid="stuks")],
        )
        r2 = _make_recipe(
            recipe_id="recept-b",
            ingredienten=[Ingredient(naam="wortel", hoeveelheid=3, eenheid="stuks")],
        )
        menu = WeekMenu(
            week_start="2026-02-09",
            dagen=[
                DagPlanning(dag=0, recept=r1, personen=4),
                DagPlanning(dag=1, recept=r2, personen=4),
            ],
        )
        result = gen.genereer(menu)
        assert len(result.regels) == 2
        namen = {r.naam for r in result.regels}
        assert namen == {"ui", "wortel"}

    def test_zelfde_ingredient_aggregeert(self) -> None:
        """Zelfde ingrediënt in twee recepten wordt samengevoegd."""
        gen = _make_generator()
        r1 = _make_recipe(
            recipe_id="recept-a",
            ingredienten=[Ingredient(naam="ui", hoeveelheid=2, eenheid="stuks")],
        )
        r2 = _make_recipe(
            recipe_id="recept-b",
            ingredienten=[Ingredient(naam="ui", hoeveelheid=3, eenheid="stuks")],
        )
        menu = WeekMenu(
            week_start="2026-02-09",
            dagen=[
                DagPlanning(dag=0, recept=r1, personen=4),
                DagPlanning(dag=1, recept=r2, personen=4),
            ],
        )
        result = gen.genereer(menu)
        assert len(result.regels) == 1
        assert result.regels[0].naam == "ui"
        assert result.regels[0].hoeveelheid == 5.0  # 2 + 3

    def test_zelfde_naam_andere_eenheid_apart(self) -> None:
        """Zelfde naam maar andere eenheid → twee aparte regels."""
        gen = _make_generator()
        r1 = _make_recipe(
            recipe_id="recept-a",
            ingredienten=[Ingredient(naam="tomaat", hoeveelheid=2, eenheid="stuks")],
        )
        r2 = _make_recipe(
            recipe_id="recept-b",
            ingredienten=[Ingredient(naam="tomaat", hoeveelheid=200, eenheid="gram")],
        )
        menu = WeekMenu(
            week_start="2026-02-09",
            dagen=[
                DagPlanning(dag=0, recept=r1, personen=4),
                DagPlanning(dag=1, recept=r2, personen=4),
            ],
        )
        result = gen.genereer(menu)
        assert len(result.regels) == 2
        eenheden = {r.eenheid for r in result.regels}
        assert eenheden == {"stuks", "gram"}

    def test_synoniemen_samengevoegd(self) -> None:
        """Synoniemen (uien + ui) worden samengevoegd."""
        gen = _make_generator()
        r1 = _make_recipe(
            recipe_id="recept-a",
            ingredienten=[Ingredient(naam="uien", hoeveelheid=2, eenheid="stuks")],
        )
        r2 = _make_recipe(
            recipe_id="recept-b",
            ingredienten=[Ingredient(naam="ui", hoeveelheid=1, eenheid="stuks")],
        )
        menu = WeekMenu(
            week_start="2026-02-09",
            dagen=[
                DagPlanning(dag=0, recept=r1, personen=4),
                DagPlanning(dag=1, recept=r2, personen=4),
            ],
        )
        result = gen.genereer(menu)
        assert len(result.regels) == 1
        assert result.regels[0].naam == "ui"
        assert result.regels[0].hoeveelheid == 3.0


class TestAfrondingNaAggregatie:
    """Tests voor sum-then-round correctheid."""

    def test_gram_afronding_na_optelling(self) -> None:
        """123g + 123g + 123g = 369g → afgerond naar 370g (niet 3×125=375)."""
        gen = _make_generator()
        recepten = []
        for i in range(3):
            recepten.append(
                _make_recipe(
                    recipe_id=f"recept-{i}",
                    ingredienten=[
                        Ingredient(naam="bloem", hoeveelheid=123, eenheid="gram")
                    ],
                )
            )
        dagen = [
            DagPlanning(dag=i, recept=r, personen=4) for i, r in enumerate(recepten)
        ]
        menu = WeekMenu(week_start="2026-02-09", dagen=dagen)
        result = gen.genereer(menu)
        bloem = result.regels[0]
        assert bloem.hoeveelheid == 370.0  # round(369/5)*5 = 370


class TestOpmerkingen:
    """Tests voor opmerkingen verzamelen."""

    def test_opmerkingen_verzameld(self) -> None:
        gen = _make_generator()
        r1 = _make_recipe(
            recipe_id="recept-a",
            ingredienten=[
                Ingredient(
                    naam="ui", hoeveelheid=2, eenheid="stuks", opmerking="fijngesneden"
                )
            ],
        )
        r2 = _make_recipe(
            recipe_id="recept-b",
            ingredienten=[
                Ingredient(
                    naam="ui", hoeveelheid=1, eenheid="stuks", opmerking="in ringen"
                )
            ],
        )
        menu = WeekMenu(
            week_start="2026-02-09",
            dagen=[
                DagPlanning(dag=0, recept=r1, personen=4),
                DagPlanning(dag=1, recept=r2, personen=4),
            ],
        )
        result = gen.genereer(menu)
        assert "fijngesneden" in result.regels[0].opmerkingen
        assert "in ringen" in result.regels[0].opmerkingen

    def test_none_opmerkingen_gefilterd(self) -> None:
        gen = _make_generator()
        r1 = _make_recipe(
            recipe_id="recept-a",
            ingredienten=[
                Ingredient(naam="ui", hoeveelheid=2, eenheid="stuks", opmerking=None)
            ],
        )
        menu = WeekMenu(
            week_start="2026-02-09",
            dagen=[DagPlanning(dag=0, recept=r1, personen=4)],
        )
        result = gen.genereer(menu)
        assert result.regels[0].opmerkingen == []

    def test_dubbele_opmerkingen_gededupliceerd(self) -> None:
        gen = _make_generator()
        r1 = _make_recipe(
            recipe_id="recept-a",
            ingredienten=[
                Ingredient(
                    naam="ui", hoeveelheid=2, eenheid="stuks", opmerking="fijngesneden"
                )
            ],
        )
        r2 = _make_recipe(
            recipe_id="recept-b",
            ingredienten=[
                Ingredient(
                    naam="ui", hoeveelheid=1, eenheid="stuks", opmerking="fijngesneden"
                )
            ],
        )
        menu = WeekMenu(
            week_start="2026-02-09",
            dagen=[
                DagPlanning(dag=0, recept=r1, personen=4),
                DagPlanning(dag=1, recept=r2, personen=4),
            ],
        )
        result = gen.genereer(menu)
        assert result.regels[0].opmerkingen == ["fijngesneden"]


class TestOrigineleNamen:
    """Tests voor originele namen tracking."""

    def test_synoniemen_alle_varianten(self) -> None:
        """Bij synoniemen worden alle originele namen bewaard."""
        gen = _make_generator()
        r1 = _make_recipe(
            recipe_id="recept-a",
            ingredienten=[Ingredient(naam="uien", hoeveelheid=2, eenheid="stuks")],
        )
        r2 = _make_recipe(
            recipe_id="recept-b",
            ingredienten=[Ingredient(naam="ui", hoeveelheid=1, eenheid="stuks")],
        )
        menu = WeekMenu(
            week_start="2026-02-09",
            dagen=[
                DagPlanning(dag=0, recept=r1, personen=4),
                DagPlanning(dag=1, recept=r2, personen=4),
            ],
        )
        result = gen.genereer(menu)
        assert result.regels[0].originele_namen == frozenset({"uien", "ui"})

    def test_identiek_een_naam(self) -> None:
        """Bij identieke namen, één unieke naam."""
        gen = _make_generator()
        r1 = _make_recipe(
            recipe_id="recept-a",
            ingredienten=[Ingredient(naam="ui", hoeveelheid=2, eenheid="stuks")],
        )
        r2 = _make_recipe(
            recipe_id="recept-b",
            ingredienten=[Ingredient(naam="ui", hoeveelheid=1, eenheid="stuks")],
        )
        menu = WeekMenu(
            week_start="2026-02-09",
            dagen=[
                DagPlanning(dag=0, recept=r1, personen=4),
                DagPlanning(dag=1, recept=r2, personen=4),
            ],
        )
        result = gen.genereer(menu)
        assert result.regels[0].originele_namen == frozenset({"ui"})


class TestSortering:
    """Tests voor alfabetische sortering."""

    def test_regels_alfabetisch(self) -> None:
        gen = _make_generator()
        recept = _make_recipe(
            ingredienten=[
                Ingredient(naam="wortel", hoeveelheid=3, eenheid="stuks"),
                Ingredient(naam="aardappel", hoeveelheid=500, eenheid="gram"),
                Ingredient(naam="knoflook", hoeveelheid=2, eenheid="teen"),
            ],
        )
        menu = WeekMenu(
            week_start="2026-02-09",
            dagen=[DagPlanning(dag=0, recept=recept, personen=4)],
        )
        result = gen.genereer(menu)
        namen = [r.naam for r in result.regels]
        assert namen == ["aardappel", "knoflook", "wortel"]


class TestPeperSnufNaarSmaak:
    """Edge case: peper snuf + peper naar smaak → één regel."""

    def test_peper_snuf_en_naar_smaak(self) -> None:
        gen = _make_generator()
        r1 = _make_recipe(
            recipe_id="recept-a",
            ingredienten=[
                Ingredient(naam="peper", hoeveelheid=1, eenheid="snuf"),
            ],
        )
        r2 = _make_recipe(
            recipe_id="recept-b",
            ingredienten=[
                Ingredient(naam="peper", hoeveelheid=1, eenheid="naar smaak"),
            ],
        )
        menu = WeekMenu(
            week_start="2026-02-09",
            dagen=[
                DagPlanning(dag=0, recept=r1, personen=4),
                DagPlanning(dag=1, recept=r2, personen=4),
            ],
        )
        result = gen.genereer(menu)
        peper_regels = [r for r in result.regels if r.naam == "peper"]
        assert len(peper_regels) == 1
        assert peper_regels[0].eenheid == "naar smaak"
        assert peper_regels[0].hoeveelheid == 1.0


class TestZelfdeReceptMeerdereDagen:
    """Edge case: zelfde recept op meerdere dagen."""

    def test_zelfde_recept_twee_dagen(self) -> None:
        gen = _make_generator()
        recept = _make_recipe(
            ingredienten=[
                Ingredient(naam="pasta", hoeveelheid=400, eenheid="gram"),
            ],
            basis_porties=4,
        )
        menu = WeekMenu(
            week_start="2026-02-09",
            dagen=[
                DagPlanning(dag=0, recept=recept, personen=4),
                DagPlanning(dag=1, recept=recept, personen=2),
            ],
        )
        result = gen.genereer(menu)
        pasta = result.regels[0]
        # 400 (4 pers) + 200 (2 pers) = 600g, afgerond naar 5 = 600
        assert pasta.hoeveelheid == 600.0


class TestRecepten:
    """Tests voor recepten-tracking per regel."""

    def test_een_recept(self) -> None:
        gen = _make_generator()
        recept = _make_recipe(
            recipe_id="pasta-bolognese",
            ingredienten=[Ingredient(naam="ui", hoeveelheid=2, eenheid="stuks")],
        )
        menu = WeekMenu(
            week_start="2026-02-09",
            dagen=[DagPlanning(dag=0, recept=recept, personen=4)],
        )
        result = gen.genereer(menu)
        ui_regel = next(r for r in result.regels if r.naam == "ui")
        assert ui_regel.recepten == ("Pasta Bolognese",)

    def test_drie_recepten_week_volgorde(self) -> None:
        """Ui in maandag (pasta), dinsdag (soep), donderdag (quiche)."""
        gen = _make_generator()
        pasta = _make_recipe(
            recipe_id="pasta-bolognese",
            ingredienten=[Ingredient(naam="ui", hoeveelheid=1, eenheid="stuks")],
        )
        soep = _make_recipe(
            recipe_id="groentesoep",
            ingredienten=[Ingredient(naam="ui", hoeveelheid=1, eenheid="stuks")],
        )
        quiche = _make_recipe(
            recipe_id="quiche",
            ingredienten=[Ingredient(naam="ui", hoeveelheid=1, eenheid="stuks")],
        )
        menu = WeekMenu(
            week_start="2026-02-09",
            dagen=[
                DagPlanning(dag=0, recept=pasta, personen=4),
                DagPlanning(dag=1, recept=soep, personen=4),
                DagPlanning(dag=3, recept=quiche, personen=4),
            ],
        )
        result = gen.genereer(menu)
        ui_regel = next(r for r in result.regels if r.naam == "ui")
        assert ui_regel.recepten == ("Pasta Bolognese", "Groentesoep", "Quiche")

    def test_zelfde_recept_meerdere_dagen_zonder_duplicaten(self) -> None:
        """Recept op maandag en woensdag → recept komt één keer voor."""
        gen = _make_generator()
        recept = _make_recipe(
            recipe_id="pasta-bolognese",
            ingredienten=[Ingredient(naam="ui", hoeveelheid=1, eenheid="stuks")],
        )
        menu = WeekMenu(
            week_start="2026-02-09",
            dagen=[
                DagPlanning(dag=0, recept=recept, personen=4),
                DagPlanning(dag=2, recept=recept, personen=4),
            ],
        )
        result = gen.genereer(menu)
        ui_regel = next(r for r in result.regels if r.naam == "ui")
        assert ui_regel.recepten == ("Pasta Bolognese",)
