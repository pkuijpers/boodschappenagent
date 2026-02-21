"""Menu routes — weekoverzicht en gerelateerde endpoints."""

from datetime import date, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import RedirectResponse

from boodschappenagent.models import Categorie, Recipe, Seizoen
from boodschappenagent.planner import DagInput, DagPlanning, MenuPlanner, WeekMenu
from boodschappenagent.planner.history import MenuHistory
from boodschappenagent.repository import RecipeSearch
from boodschappenagent.web.dependencies import (
    get_all_recipes,
    get_menu_history,
    get_menu_planner,
)

MAAND_NAAR_SEIZOEN = {
    12: Seizoen.WINTER,
    1: Seizoen.WINTER,
    2: Seizoen.WINTER,
    3: Seizoen.LENTE,
    4: Seizoen.LENTE,
    5: Seizoen.LENTE,
    6: Seizoen.ZOMER,
    7: Seizoen.ZOMER,
    8: Seizoen.ZOMER,
    9: Seizoen.HERFST,
    10: Seizoen.HERFST,
    11: Seizoen.HERFST,
}

router = APIRouter()

DAG_NAMEN = [
    "Maandag",
    "Dinsdag",
    "Woensdag",
    "Donderdag",
    "Vrijdag",
    "Zaterdag",
    "Zondag",
]

CATEGORIE_EMOJI = {
    "vlees": "\U0001f969",
    "gevogelte": "\U0001f357",
    "vis": "\U0001f41f",
    "vegetarisch": "\U0001f96c",
    "veganistisch": "\U0001f331",
}


@router.get("/")
async def root():
    """Redirect root naar weekoverzicht."""
    return RedirectResponse(url="/week")


def _build_week_context(request: Request) -> dict:
    """Bouw template context op basis van app.state weekmenu."""
    week_menu = getattr(request.app.state, "week_menu", None)
    hellofresh_dagen = getattr(request.app.state, "hellofresh_dagen", set())

    dagen = []
    week_nummer = None

    if week_menu:
        week_start = date.fromisoformat(week_menu.week_start)
        week_nummer = week_start.isocalendar().week

        for dag_planning in week_menu.dagen:
            dag = dag_planning.dag
            if dag in hellofresh_dagen:
                dag_type = "hellofresh"
            elif dag_planning.personen == 0:
                dag_type = "niet-thuis"
            else:
                dag_type = "recept"

            categorie_emoji = ""
            if dag_planning.recept:
                categorie_emoji = CATEGORIE_EMOJI.get(
                    dag_planning.recept.categorie.value, ""
                )

            dagen.append(
                {
                    "dag": dag,
                    "dag_naam": DAG_NAMEN[dag],
                    "type": dag_type,
                    "recept": dag_planning.recept,
                    "personen": dag_planning.personen,
                    "categorie_emoji": categorie_emoji,
                }
            )

    return {
        "week_nummer": week_nummer,
        "dagen": dagen,
    }


def _render_week(request: Request, context: dict):
    """Render week template als full page of HTMX fragment."""
    templates = request.app.state.templates
    is_htmx = request.headers.get("HX-Request") == "true"
    template_name = "fragments/week_content.html" if is_htmx else "pages/week.html"
    return templates.TemplateResponse(
        request=request,
        name=template_name,
        context=context,
    )


def _generate_week_menu(request: Request, planner: MenuPlanner) -> None:
    """Genereer een weekmenu en sla op in app.state."""
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    seizoen = MAAND_NAAR_SEIZOEN[today.month]
    dag_inputs = [DagInput(dag=i, personen=2) for i in range(7)]
    week_menu = planner.plan_week(
        week_input=dag_inputs,
        seizoen=seizoen,
        week_start=week_start.isoformat(),
    )
    request.app.state.week_menu = week_menu


@router.get("/week")
async def week(
    request: Request,
    planner: Annotated[MenuPlanner, Depends(get_menu_planner)],
):
    """Weekoverzicht pagina met dagkaarten."""
    if getattr(request.app.state, "week_menu", None) is None:
        _generate_week_menu(request, planner)
    context = _build_week_context(request)
    return _render_week(request, context)


@router.post("/week/genereer")
async def genereer(
    request: Request,
    planner: Annotated[MenuPlanner, Depends(get_menu_planner)],
):
    """Genereer een volledig nieuw weekmenu."""
    _generate_week_menu(request, planner)
    context = _build_week_context(request)
    return _render_week(request, context)


