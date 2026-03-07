"""Boodschappenlijst routes."""

from datetime import date
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from boodschappenagent.ah import AHIntegratie, AHTokenManager
from boodschappenagent.boodschappenlijst import BoodschappenlijstGenerator
from boodschappenagent.boodschappenlijst.models import Boodschappenlijst
from boodschappenagent.voorraadbeheer import BoodschappenlijstFilter
from boodschappenagent.web.dependencies import (
    get_ah_integratie,
    get_ah_token_manager,
    get_boodschappenlijst_filter,
    get_boodschappenlijst_generator,
)

router = APIRouter()


def _get_week_menu(request: Request):
    return getattr(request.app.state, "week_menu", None)


def _get_boodschappenlijst(request: Request) -> Boodschappenlijst | None:
    """Haal de boodschappenlijst op uit app.state."""
    return getattr(request.app.state, "boodschappenlijst_model", None)


def _get_items(request: Request) -> list[dict]:
    """Haal de boodschappenlijst items (dicts) op uit app.state."""
    return getattr(request.app.state, "boodschappenlijst", None) or []


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

    # Bewaar het model voor AH-integratie
    request.app.state.boodschappenlijst_model = gefilterd

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
    token_manager: Annotated[AHTokenManager, Depends(get_ah_token_manager)],
):
    """Boodschappenlijst pagina — gefilterd op weekmenu + voorraad."""
    week_menu = _get_week_menu(request)
    if week_menu is None:
        return RedirectResponse(url="/week", status_code=303)

    items = _build_boodschappenlijst_state(request, generator, lijst_filter)
    week_nr = _week_nummer(week_menu.week_start)

    try:
        ah_authenticated = token_manager.is_authenticated()
    except Exception:
        ah_authenticated = False

    context = {
        "week_nr": week_nr,
        "items": items,
        "totaal": len(items),
        "ah_authenticated": ah_authenticated,
    }
    templates = request.app.state.templates
    is_htmx = request.headers.get("HX-Request") == "true"
    template_name = (
        "fragments/boodschappen_content.html" if is_htmx else "pages/boodschappen.html"
    )
    return templates.TemplateResponse(
        request=request, name=template_name, context=context
    )


def _get_item(request: Request, item_id: str) -> dict:
    """Zoek item op id in app state, gooi 404 als niet gevonden."""
    items = _get_items(request)
    item = next((i for i in items if i["id"] == item_id), None)
    if item is None:
        raise HTTPException(status_code=404, detail="Item niet gevonden")
    return item


def _header_context(request: Request) -> dict:
    """Geeft week_nr en totaal voor de OOB header."""
    week_menu = _get_week_menu(request)
    items = _get_items(request)
    week_nr = _week_nummer(week_menu.week_start) if week_menu else 0
    return {"week_nr": week_nr, "totaal": len(items)}


@router.patch("/boodschappen/{item_id}/hoeveelheid")
async def update_hoeveelheid(
    item_id: str,
    request: Request,
    hoeveelheid: Annotated[float, Form()],
):
    """Hoeveelheid aanpassen van een boodschapitem."""
    item = _get_item(request, item_id)
    item["hoeveelheid"] = hoeveelheid
    templates = request.app.state.templates
    return templates.TemplateResponse(
        request=request, name="components/boodschapitem.html", context={"item": item}
    )


@router.patch("/boodschappen/{item_id}")
async def toggle_checked(
    item_id: str,
    request: Request,
    checked: Annotated[str, Form()],
):
    """Toggle checked status van een boodschapitem."""
    item = _get_item(request, item_id)
    item["checked"] = checked.lower() == "true"
    templates = request.app.state.templates
    return templates.TemplateResponse(
        request=request, name="components/boodschapitem.html", context={"item": item}
    )


@router.delete("/boodschappen/{item_id}")
async def verwijder_item(item_id: str, request: Request):
    """Verwijder een boodschapitem en stuur OOB header update."""
    item = _get_item(request, item_id)
    items = request.app.state.boodschappenlijst
    items.remove(item)
    templates = request.app.state.templates
    return templates.TemplateResponse(
        request=request,
        name="fragments/boodschappen_header_oob.html",
        context=_header_context(request),
    )


@router.post("/boodschappen/toevoegen")
async def handmatig_toevoegen(
    request: Request,
    naam: Annotated[str, Form()],
    hoeveelheid: Annotated[float, Form()] = 1.0,
    eenheid: Annotated[str, Form()] = "stuks",
):
    """Handmatig een product toevoegen aan de boodschappenlijst."""
    if not naam or not naam.strip():
        raise HTTPException(status_code=422, detail="Naam is verplicht")

    if getattr(request.app.state, "boodschappenlijst", None) is None:
        request.app.state.boodschappenlijst = []
    items = request.app.state.boodschappenlijst

    item = {
        "id": str(uuid4()),
        "naam": naam.strip(),
        "hoeveelheid": hoeveelheid,
        "eenheid": eenheid,
        "checked": False,
        "handmatig": True,
    }
    items.append(item)

    templates = request.app.state.templates
    item_html = templates.get_template("components/boodschapitem.html").render(
        {"item": item, "request": request}
    )
    header_html = templates.get_template(
        "fragments/boodschappen_header_oob.html"
    ).render({**_header_context(request), "request": request})
    return HTMLResponse(content=item_html + header_html)


@router.post("/boodschappen/verstuur-naar-ah")
async def verstuur_naar_ah(
    request: Request,
    token_manager: Annotated[AHTokenManager, Depends(get_ah_token_manager)],
    ah_integratie: Annotated[AHIntegratie, Depends(get_ah_integratie)],
):
    """Verstuur boodschappenlijst naar Albert Heijn."""
    templates = request.app.state.templates

    # Check of gebruiker ingelogd is (kan een exception gooien bij verlopen tokens)
    try:
        authenticated = token_manager.is_authenticated()
    except Exception:
        return RedirectResponse(url="/ah/login", status_code=303)

    if not authenticated:
        return RedirectResponse(url="/ah/login", status_code=303)

    # Check of er een boodschappenlijst is
    lijst = _get_boodschappenlijst(request)
    if lijst is None:
        return RedirectResponse(url="/week", status_code=303)

    # Check op lege lijst
    if len(lijst.regels) == 0:
        return templates.TemplateResponse(
            request=request,
            name="pages/ah_error.html",
            context={"error_type": "lege_lijst"},
        )

    # Sync naar AH
    try:
        resultaat = ah_integratie.sync_naar_lijst(lijst)
    except Exception:
        return templates.TemplateResponse(
            request=request,
            name="pages/ah_error.html",
            context={"error_type": "api_error"},
        )

    return templates.TemplateResponse(
        request=request,
        name="pages/ah_bevestiging.html",
        context={"resultaat": resultaat},
    )
