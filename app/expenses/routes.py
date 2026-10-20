"""Rutas de gastos: dashboard, visor, actualizacion, envio a Sheets."""

import asyncio
import os
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from starlette.responses import Response

from app.auth.permissions import get_current_user
from app.auth.session import session_cookie_name, verify_session
from app.database.models import (
    AuditEvent,
    CatalogCache,
    ExpenseRecord,
    ExtractionRun,
    ImageFile,
    ProcessingQueue,
    SheetSync,
    User,
)
from app.database.session import get_db
from app.expenses import activity
from app.expenses.queue import process_batch, reset_job_to_en_cola
from app.external.sender import send_expense as send_expense_to_postgres
from app.sheets.sender import send_expense as send_expense_to_sheets
from app.templates import render

router = APIRouter()

# Secciona la comprobacion is_busy + creacion del task en POST /expenses/process.
# process_batch tarda varios await (primer claim) en llamar set_batch; sin este
# lock dos POST casi simultaneos pasarian ambos el check y crearian dos lotes
# (dos ANALIZANDO en paralelo, rompiendo R008).
_process_lock = asyncio.Lock()

SHEETS_STUCK_AFTER = timedelta(minutes=15)


def _as_aware_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _is_stuck_sheets_send(record: ExpenseRecord, now: datetime | None = None) -> bool:
    if record.status != "ENVIANDO":
        return False
    if record.sheet_name and record.sheet_row and record.sent_at:
        return False
    reference_time = _as_aware_utc(record.updated_at) or _as_aware_utc(record.created_at)
    if reference_time is None:
        return True
    current_time = now or datetime.now(UTC)
    return current_time - reference_time >= SHEETS_STUCK_AFTER


def _bulk_message(message: str, css_class: str = "") -> str:
    class_attr = f' class="{css_class}"' if css_class else ""
    return f"<span{class_attr}>{message}</span>"


def _send_target() -> str:
    return os.environ.get("GASTOSIA_SEND_TARGET", "postgres").strip().lower()


async def _dispatch_send(record_id: str, group_code: str) -> dict[str, object]:
    if _send_target() == "sheets":
        return await send_expense_to_sheets(record_id, group_code)
    return await send_expense_to_postgres(record_id, group_code)


def _send_success_text(result: dict[str, object]) -> str:
    description = result.get("description") or ""
    tab = result.get("tab") or ""
    row = result.get("row")
    destination = f"fila {row} en {tab}" if row is not None else f"mes {tab}"
    return f"Enviado — {description} ({destination})"


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
        "ERROR_SHEETS",
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

    q = (
        select(ExpenseRecord)
        .where(ExpenseRecord.status == "ERROR_PROCESAMIENTO")
        .order_by(ExpenseRecord.created_at.desc())
        .limit(20)
    )
    if user.role != "admin":
        q = q.where(ExpenseRecord.owner_id == user.id)

    result = await db.execute(q)
    records = result.scalars().all()

    errors = []
    for record in records:
        err_result = await db.execute(
            select(ExtractionRun)
            .where(
                ExtractionRun.record_id == record.id,
                ExtractionRun.error_message.isnot(None),
                ExtractionRun.error_message != "",
            )
            .order_by(ExtractionRun.created_at.desc())
            .limit(1)
        )
        erun = err_result.scalar_one_or_none()
        errors.append(
            {
                "record_id": str(record.id),
                "timestamp": (
                    erun.created_at.strftime("%H:%M:%S") if erun and erun.created_at else "?"
                ),
                "engine": erun.model_name if erun else "?",
                "filename": record.source_filename or "?",
                "message": erun.error_message if erun else "Error de extraccion",
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

    all_categories = cats.scalars().all()
    if record.account_id:
        filtered = [c for c in all_categories if c.parent_id == record.account_id]
        # Sin parent_id poblado en el catalogo no habria coincidencias;
        # en ese caso mostrar todas para no dejar el combo vacio.
        categories = filtered or list(all_categories)
    else:
        categories = list(all_categories)

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
            categories=categories,
            accounts=accounts.scalars().all(),
            extraction_error=extraction_error,
        )
    )


