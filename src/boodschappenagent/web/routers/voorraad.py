"""Voorraad routes — voorraadcheck pagina."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse

from boodschappenagent.voorraadbeheer import VoorraadRepository
from boodschappenagent.voorraadbeheer.presets import STANDAARD_HOUDBAAR, VERSE_BASICS
from boodschappenagent.web.dependencies import get_voorraad_repository

router = APIRouter()

_STANDAARD_HOUDBAAR_SET = set(STANDAARD_HOUDBAAR)


def _build_voorraad_context(
    request: Request, repository: VoorraadRepository
) -> dict:
    """Bouw template context voor voorraadcheck pagina."""
    week_menu = request.app.state.week_menu
    op_voorraad_namen = repository.op_voorraad_namen()

    # Houdbare items: ingrediënten uit weekmenu die in STANDAARD_HOUDBAAR staan
    gezien: set[str] = set()
    houdbaar_items = []
    for dag in week_menu.geplande_dagen:
        assert dag.recept is not None
        for ing in dag.recept.ingredienten:
            naam = ing.naam.lower()
            if naam in _STANDAARD_HOUDBAAR_SET and naam not in gezien:
                houdbaar_items.append(
                    {
                        "naam": naam,
                        "context": dag.recept.naam,
                        "op_voorraad": naam in op_voorraad_namen,
                    }
                )
                gezien.add(naam)
    houdbaar_items.sort(key=lambda x: x["naam"])

    # Verse basics: altijd tonen
    vers_items = [
        {
            "naam": naam,
            "context": None,
            "op_voorraad": naam in op_voorraad_namen,
        }
        for naam, *_ in VERSE_BASICS
    ]

    return {
        "houdbaar_items": houdbaar_items,
        "vers_items": vers_items,
    }


@router.get("/voorraad")
async def voorraad(
    request: Request,
    repository: Annotated[VoorraadRepository, Depends(get_voorraad_repository)],
):
    """Voorraadcheck pagina — houdbare producten en verse basics."""
    week_menu = getattr(request.app.state, "week_menu", None)
    if week_menu is None:
        return RedirectResponse(url="/week", status_code=303)

    context = _build_voorraad_context(request, repository)
    templates = request.app.state.templates
    is_htmx = request.headers.get("HX-Request") == "true"
    template_name = (
        "fragments/voorraad_content.html" if is_htmx else "pages/voorraad.html"
    )
    return templates.TemplateResponse(
        request=request, name=template_name, context=context
    )
