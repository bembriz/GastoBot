"""Rutas de gastos: dashboard, visor, actualizacion, envio a Sheets."""

import os
from datetime import datetime

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.auth.permissions import get_current_user, require_owner_or_admin
from app.auth.session import session_cookie_name, verify_session
from app.database.models import CatalogCache, ExpenseRecord, ImageFile, ProcessingQueue, User
from app.database.session import get_db
from app.templates import render

router = APIRouter()


async def get_user(request: Request, db: AsyncSession) -> User | None:
    token = request.cookies.get(session_cookie_name())
    if not token:
        return None
    data = verify_session(token)
    if not data:
        return None
    result = await db.execute(select(User).where(User.id == data["user_id"]))
    return result.scalar_one_or_none()


@router.get("/", response_class=HTMLResponse)
async def root(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_user(request, db)
    if user:
        return RedirectResponse("/dashboard")
    return HTMLResponse(render("login.html", request=request, user=None))


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return HTMLResponse(render("login.html", request=request, user=None))


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_user(request, db)
    if not user:
        return RedirectResponse("/login")
    return HTMLResponse(render("dashboard.html", request=request, user=user))


@router.get("/dashboard/status", response_class=HTMLResponse)
async def dashboard_status(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_user(request, db)
    if not user:
        return HTMLResponse("")

    active_statuses = [
        "DETECTADO", "ESPERANDO_ARCHIVO_ESTABLE", "EN_COLA", "ANALIZANDO",
        "LISTO_PARA_REVISION", "REQUIERE_REVISION", "PENDIENTE_DE_ENVIO",
        "DUPLICADO_PROBABLE",
    ]

    q = select(ExpenseRecord).where(ExpenseRecord.status.in_(active_statuses))
    if user.role != "admin":
        q = q.where(ExpenseRecord.owner_id == user.id)

    q = q.order_by(ExpenseRecord.created_at.desc()).limit(50)
    result = await db.execute(q)
    records = result.scalars().all()

    owner_ids = {r.owner_id for r in records if r.owner_id}
    owners = {}
    if owner_ids:
        users_result = await db.execute(select(User).where(User.id.in_(owner_ids)))
        owners = {u.id: u.username for u in users_result.scalars().all()}

    record_data = []
    for r in records:
        record_data.append({
            "id": str(r.id),
            "source_filename": r.source_filename,
            "transaction_date": str(r.transaction_date) if r.transaction_date else None,
            "amount": float(r.amount) if r.amount else None,
            "bank": r.bank,
            "status": r.status,
            "confidence_json": r.confidence_json,
            "owner_name": owners.get(r.owner_id, "?"),
        })

    return HTMLResponse(render("expense_list.html", request=request, user=user, records=record_data))


@router.get("/expenses/{record_id}", response_class=HTMLResponse)
async def expense_detail(
    record_id: str, request: Request, db: AsyncSession = Depends(get_db)
):
    user = await get_user(request, db)
    if not user:
        return RedirectResponse("/login")

    result = await db.execute(
        select(ExpenseRecord)
        .options(joinedload(ExpenseRecord.image_file))
        .where(ExpenseRecord.id == record_id)
    )
    record = result.unique().scalar_one_or_none()
    if not record:
        raise HTTPException(404, "Comprobante no encontrado")

    cats = await db.execute(
        select(CatalogCache).where(CatalogCache.catalog_type == "categoria", CatalogCache.is_active == True)
    )
    accounts = await db.execute(
        select(CatalogCache).where(CatalogCache.catalog_type == "cuenta", CatalogCache.is_active == True)
    )

    return HTMLResponse(render("expense_detail.html",
        request=request, user=user, record=record,
        categories=cats.scalars().all(), accounts=accounts.scalars().all()))


@router.put("/expenses/{record_id}")
async def update_expense(
    record_id: str,
    transaction_date: str = Form(None),
    group_code: str = Form(None),
    ticket_description: str = Form(None),
    category_id: str = Form(None),
    account_id: str = Form(None),
    amount: float = Form(None),
    bank: str = Form(None),
    transaction_type: str = Form(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ExpenseRecord).where(ExpenseRecord.id == record_id))
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(404)

    if transaction_date is not None:
        record.transaction_date = datetime.strptime(transaction_date, "%Y-%m-%d").date()
    if group_code is not None:
        record.group_code = group_code.upper() if group_code else None
    if ticket_description is not None:
        record.ticket_description = ticket_description
    if category_id:
        record.category_id = category_id
    if account_id:
        record.account_id = account_id
    if amount is not None:
        record.amount = amount
    if bank is not None:
        record.bank = bank.upper() if bank else None
    if transaction_type is not None:
        record.transaction_type = transaction_type

    if record.group_code and record.consecutive and record.ticket_description:
        record.final_description = f"{record.group_code}-{record.consecutive}-{record.ticket_description}"

    await db.commit()
    return HTMLResponse('<span style="color:var(--success);">✓ Guardado</span>')
