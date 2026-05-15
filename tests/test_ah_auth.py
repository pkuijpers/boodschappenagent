"""
Unit tests for AH Token Manager.

Run with: uv run pytest tests/test_ah_auth.py -v
"""

import json
import time
from unittest.mock import Mock, patch

import pytest

from boodschappenagent.ah.auth import AHTokenManager

PATCH_POST = "boodschappenagent.ah.auth.requests.post"


@pytest.fixture
def token_file(tmp_path):
    """Provide a temporary token file path."""
    return tmp_path / "tokens.json"


@pytest.fixture
def token_manager(token_file):
    """Create a token manager with a temporary token file."""
    return AHTokenManager(token_path=token_file)


@pytest.fixture
def mock_token_response():
    """Sample token response from AH API."""
    return {
        "access_token": "test-access-token",
        "refresh_token": "test-refresh-token",
        "expires_in": 7199,
    }


# =============================================================================
# Login Tests
# =============================================================================


class TestLogin:
    """Tests for AHTokenManager.login method."""

    def test_login_exchanges_code_for_tokens(self, token_manager, mock_token_response):
        """Login should POST auth code to token endpoint."""
        mock_response = Mock()
        mock_response.json.return_value = mock_token_response
        mock_response.raise_for_status = Mock()

        with patch(PATCH_POST, return_value=mock_response) as mock_post:
            token_manager.login("test-auth-code")

        mock_post.assert_called_once_with(
            AHTokenManager.TOKEN_URL,
            json={
                "clientId": "appie",
                "code": "test-auth-code",
            },
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Appie/8.22.3",
                "X-Application": "AHWEBSHOP",
            },
        )

    def test_login_saves_tokens(self, token_manager, token_file, mock_token_response):
        """Login should persist tokens to disk."""
        mock_response = Mock()
        mock_response.json.return_value = mock_token_response
        mock_response.raise_for_status = Mock()

        with patch(PATCH_POST, return_value=mock_response):
            token_manager.login("test-auth-code")

        assert token_file.exists()
        saved = json.loads(token_file.read_text())
        assert saved["access_token"] == "test-access-token"
        assert saved["refresh_token"] == "test-refresh-token"
        assert "expires_at" in saved

    def test_login_raises_on_http_error(self, token_manager):
        """Login should propagate HTTP errors."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("401 Unauthorized")

        with (
            patch(PATCH_POST, return_value=mock_response),
            pytest.raises(Exception, match="401 Unauthorized"),
        ):
            token_manager.login("bad-code")


# =============================================================================
# Refresh Tests
# =============================================================================


class TestRefresh:
    """Tests for AHTokenManager.refresh method."""

    def test_refresh_updates_tokens(self, token_manager, mock_token_response):
        """Refresh should POST refresh token and update."""
        token_manager._access_token = "old-access-token"
        token_manager._refresh_token = "old-refresh-token"
        token_manager._expires_at = 0

        mock_response = Mock()
        mock_response.json.return_value = mock_token_response
        mock_response.raise_for_status = Mock()

        with patch(PATCH_POST, return_value=mock_response) as mock_post:
            token_manager.refresh()

        mock_post.assert_called_once_with(
            AHTokenManager.REFRESH_URL,
            json={
                "clientId": "appie",
                "refreshToken": "old-refresh-token",
            },
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Appie/8.22.3",
                "X-Application": "AHWEBSHOP",
            },
        )
        assert token_manager._access_token == "test-access-token"
        assert token_manager._refresh_token == "test-refresh-token"

    def test_refresh_raises_without_refresh_token(self, token_manager):
        """Refresh should raise if no refresh token is available."""
        with pytest.raises(Exception, match="No refresh token"):
            token_manager.refresh()


# =============================================================================
# get_access_token Tests
# =============================================================================


class TestGetAccessToken:
    """Tests for AHTokenManager.get_access_token method."""

    def test_returns_valid_token(self, token_manager):
        """Should return token if not expired."""
        token_manager._access_token = "valid-token"
        token_manager._refresh_token = "refresh-token"
        token_manager._expires_at = time.time() + 3600

        assert token_manager.get_access_token() == "valid-token"

    def test_auto_refreshes_when_expired(self, token_manager, mock_token_response):
        """Should refresh and return new token if expired."""
        token_manager._access_token = "expired-token"
        token_manager._refresh_token = "refresh-token"
        token_manager._expires_at = time.time() - 100

        mock_response = Mock()
        mock_response.json.return_value = mock_token_response
        mock_response.raise_for_status = Mock()

        with patch(PATCH_POST, return_value=mock_response):
            token = token_manager.get_access_token()

        assert token == "test-access-token"

    def test_raises_when_not_authenticated(self, token_manager):
        """Should raise if no tokens are available."""
        with pytest.raises(Exception, match="Not authenticated"):
            token_manager.get_access_token()


# =============================================================================
# Token Persistence Tests
# =============================================================================


class TestTokenPersistence:
    """Tests for token save/load."""

    def test_save_and_load_roundtrip(self, token_file):
        """Tokens saved should be loadable by another instance."""
        manager1 = AHTokenManager(token_path=token_file)
        manager1._access_token = "saved-access"
        manager1._refresh_token = "saved-refresh"
        manager1._expires_at = 1738900000.0
        manager1._save_tokens()

        manager2 = AHTokenManager(token_path=token_file)
        assert manager2._access_token == "saved-access"
        assert manager2._refresh_token == "saved-refresh"
        assert manager2._expires_at == 1738900000.0

    def test_loads_nothing_when_no_file(self, token_file):
        """Should start empty when no token file exists."""
        manager = AHTokenManager(token_path=token_file)
        assert manager._access_token is None
        assert manager._refresh_token is None

    def test_creates_parent_directory(self, tmp_path):
        """Should create parent directories when saving."""
        nested_path = tmp_path / "sub" / "dir" / "tokens.json"
        manager = AHTokenManager(token_path=nested_path)
        manager._access_token = "token"
        manager._refresh_token = "refresh"
        manager._expires_at = 0.0
        manager._save_tokens()

        assert nested_path.exists()


# =============================================================================
# is_authenticated Tests
# =============================================================================


class TestIsAuthenticated:
    """Tests for AHTokenManager.is_authenticated method."""

    def test_true_when_has_refresh_token(self, token_manager):
        """Should be true when refresh token is present."""
        token_manager._refresh_token = "some-refresh-token"
        assert token_manager.is_authenticated() is True

    def test_false_when_no_tokens(self, token_manager):
        """Should be false when no tokens are stored."""
        assert token_manager.is_authenticated() is False
