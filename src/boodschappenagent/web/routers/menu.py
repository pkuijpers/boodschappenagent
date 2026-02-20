"""Menu routes — weekoverzicht en gerelateerde endpoints."""

from datetime import date

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

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


@router.get("/week")
async def week(request: Request):
    """Weekoverzicht pagina met dagkaarten."""
    templates = request.app.state.templates

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

    context = {
        "week_nummer": week_nummer,
        "dagen": dagen,
    }

    is_htmx = request.headers.get("HX-Request") == "true"
    template_name = "fragments/week_content.html" if is_htmx else "pages/week.html"

    return templates.TemplateResponse(
        request=request,
        name=template_name,
        context=context,
    )
