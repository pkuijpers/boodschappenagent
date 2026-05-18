"""Boodschappenlijst routes."""

from datetime import date
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from boodschappenagent.ah import AHIntegratie, AHTokenManager
from boodschappenagent.ah.integration import ProductMatch, SyncResultaat
from boodschappenagent.ah.preferences import MatchReviewItem, MatchVoorkeurenRepository
from boodschappenagent.boodschappenlijst import BoodschappenlijstGenerator
from boodschappenagent.boodschappenlijst.models import (
    Boodschappenlijst,
    BoodschappenRegel,
)
from boodschappenagent.voorraadbeheer import BoodschappenlijstFilter
from boodschappenagent.web.dependencies import (
    get_ah_integratie,
    get_ah_token_manager,
    get_boodschappenlijst_filter,
    get_boodschappenlijst_generator,
    get_match_voorkeuren_repository,
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
            "eerste_recept": regel.recepten[0] if regel.recepten else None,
            "extra_aantal": max(0, len(regel.recepten) - 1),
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

    ah_authenticated = _is_ah_authenticated(token_manager)

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


def _is_ah_authenticated(token_manager: AHTokenManager) -> bool:
    """Check AH auth status; geeft False bij elke fout."""
    try:
        return token_manager.is_authenticated()
    except Exception:
        return False


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
        "eerste_recept": None,
        "extra_aantal": 0,
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
    voorkeuren_repo: Annotated[
        MatchVoorkeurenRepository, Depends(get_match_voorkeuren_repository)
    ],
):
    """Match boodschappenlijst aan AH producten en redirect naar match-review."""
    templates = request.app.state.templates

    if not _is_ah_authenticated(token_manager):
        return RedirectResponse(url="/ah/login", status_code=303)

    sentinel = _get_boodschappenlijst(request)
    if sentinel is None:
        return RedirectResponse(url="/week", status_code=303)

    te_versturen = [item for item in _get_items(request) if not item.get("checked")]

    if not te_versturen:
        return templates.TemplateResponse(
            request=request,
            name="pages/ah_error.html",
            context={"error_type": "lege_lijst"},
        )

    regels = [
        BoodschappenRegel(
            naam=item["naam"],
            hoeveelheid=item["hoeveelheid"],
            eenheid=item["eenheid"],
            originele_namen=frozenset({item["naam"]}),
        )
        for item in te_versturen
    ]
    lijst = Boodschappenlijst(week_start=sentinel.week_start, regels=regels)

    try:
        matches = ah_integratie.zoek_producten(lijst, voorkeuren_repo=voorkeuren_repo)
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


@router.get("/boodschappen/match-review")
async def match_review(request: Request):
    """Match-review pagina — toont alle gematche items voor bevestiging."""
    items = getattr(request.app.state, "match_review_items", None) or []
    if not items:
        return RedirectResponse(url="/boodschappen", status_code=303)

    templates = request.app.state.templates
    return templates.TemplateResponse(
        request=request,
        name="pages/match_review.html",
        context={"items": items},
    )


@router.post("/boodschappen/bevestig-matches")
async def bevestig_matches(
    request: Request,
    token_manager: Annotated[AHTokenManager, Depends(get_ah_token_manager)],
    ah_integratie: Annotated[AHIntegratie, Depends(get_ah_integratie)],
    voorkeuren_repo: Annotated[
        MatchVoorkeurenRepository, Depends(get_match_voorkeuren_repository)
    ],
):
    """Maak AH-lijst aan van bevestigde matches; sla correcties op als voorkeur."""
    if not _is_ah_authenticated(token_manager):
        return RedirectResponse(url="/ah/login", status_code=303)

    items: list[MatchReviewItem] = (
        getattr(request.app.state, "match_review_items", None) or []
    )

    if any(item.product is None for item in items):
        raise HTTPException(
            status_code=400,
            detail=(
                "Niet alle items hebben een match"
                " — bevestig pas als alle items een product hebben"
            ),
        )

    sentinel = _get_boodschappenlijst(request)
    lijst_naam = f"Boodschappen {sentinel.week_start}" if sentinel else "Boodschappen"

    lijst_id = ah_integratie.create_list(lijst_naam)

    product_quantities: dict[int, int] = {}
    for item in items:
        product_quantities[item.product.id] = (
            product_quantities.get(item.product.id, 0) + item.aantal
        )
    if product_quantities:
        ah_integratie.add_products_to_list(lijst_id, list(product_quantities.items()))

    # Sla bevestigde matches op als voorkeur (US3)
    # Skip alleen items die al als ongewijzigde voorkeur zijn ingeladen.
    from datetime import datetime

    from boodschappenagent.ah.preferences import MatchVoorkeur

    for item in items:
        if item.product is not None and (item.gecorrigeerd or item.bron != "voorkeur"):
            voorkeuren_repo.save(
                MatchVoorkeur(
                    ingredient_naam=item.naam.lower().strip(),
                    article_id=item.product.id,
                    product_naam=item.product.title,
                    updated_at=datetime.now().isoformat(timespec="seconds"),
                )
            )

    # Bouw SyncResultaat voor de bevestigingspagina
    productmatches = [
        ProductMatch(
            regel=type("Regel", (), {"naam": item.naam})(),
            product=item.product,
            bron=item.bron,
            aantal=item.aantal,
        )
        for item in items
    ]
    resultaat = SyncResultaat(
        lijst_id=lijst_id,
        lijst_naam=lijst_naam,
        matches=productmatches,
    )
    request.app.state.sync_resultaat = resultaat

    request.app.state.match_review_items = []

    redirect_url = "/boodschappen/ah-bevestiging"
    if request.headers.get("HX-Request") == "true":
        response = Response(status_code=200)
        response.headers["HX-Redirect"] = redirect_url
        return response
    return RedirectResponse(url=redirect_url, status_code=303)