@router.get("/expenses/{record_id}/image")
async def expense_image(
    record_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    result = await db.execute(
        select(ExpenseRecord)
        .options(joinedload(ExpenseRecord.image_file))
        .where(ExpenseRecord.id == record_id)
    )
    record = result.unique().scalar_one_or_none()
    if not record:
        raise HTTPException(404, "Comprobante no encontrado")

    if user.role != "admin" and record.owner_id != user.id:
        raise HTTPException(403, "No autorizado")

    image = record.image_file
    if not image:
        raise HTTPException(404, "Imagen no encontrada")

    path = image.original_path or image.optimized_path
    if not path or not os.path.exists(path):
        raise HTTPException(404, "Archivo de imagen no accesible")

    return FileResponse(path, media_type=image.mime_type)


@router.get("/images/{record_id}/view")
async def view_image(
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
        raise HTTPException(404, "Imagen no encontrada")

    if user.role != "admin" and record.owner_id != user.id:
        raise HTTPException(403, "No autorizado")

    image = record.image_file
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

    if not cats and account_id and account_id != "0":
        # La cuenta no tiene categorias ligadas (parent_id sin poblar);
        # devolver todas las activas para no dejar el combo vacio.
        fallback = await db.execute(
            select(CatalogCache)
            .where(CatalogCache.catalog_type == "categoria", CatalogCache.is_active)
            .order_by(CatalogCache.description)
        )
        cats = fallback.scalars().all()

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
    record_result = await db.execute(select(ExpenseRecord).where(ExpenseRecord.id == record_id))
    record = record_result.scalar_one_or_none()
    if not record:
        raise HTTPException(404, "Comprobante no encontrado")
    if user.role != "admin" and record.owner_id != user.id:
        raise HTTPException(403, "No autorizado")

    result = await _dispatch_send(record_id, group_code)
    if result.get("success"):
        return HTMLResponse(
            f'<span style="color:var(--success);">&#10003; {_send_success_text(result)}</span>'
        )
    return HTMLResponse(f'<span class="error">{result.get("error")}</span>')


@router.post("/expenses/{record_id}/retry")
async def retry_expense(
    record_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    result = await db.execute(select(ExpenseRecord).where(ExpenseRecord.id == record_id))
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(404, "Comprobante no encontrado")

    if user.role != "admin" and record.owner_id != user.id:
        raise HTTPException(403, "No autorizado")

    if record.status != "ERROR_PROCESAMIENTO":
        raise HTTPException(409, "El registro no esta en estado de error")

    record.status = "EN_COLA"
    record.transaction_date = None
    record.amount = None
    record.ticket_description = None
    record.bank = None
    record.transaction_type = None
    record.confidence_json = None
    record.group_code = None
    record.consecutive = None
    record.final_description = None
    record.sent_at = None

    q_result = await db.execute(
        select(ProcessingQueue).where(ProcessingQueue.record_id == record.id)
    )
    queue_entry = q_result.scalar_one_or_none()
    if queue_entry:
        queue_entry.status = "EN_COLA"
        queue_entry.enqueued_at = datetime.now(UTC)
        queue_entry.claimed_at = None
        queue_entry.completed_at = None
        queue_entry.worker_id = None
        queue_entry.attempts = 0
        queue_entry.last_error = None
    else:
        db.add(ProcessingQueue(record_id=record.id, status="EN_COLA"))

    await db.commit()
    return HTMLResponse('<span style="color:var(--success);">✓ Reenviado a la cola</span>')


@router.post("/expenses/bulk-send")
async def bulk_send_expenses(
    record_ids: list[str] | None = Form(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    if not record_ids:
        return HTMLResponse(
            _bulk_message("Selecciona al menos un comprobante para enviar.", "error"),
            status_code=400,
        )

    results = []
    for rid in record_ids:
        record = (
            await db.execute(select(ExpenseRecord).where(ExpenseRecord.id == rid))
        ).scalar_one_or_none()
        if not record:
            results.append(f"<span class='error'>{rid[:8]}... no encontrado</span>")
            continue
        if user.role != "admin" and record.owner_id != user.id:
            results.append(f"<span class='error'>{record.source_filename}: no autorizado</span>")
            continue
        if _is_stuck_sheets_send(record):
            record.status = "PENDIENTE_DE_ENVIO"
            await db.commit()
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
            result = await _dispatch_send(rid, record.group_code)  # type: ignore[arg-type]
            if result.get("success"):
                tab = result.get("tab")
                row = result.get("row")
                destination = f"fila {row} en {tab}" if row is not None else f"mes {tab}"
                results.append(
                    f"<span style='color:var(--success);'>"
                    f"&#10003; {record.source_filename}: {destination}"
                    f"</span>"
                )
            else:
                results.append(
                    f"<span class='error'>{record.source_filename}: {result.get('error')}</span>"
                )
        except Exception as e:
            results.append(f"<span class='error'>{record.source_filename}: {e}</span>")

    return HTMLResponse("<br>".join(results))


async def _delete_expense_record(db: AsyncSession, record: ExpenseRecord) -> None:
    await db.execute(delete(SheetSync).where(SheetSync.record_id == record.id))
    await db.execute(delete(AuditEvent).where(AuditEvent.record_id == record.id))
    await db.execute(delete(ImageFile).where(ImageFile.record_id == record.id))
    await db.execute(delete(ProcessingQueue).where(ProcessingQueue.record_id == record.id))
    await db.execute(delete(ExtractionRun).where(ExtractionRun.record_id == record.id))
    await db.delete(record)


@router.post("/expenses/bulk-delete", response_class=HTMLResponse)
async def bulk_delete_expenses(
    record_ids: list[str] | None = Form(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    if not record_ids:
        return HTMLResponse(
            _bulk_message("Selecciona al menos un comprobante para eliminar.", "error"),
            status_code=400,
        )

    results = []
    for rid in record_ids:
        record = (
            await db.execute(select(ExpenseRecord).where(ExpenseRecord.id == rid))
        ).scalar_one_or_none()
        if not record:
            results.append(f"<span class='error'>{rid[:8]}... no encontrado</span>")
            continue
        if user.role != "admin" and record.owner_id != user.id:
            results.append(f"<span class='error'>{record.source_filename}: no autorizado</span>")
            continue

        filename = record.source_filename or str(record.id)
        await _delete_expense_record(db, record)
        await db.commit()
        results.append(f"<span style='color:var(--success);'>{filename}: eliminado</span>")

    return HTMLResponse("<br>".join(results))


def _log_task_result(task: asyncio.Task[int]) -> None:
    """Done-callback: evita 'Task exception was never retrieved' en fire-and-forget."""
    if task.cancelled():
        return
    exc = task.exception()
    if exc is not None:
        print(f"[Procesamiento] Tarea termino con error: {exc}")


@router.post("/expenses/process", response_class=HTMLResponse)
async def process_manual(
    request: Request,
    engine: str = Form(...),
    db: AsyncSession = Depends(get_db),
) -> Response:
    user = await get_user(request, db)
    if not user:
        return RedirectResponse("/login")
    if engine not in ("gemini", "kimi"):
        return HTMLResponse("Motor no valido", status_code=400)

    owner_id = None if user.role == "admin" else user.id
    async with _process_lock:
        if activity.is_busy():
            return HTMLResponse("Proceso en curso", status_code=409)
        # Guard de direccion doble (I3): el worker automatico NO marca
        # activity busy; si sostiene un job ANALIZANDO (ventana claim->
        # set_batch o proceso largo), un lote manual no debe arrancar.
        # R008: un solo ANALIZANDO a la vez.
        in_flight = await db.execute(
            select(ProcessingQueue.id).where(ProcessingQueue.status == "ANALIZANDO").limit(1)
        )
        if in_flight.scalar_one_or_none() is not None:
            return HTMLResponse("Ya hay una imagen en ANALIZANDO", status_code=409)
        task = asyncio.create_task(process_batch(engine, owner_id, activity.push_event))
        activity.attach_task(task)
        task.add_done_callback(_log_task_result)
        activity.push_event("info", f"Lote iniciado (motor {engine})")
        # busy sincrono: sin esto el segundo POST del mismo instante ve
        # is_busy()==False hasta que process_batch complete el primer claim.
        # record_id/filename vacios hasta ese claim; el primer set_batch del
        # batch los rellena y clear_batch (finally) los limpia.
        activity.set_batch("", "", engine)
    return HTMLResponse("Procesamiento iniciado")


@router.post("/expenses/stop", response_class=HTMLResponse)
async def stop_manual(request: Request, db: AsyncSession = Depends(get_db)) -> Response:
    user = await get_user(request, db)
    if not user:
        return RedirectResponse("/login")
    if not activity.is_busy():
        return HTMLResponse("No hay proceso en curso")

    task = activity.pop_task()
    if task:
        task.cancel()
    # CancelledError es BaseException: process_batch solo corre su finally
    # (clear_batch), NO resetea el job. El reset lo hace aqui el route.
    # Barrido por status en vez del record_id del state: R008 garantiza a lo
    # mas un ANALIZANDO, y cubre la ventana claim->set_batch donde el state
    # todavia muestra el job anterior y el recien reclamado quedaria atascado
    # (recover_stale_jobs solo corre al arranque).
    result = await db.execute(select(ProcessingQueue).where(ProcessingQueue.status == "ANALIZANDO"))
    for job in result.scalars().all():
        await reset_job_to_en_cola(db, job)
    activity.push_event("stop", "Lote detenido")
    activity.clear_batch()
    return HTMLResponse("Lote detenido")


@router.get("/dashboard/activity", response_class=HTMLResponse)
async def dashboard_activity(request: Request, db: AsyncSession = Depends(get_db)) -> Response:
    user = await get_user(request, db)
    if not user:
        return RedirectResponse("/login")

    count_q = (
        select(func.count()).select_from(ExpenseRecord).where(ExpenseRecord.status == "EN_COLA")
    )
    if user.role != "admin":
        count_q = count_q.where(ExpenseRecord.owner_id == user.id)
    queued = (await db.execute(count_q)).scalar_one()

    return HTMLResponse(
        render(
            "activity_panel.html",
            request=request,
            user=user,
            state=activity.get_state(),
            events=activity.get_events(),
            queued=queued,
        )
    )
