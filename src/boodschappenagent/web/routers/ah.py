"""Albert Heijn integratie routes."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/ah", tags=["ah"])

AH_LOGIN_URL = (
    "https://login.ah.nl/secure/oauth/authorize"
    "?client_id=appie&redirect_uri=appie://login-exit&response_type=code"
)


@router.get("/login", response_class=HTMLResponse)
async def login_pagina(request: Request):
    """Toon de AH login pagina met instructies en code-invoerveld."""
    templates = request.app.state.templates
    is_htmx = request.headers.get("HX-Request") == "true"
    template_name = (
        "fragments/ah_login_content.html" if is_htmx else "pages/ah_login.html"
    )
    return templates.TemplateResponse(
        template_name,
        {"request": request, "login_url": AH_LOGIN_URL},
    )
