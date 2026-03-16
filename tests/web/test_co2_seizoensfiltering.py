"""Integratietests voor S4: CO2-seizoensfiltering door de keten.

Test de volledige keten: RecipeRepository → MenuPlanner (CO2-filter) → WeekMenu.
Gebruikt echte recepten uit data/recipes/ en de productie seizoenskalender.
"""

from boodschappenagent.models import Basis, Categorie, Ingredient
from boodschappenagent.models.recipe import Recipe
from boodschappenagent.planner import DagInput, MenuPlanner
from boodschappenagent.planner.seizoen_kalender import SeizoenKalender


def _make_recipe(id: str, ingredienten: list[Ingredient]) -> Recipe:
    """Maak een minimaal Recipe met opgegeven ingrediënten voor seizoenstests."""
    return Recipe(
        id=id,
        naam=id.replace("-", " ").title(),
        categorie=Categorie.VEGETARISCH,
        basis=Basis.GEEN,
        basis_porties=2,
        ingredienten=ingredienten,
    )


class TestSeizoenFilteringKeten:
    """S4.1-S4.2: Planner filtert recepten op CO2-seizoensgeschiktheid per maand.

    Verifieert de keten Repository → Planner: alle recepten in het gegenereerde
    weekmenu voldoen aan de CO2-meerderheidsregel voor de opgegeven maand.
    """

    def test_februari_menu_bevat_alleen_seizoensgeschikte_recepten(
        self, menu_planner: MenuPlanner
    ):
        """S4.1: Weekmenu voor februari bevat alleen recepten met >50% low-CO2 groenten.

        Wintergroenten met lage CO2 in februari: prei, wortel, ui, champignon,
        boerenkool, spruitjes, spinazie, pompoen, rode biet, knolselderij, etc.
        """
        dag_inputs = [DagInput(dag=i, personen=2) for i in range(7)]
        week_menu = menu_planner.plan_week(
            week_input=dag_inputs,
            maand="feb",
            week_start="2026-02-16",
        )

        kalender = SeizoenKalender()
        for dag in week_menu.geplande_dagen:
            assert dag.recept is not None
            assert kalender.recept_is_seizoensgeschikt(dag.recept, "feb"), (
                f"Recept '{dag.recept.naam}' is niet seizoensgeschikt voor februari"
            )

    def test_juli_menu_bevat_alleen_seizoensgeschikte_recepten(
        self, menu_planner: MenuPlanner
    ):
        """S4.2: Weekmenu voor juli bevat alleen recepten met >50% low-CO2 groenten.

        Zomergroenten met lage CO2 in juli: tomaat, paprika, courgette,
        sperziebonen, broccoli, komkommer, sla, aubergine, etc.
        """
        dag_inputs = [DagInput(dag=i, personen=2) for i in range(7)]
        week_menu = menu_planner.plan_week(
            week_input=dag_inputs,
            maand="jul",
            week_start="2026-07-06",
        )

        kalender = SeizoenKalender()
        for dag in week_menu.geplande_dagen:
            assert dag.recept is not None
            assert kalender.recept_is_seizoensgeschikt(dag.recept, "jul"), (
                f"Recept '{dag.recept.naam}' is niet seizoensgeschikt voor juli"
            )

    def test_februari_menu_heeft_zeven_geplande_dagen(self, menu_planner: MenuPlanner):
        """S4.1: Voldoende seizoensgeschikte recepten beschikbaar voor februari."""
        dag_inputs = [DagInput(dag=i, personen=2) for i in range(7)]
        week_menu = menu_planner.plan_week(
            week_input=dag_inputs,
            maand="feb",
            week_start="2026-02-16",
        )

        assert len(week_menu.geplande_dagen) == 7

    def test_juli_menu_heeft_zeven_geplande_dagen(self, menu_planner: MenuPlanner):
        """S4.2: Voldoende seizoensgeschikte recepten beschikbaar voor juli."""
        dag_inputs = [DagInput(dag=i, personen=2) for i in range(7)]
        week_menu = menu_planner.plan_week(
            week_input=dag_inputs,
            maand="jul",
            week_start="2026-07-06",
        )

        assert len(week_menu.geplande_dagen) == 7


