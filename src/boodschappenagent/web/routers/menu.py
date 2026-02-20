"""Menu routes — weekoverzicht en gerelateerde endpoints."""

from datetime import date, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse

from boodschappenagent.models import Seizoen
from boodschappenagent.planner import DagInput, MenuPlanner
from boodschappenagent.web.dependencies import get_menu_planner

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
