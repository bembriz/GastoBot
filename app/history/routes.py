"""Historial de gastos — busqueda, filtros, edicion."""

from datetime import date, datetime

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.permissions import get_current_user, session_cookie_name, verify_session
from app.database.models import ExpenseRecord, User
from app.database.session import get_db

router = APIRouter(prefix="/history")
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
async def history_page(
    request: Request,
    q: str = Query(None),
    db: AsyncSession = Depends(get_db),
):
    user = await get_user(request, db)
    if not user:
        return RedirectResponse("/login")

    query = select(ExpenseRecord)
    if user.role != "admin":
        query = query.where(ExpenseRecord.owner_id == user.id)

    if q:
        query = query.where(
            (ExpenseRecord.final_description.ilike(f"%{q}%"))
            | (ExpenseRecord.group_code.ilike(f"%{q}%"))
            | (ExpenseRecord.bank.ilike(f"%{q}%"))
        )

    query = query.order_by(ExpenseRecord.created_at.desc()).limit(100)
    result = await db.execute(query)
    records = result.scalars().all()

    return templates.TemplateResponse("history.html", {
        "request": request, "user": user, "records": records, "q": q or "",
    })


@router.put("/{record_id}")
async def update_history_record(
    record_id: str,
    transaction_date: str = Form(None),
    amount: float = Form(None),
    bank: str = Form(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ExpenseRecord).where(ExpenseRecord.id == record_id))
    record = result.scalar_one_or_none()
    if not record:
        return HTMLResponse('<span class="error">No encontrado</span>')

    if transaction_date:
        record.transaction_date = datetime.strptime(transaction_date, "%Y-%m-%d").date()
    if amount is not None:
        record.amount = amount
    if bank:
        record.bank = bank.upper()

    await db.commit()
    return HTMLResponse('<span style="color:var(--success)">✓ Actualizado</span>')
