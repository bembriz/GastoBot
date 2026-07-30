import time
import uuid
from unittest.mock import patch

import pytest
from app.auth.session import (
    MAX_AGE_SECONDS,
    create_session,
    delete_session,
    session_cookie_name,
    verify_session,
)


class TestCreateSession:
    def test_create_session_returns_string(self):
        token = create_session(uuid.uuid4(), "testuser", "standard")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_session_contains_periods(self):
        """itsdangerous tokens contain periods as separators."""
        token = create_session(uuid.uuid4(), "ruben", "admin")
        assert "." in token


class TestVerifySession:
    def test_verify_session_valid_token(self):
        user_id = uuid.uuid4()
        token = create_session(user_id, "validuser", "standard")
        result = verify_session(token)
        assert result is not None
        assert result["user_id"] == str(user_id)
        assert result["username"] == "validuser"
        assert result["role"] == "standard"

    def test_verify_session_invalid_token(self):
        result = verify_session("this-is-not-a-valid-token-at-all")
        assert result is None

    def test_verify_session_tampered_token(self):
        user_id = uuid.uuid4()
        token = create_session(user_id, "tamperme", "admin")
        tampered = token[:-5] + "abcde"
        result = verify_session(tampered)
        assert result is None

    def test_verify_session_empty_token(self):
        result = verify_session("")
        assert result is None

    def test_verify_session_expired_token(self):
        with patch.object(
            __import__("app.auth.session", fromlist=["MAX_AGE_SECONDS"]),
            "MAX_AGE_SECONDS",
            -1,
        ):
            user_id = uuid.uuid4()
            token = create_session(user_id, "expired", "standard")
            result = verify_session(token)
            assert result is None


class TestSessionHelpers:
    def test_session_cookie_name(self):
        assert session_cookie_name() == "gastosia_session"

    def test_delete_session_returns_empty_string(self):
        assert delete_session() == ""