class TestIngredientMatchingKeten:
    """S4.3: Ingredient-matching via de productie SeizoenKalender.

    Verifieert dat de productie-kalender (echte JSON data) ingrediëntnamen
    correct herkent met substring/stam-matching.
    """

    def test_rode_paprika_herkend_als_paprika(self):
        """S4.3: 'rode paprika' wordt herkend als 'paprika' in de productie-kalender."""
        kalender = SeizoenKalender()
        assert kalender.match_ingredient("rode paprika") == "paprika"

    def test_gele_paprika_herkend_als_paprika(self):
        """S4.3: 'gele paprika' wordt herkend als 'paprika' in de productie-kalender."""
        kalender = SeizoenKalender()
        assert kalender.match_ingredient("gele paprika") == "paprika"

    def test_cherrytomaten_herkend_als_tomaat(self):
        """S4.3: 'cherrytomaten' wordt herkend als 'tomaat' via stammatching."""
        kalender = SeizoenKalender()
        assert kalender.match_ingredient("cherrytomaten") == "tomaat"

    def test_kastanjechampignons_herkend(self):
        """S4.3: 'kastanjechampignons' wordt herkend als 'champignon'."""
        kalender = SeizoenKalender()
        assert kalender.match_ingredient("kastanjechampignons") == "champignon"


class TestMeerderheidsRegelKeten:
    """S4.4-S4.5: Meerderheidsregel via de productie SeizoenKalender.

    Verifieert de >50% regel met de echte productie-kalenderdata zodat
    de keten consistent gedraagt voor echte ingrediëntnamen.
    """

    def test_meerderheid_in_seizoen_is_geschikt(self):
        """S4.4: Recept met 3 seizoensgroenten, 2 in seizoen (feb) → geschikt.

        Februari: boerenkool ✅ (nov-feb), pompoen ✅ (sep-mrt), tomaat ❌ = 2/3.
        Jaar-rond groenten (prei, wortel) tellen niet mee.
        """
        kalender = SeizoenKalender()
        recept = _make_recipe(
            "test-feb-geschikt",
            [
                Ingredient(naam="boerenkool", hoeveelheid=200, eenheid="gram"),
                Ingredient(naam="pompoen", hoeveelheid=300, eenheid="gram"),
                Ingredient(naam="tomaat", hoeveelheid=2, eenheid="stuks"),
            ],
        )
        assert kalender.recept_is_seizoensgeschikt(recept, "feb") is True

    def test_minderheid_in_seizoen_is_niet_geschikt(self):
        """S4.5: Recept met 3 groenten, 1 in seizoen (feb) → niet geschikt (1/3 < 50%).

        Februari: prei ✅, tomaat ❌, rode paprika ❌ = 1/3 < 50%.
        """
        kalender = SeizoenKalender()
        recept = _make_recipe(
            "test-feb-ongeschikt",
            [
                Ingredient(naam="prei", hoeveelheid=2, eenheid="stuks"),
                Ingredient(naam="tomaat", hoeveelheid=2, eenheid="stuks"),
                Ingredient(naam="rode paprika", hoeveelheid=1, eenheid="stuks"),
            ],
        )
        assert kalender.recept_is_seizoensgeschikt(recept, "feb") is False

    def test_paprika_niet_in_seizoen_in_februari(self):
        """S4.5: Paprika heeft hoge CO2 in februari (alleen jun-okt laag).

        Verifieert dat de productie-kalender paprika correct markeert als
        niet beschikbaar met lage CO2 in de winter.
        """
        kalender = SeizoenKalender()
        groenten = kalender.groenten_in_seizoen("feb")
        assert "paprika" not in groenten

    def test_paprika_in_seizoen_in_juli(self):
        """S4.2: Paprika heeft lage CO2 in juli (jun-okt).

        Verifieert dat de productie-kalender paprika correct markeert als
        beschikbaar met lage CO2 in de zomer.
        """
        kalender = SeizoenKalender()
        groenten = kalender.groenten_in_seizoen("jul")
        assert "paprika" in groenten
