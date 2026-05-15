"""Ingredient-selectie routes — scherm tussen weekmenu en voorraadcheck."""

from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import RedirectResponse

router = APIRouter()


def _init_ingredient_selectie(request: Request) -> None:
    """Initialiseer ingredient_selectie vanuit week_menu als nog niet aanwezig."""
    bestaand = getattr(request.app.state, "ingredient_selectie", None)
    if bestaand:
        return
    week_menu = request.app.state.week_menu
    items = []
    for dag in week_menu.geplande_dagen:
        scaled = dag.recept.scale_to_portions(dag.personen)
        for ing in scaled.ingredienten:
            items.append(
                {
                    "id": str(uuid4()),
                    "recept_naam": dag.recept.naam,
                    "naam": ing.naam,
                    "hoeveelheid": ing.hoeveelheid,
                    "eenheid": ing.eenheid,
                    "geselecteerd": True,
                }
            )
    request.app.state.ingredient_selectie = items


def _build_groepen_context(request: Request) -> dict:
    """Bouw template context met groepen per recept."""
    items = request.app.state.ingredient_selectie
    groepen: list[dict] = []
    seen: dict[str, int] = {}
    for item in items:
        naam = item["recept_naam"]
        if naam not in seen:
            seen[naam] = len(groepen)
            groepen.append({"recept_naam": naam, "ingredienten": []})
        groepen[seen[naam]]["ingredienten"].append(item)
    totaal_geselecteerd = sum(1 for i in items if i["geselecteerd"])
    return {"groepen": groepen, "totaal_geselecteerd": totaal_geselecteerd}


@router.get("/ingredient-selectie")
async def ingredient_selectie(request: Request):
    """Ingredient-selectiescherm — toont alle recept-ingrediënten."""
    if getattr(request.app.state, "week_menu", None) is None:
        return RedirectResponse(url="/week", status_code=303)
    _init_ingredient_selectie(request)
    context = _build_groepen_context(request)
    templates = request.app.state.templates
    is_htmx = request.headers.get("HX-Request") == "true"
    template_name = (
        "fragments/ingredient_selectie_content.html"
        if is_htmx
        else "pages/ingredient_selectie.html"
    )
    return templates.TemplateResponse(
        request=request, name=template_name, context=context
    )


@router.post("/ingredient-selectie/bevestig")
async def ingredient_selectie_bevestig(request: Request):
    """Sla de huidige selectie op en redirect naar voorraadcheck."""
    if getattr(request.app.state, "week_menu", None) is None:
        return RedirectResponse(url="/week", status_code=303)
    return RedirectResponse(url="/voorraad", status_code=303)


@router.post("/ingredient-selectie/{item_id}/toggle")
async def ingredient_selectie_toggle(item_id: str, request: Request):
    """Toggle geselecteerd-status van één ingredient."""
    items = getattr(request.app.state, "ingredient_selectie", [])
    item = next((i for i in items if i["id"] == item_id), None)
    if item is None:
        raise HTTPException(status_code=404, detail="Item niet gevonden")
    item["geselecteerd"] = not item["geselecteerd"]
    templates = request.app.state.templates
    return templates.TemplateResponse(
        request=request,
        name="components/ingredient_selectie_item.html",
        context={"item": item},
    )


@router.patch("/ingredient-selectie/{item_id}/hoeveelheid")
async def ingredient_selectie_hoeveelheid(
    item_id: str,
    request: Request,
    hoeveelheid: Annotated[float, Form()],
):
    """Pas hoeveelheid van één ingredient aan."""
    items = getattr(request.app.state, "ingredient_selectie", [])
    item = next((i for i in items if i["id"] == item_id), None)
    if item is None:
        raise HTTPException(status_code=404, detail="Item niet gevonden")
    item["hoeveelheid"] = hoeveelheid
    templates = request.app.state.templates
    return templates.TemplateResponse(
        request=request,
        name="components/ingredient_selectie_item.html",
        context={"item": item},
    )