@router.post("/week/shuffle")
async def shuffle(
    request: Request,
    dag: Annotated[int, Form()],
    planner: Annotated[MenuPlanner, Depends(get_menu_planner)],
):
    """Shuffle het recept voor een specifieke dag.

    Args:
        dag: Dagnummer (0-6) waarvoor het recept vervangen moet worden.
    """
    week_menu = getattr(request.app.state, "week_menu", None)
    if week_menu is None:
        raise HTTPException(status_code=404, detail="Geen weekmenu beschikbaar")

    # Controleer of de dag een recept heeft (niet niet-thuis/hellofresh)
    dag_planning = next((d for d in week_menu.dagen if d.dag == dag), None)
    if dag_planning is None or dag_planning.personen == 0:
        raise HTTPException(
            status_code=422,
            detail="Kan geen recept shufflen voor een niet-thuis dag",
        )

    hellofresh_dagen = getattr(request.app.state, "hellofresh_dagen", set())
    if dag in hellofresh_dagen:
        raise HTTPException(
            status_code=422,
            detail="Kan geen recept shufflen voor een HelloFresh dag",
        )

    seizoen = MAAND_NAAR_SEIZOEN[date.today().month]
    new_menu = planner.vervang_recept(week_menu, dag, seizoen)
    request.app.state.week_menu = new_menu

    context = _build_week_context(request)
    return _render_week(request, context)


# --- Helpers voor receptkiezer ---


def _format_tijd_geleden(datum: date | None, *, vandaag: date | None = None) -> str:
    """Formatteer tijdsverschil als leesbare tekst."""
    if datum is None:
        return "Nog nooit"
    today = vandaag or date.today()
    days = (today - datum).days
    if days == 0:
        return "Vandaag"
    if days < 7:
        return f"{days} d geleden"
    if days < 30:
        return f"{days // 7} wk geleden"
    return f"{days // 30} mnd geleden"


def _get_laatst_gegeten_dict(history: MenuHistory) -> dict[str, date]:
    """Bereken laatste eetdatum per recept-id uit history."""
    entries = history.load()
    result: dict[str, date] = {}
    for entry in entries:
        recept_id = entry["recept_id"]
        datum = date.fromisoformat(entry["datum"])
        if recept_id not in result or datum > result[recept_id]:
            result[recept_id] = datum
    return result


def _validate_dag_voor_kiezer(request: Request, dag: int) -> None:
    """Valideer dat dag geschikt is voor de receptkiezer."""
    if dag < 0 or dag > 6:
        raise HTTPException(status_code=422, detail="Ongeldig dagnummer")

    week_menu = getattr(request.app.state, "week_menu", None)
    if week_menu is None:
        raise HTTPException(status_code=404, detail="Geen weekmenu beschikbaar")

    hellofresh_dagen = getattr(request.app.state, "hellofresh_dagen", set())
    if dag in hellofresh_dagen:
        raise HTTPException(
            status_code=422, detail="Kan geen recept kiezen voor een HelloFresh dag"
        )

    dag_planning = next((d for d in week_menu.dagen if d.dag == dag), None)
    if dag_planning is None or dag_planning.personen == 0:
        raise HTTPException(
            status_code=422, detail="Kan geen recept kiezen voor een niet-thuis dag"
        )


def _build_dag_context(dag: int, request: Request) -> dict:
    """Bouw template context voor een enkele dagkaart."""
    week_menu = request.app.state.week_menu
    hellofresh_dagen = getattr(request.app.state, "hellofresh_dagen", set())
    dag_planning = next(d for d in week_menu.dagen if d.dag == dag)

    if dag in hellofresh_dagen:
        dag_type = "hellofresh"
    elif dag_planning.personen == 0:
        dag_type = "niet-thuis"
    else:
        dag_type = "recept"

    categorie_emoji = ""
    if dag_planning.recept:
        categorie_emoji = CATEGORIE_EMOJI.get(dag_planning.recept.categorie.value, "")

    return {
        "dag": dag,
        "dag_naam": DAG_NAMEN[dag],
        "type": dag_type,
        "recept": dag_planning.recept,
        "personen": dag_planning.personen,
        "categorie_emoji": categorie_emoji,
    }


# --- Receptkiezer routes ---


