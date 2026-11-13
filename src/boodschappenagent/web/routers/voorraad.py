"""Voorraad routes — voorraadcheck pagina."""

from datetime import date
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse

from boodschappenagent.ah import AHIntegratie, AHTokenManager
from boodschappenagent.ah.preferences import MatchReviewItem, MatchVoorkeurenRepository
from boodschappenagent.boodschappenlijst import BoodschappenlijstFilter
from boodschappenagent.boodschappenlijst.generator import BoodschappenlijstGenerator
from boodschappenagent.boodschappenlijst.models import (
    Boodschappenlijst,
    BoodschappenRegel,
)
from boodschappenagent.voorraadbeheer import VoorraadRepository
from boodschappenagent.voorraadbeheer.models import VoorraadItem, VoorraadType
from boodschappenagent.web.dependencies import (
    get_ah_integratie,
    get_ah_token_manager,
    get_boodschappenlijst_filter,
    get_boodschappenlijst_generator,
    get_match_voorkeuren_repository,
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


def _aggregeer_ingredient_selectie(
    ingredient_selectie: list[dict],
    generator: BoodschappenlijstGenerator,
    week_start: str,
) -> Boodschappenlijst:
    """Aggregeer geselecteerde ingrediënten tot een Boodschappenlijst."""
    normalizer = generator._normalizer
    calculator = generator._calculator

    hoeveelheden: dict[tuple[str, str], float] = {}
    originele_namen: dict[tuple[str, str], set[str]] = {}
    recepten_per_key: dict[tuple[str, str], list[str]] = {}

    for item in ingredient_selectie:
        if not item["geselecteerd"]:
            continue
        norm_naam, norm_eenheid = normalizer.normaliseer(item["naam"], item["eenheid"])
        key = (norm_naam, norm_eenheid)
        if normalizer.is_niet_aggregeerbaar(norm_eenheid):
            hoeveelheden[key] = 1.0
        else:
            hoeveelheden[key] = hoeveelheden.get(key, 0.0) + item["hoeveelheid"]
        if key not in originele_namen:
            originele_namen[key] = set()
        originele_namen[key].add(item["naam"])
        if key not in recepten_per_key:
            recepten_per_key[key] = []
        if item["recept_naam"] not in recepten_per_key[key]:
            recepten_per_key[key].append(item["recept_naam"])

    regels: list[BoodschappenRegel] = []
    for key, totaal in hoeveelheden.items():
        norm_naam, norm_eenheid = key
        afgerond = calculator.round_quantity(totaal, norm_eenheid)
        regels.append(
            BoodschappenRegel(
                naam=norm_naam,
                hoeveelheid=afgerond,
                eenheid=norm_eenheid,
                originele_namen=frozenset(originele_namen[key]),
                recepten=tuple(recepten_per_key[key]),
            )
        )
    regels.sort(key=lambda r: r.naam)
    return Boodschappenlijst(week_start=week_start, regels=regels)


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
        return RedirectResponse(
            url="/ah/login?terug=/week&next=/voorraad", status_code=303
        )

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
async def voorraad_bevestig(
    request: Request,
    token_manager: Annotated[AHTokenManager, Depends(get_ah_token_manager)],
    generator: Annotated[
        BoodschappenlijstGenerator, Depends(get_boodschappenlijst_generator)
    ],
    lijst_filter: Annotated[
        BoodschappenlijstFilter, Depends(get_boodschappenlijst_filter)
    ],
    ah_integratie: Annotated[AHIntegratie, Depends(get_ah_integratie)],
    voorkeuren_repo: Annotated[
        MatchVoorkeurenRepository, Depends(get_match_voorkeuren_repository)
    ],
):
    """Bevestig voorraad: aggregeer ingrediënten en start AH-matching."""
    if _get_week_menu(request) is None:
        return RedirectResponse(url="/week", status_code=303)

    if not _is_ah_authenticated(token_manager):
        return RedirectResponse(
            url="/ah/login?terug=/voorraad&next=/voorraad", status_code=303
        )

    week_start = request.app.state.week_menu.week_start
    ingredient_selectie = getattr(request.app.state, "ingredient_selectie", []) or []

    lijst = _aggregeer_ingredient_selectie(ingredient_selectie, generator, week_start)
    gecombineerd = lijst_filter.voeg_pantry_toe(lijst)

    templates = request.app.state.templates

    if not gecombineerd.regels:
        return templates.TemplateResponse(
            request=request,
            name="pages/ah_error.html",
            context={"error_type": "lege_lijst"},
        )

    request.app.state.boodschappenlijst_model = gecombineerd
    request.app.state.boodschappenlijst = [
        {
            "id": str(uuid4()),
            "naam": regel.naam,
            "hoeveelheid": regel.hoeveelheid,
            "eenheid": regel.eenheid,
            "checked": False,
            "handmatig": False,
            "eerste_recept": regel.recepten[0] if regel.recepten else None,
            "extra_aantal": max(0, len(regel.recepten) - 1),
        }
        for regel in gecombineerd.regels
    ]

    try:
        matches = ah_integratie.zoek_producten(
            gecombineerd, voorkeuren_repo=voorkeuren_repo
        )
    except Exception:
        return templates.TemplateResponse(
            request=request,
            name="pages/ah_error.html",
            context={"error_type": "api_error"},
        )

    review_items = [
        MatchReviewItem(
            id=str(uuid4()),
            naam=match.regel.naam,
            hoeveelheid=getattr(match.regel, "hoeveelheid", None),
            eenheid=getattr(match.regel, "eenheid", "stuks"),
            product=match.product,
            bron=match.bron,
            gecorrigeerd=False,
            aantal=match.aantal,
        )
        for match in matches
    ]
    request.app.state.match_review_items = review_items

    return RedirectResponse(url="/boodschappen/match-review", status_code=303)


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
