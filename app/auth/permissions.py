"""Dependencias de control de acceso (RBAC)."""

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.session import verify_session, session_cookie_name
from app.database.models import User
from app.database.session import get_db


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    token = request.cookies.get(session_cookie_name())
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado",
            headers={"HX-Redirect": "/login"},
        )

    session_data = verify_session(token)
    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesion expirada",
            headers={"HX-Redirect": "/login"},
        )

    user_id = session_data["user_id"]
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado o inactivo",
        )

    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso restringido a administradores",
        )
    return user


async def require_owner_or_admin(
    record_owner_id: str,
    user: User = Depends(get_current_user),
) -> User:
    if user.role != "admin" and str(user.id) != str(record_owner_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No autorizado para este recurso",
        )
    return user
