"""Voorraad routes — voorraadcheck pagina."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse

from boodschappenagent.ah import AHIntegratie, AHTokenManager
from boodschappenagent.voorraadbeheer import VoorraadRepository
from boodschappenagent.voorraadbeheer.models import VoorraadItem, VoorraadType
from boodschappenagent.web.dependencies import (
    get_ah_integratie,
    get_ah_token_manager,
    get_voorraad_repository,
)

router = APIRouter()


def _get_week_menu(request: Request):
    return getattr(request.app.state, "week_menu", None)


def _is_ah_authenticated(token_manager: AHTokenManager) -> bool:
    """Check AH auth status; geeft False bij elke fout."""
    try:
        return token_manager.is_authenticated()
    except Exception:
        return False


def _haal_voorraad_producten(ah_integratie: AHIntegratie) -> list[dict]:
    """Haal producten op uit de AH 'Voorraad' favorietenlijst."""
    try:
        producten = ah_integratie.haal_voorraad_producten()
        return [{"naam": p.title, "id": str(p.id)} for p in producten]
    except Exception:
        return []


def _build_voorraad_context(
    repository: VoorraadRepository, producten: list[dict]
) -> dict:
    """Bouw template context voor voorraadcheck pagina."""
    op_voorraad_namen = repository.op_voorraad_namen()
    items = [
        {
            "naam": p["naam"],
            "id": p["id"],
            "context": None,
            "op_voorraad": p["naam"].lower() in op_voorraad_namen,
        }
        for p in producten
    ]
    return {
        "voorraad_items": items,
        "ah_fout": len(producten) == 0,
    }


@router.get("/voorraad")
async def voorraad(
    request: Request,
    repository: Annotated[VoorraadRepository, Depends(get_voorraad_repository)],
    token_manager: Annotated[AHTokenManager, Depends(get_ah_token_manager)],
    ah_integratie: Annotated[AHIntegratie, Depends(get_ah_integratie)],
):
    """Voorraadcheck pagina — producten uit AH Voorraad lijst."""
    if _get_week_menu(request) is None:
        return RedirectResponse(url="/week", status_code=303)

    if not _is_ah_authenticated(token_manager):
        return RedirectResponse(url="/ah/login?terug=/week&next=/voorraad", status_code=303)

    producten = _haal_voorraad_producten(ah_integratie)
    if producten:
        repository.sync_met_ah_namen({p["naam"] for p in producten})
    context = _build_voorraad_context(repository, producten)
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


@router.post("/voorraad/{product_id}/status")
async def voorraad_toggle(
    product_id: str,
    request: Request,
    naam: Annotated[str, Form()],
    op_voorraad: Annotated[str, Form()],
    repository: Annotated[VoorraadRepository, Depends(get_voorraad_repository)],
    ah_integratie: Annotated[AHIntegratie, Depends(get_ah_integratie)],
):
    """Toggle voorraadstatus van een product — retourneert enkelvoudig HTMX-fragment."""
    if _get_week_menu(request) is None:
        raise HTTPException(status_code=404)

    producten = _haal_voorraad_producten(ah_integratie)
    product_ids = {p["id"] for p in producten}
    if product_id not in product_ids:
        raise HTTPException(status_code=404)

    is_op_voorraad = op_voorraad.lower() in ("true", "1", "yes", "ja")
    repository.update_item(
        VoorraadItem(
            naam=naam.lower(),
            type=VoorraadType.HOUDBAAR,
            op_voorraad=is_op_voorraad,
            laatst_gecheckt=str(date.today()),
        )
    )

    templates = request.app.state.templates
    return templates.TemplateResponse(
        request=request,
        name="components/voorraaditem.html",
        context={
            "item": {
                "naam": naam,
                "id": product_id,
                "context": None,
                "op_voorraad": is_op_voorraad,
            }
        },
    )
