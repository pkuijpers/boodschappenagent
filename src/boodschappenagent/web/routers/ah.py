"""Albert Heijn integratie routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from boodschappenagent.ah import AHTokenManager
from boodschappenagent.web.dependencies import get_ah_token_manager

router = APIRouter(prefix="/ah", tags=["ah"])

AH_LOGIN_URL = (
    "https://login.ah.nl/secure/oauth/authorize"
    "?client_id=appie&redirect_uri=appie://login-exit&response_type=code"
)


def _render_login(
    request: Request, terug: str = "/boodschappen", error: str | None = None
):
    """Render de login pagina (full page of HTMX fragment)."""
    templates = request.app.state.templates
    is_htmx = request.headers.get("HX-Request") == "true"
    template_name = (
        "fragments/ah_login_content.html" if is_htmx else "pages/ah_login.html"
    )
    return templates.TemplateResponse(
        request=request,
        name=template_name,
        context={"login_url": AH_LOGIN_URL, "terug": terug, "error": error},
    )


@router.get("/login", response_class=HTMLResponse)
async def login_pagina(
    request: Request,
    terug: Annotated[str, Query()] = "/boodschappen",
):
    """Toon de AH login pagina met instructies en code-invoerveld."""
    return _render_login(request, terug=terug)


@router.post("/login")
async def login_verwerken(
    request: Request,
    token_manager: Annotated[AHTokenManager, Depends(get_ah_token_manager)],
    code: str = Form(..., min_length=1),
    next: str = Query(default="/boodschappen"),
):
    """Verwerk authorization code en sla tokens op."""
    try:
        token_manager.login(code)
    except Exception:
        return _render_login(
            request, terug=next, error="Ongeldige code. Probeer opnieuw."
        )
    return RedirectResponse(url=next, status_code=303)


@router.get("/status")
async def status_check(
    token_manager: Annotated[AHTokenManager, Depends(get_ah_token_manager)],
):
    """Check of AH-tokens geldig zijn."""
    authenticated = token_manager.is_authenticated()
    if not authenticated:
        # Probeer te refreshen als er een refresh token is
        try:
            token_manager.refresh()
            authenticated = token_manager.is_authenticated()
        except Exception:
            pass
    return JSONResponse({"authenticated": authenticated})


@router.post("/logout")
async def logout(
    token_manager: Annotated[AHTokenManager, Depends(get_ah_token_manager)],
):
    """Verwijder tokens en redirect naar login pagina."""
    # Verwijder token bestand als het bestaat
    if hasattr(token_manager, "_token_path") and token_manager._token_path.exists():
        token_manager._token_path.unlink()
    return RedirectResponse(url="/ah/login", status_code=303)
