"""Rutas de gastos: dashboard, visor, actualizacion, envio a Sheets."""

import os
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from starlette.responses import Response

from app.auth.permissions import get_current_user
from app.auth.session import session_cookie_name, verify_session
from app.database.models import CatalogCache, ExpenseRecord, ExtractionRun, ImageFile, User
from app.database.session import get_db
from app.sheets.sender import send_expense as send_expense_to_sheets
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
async def root(request: Request, db: AsyncSession = Depends(get_db)) -> Response:
    user = await get_user(request, db)
    if user:
        return RedirectResponse("/dashboard")
    return HTMLResponse(render("login.html", request=request, user=None))


@router.get("/login", response_class=HTMLResponse)
async def login_page(
    request: Request, change: str = "", db: AsyncSession = Depends(get_db)
) -> HTMLResponse:
    if change == "1":
        user = await get_user(request, db)
        if user and user.password_change_required:
            return HTMLResponse(
                render("login.html", request=request, user=None, change_password=True)
            )
    return HTMLResponse(render("login.html", request=request, user=None))


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: AsyncSession = Depends(get_db)) -> Response:
    user = await get_user(request, db)
    if not user:
        return RedirectResponse("/login")
    return HTMLResponse(render("dashboard.html", request=request, user=user))


@router.get("/dashboard/status", response_class=HTMLResponse)
async def dashboard_status(request: Request, db: AsyncSession = Depends(get_db)) -> HTMLResponse:
    user = await get_user(request, db)
    if not user:
        return HTMLResponse("")

    active_statuses = [
        "DETECTADO",
        "ESPERANDO_ARCHIVO_ESTABLE",
        "EN_COLA",
        "ANALIZANDO",
        "REQUIERE_REVISION",
        "PENDIENTE_DE_ENVIO",
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
        record_data.append(
            {
                "id": str(r.id),
                "source_filename": r.source_filename,
                "transaction_date": str(r.transaction_date) if r.transaction_date else None,
                "amount": float(r.amount) if r.amount else None,
                "bank": r.bank,
                "ticket_description": r.ticket_description,
                "group_code": r.group_code,
                "category_id": str(r.category_id) if r.category_id else None,
                "account_id": str(r.account_id) if r.account_id else None,
                "status": r.status,
                "confidence_json": r.confidence_json,
                "owner_name": owners.get(r.owner_id, "?"),
            }
        )

    return HTMLResponse(
        render("expense_list.html", request=request, user=user, records=record_data)
    )


@router.get("/dashboard/errors", response_class=HTMLResponse)
async def dashboard_errors(request: Request, db: AsyncSession = Depends(get_db)) -> HTMLResponse:
    user = await get_user(request, db)
    if not user:
        return HTMLResponse("")

    result = await db.execute(
        select(ExtractionRun)
        .where(
            ExtractionRun.error_message.isnot(None),
            ExtractionRun.error_message != "",
        )
        .order_by(ExtractionRun.created_at.desc())
        .limit(20)
    )
    err_runs = result.scalars().all()

    errors = []
    for erun in err_runs:
        record_result = await db.execute(
            select(ExpenseRecord).where(ExpenseRecord.id == erun.record_id)
        )
        record = record_result.scalar_one_or_none()
        errors.append(
            {
                "timestamp": erun.created_at.strftime("%H:%M:%S") if erun.created_at else "?",
                "engine": erun.model_name or "?",
                "filename": record.source_filename if record else "?",
                "message": erun.error_message or "?",
            }
        )

    return HTMLResponse(render("error_log.html", request=request, user=user, errors=errors))


@router.get("/expenses/{record_id}", response_class=HTMLResponse)
async def expense_detail(
    record_id: str, request: Request, db: AsyncSession = Depends(get_db)
) -> Response:
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
        select(CatalogCache).where(CatalogCache.catalog_type == "categoria", CatalogCache.is_active)
    )
    accounts = await db.execute(
        select(CatalogCache).where(CatalogCache.catalog_type == "cuenta", CatalogCache.is_active)
    )

    extraction_error = None
    if record.status == "ERROR_PROCESAMIENTO":
        err_result = await db.execute(
            select(ExtractionRun)
            .where(ExtractionRun.record_id == record.id)
            .order_by(ExtractionRun.created_at.desc())
            .limit(1)
        )
        erun = err_result.scalar_one_or_none()
        if erun and erun.error_message:
            extraction_error = erun.error_message

    return HTMLResponse(
        render(
            "expense_detail.html",
            request=request,
            user=user,
            record=record,
            categories=cats.scalars().all(),
            accounts=accounts.scalars().all(),
            extraction_error=extraction_error,
        )
    )