@router.get("/boodschappen/ah-bevestiging")
async def ah_bevestiging(request: Request):
    """Bevestigingspagina na het aanmaken van de AH-lijst."""
    resultaat = getattr(request.app.state, "sync_resultaat", None)
    if resultaat is None:
        return RedirectResponse(url="/week", status_code=303)

    templates = request.app.state.templates
    return templates.TemplateResponse(
        request=request,
        name="pages/ah_bevestiging.html",
        context={"resultaat": resultaat},
    )


@router.get("/boodschappen/zoek-product")
async def zoek_product(
    request: Request,
    q: str,
    item_id: str,
    ah_integratie: Annotated[AHIntegratie, Depends(get_ah_integratie)],
):
    """Zoek AH-producten voor het corrigeren van een match (HTMX fragment)."""
    items: list[MatchReviewItem] = (
        getattr(request.app.state, "match_review_items", None) or []
    )
    item = next((i for i in items if i.id == item_id), None)
    if item is None:
        raise HTTPException(status_code=404, detail="Item niet gevonden")

    producten = []
    if q and q.strip():
        try:
            producten = ah_integratie.zoek_producten_voor_correctie(q)
        except Exception:
            producten = []

    templates = request.app.state.templates
    # q leeg → initieel openen: zoekbalk + lege container.
    # q gevuld → alleen resultaten, zodat de input niet wordt vervangen.
    template_name = (
        "fragments/zoekresultaten_inner.html"
        if q and q.strip()
        else "fragments/zoekresultaten.html"
    )
    return templates.TemplateResponse(
        request=request,
        name=template_name,
        context={"producten": producten, "item_id": item_id},
    )


@router.post("/boodschappen/kies-product")
async def kies_product(
    request: Request,
    item_id: Annotated[str, Form()],
    article_id: Annotated[int, Form()],
    title: Annotated[str, Form()],
    ah_integratie: Annotated[AHIntegratie, Depends(get_ah_integratie)],
    brand: Annotated[str, Form()] = "",
    size: Annotated[str, Form()] = "",
    price: Annotated[float, Form()] = 0.0,
    category: Annotated[str, Form()] = "",
):
    """Kies een alternatief product voor een match-review item (HTMX OOB swap)."""
    if article_id <= 0:
        raise HTTPException(status_code=400, detail="Ongeldig article_id")

    items: list[MatchReviewItem] = (
        getattr(request.app.state, "match_review_items", None) or []
    )
    item = next((i for i in items if i.id == item_id), None)
    if item is None:
        raise HTTPException(status_code=404, detail="Item niet gevonden")

    from boodschappenagent.ah.models import Product

    product = Product(
        id=article_id,
        title=title,
        brand=brand,
        size=size,
        price=price,
        category=category,
        is_orderable=True,
    )

    regel = BoodschappenRegel(
        naam=item.naam,
        hoeveelheid=item.hoeveelheid or 1.0,
        eenheid=item.eenheid,
        originele_namen=frozenset({item.naam}),
    )
    match = ah_integratie.kies_product_voor_regel(regel, product)
    item.product = match.product
    item.bron = match.bron
    item.gecorrigeerd = True
    item.aantal = match.aantal

    alle_gevonden = all(i.product is not None for i in items)

    templates = request.app.state.templates

    card_html = templates.get_template("fragments/match_review_item.html").render(
        {"item": item, "request": request}
    )
    btn_html = templates.get_template("fragments/bevestig_btn.html").render(
        {"alle_gevonden": alle_gevonden, "request": request}
    )
    return HTMLResponse(content=card_html + btn_html)
