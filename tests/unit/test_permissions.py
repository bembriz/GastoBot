from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.auth.permissions import get_current_user, require_admin, require_owner_or_admin
from app.database.models import User


def _make_user(role: str = "admin", is_active: bool = True) -> User:
    import uuid as _uuid

    u = User(
        id=_uuid.uuid4(),
        username="test",
        password_hash="...",
        role=role,
        is_active=is_active,
    )
    return u


class TestGetCurrentUser:
    async def test_no_cookie_raises_401(self):
        request = MagicMock()
        request.cookies.get.return_value = None
        db = AsyncMock()

        with pytest.raises(HTTPException) as exc:
            await get_current_user(request, db)
        assert exc.value.status_code == 401

    async def test_invalid_session_raises_401(self):
        request = MagicMock()
        request.cookies.get.return_value = "bad-token"
        db = AsyncMock()

        with (
            patch("app.auth.permissions.verify_session", return_value=None),
            pytest.raises(HTTPException) as exc,
        ):
            await get_current_user(request, db)
        assert exc.value.status_code == 401

    async def test_valid_session_user_not_found_raises_401(self):
        request = MagicMock()
        request.cookies.get.return_value = "good-token"
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        with (
            patch(
                "app.auth.permissions.verify_session",
                return_value={"user_id": "fake-id"},
            ),
            pytest.raises(HTTPException) as exc,
        ):
            await get_current_user(request, db)
        assert exc.value.status_code == 401

    async def test_valid_session_inactive_user_raises_401(self):
        request = MagicMock()
        request.cookies.get.return_value = "good-token"
        db = AsyncMock()
        user = _make_user(role="standard", is_active=False)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = user
        db.execute.return_value = mock_result

        with (
            patch(
                "app.auth.permissions.verify_session",
                return_value={"user_id": str(user.id)},
            ),
            pytest.raises(HTTPException) as exc,
        ):
            await get_current_user(request, db)
        assert exc.value.status_code == 401

    async def test_valid_session_active_user_returns_user(self):
        request = MagicMock()
        request.cookies.get.return_value = "good-token"
        db = AsyncMock()
        user = _make_user(role="admin", is_active=True)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = user
        db.execute.return_value = mock_result

        with patch(
            "app.auth.permissions.verify_session",
            return_value={"user_id": str(user.id)},
        ):
            result = await get_current_user(request, db)
        assert result is user


class TestRequireAdmin:
    def test_admin_passes(self):
        user = _make_user(role="admin")
        assert require_admin(user) is user

    def test_non_admin_raises_403(self):
        user = _make_user(role="standard")
        with pytest.raises(HTTPException) as exc:
            require_admin(user)
        assert exc.value.status_code == 403


class TestRequireOwnerOrAdmin:
    async def test_admin_passes(self):
        user = _make_user(role="admin")
        result = await require_owner_or_admin("other-id", user)
        assert result is user

    async def test_owner_passes(self):
        user = _make_user(role="standard")
        result = await require_owner_or_admin(str(user.id), user)
        assert result is user

    async def test_non_owner_non_admin_raises_403(self):
        user = _make_user(role="standard")
        with pytest.raises(HTTPException) as exc:
            await require_owner_or_admin("other-id", user)
        assert exc.value.status_code == 403
