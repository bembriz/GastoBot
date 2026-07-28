"""Manejo de sesiones con cookies firmadas (itsdangerous)."""

import os
import uuid
from datetime import datetime, timedelta, timezone

from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

SESSION_SECRET = os.environ["GASTOSIA_SESSION_SECRET"]
MAX_AGE_SECONDS = int(os.environ.get("GASTOSIA_SESSION_MAX_AGE", "28800"))

serializer = URLSafeTimedSerializer(SESSION_SECRET, salt="gastosia-session")


def create_session(user_id: uuid.UUID, username: str, role: str) -> str:
    payload = {
        "user_id": str(user_id),
        "username": username,
        "role": role,
    }
    return serializer.dumps(payload)


def verify_session(token: str) -> dict | None:
    try:
        data = serializer.loads(token, max_age=MAX_AGE_SECONDS)
        return data
    except (BadSignature, SignatureExpired):
        return None


def delete_session() -> str:
    return ""


def session_cookie_name() -> str:
    return "gastosia_session"
