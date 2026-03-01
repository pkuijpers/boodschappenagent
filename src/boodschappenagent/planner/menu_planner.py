"""Weekmenu-planner met variatie- en CO2-seizoenslogica."""

from __future__ import annotations

import random

from boodschappenagent.models import Recipe
from boodschappenagent.planner.history import MenuHistory
from boodschappenagent.planner.models import DagInput, DagPlanning, WeekMenu
from boodschappenagent.planner.seizoen_kalender import SeizoenKalender
from boodschappenagent.repository.recipe_search import RecipeSearch


class MenuPlanner:
    """Weekmenu-planner met variatie- en CO2-seizoenslogica."""

    def __init__(
        self,
        recipes: list[Recipe],
        history: MenuHistory,
        kalender: SeizoenKalender,
        *,
        random_seed: int | None = None,
    ) -> None:
        self._recipes = recipes
        self._history = history
        self._kalender = kalender
        self._rng = random.Random(random_seed)

    def _seasonal_and_recent(self, maand: str) -> tuple[list[Recipe], set[str]]:
        """Haal seizoensgeschikte recepten en recent gegeten IDs op."""
        seasonal = (
            RecipeSearch(self._recipes)
            .filter_by_co2_maand(self._kalender, maand)
            .results
        )
        recent_ids = self._history.recent_recipe_ids()
        return seasonal, recent_ids

    def plan_week(
        self,
        week_input: list[DagInput],
        maand: str,
        week_start: str,
    ) -> WeekMenu:
        """Plan een weekmenu.

        Args:
            week_input: Per dag het aantal personen (0 = niet thuis).
            maand: Maandafkorting (jan, feb, ..., dec) voor CO2-filtering.
            week_start: Maandag van de week (YYYY-MM-DD).

        Returns:
            WeekMenu met voor elke dag een recept.

        Raises:
            ValueError: Als er geen kandidaat-recepten beschikbaar zijn.
        """
        seasonal, recent_ids = self._seasonal_and_recent(maand)

        dagen: list[DagPlanning] = []
        used_ids: set[str] = set()
        vorige: DagPlanning | None = None

        for dag_input in sorted(week_input, key=lambda d: d.dag):
            if dag_input.personen == 0:
                dag = DagPlanning(dag=dag_input.dag, recept=None, personen=0)
                dagen.append(dag)
                continue

            candidates = self._filter_candidates_with_fallback(
                seasonal, used_ids, recent_ids, vorige
            )
            recipe = self._rng.choice(candidates)
            used_ids.add(recipe.id)

            dag = DagPlanning(
                dag=dag_input.dag, recept=recipe, personen=dag_input.personen
            )
            dagen.append(dag)
            vorige = dag

        return WeekMenu(week_start=week_start, dagen=dagen)

    def vervang_recept(
        self,
        week_menu: WeekMenu,
        dag: int,
        maand: str,
    ) -> WeekMenu:
        """Vervang het recept voor een specifieke dag.

        Houdt rekening met variatie t.o.v. de buren (dag ervoor/erna).

        Args:
            week_menu: Het huidige weekmenu.
            dag: De dag (0-6) waarvoor het recept vervangen moet worden.
            maand: Maandafkorting (jan, feb, ..., dec) voor CO2-filtering.

        Returns:
            Nieuw WeekMenu met het vervangen recept.
        """
        seasonal, recent_ids = self._seasonal_and_recent(maand)

        dagen_by_dag = {d.dag: d for d in week_menu.dagen}
        target = dagen_by_dag[dag]

        # IDs van andere dagen deze week + het huidige recept uitsluiten
        used_ids = {d.recept.id for d in week_menu.geplande_dagen if d.dag != dag}
        used_ids.add(target.recept.id)

        # Zoek vorige geplande dag (met recept) vóór target
        vorige = None
        for d in sorted(week_menu.geplande_dagen, key=lambda x: x.dag):
            if d.dag < dag:
                vorige = d

        candidates = self._filter_candidates_with_fallback(
            seasonal, used_ids, recent_ids, vorige
        )
        nieuw_recept = self._rng.choice(candidates)

        nieuwe_dagen = [
            DagPlanning(dag=d.dag, recept=nieuw_recept, personen=d.personen)
            if d.dag == dag
            else d
            for d in week_menu.dagen
        ]

        return WeekMenu(week_start=week_menu.week_start, dagen=nieuwe_dagen)

    def _filter_candidates_with_fallback(
        self,
        seasonal: list[Recipe],
        used_ids: set[str],
        recent_ids: set[str],
        vorige: DagPlanning | None,
    ) -> list[Recipe]:
        """Filter kandidaten met progressieve relaxatie.

        Probeert steeds minder strikte constraints tot er
        kandidaten overblijven:
        1. Alle constraints (categorie + basis + recent + used)
        2. Relaxeer basis-constraint
        3. Relaxeer categorie-constraint
        4. Relaxeer recent-constraint
        5. Alleen used-constraint (geen duplicaten deze week)

        Raises:
            ValueError: Als er helemaal geen recepten zijn.
        """
        not_used = [r for r in seasonal if r.id not in used_ids]
        not_used_not_recent = [r for r in not_used if r.id not in recent_ids]

        if vorige and vorige.recept:
            vorige_cat = vorige.recept.categorie
            vorige_bas = vorige.recept.basis

            # Strengst: andere categorie EN andere basis EN niet recent
            strict = [
                r
                for r in not_used_not_recent
                if r.categorie != vorige_cat and r.basis != vorige_bas
            ]
            if strict:
                return strict

            # Relaxeer basis: andere categorie, niet recent
            relax_basis = [r for r in not_used_not_recent if r.categorie != vorige_cat]
            if relax_basis:
                return relax_basis

            # Relaxeer categorie: andere basis, niet recent
            relax_cat = [r for r in not_used_not_recent if r.basis != vorige_bas]
            if relax_cat:
                return relax_cat

        # Niet recent, geen variatie-eis
        if not_used_not_recent:
            return not_used_not_recent

        # Relaxeer recent: alleen geen duplicaten deze week
        if not_used:
            return not_used

        if not seasonal:
            msg = "geen kandidaat-recepten beschikbaar voor de huidige maand"
            raise ValueError(msg)

        # Laatste redmiddel: sta duplicaten toe
        return seasonal
