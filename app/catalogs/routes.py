"""CRUD de catalogos (categorias, cuentas) — solo admin."""

import uuid

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.permissions import get_current_user, require_admin, session_cookie_name, verify_session
from app.database.models import CatalogCache, User
from app.database.session import get_db

router = APIRouter(prefix="/catalogs")
templates = Jinja2Templates(directory="templates")


async def get_user(request: Request, db: AsyncSession) -> User | None:
    token = request.cookies.get(session_cookie_name())
    if not token:
        return None
    data = verify_session(token)
    if not data:
        return None
    result = await db.execute(select(User).where(User.id == data["user_id"]))
    return result.scalar_one_or_none()


@router.get("", response_class=HTMLResponse)
async def catalogs_page(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_user(request, db)
    if not user:
        return RedirectResponse("/login")
    if user.role != "admin":
        return HTMLResponse("<h2>Acceso restringido</h2>", status_code=403)

    cats = await db.execute(
        select(CatalogCache).where(CatalogCache.catalog_type == "categoria").order_by(CatalogCache.code)
    )
    accs = await db.execute(
        select(CatalogCache).where(CatalogCache.catalog_type == "cuenta").order_by(CatalogCache.code)
    )
    return templates.TemplateResponse("catalogs.html", {
        "request": request, "user": user,
        "categories": cats.scalars().all(), "accounts": accs.scalars().all(),
    })


@router.post("/categoria")
async def create_category(
    code: str = Form(...),
    description: str = Form(...),
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    cat = CatalogCache(id=uuid.uuid4(), catalog_type="categoria", code=code.upper(), description=description)
    db.add(cat)
    await db.commit()
    return HTMLResponse(f'<div id="catalog-list" hx-get="/catalogs" hx-trigger="load" hx-swap="outerHTML"></div>')


@router.put("/categoria/{cat_id}/toggle")
async def toggle_category(
    cat_id: str,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(CatalogCache).where(CatalogCache.id == cat_id))
    cat = result.scalar_one_or_none()
    if cat:
        cat.is_active = not cat.is_active
        await db.commit()
    return HTMLResponse(f'<div id="catalog-list" hx-get="/catalogs" hx-trigger="load" hx-swap="outerHTML"></div>')


@router.post("/cuenta")
async def create_account(
    code: str = Form(...),
    description: str = Form(...),
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    acc = CatalogCache(id=uuid.uuid4(), catalog_type="cuenta", code=code, description=description)
    db.add(acc)
    await db.commit()
    return HTMLResponse(f'<div id="catalog-list" hx-get="/catalogs" hx-trigger="load" hx-swap="outerHTML"></div>')


@router.put("/cuenta/{acc_id}/toggle")
async def toggle_account(
    acc_id: str,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(CatalogCache).where(CatalogCache.id == acc_id))
    acc = result.scalar_one_or_none()
    if acc:
        acc.is_active = not acc.is_active
        await db.commit()
    return HTMLResponse(f'<div id="catalog-list" hx-get="/catalogs" hx-trigger="load" hx-swap="outerHTML"></div>')
