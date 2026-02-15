"""Menu routes — weekoverzicht en gerelateerde endpoints."""

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

router = APIRouter()


@router.get("/")
async def root():
    """Redirect root naar weekoverzicht."""
    return RedirectResponse(url="/week")


@router.get("/week")
async def week(request: Request):
    """Weekoverzicht pagina."""
    templates = request.app.state.templates
    return templates.TemplateResponse(
        request=request,
        name="pages/week.html",
    )
