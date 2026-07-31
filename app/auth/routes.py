"""Endpoints de autenticacion: login, logout, change-password."""

from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, Form, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.password import hash_password, verify_password
from app.auth.permissions import get_current_user
from app.auth.session import (
    MAX_AGE_SECONDS,
    create_session,
    session_cookie_name,
)
from app.database.models import User
from app.database.session import get_db
from app.templates import render

router = APIRouter(prefix="", tags=["auth"])

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 15
MIN_PASSWORD_LENGTH = 8


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=session_cookie_name(),
        value=token,
        max_age=MAX_AGE_SECONDS,
        httponly=True,
        secure=False,
        samesite="lax",
        path="/",
    )


@router.post("/login")
async def login(
    request: Request,
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        return HTMLResponse(
            render("login.html", request=request, user=None, error="Credenciales invalidas"),
            status_code=401,
        )

    if user.locked_until and user.locked_until > datetime.now(UTC):
        remaining = int((user.locked_until - datetime.now(UTC)).total_seconds() / 60)
        return HTMLResponse(
            render(
                "login.html",
                request=request,
                user=None,
                error=f"Cuenta bloqueada. Intente en {remaining} minutos",
            ),
            status_code=423,
        )

    if not verify_password(password, user.password_hash):
        user.failed_attempts += 1
        if user.failed_attempts >= MAX_FAILED_ATTEMPTS:
            user.locked_until = datetime.now(UTC) + timedelta(minutes=LOCKOUT_MINUTES)
        await db.commit()
        remaining = max(0, MAX_FAILED_ATTEMPTS - user.failed_attempts)
        return HTMLResponse(
            render(
                "login.html",
                request=request,
                user=None,
                error=f"Credenciales invalidas. {remaining} intentos restantes",
            ),
            status_code=401,
        )

    user.failed_attempts = 0
    user.locked_until = None
    user.last_login = datetime.now(UTC)
    await db.commit()

    token = create_session(user.id, user.username, user.role)

    if user.password_change_required:
        resp = HTMLResponse(
            render("login.html", request=request, user=None, change_password=True),
        )
        set_session_cookie(resp, token)
        return resp

    resp = HTMLResponse("")
    set_session_cookie(resp, token)
    resp.headers["HX-Redirect"] = "/dashboard"
    return resp


@router.get("/logout")
@router.post("/logout")
async def logout(response: Response) -> RedirectResponse:
    response.delete_cookie(
        key=session_cookie_name(),
        path="/",
        httponly=True,
        samesite="lax",
    )
    return RedirectResponse("/login", status_code=302)


@router.post("/change-password")
async def change_password(
    request: Request,
    response: Response,
    current_password: str = Form(...),
    new_password: str = Form(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    if not verify_password(current_password, user.password_hash):
        return HTMLResponse('<span class="error">Contrasena actual incorrecta</span>')

    if len(new_password) < MIN_PASSWORD_LENGTH:
        return HTMLResponse(f'<span class="error">Minimo {MIN_PASSWORD_LENGTH} caracteres</span>')

    user.password_hash = hash_password(new_password)
    user.password_change_required = False
    await db.commit()

    response.headers["HX-Redirect"] = "/dashboard"
    return HTMLResponse("")


@router.get("/api/me")
async def get_me(user: User = Depends(get_current_user)) -> dict[str, Any]:
    return {
        "id": str(user.id),
        "username": user.username,
        "role": user.role,
        "password_change_required": user.password_change_required,
    }