@router.get("/week/dag/{dag}/receptkiezer")
async def receptkiezer(
    dag: int,
    request: Request,
    recipes: Annotated[list[Recipe], Depends(get_all_recipes)],
    history: Annotated[MenuHistory, Depends(get_menu_history)],
    search: str = "",
    categorie: Annotated[list[str] | None, Query()] = None,
):
    """Toon receptkiezer voor een specifieke dag."""
    if categorie is None:
        categorie = []
    _validate_dag_voor_kiezer(request, dag)

    # Filter recepten
    recipe_search = RecipeSearch(recipes)
    if search:
        recipe_search = recipe_search.search_by_naam(search)
    if categorie:
        # Meerdere categorieën: verzamel recepten die matchen met een ervan
        filtered: list[Recipe] = []
        for cat_value in categorie:
            try:
                cat = Categorie(cat_value)
                filtered.extend(
                    RecipeSearch(recipe_search.results).filter_by_categorie(cat).results
                )
            except ValueError:
                pass
        # Ontdubbel maar behoud volgorde
        seen: set[str] = set()
        unique: list[Recipe] = []
        for r in filtered:
            if r.id not in seen:
                seen.add(r.id)
                unique.append(r)
        filtered_recipes = unique
    else:
        filtered_recipes = recipe_search.results

    # Sortering: laatst gegeten
    laatst_gegeten = _get_laatst_gegeten_dict(history)
    sorted_recipes = sorted(
        filtered_recipes,
        key=lambda r: laatst_gegeten.get(r.id, date(1900, 1, 1)),
    )

    # Bouw recept context
    vandaag = date.today()
    recepten_context = []
    for r in sorted_recipes:
        laatst = laatst_gegeten.get(r.id)
        recepten_context.append(
            {
                "id": r.id,
                "naam": r.naam,
                "categorie": r.categorie,
                "basis": r.basis.value,
                "bereidingstijd_min": r.bereidingstijd_min,
                "categorie_emoji": CATEGORIE_EMOJI.get(r.categorie.value, ""),
                "laatst_gegeten": _format_tijd_geleden(laatst, vandaag=vandaag),
            }
        )

    templates = request.app.state.templates

    # HTMX live zoek: alleen receptenlijst fragment
    if request.headers.get("HX-Target") == "recepten-lijst":
        return templates.TemplateResponse(
            request=request,
            name="fragments/recepten_lijst.html",
            context={"recepten": recepten_context, "dag": dag},
        )

    # Volledige receptkiezer sheet
    alle_categorieen = [
        Categorie.VLEES,
        Categorie.GEVOGELTE,
        Categorie.VIS,
        Categorie.VEGETARISCH,
    ]

    return templates.TemplateResponse(
        request=request,
        name="pages/receptkiezer.html",
        context={
            "dag": dag,
            "recepten": recepten_context,
            "search": search,
            "geselecteerde_categorieen": categorie,
            "categorieen": alle_categorieen,
            "categorie_emoji": CATEGORIE_EMOJI,
        },
    )


@router.post("/week/dag/{dag}/kies/{recipe_id}")
async def kies_recept(
    dag: int,
    recipe_id: str,
    request: Request,
    recipes: Annotated[list[Recipe], Depends(get_all_recipes)],
):
    """Toon portiescherm voor een gekozen recept."""
    week_menu = getattr(request.app.state, "week_menu", None)
    if week_menu is None:
        raise HTTPException(status_code=404, detail="Geen weekmenu beschikbaar")

    recept = next((r for r in recipes if r.id == recipe_id), None)
    if recept is None:
        raise HTTPException(status_code=404, detail="Recept niet gevonden")

    dag_planning = next((d for d in week_menu.dagen if d.dag == dag), None)
    huidig_personen = dag_planning.personen if dag_planning else 2

    templates = request.app.state.templates
    return templates.TemplateResponse(
        request=request,
        name="pages/porties.html",
        context={
            "dag": dag,
            "recept": recept,
            "huidig_personen": huidig_personen,
        },
    )


@router.post("/week/dag/{dag}/bevestig")
async def bevestig(
    dag: int,
    request: Request,
    recipes: Annotated[list[Recipe], Depends(get_all_recipes)],
    recipe_id: Annotated[str, Form()],
    personen: Annotated[int, Form()],
):
    """Bevestig recept en portiekeuze, update dagkaart."""
    week_menu = getattr(request.app.state, "week_menu", None)
    if week_menu is None:
        raise HTTPException(status_code=404, detail="Geen weekmenu beschikbaar")

    recept = next((r for r in recipes if r.id == recipe_id), None)
    if recept is None:
        raise HTTPException(status_code=404, detail="Recept niet gevonden")

    if dag < 0 or dag > 6:
        raise HTTPException(status_code=422, detail="Ongeldig dagnummer")

    if personen < 1 or personen > 10:
        raise HTTPException(status_code=422, detail="Ongeldig aantal porties")

    # Bouw nieuwe dagen met vervangen dag
    nieuwe_dagen = []
    for d in week_menu.dagen:
        if d.dag == dag:
            nieuwe_dagen.append(DagPlanning(dag=dag, recept=recept, personen=personen))
        else:
            nieuwe_dagen.append(d)

    new_menu = WeekMenu(week_start=week_menu.week_start, dagen=nieuwe_dagen)
    request.app.state.week_menu = new_menu

    # Render alleen de geüpdatete dagkaart
    dag_context = _build_dag_context(dag, request)
    templates = request.app.state.templates
    response = templates.TemplateResponse(
        request=request,
        name="components/dagkaart.html",
        context={"dag": dag_context},
    )
    response.headers["HX-Trigger"] = "closeSheet"
    return response
