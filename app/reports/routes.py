"""Seccion Reportes por mes: listado, detalle y descarga Excel."""

import os

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from starlette.responses import Response

from app.auth.session import session_cookie_name, verify_session
from app.database.models import ExpenseRecord, User
from app.database.session import get_db
from app.external.engine import external_session
from app.external.layout import CAMPOS, COLUMNAS, normalize_month
from app.external.repository import get_record, list_months, records_for_month
from app.reports.excel import build_workbook
from app.templates import render

router = APIRouter(prefix="/reports")


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
async def reports_page(
    request: Request,
    month: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Response:
    user = await get_user_req(request, db)
    if not user:
        return RedirectResponse("/login")
    if user.role != "admin":
        return HTMLResponse("<h2>Acceso restringido</h2>", status_code=403)

    selected_month = normalize_month(month) if month else None
    if month and not selected_month:
        raise HTTPException(400, "Mes invalido. Usa el formato Julio-2026 o 2026-07")

    async with external_session() as ext_db:
        months = await list_months(ext_db)
        rows = await records_for_month(ext_db, selected_month) if selected_month else []

    return HTMLResponse(
        render(
            "reports.html",
            request=request,
            user=user,
            months=months,
            selected_month=selected_month,
            records=rows,
        )
    )


@router.get("/excel")
async def download_excel(
    request: Request,
    month: str = Query(...),
    db: AsyncSession = Depends(get_db),
) -> Response:
    user = await get_user_req(request, db)
    if not user:
        return RedirectResponse("/login")
    if user.role != "admin":
        return HTMLResponse("<h2>Acceso restringido</h2>", status_code=403)

    month_label = normalize_month(month)
    if not month_label:
        raise HTTPException(400, "Mes invalido. Usa el formato Julio-2026 o 2026-07")

    async with external_session() as ext_db:
        rows = await records_for_month(ext_db, month_label, limit=100_000)

    if not rows:
        raise HTTPException(404, f"No hay registros para {month_label}")

    buffer = build_workbook(month_label, rows)
    filename = f"reporte-{month_label}.xlsx"
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{report_id}", response_class=HTMLResponse)
async def report_detail(
    report_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Response:
    user = await get_user_req(request, db)
    if not user:
        return RedirectResponse("/login")
    if user.role != "admin":
        return HTMLResponse("<h2>Acceso restringido</h2>", status_code=403)

    async with external_session() as ext_db:
        row = await get_record(ext_db, report_id)
    if not row:
        raise HTTPException(404, "Registro de reporte no encontrado")

    image_available = False
    if row.record_id:
        result = await db.execute(
            select(ExpenseRecord)
            .options(joinedload(ExpenseRecord.image_file))
            .where(ExpenseRecord.id == row.record_id)
        )
        local_record = result.unique().scalar_one_or_none()
        if local_record and local_record.image_file:
            path = local_record.image_file.original_path or local_record.image_file.optimized_path
            image_available = bool(path and os.path.exists(path))

    fields = [
        (label, getattr(row, field, "")) for label, field in zip(COLUMNAS, CAMPOS, strict=True)
    ]

    return HTMLResponse(
        render(
            "report_detail.html",
            request=request,
            user=user,
            row=row,
            fields=fields,
            image_available=image_available,
        )
    )
