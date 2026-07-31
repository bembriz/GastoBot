# Ejemplo: Ruta de vista para visor de gasto
# Archivo: app/api/webui.py

from app.expenses.repository import ExpenseRepository
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.auth.session import get_current_user, require_auth
from app.database.models import User

router = APIRouter(prefix="", tags=["webui"])
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Redirect to dashboard or login."""
    user = await get_current_user(request)
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    return RedirectResponse(url="/login", status_code=302)


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    from app.auth.service import AuthService

    auth = AuthService()
    user = await auth.authenticate(username, password)
    if not user:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Usuario o contraseña inválidos"},
            status_code=401,
        )
    # Set session cookie
    response = RedirectResponse(url="/dashboard", status_code=302)
    await auth.create_session(response, user)
    return response


@router.get("/dashboard", response_class=HTMLResponse)
@require_auth
async def dashboard(request: Request, current_user: User = Depends(get_current_user)):
    repo = ExpenseRepository()
    expenses = await repo.get_pending(current_user)
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "current_user": current_user, "expenses": expenses},
    )


@router.get("/expenses/list", response_class=HTMLResponse)
@require_auth
async def expense_list(request: Request, current_user: User = Depends(get_current_user)):
    repo = ExpenseRepository()
    expenses = await repo.get_pending(current_user)
    has_active = any(
        e.status
        in (
            "EN_COLA",
            "ANALIZANDO",
            "ESPERANDO_ARCHIVO_ESTABLE",
            "LISTO_PARA_REVISION",
            "REQUIERE_REVISION",
            "PENDIENTE_DE_ENVIO",
        )
        for e in expenses
    )
    return templates.TemplateResponse(
        "partials/expense-table.html",
        {
            "request": request,
            "current_user": current_user,
            "expenses": expenses,
            "polling_active": has_active,
        },
    )


@router.get("/expenses/{record_id}", response_class=HTMLResponse)
@require_auth
async def expense_viewer(
    request: Request, record_id: int, current_user: User = Depends(get_current_user)
):
    repo = ExpenseRepository()
    expense = await repo.get_by_id(record_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Gasto no encontrado")
    if current_user.role != "admin" and expense.owner != current_user.username:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    return templates.TemplateResponse(
        "expense-viewer.html",
        {"request": request, "current_user": current_user, "expense": expense},
    )


@router.get("/expenses/{record_id}/status", response_class=HTMLResponse)
@require_auth
async def expense_status(
    request: Request, record_id: int, current_user: User = Depends(get_current_user)
):
    repo = ExpenseRepository()
    expense = await repo.get_by_id(record_id)
    if not expense:
        raise HTTPException(status_code=404)
    if current_user.role != "admin" and expense.owner != current_user.username:
        raise HTTPException(status_code=403)
    is_terminal = expense.status in (
        "ENVIADO",
        "DUPLICADO_EXACTO",
        "ERROR_PROCESAMIENTO",
        "ERROR_SHEETS",
    )
    return templates.TemplateResponse(
        "partials/expense-status.html",
        {
            "request": request,
            "current_user": current_user,
            "expense": expense,
            "polling_active": not is_terminal,
        },
    )


@router.post("/expenses/{record_id}/save")
@require_auth
async def save_expense(
    request: Request,
    record_id: int,
    current_user: User = Depends(get_current_user),
    transaction_date: str = Form(None),
    group_code: str = Form(None),
    ticket_description: str = Form(None),
    category_id: int = Form(None),
    account_id: int = Form(None),
    unit_price: float = Form(None),
    total: float = Form(None),
    bank: str = Form(None),
    transaction_type: str = Form(None),
):
    repo = ExpenseRepository()
    expense = await repo.get_by_id(record_id)
    if not expense:
        raise HTTPException(status_code=404)
    if current_user.role != "admin" and expense.owner != current_user.username:
        raise HTTPException(status_code=403)

    # Optimistic locking check via hidden updated_at field
    submitted_updated_at = (await request.form()).get("updated_at")
    if submitted_updated_at and submitted_updated_at != str(expense.updated_at):
        return templates.TemplateResponse(
            "partials/expense-form.html",
            {
                "request": request,
                "current_user": current_user,
                "expense": expense,
                "error": "El registro fue modificado por otro usuario. Recarga la página.",
            },
            status_code=409,
        )

    await repo.update(
        record_id,
        {
            "transaction_date": transaction_date,
            "group_code": group_code,
            "ticket_description": ticket_description,
            "category_id": category_id,
            "account_id": account_id,
            "unit_price": unit_price,
            "total": total,
            "bank": bank,
            "transaction_type": transaction_type,
        },
    )
    expense = await repo.get_by_id(record_id)
    return templates.TemplateResponse(
        "partials/expense-form.html",
        {
            "request": request,
            "current_user": current_user,
            "expense": expense,
            "success": "Cambios guardados correctamente",
        },
    )
