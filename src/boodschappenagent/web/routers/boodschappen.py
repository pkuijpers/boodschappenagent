"""Boodschappenlijst routes."""

from datetime import date
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse

from boodschappenagent.boodschappenlijst import BoodschappenlijstGenerator
from boodschappenagent.voorraadbeheer import BoodschappenlijstFilter
from boodschappenagent.web.dependencies import (
    get_boodschappenlijst_filter,
    get_boodschappenlijst_generator,
)

router = APIRouter()


def _get_week_menu(request: Request):
    return getattr(request.app.state, "week_menu", None)


def _week_nummer(week_start: str) -> int:
    d = date.fromisoformat(week_start)
    return d.isocalendar().week


def _build_boodschappenlijst_state(
    request: Request,
    generator: BoodschappenlijstGenerator,
    lijst_filter: BoodschappenlijstFilter,
) -> list[dict]:
    """Genereer en sla boodschappenlijst op als mutable state."""
    week_menu = _get_week_menu(request)
    lijst = generator.genereer(week_menu)
    gefilterd = lijst_filter.filter_op_voorraad(lijst)

    items = [
        {
            "id": str(uuid4()),
            "naam": regel.naam,
            "hoeveelheid": regel.hoeveelheid,
            "eenheid": regel.eenheid,
            "checked": False,
            "handmatig": False,
        }
        for regel in gefilterd.regels
    ]
    request.app.state.boodschappenlijst = items
    return items


@router.get("/boodschappen")
async def boodschappen(
    request: Request,
    generator: Annotated[
        BoodschappenlijstGenerator, Depends(get_boodschappenlijst_generator)
    ],
    lijst_filter: Annotated[
        BoodschappenlijstFilter, Depends(get_boodschappenlijst_filter)
    ],
):
    """Boodschappenlijst pagina — gefilterd op weekmenu + voorraad."""
    week_menu = _get_week_menu(request)
    if week_menu is None:
        return RedirectResponse(url="/week", status_code=303)

    items = _build_boodschappenlijst_state(request, generator, lijst_filter)
    week_nr = _week_nummer(week_menu.week_start)

    context = {
        "week_nr": week_nr,
        "items": items,
        "totaal": len(items),
    }
    templates = request.app.state.templates
    is_htmx = request.headers.get("HX-Request") == "true"
    template_name = (
        "fragments/boodschappen_content.html" if is_htmx else "pages/boodschappen.html"
    )
    return templates.TemplateResponse(
        request=request, name=template_name, context=context
    )
