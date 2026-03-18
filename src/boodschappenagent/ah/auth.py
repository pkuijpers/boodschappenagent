"""AH OAuth2 Token Manager voor de Mobile API."""

import json
import time
from pathlib import Path

import requests

DEFAULT_TOKEN_PATH = Path(__file__).parents[3] / "data" / "ah_tokens.json"

AUTH_HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Appie/8.22.3",
    "X-Application": "AHWEBSHOP",
}


class AHTokenManager:
    """Beheert OAuth2 tokens voor de AH Mobile API.

    Eenmalige setup:
        1. Open: https://login.ah.nl/secure/oauth/authorize?client_id=appie&redirect_uri=appie://login-exit&response_type=code
        2. Log in → browser redirect faalt → kopieer code uit URL
        3. manager.login(code)

    Daarna automatisch: get_access_token() refresht wanneer nodig.
    """

    TOKEN_URL = "https://api.ah.nl/mobile-auth/v1/auth/token"
    REFRESH_URL = "https://api.ah.nl/mobile-auth/v1/auth/token/refresh"
    CLIENT_ID = "appie"

    def __init__(self, token_path: Path | None = None):
        self._token_path = token_path or DEFAULT_TOKEN_PATH
        self._access_token: str | None = None
        self._refresh_token: str | None = None
        self._expires_at: float = 0.0
        self._load_tokens()

    def login(self, auth_code: str) -> None:
        """Wissel authorization code in voor tokens."""
        response = requests.post(
            self.TOKEN_URL,
            json={"clientId": self.CLIENT_ID, "code": auth_code},
            headers=AUTH_HEADERS,
        )
        response.raise_for_status()
        self._store_response(response.json())

    def refresh(self) -> None:
        """Vernieuw access token met refresh token."""
        if not self._refresh_token:
            raise Exception("No refresh token available. Run login() first.")

        response = requests.post(
            self.REFRESH_URL,
            json={"clientId": self.CLIENT_ID, "refreshToken": self._refresh_token},
            headers=AUTH_HEADERS,
        )
        response.raise_for_status()
        self._store_response(response.json())

    def get_access_token(self) -> str:
        """Geef geldig access token terug, refresh automatisch als verlopen."""
        if not self._refresh_token:
            raise Exception("Not authenticated. Run login() first.")

        if self._is_expired():
            self.refresh()

        return self._access_token

    def is_authenticated(self) -> bool:
        """Check of er een refresh token beschikbaar is."""
        return self._refresh_token is not None

    def _is_expired(self) -> bool:
        """Check of access token verlopen is (met 60s marge)."""
        return time.time() >= (self._expires_at - 60)

    def _store_response(self, data: dict) -> None:
        """Sla tokens op uit API response."""
        self._access_token = data["access_token"]
        self._refresh_token = data["refresh_token"]
        self._expires_at = time.time() + data["expires_in"]
        self._save_tokens()

    def _save_tokens(self) -> None:
        """Schrijf tokens naar disk."""
        self._token_path.parent.mkdir(parents=True, exist_ok=True)
        self._token_path.write_text(
            json.dumps(
                {
                    "access_token": self._access_token,
                    "refresh_token": self._refresh_token,
                    "expires_at": self._expires_at,
                }
            )
        )

    def _load_tokens(self) -> None:
        """Laad tokens van disk als beschikbaar."""
        if not self._token_path.exists():
            return

        data = json.loads(self._token_path.read_text())
        self._access_token = data.get("access_token")
        self._refresh_token = data.get("refresh_token")
        self._expires_at = data.get("expires_at", 0.0)