@router.get("/images/{record_id}/view")
async def view_image(
    record_id: str, request: Request, db: AsyncSession = Depends(get_db)
) -> Response:
    user = await get_user(request, db)
    if not user:
        return RedirectResponse("/login")

    result = await db.execute(select(ImageFile).where(ImageFile.record_id == record_id))
    image = result.scalar_one_or_none()
    if not image:
        raise HTTPException(404, "Imagen no encontrada")

    path = image.optimized_path or image.original_path
    if not os.path.exists(path):
        raise HTTPException(404, "Archivo de imagen no accesible")

    return FileResponse(path)


@router.get("/categories/by-account", response_class=HTMLResponse)
async def categories_by_account(
    request: Request,
    db: AsyncSession = Depends(get_db),
    account_id: str = "0",
    category_id: str = "",
) -> HTMLResponse:
    user = await get_user(request, db)
    if not user:
        return HTMLResponse("")

    q = (
        select(CatalogCache)
        .where(
            CatalogCache.catalog_type == "categoria",
            CatalogCache.is_active,
        )
        .order_by(CatalogCache.description)
    )

    if account_id and account_id != "0":
        q = q.where(CatalogCache.parent_id == account_id)

    cats_result = await db.execute(q)
    cats = cats_result.scalars().all()

    options = ['<option value="">--</option>']
    for c in cats:
        sel = " selected" if str(c.id) == category_id else ""
        options.append(f'<option value="{c.id}"{sel}>{c.description}</option>')
    return HTMLResponse("\n".join(options))


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
) -> HTMLResponse:
    result = await db.execute(select(ExpenseRecord).where(ExpenseRecord.id == record_id))
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(404)

    if transaction_date is not None:
        record.transaction_date = datetime.strptime(transaction_date, "%Y-%m-%d")
    if group_code is not None:
        record.group_code = group_code.upper() if group_code else None
    if ticket_description is not None:
        record.ticket_description = ticket_description
    if category_id:
        record.category_id = uuid.UUID(category_id)
    if account_id:
        record.account_id = uuid.UUID(account_id)
    if amount is not None:
        record.amount = amount
    if bank is not None:
        record.bank = bank.upper() if bank else None
    if transaction_type is not None:
        record.transaction_type = transaction_type

    if record.group_code and record.ticket_description:
        if record.consecutive:
            record.final_description = (
                f"{record.group_code}-{record.consecutive}-{record.ticket_description}"
            )
        else:
            record.final_description = f"{record.group_code}--{record.ticket_description}"

    if record.status in ("REQUIERE_REVISION", "PENDIENTE_DE_ENVIO"):
        required = [
            record.transaction_date,
            record.amount,
            record.bank,
            record.group_code,
            record.category_id,
            record.account_id,
            record.transaction_type,
        ]
        if all(required):
            record.status = "PENDIENTE_DE_ENVIO"
        else:
            record.status = "REQUIERE_REVISION"

    await db.commit()
    return HTMLResponse('<span style="color:var(--success);">✓ Guardado</span>')


@router.post("/expenses/{record_id}/send")
async def send_expense(
    record_id: str,
    group_code: str = Form(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    result = await send_expense_to_sheets(record_id, group_code)
    if result["success"]:
        return HTMLResponse(
            f'<span style="color:var(--success);">✓ Enviado — {result.get("description")} '
            f"(fila {result.get('row')} en {result.get('tab')})</span>"
        )
    return HTMLResponse(f'<span class="error">{result["error"]}</span>')


@router.post("/expenses/bulk-send")
async def bulk_send_expenses(
    record_ids: list[str] = Form(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    results = []
    for rid in record_ids:
        record = (
            await db.execute(select(ExpenseRecord).where(ExpenseRecord.id == rid))
        ).scalar_one_or_none()
        if not record:
            results.append(f"<span class='error'>{rid[:8]}... no encontrado</span>")
            continue
        if not all(
            [
                record.transaction_date,
                record.amount,
                record.bank,
                record.group_code,
                record.category_id,
                record.account_id,
            ]
        ):
            results.append(f"<span class='error'>{record.source_filename}: incompleto</span>")
            continue
        if record.status in ("ENVIADO", "ENVIANDO"):
            results.append(
                f"<span style='color:var(--muted);'>{record.source_filename}: ya enviado</span>"
            )
            continue
        try:
            result = await send_expense_to_sheets(rid, record.group_code)  # type: ignore[arg-type]
            if result["success"]:
                results.append(
                    f"<span style='color:var(--success);'>"
                    f"&#10003; {record.source_filename}: fila {result.get('row')}"
                    f"</span>"
                )
            else:
                results.append(
                    f"<span class='error'>{record.source_filename}: {result['error']}</span>"
                )
        except Exception as e:
            results.append(f"<span class='error'>{record.source_filename}: {e}</span>")

    return HTMLResponse("<br>".join(results))
