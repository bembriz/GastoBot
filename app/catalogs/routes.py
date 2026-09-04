"""CRUD de catalogos (categorias, cuentas) — solo admin."""

import uuid

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import Response

from app.auth.permissions import require_admin
from app.auth.session import session_cookie_name, verify_session
from app.database.models import CatalogCache, User
from app.database.session import get_db
from app.templates import render

router = APIRouter(prefix="/catalogs")


async def get_user_req(request: Request, db: AsyncSession) -> User | None:
    token = request.cookies.get(session_cookie_name())
    if not token:
        return None
    data = verify_session(token)
    if not data:
        return None
    result = await db.execute(select(User).where(User.id == data["user_id"]))
    return result.scalar_one_or_none()


@router.get("", response_class=HTMLResponse)
async def catalogs_page(request: Request, db: AsyncSession = Depends(get_db)) -> Response:
    user = await get_user_req(request, db)
    if not user:
        return RedirectResponse("/login")
    if user.role != "admin":
        return HTMLResponse("<h2>Acceso restringido</h2>", status_code=403)

    cats = await db.execute(
        select(CatalogCache)
        .where(CatalogCache.catalog_type == "categoria")
        .order_by(CatalogCache.code)
    )
    accs = await db.execute(
        select(CatalogCache)
        .where(CatalogCache.catalog_type == "cuenta")
        .order_by(CatalogCache.code)
    )
    acc_list = accs.scalars().all()
    return HTMLResponse(
        render(
            "catalogs.html",
            request=request,
            user=user,
            categories=cats.scalars().all(),
            accounts=acc_list,
            accounts_by_id={str(a.id): a for a in acc_list},
        )
    )


@router.post("/categoria")
async def create_category(
    code: str = Form(...),
    description: str = Form(...),
    parent_id: str = Form(""),
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    parent_uuid = None
    if parent_id:
        try:
            parent_uuid = uuid.UUID(parent_id)
        except ValueError:
            return HTMLResponse("Cuenta padre invalida", status_code=400)
    cat = CatalogCache(
        id=uuid.uuid4(),
        catalog_type="categoria",
        code=code.upper(),
        description=description,
        parent_id=parent_uuid,
    )
    db.add(cat)
    await db.commit()
    return HTMLResponse("OK")


@router.put("/categoria/{cat_id}/toggle")
async def toggle_category(
    cat_id: str,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    result = await db.execute(select(CatalogCache).where(CatalogCache.id == cat_id))
    cat = result.scalar_one_or_none()
    if cat:
        cat.is_active = not cat.is_active
        await db.commit()
    return HTMLResponse("OK")


@router.post("/cuenta")
async def create_account(
    code: str = Form(...),
    description: str = Form(...),
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    acc = CatalogCache(id=uuid.uuid4(), catalog_type="cuenta", code=code, description=description)
    db.add(acc)
    await db.commit()
    return HTMLResponse("OK")


@router.put("/cuenta/{acc_id}/toggle")
async def toggle_account(
    acc_id: str,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    result = await db.execute(select(CatalogCache).where(CatalogCache.id == acc_id))
    acc = result.scalar_one_or_none()
    if acc:
        acc.is_active = not acc.is_active
        await db.commit()
    return HTMLResponse("OK")
