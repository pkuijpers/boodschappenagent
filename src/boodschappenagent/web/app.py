"""FastAPI app factory voor boodschappenagent."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from boodschappenagent.web.routers import menu, voorraad

TEMPLATES_DIR = Path(__file__).parent / "templates"
STATIC_DIR = Path(__file__).parent / "static"


def create_app() -> FastAPI:
    """Maak en configureer de FastAPI-applicatie."""
    app = FastAPI(title="Albert", docs_url=None, redoc_url=None)

    # Jinja2 templates
    templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
    app.state.templates = templates

    # Static files
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    # Routers
    app.include_router(menu.router)
    app.include_router(voorraad.router)

    return app
