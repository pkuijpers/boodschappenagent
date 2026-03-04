"""Voorraad routes — voorraadcheck pagina."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse

from boodschappenagent.voorraadbeheer import VoorraadRepository
from boodschappenagent.voorraadbeheer.models import VoorraadItem, VoorraadType
from boodschappenagent.voorraadbeheer.presets import STANDAARD_HOUDBAAR, VERSE_BASICS
from boodschappenagent.web.dependencies import get_voorraad_repository

router = APIRouter()

_STANDAARD_HOUDBAAR_SET = set(STANDAARD_HOUDBAAR)


def _get_week_menu(request: Request):
    return getattr(request.app.state, "week_menu", None)


def _build_voorraad_context(
    request: Request, repository: VoorraadRepository
) -> dict:
    """Bouw template context voor voorraadcheck pagina."""
    week_menu = _get_week_menu(request)
    op_voorraad_namen = repository.op_voorraad_namen()

    # Houdbare items: ingrediënten uit weekmenu die in STANDAARD_HOUDBAAR staan
    gezien: set[str] = set()
    houdbaar_items = []
    for dag in week_menu.geplande_dagen:
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
    if _get_week_menu(request) is None:
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


@router.post("/voorraad/bevestig")
async def voorraad_bevestig(request: Request):
    """Bevestig voorraad en redirect naar boodschappenlijst."""
    if _get_week_menu(request) is None:
        return RedirectResponse(url="/week", status_code=303)
    return RedirectResponse(url="/boodschappen", status_code=303)


@router.post("/voorraad/{item}/status")
async def voorraad_toggle(
    item: str,
    request: Request,
    op_voorraad: Annotated[str, Form()],
    repository: Annotated[VoorraadRepository, Depends(get_voorraad_repository)],
):
    """Toggle voorraadstatus van een item — retourneert enkelvoudig HTMX-fragment."""
    if _get_week_menu(request) is None:
        raise HTTPException(status_code=404)

    context = _build_voorraad_context(request, repository)
    houdbaar_by_naam = {i["naam"]: i for i in context["houdbaar_items"]}
    vers_by_naam = {i["naam"]: i for i in context["vers_items"]}

    if item not in houdbaar_by_naam and item not in vers_by_naam:
        raise HTTPException(status_code=404)

    if item in houdbaar_by_naam:
        voorraad_type = VoorraadType.HOUDBAAR
        item_context = houdbaar_by_naam[item]["context"]
    else:
        voorraad_type = VoorraadType.VERS_BASIS
        item_context = None

    is_op_voorraad = op_voorraad.lower() in ("true", "1", "yes", "ja")
    repository.update_item(
        VoorraadItem(
            naam=item,
            type=voorraad_type,
            op_voorraad=is_op_voorraad,
            laatst_gecheckt=str(date.today()),
        )
    )

    templates = request.app.state.templates
    return templates.TemplateResponse(
        request=request,
        name="components/voorraaditem.html",
        context={"item": {
            "naam": item,
            "context": item_context,
            "op_voorraad": is_op_voorraad,
        }},
    )
