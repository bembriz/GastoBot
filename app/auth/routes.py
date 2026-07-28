"""Endpoints de autenticacion: login, logout, change-password."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Form, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.password import hash_password, verify_password
from app.auth.permissions import get_current_user
from app.auth.session import (
    MAX_AGE_SECONDS,
    create_session,
    delete_session,
    session_cookie_name,
)
from app.database.models import User
from app.database.session import get_db

router = APIRouter(prefix="", tags=["auth"])

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 15
MIN_PASSWORD_LENGTH = 8


class LoginResponse(BaseModel):
    username: str
    role: str
    password_change_required: bool

    model_config = {"from_attributes": True}


@router.post("/login", response_model=LoginResponse)
async def login(
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales invalidas")

    if user.locked_until and user.locked_until > datetime.now(timezone.utc):
        remaining = int((user.locked_until - datetime.now(timezone.utc)).total_seconds() / 60)
        raise HTTPException(
            status_code=423,
            detail=f"Cuenta bloqueada. Intente de nuevo en {remaining} minutos",
        )

    if not verify_password(password, user.password_hash):
        user.failed_attempts += 1
        if user.failed_attempts >= MAX_FAILED_ATTEMPTS:
            user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_MINUTES)
        await db.commit()
        remaining = max(0, MAX_FAILED_ATTEMPTS - user.failed_attempts)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Credenciales invalidas. {remaining} intentos restantes",
        )

    user.failed_attempts = 0
    user.locked_until = None
    user.last_login = datetime.now(timezone.utc)
    await db.commit()

    token = create_session(user.id, user.username, user.role)
    response.set_cookie(
        key=session_cookie_name(),
        value=token,
        max_age=MAX_AGE_SECONDS,
        httponly=True,
        secure=True,
        samesite="strict",
        path="/",
    )

    return LoginResponse(
        username=user.username,
        role=user.role,
        password_change_required=user.password_change_required,
    )


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(
        key=session_cookie_name(),
        path="/",
        httponly=True,
        secure=True,
        samesite="strict",
    )
    return {"message": "Sesion cerrada"}


@router.post("/change-password")
async def change_password(
    current_password: str = Form(...),
    new_password: str = Form(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(current_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Contrasena actual incorrecta")

    if len(new_password) < MIN_PASSWORD_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La nueva contrasena debe tener al menos {MIN_PASSWORD_LENGTH} caracteres",
        )

    user.password_hash = hash_password(new_password)
    user.password_change_required = False
    await db.commit()

    return {"message": "Contrasena actualizada. Inicie sesion nuevamente."}


@router.get("/api/me")
async def get_me(user: User = Depends(get_current_user)):
    return {
        "id": str(user.id),
        "username": user.username,
        "role": user.role,
        "password_change_required": user.password_change_required,
    }
