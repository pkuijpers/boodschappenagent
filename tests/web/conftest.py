"""FastAPI TestClient fixtures voor web tests."""

import pytest
from fastapi.testclient import TestClient

from boodschappenagent.web.app import create_app


@pytest.fixture
def client() -> TestClient:
    """TestClient met de FastAPI app."""
    app = create_app()
    return TestClient(app)
